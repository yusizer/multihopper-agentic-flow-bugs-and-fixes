"""Broadcast prepared transactions in strict order + poll confirmations.

Order: keeperFundingTx → routeInitTxs[] → orchestratorInitTx → sessionInitTxs[]
Each group must reach `confirmed` before the next. 3s delay after last
routeInitTx and after orchestratorInitTx (RPC propagation, esp. devnet).

Two-step confirm-broadcast:
  1. immediately after keeperFundingTx → confirm-broadcast(keeperFundingSignature, routeInitSignatures:[])
  2. after all remaining → confirm-broadcast(all remaining sigs)

Resume: if blockhash expired / broadcast failed mid-way → re-/prepare with new
Idempotency-Key; null fields = already confirmed, skip.
"""
import base64, time, requests

CONFIRM_TIMEOUT_S = 60   # ~blockhash lifetime
POLL_INTERVAL_S = 5
PROPAGATION_DELAY_S = 3

def _send(rpc_url, tx_b64, retries=4, skip_preflight=False):
    body = ({"jsonrpc": "2.0", "id": 1, "method": "sendTransaction",
             "params": [tx_b64, {"encoding": "base64", "skipPreflight": skip_preflight}]})
    last = None
    for i in range(retries):
        r = requests.post(rpc_url, json=body, timeout=30)
        out = r.json()
        if "error" not in out:
            return out["result"]  # signature
        last = out["error"]
        # transient RPC errors (blockhash not found / simulation / -32002) → retry after brief wait
        time.sleep(3)
    raise RuntimeError(f"sendTransaction error: {last}")

def _status(rpc_url, sig):
    body = ({"jsonrpc": "2.0", "id": 1, "method": "getSignatureStatuses",
             "params": [[sig]]})
    r = requests.post(rpc_url, json=body, timeout=30)
    val = r.json()["result"]["value"][0]
    return val

def broadcast_and_confirm(rpc_url, tx_b64, logger=print, skip_preflight=False):
    """Send tx, poll until confirmed/finalized (or timeout). Returns signature.

    Finding F5: the official Python example returns the sig after a 60s timeout
    WITHOUT confirmation, then calls confirm-broadcast → silent stall. We do
    NOT do that here; on timeout we raise so the caller can re-/prepare.
    """
    sig = _send(rpc_url, tx_b64, skip_preflight=skip_preflight)
    logger(f"[bc] sent sig={sig}")
    deadline = time.time() + CONFIRM_TIMEOUT_S
    while time.time() < deadline:
        st = _status(rpc_url, sig)
        if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
            logger(f"[bc] confirmed={st.get('confirmationStatus')}")
            return sig
        time.sleep(POLL_INTERVAL_S)
    # Do NOT return sig unconfirmed (that is the F5 bug). Raise.
    raise TimeoutError(f"tx {sig} not confirmed within {CONFIRM_TIMEOUT_S}s")

def broadcast_signed_txs(prepared_signed, client, transfer_id, rpc_url, logger=print):
    """Strict-order broadcast + two-step confirm-broadcast. Returns sigs dict."""
    sigs = {"routeInitSignatures": [], "sessionInitSignatures": []}

    # 1) keeperFundingTx → confirm-broadcast (intermediate)
    if prepared_signed.get("keeperFundingTx"):
        ksig = broadcast_and_confirm(rpc_url, prepared_signed["keeperFundingTx"], logger)
        sigs["keeperFundingSignature"] = ksig
        # intermediate call: protects against double-funding on resume
        client.confirm_broadcast(transfer_id, {
            "routeInitSignatures": [],
            "keeperFundingSignature": ksig,
        })
        logger(f"[bc] intermediate confirm-broadcast (keeperFunding) done")

    # 2) routeInitTxs[]
    r = prepared_signed.get("routeInitTxs") or []
    for i, x in enumerate(r):
        s = broadcast_and_confirm(rpc_url, x["base64"], logger)
        sigs["routeInitSignatures"].append(s)
        if i < len(r) - 1:
            time.sleep(PROPAGATION_DELAY_S)
    if r:
        time.sleep(PROPAGATION_DELAY_S)

    # 3) orchestratorInitTx
    if prepared_signed.get("orchestratorInitTx"):
        osig = broadcast_and_confirm(rpc_url, prepared_signed["orchestratorInitTx"], logger)
        sigs["orchestratorInitSignature"] = osig
        time.sleep(PROPAGATION_DELAY_S)

    # 4) sessionInitTxs[]
    s_ = prepared_signed.get("sessionInitTxs") or []
    for x in s_:
        sig = broadcast_and_confirm(rpc_url, x, logger)
        sigs["sessionInitSignatures"].append(sig)

    return sigs

def final_confirm(client, transfer_id, sigs, logger=print):
    """Step 2: final confirm-broadcast with all remaining signatures."""
    body = {
        "routeInitSignatures": sigs.get("routeInitSignatures", []),
        "sessionInitSignatures": sigs.get("sessionInitSignatures", []),
    }
    if sigs.get("keeperFundingSignature"):
        body["keeperFundingSignature"] = sigs["keeperFundingSignature"]
    if sigs.get("orchestratorInitSignature"):
        body["orchestratorInitSignature"] = sigs["orchestratorInitSignature"]
    res = client.confirm_broadcast(transfer_id, body)
    logger(f"[bc] final confirm-broadcast -> {res}")
    return res

def deploy_with_resume(client, transfer_id, keypair, rpc_url, max_attempts=3, logger=print):
    """Full deploy loop with re-/prepare resume on blockhash expiry."""
    from sign import sign_prepared_txs
    for attempt in range(1, max_attempts + 1):
        logger(f"[deploy] attempt {attempt}/{max_attempts}")
        prepared = client.prepare(transfer_id)
        pt = prepared.get("preparedTxs", prepared)
        # resume flags (finding: isoooiso — undocumented resume.*)
        resume = pt.get("resume") or {}
        if resume.get("nothingToDo"):
            logger("[deploy] nothingToDo — already deployed")
            return client.get(transfer_id)
        signed = sign_prepared_txs(pt, keypair)
        try:
            sigs = broadcast_signed_txs(signed, client, transfer_id, rpc_url, logger)
            return final_confirm(client, transfer_id, sigs, logger)
        except (TimeoutError, RuntimeError) as e:
            logger(f"[deploy] broadcast error, will re-prepare: {e}")
            continue
    raise RuntimeError("deploy failed after max attempts")
