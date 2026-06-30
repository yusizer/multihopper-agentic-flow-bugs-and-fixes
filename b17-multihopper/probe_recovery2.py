"""Deep recovery probe: rescue/prepare + rescue/confirm with fake sigs across stuck transfers."""
import json
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)

def show(label, fn):
    try:
        r = fn()
        print(f"\n=== {label} ===\n{json.dumps(r, indent=2, default=str)[:1500]}")
    except MultiHopperError as e:
        print(f"\n=== {label} ===\nERROR {e.code} ({e.status}): {e.message}\nbody: {json.dumps(e.body, default=str)[:400]}")

for tid in [476, 475]:
    try:
        t = client.get(tid)
        print(f"\n###### transfer {tid}: status={t.get('status')} phase={t.get('phase')} recovery={t.get('recovery')} lastError={t.get('lastError')}")
    except MultiHopperError as e:
        print(f"\n###### transfer {tid}: GET ERROR {e.code} ({e.status}): {e.message}")
        continue
    show(f"rescue/prepare {tid}", lambda tid=tid: client.rescue_prepare(tid))
    show(f"rescue/confirm {tid} fake-sigs", lambda tid=tid: client.rescue_confirm(tid, {"rescueSignatures": ["FakeSigBase58_0123456789"]}))
