# Demo video script (2–3 min)

Goal: show 3–4 high-impact findings reproduced on devnet with the harness.

## Setup frame (10s)
- "MultiHopper agentic flow bounty — devnet only, mh_test_ key, Python harness."
- Show terminal, `b17-multihopper/` repo, `.env` (redacted).

## Scene 1 — F1: stuck hops + rescue false promise (60s)
1. `python run_transfer.py` → create (id=N) → prepare → sign → broadcast → confirm-broadcast. All 5 txs confirmed on devnet.
2. `GET /transfers/N` → `status=active, phase=executing, hops=0/4, lastError=null, recovery=null`.
3. Wait/poll — hops never progress.
4. `POST /transfers/N/rescue/prepare` → initially `MH_081`; later `recovery.canRescue=true, rescuableLamports=0.111 SOL` + `rescueTxs`.
5. Sign + broadcast rescue tx → **confirmed on-chain** (sig shown).
6. `POST /transfers/N/rescue/confirm` → **MH_083 "Provided signatures do not match prepared bundle — RESCUE_TX_FAILED: InstructionError:[4,{Custom:3012}]"**.
7. Narrate: "`canRescue=true` is a false promise — `rescue_step` requires privileged admin authority; the integrator cannot self-rescue. Funds locked."

## Scene 2 — F13: webhook HMAC verifier broken (40s)
1. Show registered webhook (id=134) secret (bare hex, no `whsec_`).
2. Show a delivered event from `webhook.site` — headers: `x-mh-signature` (not `x-multihopper-signature`), `x-mh-event`.
3. `python probe_verify_hmac.py` → HMAC over **raw body** = match; over **parsed/canonical JSON** = **mismatch** for `quote_created`/`processing`.
4. Narrate: "the docs verifier uses `req.body` (parsed) → rejects every webhook; `timingSafeEqual` has no length guard → RangeError DoS."

## Scene 3 — F2: intermittent 500 + SQL leak (20s)
1. `python inspect_transfer.py N` → sometimes all GETs return 500 with `Failed query: select "api_keys"..."integrations"."webhook_url"...`.
2. Narrate: "intermittent 500 on every GET endpoint, leaking the ORM/SQL query and DB schema."

## Scene 4 — F16: amount consistency not validated (20s)
1. `python probe_edge.py` → `amountRaw=0.1 SOL, amountTokens=5.0` → **200 status=quote** (no validation).
2. Narrate: "agent can create a transfer where on-chain amount and displayed amount disagree — no error."

## Closing (10s)
- "17 findings (F1–F17), all reproduced on devnet with sanitized evidence. Repo + full report: <link>."

## Recording tips
- Use OBS / Windows Game Bar (Win+G) / Camtasia.
- 1280×720 min, clear terminal font.
- Redact API key / private key (the harness already avoids printing them).
- Save as `demo.mp4`, upload unlisted YouTube or Loom, link in submission.
