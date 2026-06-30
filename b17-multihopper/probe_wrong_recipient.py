"""Angle A deep: transfer to a random recipient with NO token account.
Expect: deploy succeeds, hops stuck (recipient ATA missing per route-lifecycle),
recovery=null, rescue=MH_081. Proves funds-locked-forever for stuck hops."""
import time, uuid, sys, json
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError
from sign import load_keypair
from broadcast import deploy_with_resume
from solders.keypair import Keypair as KP

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)
kp = load_keypair(config.SOLANA_PRIVATE_KEY)

recipient = str(KP().pubkey())  # random keypair → its pubkey has no token accounts
print(f"[setup] source={kp.pubkey()} recipient={recipient} (random, NO token account)")

external = f"b17-wrong-{int(time.time())}-{uuid.uuid4().hex[:6]}"
body = {
    "tokenMint": config.SOL_DEVNET_MINT, "amountRaw": "100000000", "amountTokens": "0.1",
    "tokenDecimals": 9, "tokenSymbol": "SOL", "sourceOwner": str(kp.pubkey()),
    "recipientWallet": recipient, "hops": 7, "arrivalSeconds": 300, "externalId": external,
}
created = client.create(body)
tr = created.get("transfer", created)
tid = tr["id"]
print(f"[create] id={tid} externalId={external}")

deploy_with_resume(client, tid, kp, config.RPC_URL)

final = client.poll_until_terminal(tid, interval=10, max_iter=30)
print(f"\n[final] {json.dumps(final, indent=2, default=str)[:1500]}")

try:
    rp = client.rescue_prepare(tid)
    print(f"[rescue/prepare] {json.dumps(rp, indent=2, default=str)[:600]}")
except MultiHopperError as e:
    print(f"[rescue/prepare] ERROR {e.code} ({e.status}): {e.message}")

with open(f"evidence/wrong_recipient_{tid}.json", "w") as f:
    json.dump({"id": tid, "externalId": external, "recipient": recipient, "final": final}, f, indent=2, default=str)
print(f"\nSaved evidence/wrong_recipient_{tid}.json")
