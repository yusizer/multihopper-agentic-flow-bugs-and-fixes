"""Probe recovery endpoints (angle A) on a stuck transfer."""
import sys, json
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 476

def show(label, fn):
    try:
        r = fn()
        print(f"\n=== {label} ===\n{json.dumps(r, indent=2, default=str)[:2000]}")
    except MultiHopperError as e:
        print(f"\n=== {label} ===\nERROR {e.code} ({e.status}): {e.message}\nbody: {json.dumps(e.body, default=str)[:500]}")

# current state
t = client.get(tid)
print(f"state: status={t.get('status')} phase={t.get('phase')} recovery={t.get('recovery')} lastError={t.get('lastError')}")

# rescue flow
show(f"POST /transfers/{tid}/rescue/prepare", lambda: client.rescue_prepare(tid))
# reclaim (no client method — manual)
show(f"POST /transfers/{tid}/rescue/confirm (empty)", lambda: client.rescue_confirm(tid, {}))
