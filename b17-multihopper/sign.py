"""Signing for MultiHopper prepared transactions.

CRITICAL rule: the server pre-signs VersionedTransactions with ephemeral
keypairs. We must ADD our signature to the correct slot in the existing
signatures array — NEVER overwrite the server's partial signatures.

Implements the Python slot-based approach (the correct one per cybergod-duck's
finding — the TS `tx.sign([keypair])` variant overwrites server sigs).

NOTE on finding P1 (verify on devnet): the agentic guide shows
`msg_bytes = bytes([0x80]) + bytes(tx.message)`. In solders, `bytes(MessageV0)`
MAY already start with the 0x80 version prefix → double prefix → invalid sig.
We detect and avoid the double prefix. See verify_signing_payload().
"""
import base64
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.transaction import Transaction as LegacyTransaction

def load_keypair(b58_priv: str) -> Keypair:
    from base58 import b58decode
    return Keypair.from_bytes(b58decode(b58_priv))

def verify_signing_payload(tx: VersionedTransaction):
    """P1 verification: does bytes(tx.message) already include 0x80 prefix?"""
    msg = bytes(tx.message)
    return {"first_byte": f"0x{msg[0]:02x}", "len": len(msg),
            "already_prefixed": msg[0] == 0x80}

def sign_versioned(tx_b64: str, keypair: Keypair) -> str:
    """Sign a VersionedTransaction (v0), preserving server partial signatures."""
    tx = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
    msg_bytes = bytes(tx.message)
    # Avoid double 0x80 prefix (finding P1). solders MessageV0 may already
    # serialize with the version prefix byte.
    if msg_bytes[0] != 0x80:
        msg_bytes = bytes([0x80]) + msg_bytes
    sig = keypair.sign_message(msg_bytes)
    sigs = list(tx.signatures)
    pubkeys = tx.message.account_keys
    idx = list(pubkeys).index(keypair.pubkey())
    sigs[idx] = sig
    new_tx = VersionedTransaction.populate(tx.message, sigs)
    return base64.b64encode(bytes(new_tx)).decode()

def sign_legacy(tx_b64: str, keypair: Keypair) -> str:
    """Sign a legacy Transaction (orchestratorInitTx) via partial_sign."""
    tx = LegacyTransaction.from_bytes(base64.b64decode(tx_b64))
    tx.partial_sign([keypair], tx.message.recent_blockhash)
    return base64.b64encode(bytes(tx)).decode()

def sign_prepared_txs(prepared: dict, keypair: Keypair) -> dict:
    """Sign all 4 groups; skip null/absent (already confirmed on-chain).

    Returns dict with same keys, signed base64 (or None if skipped).
    """
    out = {}
    # keeperFundingTx: plain base64 string
    k = prepared.get("keeperFundingTx")
    out["keeperFundingTx"] = sign_versioned(k, keypair) if k else None
    # routeInitTxs: list of {"base64": "..."}
    r = prepared.get("routeInitTxs")
    if r:
        out["routeInitTxs"] = [{"base64": sign_versioned(x["base64"], keypair)} for x in r]
    else:
        out["routeInitTxs"] = None
    # orchestratorInitTx: plain base64 (legacy)
    o = prepared.get("orchestratorInitTx")
    out["orchestratorInitTx"] = sign_legacy(o, keypair) if o else None
    # sessionInitTxs: list of plain base64 strings
    s = prepared.get("sessionInitTxs")
    if s:
        out["sessionInitTxs"] = [sign_versioned(x, keypair) for x in s]
    else:
        out["sessionInitTxs"] = None
    return out

def sigs_from_broadcast(prepared_signed: dict, broadcast_sigs: dict) -> dict:
    """Build confirm-broadcast body from broadcast results."""
    body = {
        "routeInitSignatures": broadcast_sigs.get("routeInitSignatures", []),
        "sessionInitSignatures": broadcast_sigs.get("sessionInitSignatures", []),
    }
    if broadcast_sigs.get("keeperFundingSignature"):
        body["keeperFundingSignature"] = broadcast_sigs["keeperFundingSignature"]
    if broadcast_sigs.get("orchestratorInitSignature"):
        body["orchestratorInitSignature"] = broadcast_sigs["orchestratorInitSignature"]
    return body
