# Break It Before Users Do — MultiHopper Agentic Flow Bugs & Fixes

**Bounty:** Break It Before Users Do: MultiHopper Agentic Flow Bugs & Fixes (Superteam Earn / MultiHopper / Enigma Fund)
**Environment:** MultiHopper devnet only (`https://devnet.multihopper.com/api/v1`, `mh_test_` API key, Solana devnet). No mainnet, no live funds.
**Contact:** @<YOUR_HANDLE> (Telegram / Twitter)
**Repo:** <LINK_TO_REPO>
**Demo video:** <LINK_TO_DEMO_VIDEO>

---

## Executive summary

Responsible testing of the MultiHopper agentic transfer flow on **devnet only** (`mh_test_` key, Solana devnet, no mainnet, no live funds). A reproducible Python harness drives the documented `create → prepare → sign/broadcast → confirm-broadcast → monitor` flow end-to-end, then probes recovery, webhook, MCP, fee, and validation surfaces.

**18 findings — all reproduced on devnet or confirmed in docs; all unique vs the 6 public competitor submissions (gieskuy5, isoooiso, Lucijano, cybergod-duck, greendhy, 0xNickdev).**

| # | Severity | Title |
|---|---|---|
| F1 | **Critical** | Stuck hops: `canRescue=true` is a false promise; rescue tx fails on-chain (Custom 3012) + MH_083; integrator cannot self-rescue → funds locked |
| F2 | **High** | Intermittent HTTP 500 on all GET endpoints with SQL/ORM query leak (DB schema disclosure + reliability) |
| F3 | Med | `GET /transfers/:id` signatures omit `keeperFundingSignature`/`orchestratorInitSignature` |
| F4 | Med | `hops` semantics inconsistent across API (7 vs `hopsTotal` 5/4 vs `totalSteps`) |
| F5 | Med | Rescue endpoints undocumented; `rescue_step` authority/timelock unknown |
| F6 | Med | `mh_test_` key minted on production dashboard works against mainnet (prefix ≠ cluster) |
| F7 | Med | Screening fee present in `estimate.sol.breakdown` but docs say "not in /estimate" → double-count risk |
| F8 | Med | MCP server exposes only 2 docs-tools, not the API-step tools the agentic guide describes |
| F9 | Med | Recipient ATA precondition absent from the agentic integration guide |
| F10 | Low | API `phase` enum vs `route-lifecycle` stages mismatch |
| F11 | Low | `arrivalSeconds` minimum formula (`hops × 20s`) only in dashboard/error, not API docs |
| F12 | Med | Webhook secret returned without the documented `whsec_` prefix |
| F13 | **High** | Webhook HMAC verifier broken: server signs raw body, docs example verifies parsed JSON (rejects all); `timingSafeEqual` lacks length guard (RangeError DoS) |
| F14 | Med | Webhook signature header `x-mh-signature` ≠ documented `x-multihopper-signature` |
| F15 | Med | Webhook payload undocumented, no `eventId`/dedupe (at-least-once retry → double-process) |
| F16 | **High** | `amountRaw`/`amountTokens`/`tokenDecimals` consistency not validated (mismatch → 200) |
| F17 | Med | Validation errors return `BAD_REQUEST`, not documented `MH_011`/`MH_013`; `MH_016` undocumented |
| F18 | **High** | All hops complete but transfer never settles; no API `unwrap`/`settle` endpoint (happy-path fund-lock) |

**Highest impact:** F1 + F18 are fund-safety defects where the happy path locks funds with no integrator-driven recovery. F2 is information disclosure + reliability. F13/F14 break the documented webhook integration. F8 contradicts the sponsor-highlighted MCP surface.

**Differentiators:** legit devnet (`mh_test_`) + reproducible harness (`run_transfer.py` + per-finding probes) + demo video + 18 unique findings that avoid every occupied area.

---

## What we built

A reproducible Python agent harness that drives the documented agentic transfer
flow end-to-end on MultiHopper devnet, plus targeted probes for recovery,
webhook, MCP, and fee-surface bugs.

- **Language/framework:** Python 3.11, `solders` 0.27.1, `base58`, `requests`.
- **Flow implemented:** `POST /transfers` → `POST /transfers/:id/prepare` →
  client-side slot-based signing of Versioned v0 tx (preserving server ephemeral
  partial signatures) + legacy `partial_sign` for orchestrator → strict-order
  broadcast (`keeperFundingTx` → `routeInitTxs` → `orchestratorInitTx` →
  `sessionInitTxs`, wait-for-confirmed, 3s propagation delays) → two-step
  `POST /transfers/:id/confirm-broadcast` → `GET /transfers/:id` poll.
- **Resume support:** re-`/prepare` on blockhash expiry, skip `null` groups,
  respect `resume.nothingToDo` / `routeAlreadyDeployed`.
- **Signing wallet:** devnet keypair `FVBk7NDMnzBXEZJQ5U4HZp9nVQYjPUzuyxv76JAK8EK5` (test funds only).
- **Repro:** `python run_transfer.py` (happy path) and per-finding probes
  (`probe_recovery*.py`, `probe_webhook.py`, `probe_wrong_recipient.py`,
  `probe_500.py`). All exit-coded; sanitized logs in `evidence/`.

## Method

1. Reviewed all 19 doc pages + `llms.txt` + agentic integration guide + MCP server guide.
2. Built the harness against the documented contract; ran happy path on devnet.
3. Drove edge/failure paths (stuck transfers, rescue, wrong recipient, intermittent 500s).
4. Cross-checked API responses against docs (signatures, fees, phases, events, MCP tools).

---

## Findings

### F1 — Stuck hops: `canRescue=true` is a false promise; rescue tx fails on-chain (Custom 3012) + MH_083; integrator cannot self-rescue
**Severity: Critical (fund safety / agentic reliability)**

**Affected flow:** `GET /transfers/:id` monitoring + `POST /transfers/:id/rescue/prepare` + `/rescue/confirm` recovery.

**Repro (devnet, transfer 476):**
1. `POST /transfers` (SOL, 0.1, hops=7, arrivalSeconds=300, recipient=self) → id=476.
2. `POST /transfers/476/prepare` → 4 tx groups; sign+broadcast all in strict order; all 5 txs confirmed on-chain (keeperFunding + 2 routeInit + orchestrator + session); `confirm-broadcast` ×2.
3. `GET /transfers/476` for >30 min: `status=active`, `phase=executing`, `progress.hopsCompleted=0/5`, `lastError=null`, `expiresAt` passed.
4. **Initially** `recovery=null` and `rescue/prepare` → **409 `MH_081` "Nothing to rescue"**.
5. **After time** (no agent action), `recovery` becomes `{canRescue: true, rescuableLamports: 111316960, rescuableAccounts: [orchestrator_config + 5× step_state], canReclaimRent: false}` and `rescue/prepare` returns `rescueTxs:[1 tx]` + `rescuable.totalLamports: 111316960` (0.111 SOL).
6. Sign the rescue tx (slot-based, sourceOwner keypair) + broadcast → **confirmed on-chain**, sig `2kpxgXqPi1mksZYbQgw3jdcPjhX3FbFjsAp3NcCj1yWTArbtKtS1ZT77G1evBydqhE99qxDVhqVz969GQC61ye46`.
7. `POST /transfers/476/rescue/confirm` → **400 `MH_083` "Provided signatures do not match prepared bundle — RESCUE_TX_FAILED: … InstructionError:[4,{Custom:3012}]"**.

**Evidence:** `evidence/probe_476_full.txt`, `evidence/rescue_476.json`, devnet tx sigs above + rescue sig `2kpxgXqPi1mksZYbQgw3jdcPjhX3FbFjsAp3NcCj1yWTArbtKtS1ZT77G1evBydqhE99qxDVhqVz969GQC61ye46`.

**Root cause:** `concepts/keepers` states `rescue_step` is an "admin escape hatch … requires privileged authority." The API exposes `/rescue/prepare`+`/rescue/confirm` to the integrator and `recovery.canRescue=true` suggests funds are rescuable, but the on-chain `rescue_step` instruction rejects the sourceOwner-signed rescue tx with **Custom 3012 (Anchor `AccountNotInitialized` — "The program expected this account to be already initialized")**, `InstructionError:[4,{Custom:3012}]`, after which `rescue/confirm` returns MH_083. The rescue authority account/signer is not available to the integrator — only MultiHopper's privileged/admin key can rescue. (Custom 3012 and the on-chain error table are undocumented.)

**Impact (fund safety):** `canRescue=true` is a **false promise**. An agent that follows the recovery path (prepare → sign → broadcast → confirm) gets a confirmed on-chain tx that fails with Custom 3012, then MH_083. Funds (0.111 SOL here: principal + wrapper backing + rent across orchestrator_config + 5 step_state accounts) remain locked with no integrator-driven recovery. Combined with `protocol/route-lifecycle` "Routes do not expire" and no hop-level refund, stuck hops = permanent fund lock for the integrator.

**Additional issues surfaced:**
- `recovery` is populated while `phase=executing`, contradicting `api-reference/transfers/get` which says recovery is "only populated when phase is recoverable/settled/rescued/reclaimed."
- Rescue availability is time-gated and opaque: `MH_081` first, then `canRescue=true` later — the agent cannot tell when rescue becomes available.
- The rescue tx's blockhash fails RPC simulation ("Blockhash not found") and only broadcasts with `skipPreflight=true`, which is undocumented.
- Custom 3012 and the on-chain error-code table are entirely undocumented.

**Proposed fix:**
- Either make `rescue_step` permissionless/creator-signed (so `canRescue=true` is actually usable by the integrator), or stop returning `canRescue=true` + `rescueTxs` to integrators who cannot sign it.
- Document `rescue_step` authority, the Custom 3012 error code, and the full on-chain error table.
- Populate `recovery` consistently with the documented phase set (or update the docs).
- Document the rescue-availability timing and the `skipPreflight` requirement.

---

### F2 — Intermittent HTTP 500 on all GET endpoints with SQL query leak
**Severity: High (reliability + information disclosure)**

**Affected flow:** `GET /transfers/:id`, `GET /transfers/by-external/:id`, `GET /transfers`, `GET /usage`.

**Repro (devnet):**
1. Issue any GET with a valid `mh_test_` key.
2. Intermittently the server returns:
```
HTTP 500
{"statusCode":500,"error":"Internal Server Error","message":"Failed query: select \"api_keys\".\"id\",\"api_keys\".\"integration_id\",\"api_keys\".\"key_hash\",\"api_keys\".\"key_prefix\",\"api_keys\".\"mode\",\"api_keys\".\"label\",\"api_keys\".\"is_revoked\",\"api_keys\".\"revoked_at\",\"api_keys\".\"last_used_at\",\"api_keys\".\"created_at\",\"integrations\".\"id\",\"integrations\".\"user_id\",\"integrations\".\"name\",\"integrations\".\"webhook_url\",\"integrations\".\"rew..."}
```
3. Re-running the same request seconds later succeeds (20/20 OK on re-probe).

**Evidence:** first `inspect_transfer.py` run captured simultaneous 500 on all
four GET endpoints with the leaked ORM/SQL query; `evidence/probe_476_full.txt`
for the recovered 200 responses; `probe_500.py` (20× re-probe = 0/20, confirming
intermittent).

**Impact:**
- **Information disclosure:** the error message leaks the internal DB schema and
  ORM query (`api_keys`, `integrations`, `webhook_url`, `key_hash`, `mode`,
  `is_revoked`, …). Useful for an attacker profiling the auth/integration model.
- **Reliability:** an agent polling `GET /transfers/:id` for terminal state can
  receive 500 instead of `completed`/`failed` and must distinguish a transient
  500 from a real failure. No `MH_XXX` code, no `requestId` (unlike MH_XXX
  errors which now include `requestId`).
- **Error-format inconsistency:** 500 uses Fastify's flat
  `{statusCode,error,message}` shape, not the documented `{error:{code,message}}`
  envelope — clients that parse `error.code` crash (our client did:
  `AttributeError: 'str' object has no attribute 'get'`).

**Proposed fix:**
- Never leak SQL/ORM text in error messages; return a generic `MH_091` (503) or
  `MH_090` (500) with `requestId`, no internal query text.
- Fix the upstream DB query (likely the api_keys↔integrations join) that fails
  under load.
- Return the documented `{error:{code,message,requestId}}` envelope for *all*
  errors, including 500s.

---

### F3 — `GET /transfers/:id` signatures omit `keeperFundingSignature` and `orchestratorInitSignature`
**Severity: Medium (agentic observability)**

**Affected flow:** status monitoring after `confirm-broadcast`.

**Repro (devnet, transfer 476):** after a full deploy where `keeperFundingTx`
and `orchestratorInitTx` were broadcast and confirmed on-chain and their
signatures submitted via `confirm-broadcast`, `GET /transfers/476` returns:
```json
"signatures": { "routeInit": ["3ShSCD5..."], "sessionInit": [], "hops": [] }
```
Neither `keeperFundingSignature` nor `orchestratorInitSignature` is present,
even though `confirm-broadcast` requires `keeperFundingSignature` (MH_039 if
missing) and accepts `orchestratorInitSignature`.

**Docs:** `api-reference/transfers/get` documents `signatures` as containing
only `routeInit`, `sessionInit`, `hops`.

**Impact:** An agent cannot verify from `GET` that the keeper funding and
orchestrator init were recorded. If the intermediate `confirm-broadcast` (the
double-funding-protection step) silently no-oped, the agent has no signal. Also
`routeInit` shows 1 signature though 2 `routeInitTxs` were broadcast — the
recorded set is incomplete relative to on-chain reality.

**Proposed fix:** Include `keeperFundingSignature` and `orchestratorInitSignature`
in `GET /transfers/:id` `signatures`, and ensure `routeInit`/`sessionInit`
arrays reflect all broadcast txs (or document why they may be subset).

---

### F4 — `hops` semantics are inconsistent across API surface
**Severity: Medium (agentic confusion)**

**Repro (devnet, transfer 476, requested `hops=7`):**
- `POST /transfers` body: `hops: 7` → response `hops: 7`.
- `GET /transfers/476`: `progress.hopsTotal: 5`.
- `POST /transfers/476/prepare` `resume`: `totalHops: 7`, `totalSteps: 5`,
  `completedStepIndices: [0,1,2,3,4]`.

**Impact:** An agent cannot predict how many hops will actually execute, how
many on-chain steps exist, or when `progress.hopsTotal/totalHops` will match the
requested `hops`. This breaks progress UIs, ETA math, and "are we done?" checks.
`totalSteps` (orchestrator deploy steps) vs `hopsTotal` (execute hops) vs
`hops` (requested abstraction) are three different numbers with no documented
relationship.

**Proposed fix:** Document the relationship (`hops` = requested abstraction,
`totalSteps` = orchestrator deploy steps, `progress.hopsTotal` = executable
hops) and make `progress.hopsTotal` equal the requested `hops` or explain the
delta.

---

### F5 — Rescue endpoints are undocumented; `rescue_step` authority/timelock unknown
**Severity: Medium (documentation blocker / trust model)**

**Repro (devnet):**
- `POST /transfers/476/rescue/prepare` → `MH_081` (409) "Nothing to rescue".
- `POST /transfers/476/rescue/confirm` with `{}` → `400` `BAD_REQUEST:
  rescueSignatures: Required` (note: code is the string `BAD_REQUEST`, not an
  `MH_XXX` code).
- `rescue/prepare` / `rescue/confirm` are **not** in `llms.txt` API index; no
  API-reference page exists.

**Docs:** `concepts/keepers` says `rescue_step` is an "admin escape hatch …
requires privileged authority" but does **not** specify who holds that
authority, whether a timelock applies, or whether an integrator can ever
self-rescue. `concepts/security` claims "funds are secured by program logic, not
by operator keys," which contradicts an admin-keyed rescue.

**Impact:** An agent cannot implement recovery from docs alone — the request
schema (`rescueSignatures`) had to be reverse-engineered from a validation
error. Worse, even with correct schema, `rescue_step` may require MultiHopper's
admin key, so integrator-driven rescue may be impossible — contradicting the
trustless positioning.

**Proposed fix:**
- Add an API-reference page for `/rescue/prepare` and `/rescue/confirm`
  (request/response, `MH_080`–`MH_083`, signing requirements).
- Document who holds `rescue_step` authority, whether a timelock exists, and
  whether integrators can self-rescue.
- Reconcile `concepts/security` "not by operator keys" with admin-keyed rescue.

---

### F6 — `mh_test_` API key can target mainnet (prefix ≠ cluster)
**Severity: Medium (unsafe assumption / misroute risk)**

**Docs (`concepts/environments`):** "a key is bound to the cluster of the
deployment that minted it — it is not switched by the key prefix." Production
issues both `mh_live_` and `mh_test_` keys; devnet issues only `mh_test_`.

**Impact:** An agent that infers "I'm on devnet because my key is `mh_test_`"
is wrong — a `mh_test_` key minted on the **production** dashboard works against
**mainnet** (real funds). The agentic guide's copyable `CLAUDE.md` block and
quickstart imply `mh_test_` = test, which can lead an agent to accidentally hit
mainnet with real value.

**Proposed fix:**
- Make the guide/quickstart explicit: prefix = accounting mode, **dashboard =
  cluster**; always set base URL explicitly per environment.
- Consider refusing `mh_test_` keys on the mainnet API (or emitting a loud
  warning) to prevent accidental real-fund usage from test-labeled keys.

---

### F7 — Screening fee present in `estimate.sol.breakdown` but docs say it is not
**Severity: Medium (double-count risk / doc contradiction)**

**Docs (`concepts/compliance`):** "In `/estimate`? No — you must add it on top
of the estimate yourself."

**Repro (devnet, `POST /transfers/estimate`, 0.1 SOL):**
```json
"sol": { "requiredSolUpFrontLamports": 185403092, "breakdown": {
  "routeInitRentLamports": 22223280, "orchestratorRentLamports": 18708480,
  "ataRentLamports": 3326880, "transactionFeesLamports": 50000,
  "screeningFeeLamports": 2000000, ... } }
```
`screeningFeeLamports: 2000000` (0.002 SOL) **is** in the breakdown.

**Impact:** An agent that follows the docs ("add 0.002 SOL on top of estimate")
will **double-fund** the screening fee, since `estimate` already includes it in
the breakdown (and possibly in `requiredSolUpFrontLamports`). Conversely, if the
breakdown is informational but not included in `requiredSolUpFrontLamports`, the
agent will underfund. The docs don't disambiguate.

**Proposed fix:** State explicitly whether `screeningFeeLamports` is included in
`requiredSolUpFrontLamports`; update `concepts/compliance` to match the actual
`estimate` response.

---

### F8 — MCP server does not expose the API-step tools the agentic guide describes
**Severity: Medium (documentation blocker / agent integration)**

**Docs (`guides/agentic-integration` MCP table):** lists `estimate_transfer`,
`create_transfer`, `prepare_transfer`, `sign_and_broadcast`, `confirm_broadcast`,
`get_transfer`, `list_transfers`, `prepare_rescue`, `confirm_rescue` as MCP tools.

**Real MCP server (`https://dev-docs.multihopper.com/mcp`, SSE, no auth):**
exposes only `search_multi_hopper` and `query_docs_filesystem_multi_hopper`
(both read-only documentation tools). None of the API-step tools exist.

**Impact:** An agent builder who wires the MultiHopper MCP server expecting to
drive transfers through MCP tools (as the guide implies) will find no such
tools — the MCP server is a docs search box, not an API wrapper. This is a
direct docs↔reality contradiction in the sponsor-highlighted MCP surface.

**Proposed fix:** Either (a) expose the API-step tools via MCP as documented, or
(b) correct the agentic guide to state the MCP server is documentation-only and
the API-step tools are to be implemented locally by the agent.

---

### F9 — Recipient ATA precondition is absent from the agentic integration guide
**Severity: Medium (documentation blocker)**

**Docs:** `protocol/route-lifecycle` failure case: "Recipient account missing —
the executor must ensure recipient token accounts exist before submitting.
Standard ATA creation applies." The agentic integration guide has zero mentions
of ATA creation.

**Impact:** An agent that deploys a route to a recipient without the required
token account will see the route stall in `executing` with `hopsCompleted=0`
and no error (see F1) — the exact stuck state we reproduced. The precondition
that would have prevented it is not in the guide the agent follows.

**Proposed fix:** Add an ATA-creation step to the agentic integration guide
before `confirm-broadcast` (or document that the keeper/protocol creates ATAs).

---

### F10 — API `phase` enum vs `route-lifecycle` doc stages mismatch
**Severity: Low (documentation)**

**Docs:** `api-reference/transfers/get` `phase` enum:
`quoted|deploying|executing|settled|failed|recoverable|rescued|reclaimed|expired`.
`protocol/route-lifecycle` describes four stages (Create/Deploy/Execute/Unwrap)
and explicitly says "Routes do not expire" — no `recoverable`/`expired` formal
phases.

**Impact:** An agent reasoning about phases from `route-lifecycle` will not
expect `recoverable`/`expired` and may mishandle them.

**Proposed fix:** Reconcile the phase enum across the lifecycle doc and the API
reference.

---

### F11 — `arrivalSeconds` minimum formula only in dashboard, not in API docs
**Severity: Low (documentation blocker)**

**Repro:** the provider-registration dashboard shows "Arrival Time (seconds)
Min: 140s (7 hops x 20s)". `api-reference/transfers/create` says only "Minimum:
60". `guides/agentic-integration` says "varies by hop count (MH_014)".

**Impact:** An agent that sets `arrivalSeconds=60` with `hops=7` gets `MH_014`
and cannot derive the minimum from the API docs — only from the dashboard UI.

**Proposed fix:** Document `arrivalSeconds` minimum = `hops × 20s` in the API
reference, and have `MH_014` return the required minimum in the error message.

---

### F12 — Webhook signing secret returned without the documented `whsec_` prefix
**Severity: Medium (documentation blocker / integration)**

**Repro (devnet):** `POST /api/v1/webhooks` with `{"url":"https://webhook.site/<uuid>","events":["transfer.completed","transfer.failed","transfer.recoverable","transfer.refunded"]}` returns:
```json
{"id":133,"url":"https://webhook.site/a772b5f5-...","secret":"ae8b2675191053bca52f0a84350763b590526da4c2d2dfb7e471882c8abe55b9","events":[...],"isActive":true,"createdAt":"2026-06-30T14:30:22.854Z"}
```
**Docs (`api-reference/webhooks`):** "secret: HMAC-SHA256 signing secret prefixed with `whsec_`." The returned secret is bare hex with **no `whsec_` prefix**.

**Impact:** An agent that follows the docs and prepends `whsec_` (or expects it) will compute HMAC with the wrong key and reject every webhook; an agent that strips a non-existent `whsec_` prefix will also mismatch. Additionally, `isActive:true` is returned without any URL reachability verification (the URL was a fresh, unverified webhook.site endpoint), so a mis-configured secret + unverified URL = a silently broken webhook pipeline that the integrator believes is healthy.

**Proposed fix:** Either prefix the secret with `whsec_` as documented, or update the docs to state the secret is bare hex. Verify webhook URL reachability before setting `isActive:true` (emit `MH_050` for unreachable URLs).

---

### F13 — Webhook HMAC verifier in docs is broken: server signs raw body but example verifies parsed JSON; timingSafeEqual lacks length guard
**Severity: High (security / integration)**

**Repro (devnet, real webhook delivery to webhook.site for transfer 479):** MultiHopper delivered 4 signed events (`quote_created`, `phase_changed` ×2, `processing`), each with header `x-mh-signature`. Verifying with the endpoint secret (bare hex, see F12):
- HMAC-SHA256 over the **raw body** → **matches** `x-mh-signature` for all 4 events.
- HMAC-SHA256 over **parsed-then-re-serialized JSON** (canonical, `sort_keys`) → **mismatches** for `quote_created` and `processing` (key order/content differs); matches only for the trivial `phase_changed` body.

**Docs (`api-reference/webhooks/events`):** verifier example `verifyWebhook(req.body, signature, whsec_secret)` with `createHmac('sha256', secret).update(payload).digest('hex')` and `crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))`.

**Bugs:**
1. The example passes `req.body` (a **parsed object** in Express). `.update(parsedObject)` stringifies to `[object Object]` (or, if a JSON middleware re-stringifies, to JSON with a different key order) → HMAC ≠ server signature → **every legitimate webhook is rejected**. The server signs the **raw request body**; the verifier must use `req.rawBody`, not `req.body`.
2. `crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))` has **no length check**. Node's `timingSafeEqual` throws `RangeError` when buffers differ in length. A malformed/short `x-mh-signature` crashes the handler (DoS per delivery) and exposes a timing oracle (crash vs no-crash).

**Evidence:** `evidence/webhook_events.json` (4 events with bodies + signatures).

**Impact:** An agent that copy-pastes the documented verifier either rejects every webhook (availability) or crashes on malformed signatures (DoS). The event-driven recovery path (see F1) is broken for the integrator.

**Proposed fix:** Verify HMAC over the **raw body**; document that explicitly. Add `if (a.length !== b.length) return false;` before `timingSafeEqual`. Fix the example to use `req.rawBody`.

---

### F14 — Webhook signature header is `x-mh-signature`, not the documented `x-multihopper-signature`
**Severity: Medium (documentation blocker / integration)**

**Repro (devnet):** delivered webhook headers include `x-mh-signature: 2156e337...` and `x-mh-event: transfer.quote_created`. **Docs (`api-reference/webhooks/events`):** "Header name: `x-multihopper-signature`."

**Impact:** An agent that reads `req.headers['x-multihopper-signature']` (as documented) gets `undefined` → either skips verification (insecure) or rejects the event. The actual headers are `x-mh-signature` (signature) and `x-mh-event` (event type, also undocumented).

**Proposed fix:** Update docs: signature header = `x-mh-signature`, event-type header = `x-mh-event`.

---

### F15 — Webhook payload shape is undocumented and lacks any event/idempotency identifier
**Severity: Medium (documentation blocker / reliability)**

**Repro (devnet, real payloads):**
- `transfer.quote_created`: `{status, createdAt, expiresAt, externalId, transferId, fundingStrategy, supportBundleId}`
- `transfer.processing`: `{status, amountRaw, tokenMint, updatedAt, externalId, transferId, previousStatus, supportBundleId}`
- `transfer.phase_changed`: `{at, phase, transferId}`

No `eventId`, no `deliveryId`, no sequence number, no retry flag.

**Docs:** no example payload, no field definitions, no dedupe guidance.

**Impact:** The retry schedule (5 attempts: 30s, 5m, 30m, 2h) is at-least-once. Without an `eventId`, an agent cannot deduplicate redeliveries → double-processing (e.g., double-credit on `transfer.completed`, double-rescue on `transfer.recoverable`). Different events also carry inconsistent fields (`at` vs `createdAt`/`updatedAt`; `phase_changed` has no `status`).

**Proposed fix:** Document the payload shape per event and add an `eventId` (+ delivery attempt count) for dedupe.

---

### F16 — `amountRaw`/`amountTokens`/`tokenDecimals` consistency is not validated
**Severity: High (fund safety / validation gap)**

**Repro (devnet, `POST /transfers`):**
- `amountRaw="100000000"` (0.1 SOL at decimals=9), `amountTokens="5.0"` (claims 5 SOL), `tokenDecimals=9` → **200 `status=quote`**, response preserves both `amountRaw=100000000` and `amountTokens=5.0`.
- `amountRaw="100000000"`, `amountTokens="0.1"`, `tokenDecimals=6` (raw would be 100 tokens at 6 decimals, but amountTokens says 0.1) → **200 `status=quote`**.

**Docs (`api-reference/transfers/create`):** "amountRaw is the base-unit integer string; amountTokens is the human-readable decimal representation. Together with tokenDecimals they should be consistent." No error code for inconsistency is documented (and none is returned).

**Impact:** An agent that assembles these fields from different sources (amountRaw from a ledger, amountTokens from a UI, decimals from a registry) can create a transfer where the on-chain amount (`amountRaw`) and the displayed amount (`amountTokens`) disagree, with no error. Downstream consumers trusting `amountTokens` will be wrong; actual moved funds follow `amountRaw`. Fund-safety-relevant validation gap.

**Proposed fix:** Validate `amountRaw == amountTokens × 10^tokenDecimals` and return a dedicated error on mismatch.

---

### F17 — Validation errors return generic `BAD_REQUEST`, not the documented `MH_011`/`MH_013`; `MH_016` is undocumented
**Severity: Medium (documentation / error-handling)**

**Repro (devnet, `POST /transfers`):**
- invalid `recipientWallet` → `400 BAD_REQUEST: recipientWallet: String must contain at least 32 character(s)` (docs say `MH_011`).
- `hops=2` → `400 BAD_REQUEST: hops: Number must be greater than or equal to 3` (docs say `MH_013`).
- `hops=11` → `400 BAD_REQUEST: hops: Number must be less than or equal to 10` (docs say `MH_013`).
- `arrivalSeconds=-5` → `400 BAD_REQUEST: arrivalSeconds: Number must be greater than or equal to 60` (docs say `MH_014` for hop-count minimum).
- `amountRaw="1"` → `400 MH_016: amountRaw must exceed totalFlatFeeLamports for SOL transfers (would yield non-positive hopAmount)` — **MH_016 is not in the documented error table** (docs list `MH_012` for "amount below minimum").
- `arrivalSeconds=60, hops=7` → `400 MH_014: "Arrival time below minimum for hop count — Minimum 140s for 7 hops (20s per hop)"` — the hop-count formula (`hops × 20s`) is only revealed in this error message, not in the API docs (see F11).

**Impact:** Agents that branch on `MH_011`/`MH_013` (as documented) miss format-validation errors (which arrive as `BAD_REQUEST` with a field-specific message). The error envelope is inconsistent: semantic errors use `{error:{code:"MH_XXX",message}}`, format errors use `{error:{code:"BAD_REQUEST",message:"field: rule"}}`. `MH_016` is undocumented and its message leaks internal logic ("exceed totalFlatFeeLamports", "non-positive hopAmount"). `MH_010` likewise leaks the pricing source ("No raydium pool").

**Proposed fix:** Return the documented `MH_011`/`MH_013` codes for wallet/hops validation (or update docs to say format errors are `BAD_REQUEST`). Document `MH_016`. Standardize the error envelope and avoid leaking internal field/PR names.

---

### F18 — All hops complete but transfer never settles; no API unwrap/settle endpoint
**Severity: High (fund safety / agentic reliability)**

**Repro (devnet, transfer 479):** full deploy (5 txs confirmed) + all 4 hops executed on-chain (`progress.hopsCompleted=4/4`, `signatures.hops` has 4 hop signatures), yet `GET /transfers/479` returns `status=active, phase=executing, completedAt=null, lastError=null, recovery=null` indefinitely. No terminal state is reached. (`expiresAt` has passed; `recovery` still null.)

**Docs (`protocol/route-lifecycle`):** "After the final hop, the last recipient submits `unwrap` (SPL) or `unwrap_sol` (SOL). The program burns wrapper tokens and releases original tokens from the vault. The route is then settled." The API reference has **no `unwrap`/`settle` endpoint**, and the agentic integration guide never mentions it.

**Impact:** Even when every hop executes successfully, the transfer does not reach `completed`/`settled` unless the final recipient separately submits an on-chain `unwrap` instruction — not exposed through the API and not in the agentic guide. An agent polling `GET /transfers/:id` for `completed` waits forever after `hops=N/N`; the principal remains locked in the vault (wrapper tokens minted, never burned). This is a second, distinct fund-lock failure mode alongside F1, and it occurs on the **happy path** (all hops succeed), not just edge cases.

**Proposed fix:** Expose an `unwrap`/`settle` API step (or have the keeper auto-unwrap for the recipient), and document that the recipient must call it after the final hop. Make `status=completed` reachable purely via the documented API flow.

---

## Notes / related work (not claimed by us)

The following were also observed on devnet but appear already reported by other
submitters (we do not claim priority): per-transfer `totalFlatFeeLamports=0` vs
`usage.totalFlatFeeEarned` non-zero (fee inconsistency); inconsistent error
envelope (`MH_XXX` nested vs `BAD_REQUEST` flat vs Fastify 500); create returns
`status=quote` not `awaiting_signature`; undocumented `resume.*` fields;
webhook event-list mismatch (9 vs 13 vs backend-accepted 12).

## Responsible testing

All testing was performed on MultiHopper devnet with a `mh_test_` key and devnet
test funds. No mainnet requests, no live funds, no disclosure of findings before
MultiHopper review. All logs in `evidence/` are sanitized (no private keys, seed
phrases, or API keys).
