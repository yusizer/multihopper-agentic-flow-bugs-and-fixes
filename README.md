# Break It Before Users Do — MultiHopper Agentic Flow Bugs & Fixes

Responsible testing of the MultiHopper agentic transfer flow on **devnet only**
(`https://devnet.multihopper.com/api/v1`, `mh_test_` API key, Solana devnet).
No mainnet, no live funds. All findings reproduced on devnet or confirmed in docs.

> **Status:** 18 findings (F1–F18) · 1 Critical · 5 High · 8 Medium · 4 Low.
> All unique vs the 6 public competitor submissions.
> Full report: [`b17-multihopper/findings/DRAFT.md`](b17-multihopper/findings/DRAFT.md)
> (also as [`SUBMISSION.html`](b17-multihopper/findings/SUBMISSION.html) /
> [`SUBMISSION.docx`](b17-multihopper/findings/SUBMISSION.docx) for Google Docs/Word import).

## TL;DR — highest-impact findings

| # | Severity | Finding |
|---|---|---|
| **F1** | Critical | Stuck hops: `recovery.canRescue=true` is a **false promise** — rescue tx confirms on-chain but `rescue_step` fails with **Custom 3012** and `rescue/confirm` returns **MH_083**. `rescue_step` requires privileged admin authority; the integrator **cannot self-rescue**. Funds locked forever. |
| **F18** | High | All hops complete (`hopsCompleted=N/N`) but the transfer **never settles** (`status=active, phase=executing, completedAt=null`) — there is **no API `unwrap`/`settle` endpoint**. Happy-path fund-lock. |
| **F2** | High | Intermittent **HTTP 500 on every GET endpoint** (`/transfers/:id`, `/by-external`, `/transfers`, `/usage`) with the **ORM/SQL query leaked** in the error message (`api_keys`, `integrations`, `webhook_url`…). Info disclosure + reliability. |
| **F13** | High | Webhook HMAC verifier in the docs is **broken**: the server signs the **raw body** but the example verifies **parsed JSON** (mismatches → rejects every webhook); `timingSafeEqual` has no length guard → RangeError DoS. |
| **F14** | Med | Webhook signature header is `x-mh-signature`, **not** the documented `x-multihopper-signature`. |
| **F16** | High | `amountRaw`/`amountTokens`/`tokenDecimals` **consistency is not validated** — `amountRaw=0.1 SOL` + `amountTokens=5.0` returns `200`. |
| **F8** | Med | Real MCP server exposes only 2 docs-tools, **not** the API-step tools the agentic guide describes. |

Full list with repro, evidence, and proposed fixes: [`DRAFT.md`](b17-multihopper/findings/DRAFT.md) § Findings.

## Repo layout

```
b17-multihopper/                 # Python reproducible harness + findings
  mh_client.py                   # REST client (create/prepare/confirm-broadcast/get/rescue/webhooks/usage) + MH_XXX handling
  sign.py                        # Versioned slot-based signing (preserves server partial sigs) + legacy partial_sign
  broadcast.py                   # Strict-order broadcast, poll confirmed, 3s delays, two-step confirm-broadcast, resume
  run_transfer.py                # Happy-path end-to-end (python run_transfer.py [existing_id])
  probe_recovery*.py             # F1/F5 rescue flow
  probe_rescue_execute.py        # F1 rescue sign+broadcast+confirm (reproduces Custom 3012 + MH_083)
  probe_webhook.py               # F12/F14 webhook registration
  probe_verify_hmac.py           # F13 HMAC verification (raw vs parsed)
  probe_edge.py                  # F16/F17 validation edge cases
  probe_500.py                   # F2 intermittent 500 probe
  inspect_transfer.py            # GET/by-external/list/usage/estimate inspector
  findings/DRAFT.md              # full report (18 findings)
  findings/SUBMISSION.html/.docx # import-ready for Google Docs/Word
  evidence/                      # sanitized devnet logs (probe_476_full, rescue_476, webhook_events, edge_probe)
  .env.example                   # config template (NEVER commit .env)

b17-multihopper-video/           # Remotion demo video (1920×1080, ~152s)
  src/MultiHopperDemo.tsx        # 11-shot composition with real devnet evidence on screen
  docs/demo-voiceover.txt        # voiceover script
  out/multihopper-demo.mp4       # rendered video (with voiceover)
```

## Reproduce

```powershell
cd b17-multihopper
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cp .env.example .env   # fill MH_API_KEY (mh_test_...), SOLANA_PRIVATE_KEY, RPC_URL
.venv\Scripts\python.exe run_transfer.py            # happy path
.venv\Scripts\python.exe probe_rescue_execute.py 476 # F1 rescue false promise
.venv\Scripts\python.exe probe_verify_hmac.py        # F13 webhook HMAC
.venv\Scripts\python.exe probe_edge.py               # F16/F17 validation
.venv\Scripts\python.exe inspect_transfer.py 476     # F2 500 + state
```

All scripts guard against mainnet (`config.assert_test_env()` requires `devnet` in base URL + `mh_test_` prefix).

## Demo video

`b17-multihopper-video/out/multihopper-demo.mp4` — 11 shots: title → flow → happy deploy (real tx sigs) → stuck 476 → rescue false promise (MH_083/3012) → never-settles 479 → webhook HMAC mismatch → 500+SQL leak → amount mismatch → findings summary → final card.

Render with voiceover:
```powershell
cd b17-multihopper-video
npx remotion render MultiHopperDemo out/multihopper-demo.mp4 --concurrency=3
```

## Responsible testing

- Devnet only (`mh_test_` key, Solana devnet). No mainnet, no live user funds.
- No public disclosure before MultiHopper review.
- All logs sanitized — no private keys, seed phrases, or API keys in evidence or report.
- Submission in English.

## Contact

@<YOUR_HANDLE> — Telegram / Twitter
