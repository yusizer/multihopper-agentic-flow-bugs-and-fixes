"""Happy-path end-to-end MultiHopper transfer on DEVNET.

create → prepare → sign → broadcast (strict order) → confirm-broadcast ×2 → poll
"""
import time, uuid, sys
import config
from config import assert_test_env
from mh_client import MultiHopperClient
from sign import load_keypair, sign_prepared_txs, verify_signing_payload
from broadcast import deploy_with_resume
from solders.transaction import VersionedTransaction
import base64

def main():
    assert_test_env()
    if not config.SOLANA_PRIVATE_KEY:
        sys.exit("SOLANA_PRIVATE_KEY not set")

    client = MultiHopperClient(config.API_BASE, config.API_KEY)
    kp = load_keypair(config.SOLANA_PRIVATE_KEY)
    print(f"[setup] wallet={kp.pubkey()} base={config.API_BASE}")

    existing = sys.argv[1] if len(sys.argv) > 1 else None
    if existing:
        tid = int(existing)
        print(f"[resume] reusing transfer id={tid} (skip create)")
    else:
        # 1) create
        external = f"b17-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        create_body = {
            "tokenMint": config.SOL_DEVNET_MINT,
            "amountRaw": "100000000",          # 0.1 SOL
            "amountTokens": "0.1",
            "tokenDecimals": 9,
            "tokenSymbol": "SOL",
            "sourceOwner": str(kp.pubkey()),
            "recipientWallet": str(kp.pubkey()),  # to self for happy path
            "hops": 7,
            "arrivalSeconds": 300,
            "externalId": external,
        }
        created = client.create(create_body)
        tr = created.get("transfer", created)
        tid = tr["id"]
        print(f"[create] id={tid} status={tr.get('status')} externalId={external}")
        print(f"[create] expiresAt={tr.get('expiresAt')} supportBundle={tr.get('supportBundleId')}")

    # 2) prepare + P1 verification
    prepared = client.prepare(tid)
    pt = prepared.get("preparedTxs", prepared)
    print(f"[prepare] keys={list(pt.keys())} resume={pt.get('resume')}")
    if pt.get("keeperFundingTx"):
        tx = VersionedTransaction.from_bytes(base64.b64decode(pt["keeperFundingTx"]))
        print(f"[P1-verify] signing payload: {verify_signing_payload(tx)}")

    # 3) sign + 4) broadcast + confirm
    deploy_with_resume(client, tid, kp, config.RPC_URL)

    # 5) poll
    final = client.poll_until_terminal(tid, interval=5, max_iter=120)
    print(f"[final] status={final.get('status')} phase={final.get('phase')}")
    if final.get("status") != "completed":
        print(f"[final] NOT completed — lastError={final.get('lastError')} recovery={final.get('recovery')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
