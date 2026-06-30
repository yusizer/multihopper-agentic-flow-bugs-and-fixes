"""Edge-case validation probe: test API validation gaps (N5 amount consistency, MH_014/010/011/013/012/070)."""
import time, json, requests
import config
from config import assert_test_env
from mh_client import MultiHopperClient

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)

def show(label, body, idem=True):
    headers = client._headers(idempotency=idem) if idem else {"x-api-key": client.api_key, "Content-Type": "application/json"}
    try:
        r = requests.post(f"{config.API_BASE}/transfers", json=body, headers=headers, timeout=60)
        try:
            b = r.json()
        except ValueError:
            b = {"_raw": r.text}
        if r.status_code >= 400:
            err = b.get("error", {}) if isinstance(b, dict) else {}
            code = err.get("code", "HTTP_ERR") if isinstance(err, dict) else str(err)
            msg = err.get("message", r.text[:150]) if isinstance(err, dict) else str(err)
            print(f"[{label}] -> {r.status_code} {code}: {str(msg)[:110]}")
        else:
            tr = b.get("transfer", b)
            print(f"[{label}] -> 200 status={tr.get('status')} amountRaw={tr.get('amountRaw')} amountTokens={tr.get('amountTokens')} decimals={tr.get('tokenDecimals')} hops={tr.get('hops')} arrival={tr.get('arrivalSeconds')} recipient={tr.get('recipientWallet','')[:12]}")
    except Exception as e:
        print(f"[{label}] -> EXC {e}")

t = int(time.time())
base = {"tokenMint": config.SOL_DEVNET_MINT, "sourceOwner": config.SOURCE_WALLET, "recipientWallet": config.SOURCE_WALLET, "hops": 7, "arrivalSeconds": 300}

show("amount mismatch (raw=0.1 SOL, tokens=5.0)", {**base, "amountRaw": "100000000", "amountTokens": "5.0", "tokenDecimals": 9, "tokenSymbol": "SOL", "externalId": f"edge-amt-{t}"})
show("arrivalSeconds=60 hops=7 (min 140)", {**base, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "tokenSymbol": "SOL", "arrivalSeconds": 60, "externalId": f"edge-arr-{t}"})
show("unsupported mint (1111...)", {**base, "tokenMint": "11111111111111111111111111111111", "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "externalId": f"edge-mint-{t}"})
show("invalid recipient wallet", {**base, "recipientWallet": "invalid_pubkey_xx", "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "externalId": f"edge-wallet-{t}"})
show("hops=2 (min 3)", {**base, "hops": 2, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "externalId": f"edge-hops2-{t}"})
show("hops=11 (max 10)", {**base, "hops": 11, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "externalId": f"edge-hops11-{t}"})
show("amount below min (1 lamport)", {**base, "amountRaw": "1", "amountTokens": "0.000000001", "tokenDecimals": 9, "externalId": f"edge-min-{t}"})
show("missing Idempotency-Key", {**base, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "externalId": f"edge-nokey-{t}"}, idem=False)
show("decimals=6 but raw=100000000 (0.1 SOL)", {**base, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 6, "externalId": f"edge-dec-{t}"})
show("negative arrivalSeconds", {**base, "amountRaw": "100000000", "amountTokens": "0.1", "tokenDecimals": 9, "arrivalSeconds": -5, "externalId": f"edge-negarr-{t}"})
