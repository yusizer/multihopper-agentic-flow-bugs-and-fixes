# B17 — MultiHopper Agentic Flow Bugs & Fixes

Responsible testing harness for the Superteam Earn bounty
"Break It Before Users Do: MultiHopper Agentic Flow Bugs & Fixes"
(sponsor: MultiHopper / Enigma Fund). 1000 USDC = 4×250.

> **Scope:** test environment / devnet ONLY. `mh_test_` API key. No mainnet,
> no live user funds. Do not publish findings before MultiHopper review.
> Sanitized logs only — never log private keys / seed phrases / API keys.

## Goal
Reproduce the documented agentic transfer flow on devnet, uncover real bugs
in API usage / agentic workflows, and propose concrete fixes. Submission =
Google Doc / Notion (English) + demo video + this repo.

## Flow under test
`POST /transfers` → `POST /transfers/:id/prepare` → client sign+broadcast
(4 tx groups, strict order) → `POST /transfers/:id/confirm-broadcast` ×2 →
`GET /transfers/:id` poll.

4 tx groups: `keeperFundingTx` (v0, 1st) → `routeInitTxs[]` (v0, server
pre-signed) → `orchestratorInitTx` (legacy) → `sessionInitTxs[]` (v0, server
pre-signed). Server pre-signs v0 with ephemeral keys → we ADD our sig to the
correct slot, never overwrite. `null` = already confirmed, skip.

## Stack
Python + `solders` + `base58` + `requests`. Devnet RPC.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# fill .env: MH_API_KEY (mh_test_...), SOLANA_PRIVATE_KEY (base58), RPC_URL
python run_transfer.py   # happy-path end-to-end on devnet
```

## Layout
- `mh_client.py` — REST API client (create/prepare/confirm-broadcast/get/list/estimate/rescue/webhooks/usage) + MH_XXX error handling.
- `sign.py` — Versioned (slot-based, preserves server partial sigs) + Legacy signing.
- `broadcast.py` — strict-order broadcast, poll confirmed, 3s delays, resume.
- `run_transfer.py` — happy-path end-to-end.
- `probe_*.py` — per-finding repro scripts (recovery, webhook, HMAC, wrong recipient, 500, edge, inspect).
- `convert_submission.py` — DRAFT.md → SUBMISSION.html + SUBMISSION.docx converter.
- `evidence/` — sanitized logs, tx sigs, screenshots.
- `findings/` — report drafts.

## Testing angles (free niches)
- **A Recovery** (MH_080-083): stuck transfers, rescue, rent-reclaim.
- **B Webhook security**: HMAC (raw vs parsed), timingSafeEqual length, replay/dedupe.
- **C MCP server**: tool defs, validation, error mapping, idempotency on MCP layer.
- **D non-SOL / fees**: estimate vs prepare fee drift, SPL/Token-2022, screening fee.
- **E doc/on-chain**: PDA seeds, key≠env, confirm timeout, by-external, GET signatures.

See memory `b17-bug-candidates` for the full deduped list and devnet verification steps.

## Status
- [x] Phase 0: research + plan + onboarding (devnet `mh_test_` key obtained via dashboard)
- [x] Phase 1: harness happy path (run_transfer.py, 5 txs confirmed on devnet)
- [x] Phase 2: systematic testing (angles A→E, 18 findings F1–F18, evidence/ captured)
- [x] Phase 3: demo video (https://youtu.be/roKjio6PHi8, 152s, voiceover + captions)
- [x] Phase 4: write-up (findings/DRAFT.md, SUBMISSION.docx, public Google Doc report)
- [ ] Phase 5: submit (deadline 2026-07-10)
