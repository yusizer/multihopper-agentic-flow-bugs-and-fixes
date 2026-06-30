"""Probe intermittent 500s on GET /transfers/:id. Run N times, count 500s."""
import sys, time
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 476
n = int(sys.argv[2]) if len(sys.argv) > 2 else 20

ok = err500 = other = 0
samples = []
for i in range(n):
    try:
        r = client.get(tid)
        ok += 1
        print(f"[{i:02d}] OK  status={r.get('status')} phase={r.get('phase')} hops={r.get('progress',{}).get('hopsCompleted')}/{r.get('progress',{}).get('hopsTotal')}")
    except MultiHopperError as e:
        if e.status == 500:
            err500 += 1
            if len(samples) < 2:
                samples.append(e.body)
            print(f"[{i:02d}] 500 {str(e.message)[:100]}")
        else:
            other += 1
            print(f"[{i:02d}] {e.status} {e.code}: {str(e.message)[:80]}")
    time.sleep(0.5)

print(f"\nSUMMARY: ok={ok} 500={err500} other={other} of {n}")
if samples:
    import json
    print("\n500 sample body:")
    print(json.dumps(samples[0], default=str)[:800])
