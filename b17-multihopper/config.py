"""Config loader — DEVNET ONLY. Never commit .env."""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

API_BASE = os.getenv("MH_API_BASE", "https://devnet.multihopper.com/api/v1").rstrip("/")
API_KEY = os.getenv("MH_API_KEY") or ""
SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY") or ""
RPC_URL = os.getenv("RPC_URL", "https://api.devnet.solana.com")
SOURCE_WALLET = os.getenv("SOURCE_WALLET", "").strip()

# Optional SPL for angle D
SPL_MINT = os.getenv("SPL_MINT", "").strip()
SPL_DECIMALS = int(os.getenv("SPL_DECIMALS", "6"))

# Webhook receiver (angle B)
WEBHOOK_PUBLIC_URL = os.getenv("WEBHOOK_PUBLIC_URL", "").strip()
WEBHOOK_RECEIVER_PORT = int(os.getenv("WEBHOOK_RECEIVER_PORT", "8765"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Well-known devnet mints
SOL_DEVNET_MINT = "So11111111111111111111111111111111111111112"

def assert_test_env():
    """Hard guard: refuse to run against mainnet / live keys."""
    if "devnet" not in API_BASE:
        raise SystemExit(f"SAFETY: API_BASE is not devnet ({API_BASE}). Aborting.")
    if not API_KEY.startswith("mh_test_"):
        raise SystemExit(f"SAFETY: API key is not mh_test_ prefix. Aborting.")
