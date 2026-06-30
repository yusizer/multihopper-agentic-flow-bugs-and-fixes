"""Probe a transfer across endpoints: GET, list, by-external. Robust to errors."""
import json, sys
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 476
ext = sys.argv[2] if len(sys.argv) > 2 else None

def show(label, fn):
    try:
        r = fn()
        print(f"\n=== {label} ===\n{json.dumps(r, indent=2, default=str)[:3000]}")
    except MultiHopperError as e:
        print(f"\n=== {label} ===\nERROR {e.code} ({e.status}): {e.message}\nbody: {json.dumps(e.body, default=str)[:500]}")

show(f"GET /transfers/{tid}", lambda: client.get(tid))
show(f"GET /transfers/by-external/{ext}", lambda: client.get_by_external(ext)) if ext else None
show("GET /transfers (list, status=active)", lambda: client.list({"status": "active", "limit": 20}))
show("GET /transfers (list, all recent)", lambda: client.list({"limit": 10}))
show("GET /usage", lambda: client.usage())
show("POST /transfers/estimate (auth probe)", lambda: client.estimate({
    "tokenMint": config.SOL_DEVNET_MINT, "amountRaw": "100000000",
    "tokenDecimals": 9, "hops": 7,
}))
