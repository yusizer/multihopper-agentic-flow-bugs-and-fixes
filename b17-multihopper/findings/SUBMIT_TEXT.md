# Submit text — for the Superteam Earn submission form

## Title
Break It Before Users Do — MultiHopper Agentic Flow Bugs & Fixes (18 devnet-reproduced findings)

## Summary (for the form)
Responsible testing of the MultiHopper agentic transfer flow on **devnet only**
(`mh_test_` key, Solana devnet). A reproducible Python harness drives the
documented `create → prepare → sign/broadcast → confirm-broadcast → monitor`
flow end-to-end, plus targeted probes for recovery, webhook, MCP, fee, and
validation surfaces. **18 unique findings** (1 Critical, 5 High, 8 Medium, 4 Low),
all reproduced on devnet with real on-chain evidence, all unique vs the 6 public
competitor submissions. Demo video included.

## Links (fill in before submitting)
- **Report (Google Doc, public):** https://docs.google.com/document/d/1yHJicXhMUojyMv1e1pPa8h5E4vGemLTIDbaOXGQS3b4/edit?usp=sharing
- **Repo:** https://github.com/yusizer/multihopper-agentic-flow-bugs-and-fixes
- **Demo video:** https://youtu.be/ed5UGcI1SXg

## Top findings
- **F1 (Critical, fund-safety):** Stuck hops — `recovery.canRescue=true` is a
  false promise. The rescue tx confirms on-chain but `rescue_step` fails with
  **Custom 3012** and `rescue/confirm` returns **MH_083**. `rescue_step` requires
  privileged admin authority; the integrator **cannot self-rescue** → funds locked.
- **F18 (High, fund-safety):** All hops complete (`hopsCompleted=N/N`) but the
  transfer **never settles** — no API `unwrap`/`settle` endpoint. Happy-path fund-lock.
- **F2 (High):** Intermittent **HTTP 500 on every GET** with the ORM/SQL query
  leaked (DB schema disclosure + reliability).
- **F13 (High):** Webhook HMAC verifier broken — server signs **raw body**, docs
  example verifies **parsed JSON** (rejects all); `timingSafeEqual` no length guard.
- **F14 (Med):** Webhook header `x-mh-signature` ≠ documented `x-multihopper-signature`.
- **F16 (High):** `amountRaw`/`amountTokens`/`tokenDecimals` consistency not validated.
- **F8 (Med):** MCP server exposes only 2 docs-tools, not the API-step tools the guide describes.

## Method
Python 3.11 + `solders` 0.27.1. Harness implements slot-based Versioned signing
(preserves server ephemeral partial signatures), strict-order broadcast with
confirmation polling, two-step `confirm-broadcast`, and resume on blockhash
expiry. Per-finding probes (`probe_recovery*`, `probe_verify_hmac`,
`probe_edge`, `probe_500`, `inspect_transfer`) reproduce each issue with
sanitized logs in `evidence/`. Devnet only; `config.assert_test_env()` refuses
non-devnet bases / non-`mh_test_` keys.

## Differentiators
Legit devnet (`mh_test_`) + reproducible harness + demo video + 18 findings that
avoid every area already covered by public competitors (CORS, double-funding
race, blockhash budget, TS sign-overwrite, /funding/confirm mismatch, fee
inconsistency, status=quote, resume.*, webhook events 9-vs-13, webhook
URL-no-verification, payout.completed rejection).

## Responsible testing
Devnet only, no mainnet, no live funds. No public disclosure before MultiHopper
review. Sanitized evidence (no keys/seeds). Submission in English.

## Contact
@yusif102 — Telegram
