"""Execute full rescue flow with retry: prepare → sign → broadcast → confirm (re-prepare on blockhash expiry)."""
import sys, json, time, os
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError
from sign import load_keypair, sign_versioned
from broadcast import broadcast_and_confirm

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)
kp = load_keypair(config.SOLANA_PRIVATE_KEY)
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 476

t = client.get(tid)
print(f"[state] status={t.get('status')} phase={t.get('phase')} recovery={t.get('recovery')}")

last_rp = None
for attempt in range(1, 11):
    try:
        rp = client.rescue_prepare(tid)
    except MultiHopperError as e:
        print(f"[rescue/prepare] ERROR {e.code}: {e.message}")
        sys.exit(1)
    last_rp = rp
    rescue_txs = rp.get("rescueTxs", [])
    print(f"\n[attempt {attempt}] rescueTxs={len(rescue_txs)} blockhash={rp.get('recentBlockhash','')[:10]}")
    if not rescue_txs:
        print("[rescue] no rescueTxs — nothing to do")
        break
    try:
        sigs = []
        for i, rt in enumerate(rescue_txs):
            signed = sign_versioned(rt["base64"], kp)
            bsig = broadcast_and_confirm(config.RPC_URL, signed, skip_preflight=(attempt >= 3))
            sigs.append(bsig)
            print(f"[rescue] broadcast [{i}] sig={bsig}")
        rc = client.rescue_confirm(tid, {"rescueSignatures": sigs})
        print(f"[rescue/confirm] {json.dumps(rc, indent=2, default=str)[:800]}")
        break
    except (TimeoutError, RuntimeError) as e:
        print(f"[rescue] attempt {attempt} broadcast error: {str(e)[:120]}; re-prepare")
        time.sleep(3)

time.sleep(3)
try:
    t2 = client.get(tid)
    print(f"\n[final] status={t2.get('status')} phase={t2.get('phase')} recovery={t2.get('recovery')}")
except MultiHopperError as e:
    t2 = {"error": f"{e.code}: {e.message}"}
    print(f"\n[final] GET ERROR {e.code}: {e.message}")

ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence", f"rescue_{tid}.json")
with open(ev, "w") as f:
    json.dump({"before": t, "rescue_prepare": last_rp, "after": t2}, f, indent=2, default=str)
print(f"Saved {ev}")
