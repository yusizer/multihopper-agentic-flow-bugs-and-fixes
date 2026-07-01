# b17-multihopper-video

Remotion composition for the MultiHopper "Break It Before Users Do" bounty demo
video (~152s, 1920×1080, 30fps, with voiceover + word-aligned captions). Built
with the same pipeline as `../casper3643-video` / `../agentledger-video`. All
on-screen signatures, error codes, and IDs are REAL devnet evidence from
`../b17-multihopper/evidence/` — nothing is invented.

## What's here

- `src/MultiHopperDemo.tsx` — 11-shot composition (title, agentic-flow diagram,
  7 terminal shots reproducing the real devnet findings, findings summary,
  final proof card) + word-by-word captions.
- `src/words.ts` — caption chunks (1-2 words). Auto-generated placeholder pacing
  now; word-accurate after the voiceover is recorded.
- `scripts/make_captions.py` — placeholder captions from `docs/demo-voiceover.txt`.
- `scripts/align_captions.py` — faster-whisper word-align (run AFTER voiceover).
- `scripts/make-voiceover-split.mjs` — split Yusif's recording into 10 segments.
- `docs/demo-voiceover.txt` — voiceover script (English, ~152s, ~140 wpm).
- `public/voiceover.mp3` — final voiceover (ElevenLabs "Josh" TTS, 150s).

## Real evidence shown on screen

- Transfer 476: `status=active`, `phase=executing`, `hopsCompleted=0/5`,
  `lastError=null`, `recovery=null`, `expiresAt` passed.
- Deploy tx sigs (confirmed on Solana devnet):
  - keeperFunding `4AkiNVwP…Upcw`
  - routeInit `3ShSCD5B…5wiH` + `jFWjhHDo…WRr`
  - orchestrator `2PwKVNUu…T75Y7`
  - session `4WwocT77…DrDA`
- Rescue: `canRescue=true`, `rescuableLamports=111316960` (0.111 SOL);
  rescue tx `2kpxgXqP…ye46` confirmed; `rescue/confirm` →
  `MH_083` `InstructionError:[4,{Custom:3012}]`.
- Transfer 479: `hopsCompleted=4/4`, `status=active`, `phase=executing`,
  `completedAt=null` — never settles (F18).
- Webhook: header `x-mh-signature` (NOT `x-multihopper-signature`);
  HMAC raw body = `2156e337…` (MATCH); HMAC parsed JSON = `11d7c500…` (MISMATCH);
  secret `b2d9430a…` (no `whsec_` prefix).
- 500 SQL leak: `Failed query: select "api_keys"."id",…,"integrations"."webhook_url",…`
- Amount mismatch: `amountRaw=100000000` + `amountTokens=5.0` → `200 status=quote`.
- Env: devnet, `https://devnet.multihopper.com/api/v1`, `mh_test_` key,
  wallet `FVBk7NDMnzBXEZJQ5U4HZp9nVQYjPUzuyxv76JAK8EK5`. API key + private key
  are NEVER printed (redacted).

## node_modules (junction — no separate npm install)

`node_modules` is a junction to the shared Remotion install in
`../githubbounty/agentledger-video/node_modules` (same Remotion 4.0.484 stack).

Create the junction from an elevated cmd (run as Administrator):

```cmd
cd C:\Users\yusif\Desktop\projects\githubbounty\01-solana-agents-skills\b17-multihopper-video
mklink /J node_modules ..\..\..\githubbounty\agentledger-video\node_modules
```

Or via PowerShell (no admin needed for a junction to a directory you own):

```powershell
cd C:\Users\yusif\Desktop\projects\githubbounty\01-solana-agents-skills\b17-multihopper-video
New-Item -ItemType Junction -Path node_modules -Target ..\..\..\githubbounty\agentledger-video\node_modules
```

If the junction cannot be created, run `npm install` inside this folder instead
(same deps as `package.json`).

## Render (voiceover + captions already wired — `HAS_VOICE = true`)

```powershell
cd b17-multihopper-video
npx remotion render MultiHopperDemo out/multihopper-demo.mp4 --concurrency=3
```

Output: `out/multihopper-demo.mp4` (~152s).

## Re-render after editing on-screen evidence

1. Record yourself reading `docs/demo-voiceover.txt` (one take, ~110s, ~140 wpm,
   pauses between the 10 paragraphs). Save as `public/voiceover-yusif.wav`
   (or .mp3/.m4a).
2. Split into segments + concat:
   ```powershell
   node scripts/make-voiceover-split.mjs   # -> public/voiceover.mp3
   ```
3. Word-align captions to the real audio (needs `faster-whisper`; GPU optional):
   ```powershell
   python scripts/align_captions.py        # overwrites src/words.ts
   ```
4. Enable audio in `src/MultiHopperDemo.tsx`: set `HAS_VOICE = true`.
5. Re-render:
   ```powershell
   npx remotion render MultiHopperDemo out/multihopper-demo.mp4 --concurrency=3
   ```

## Notes / honest caveats

- Terminal shots render the captured devnet evidence (real tx hashes / error
  codes from `../b17-multihopper/evidence/`), not a live screen recording.
- Voiceover is ElevenLabs TTS ("Josh"); captions are word-aligned via
  faster-whisper (`scripts/align_captions.py`).
- All testing was on MultiHopper devnet with a `mh_test_` key and devnet test
  funds — no mainnet, no live funds. API key and private key are redacted on
  screen.
