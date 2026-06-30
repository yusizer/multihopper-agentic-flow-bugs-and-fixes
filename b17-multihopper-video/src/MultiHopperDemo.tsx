import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { WORDS } from "./words";

// Voiceover: Yusif records against docs/demo-voiceover.txt -> public/voiceover.mp3.
// Until then the composition renders with word-by-word captions only (no audio).
// Drop the file in, set HAS_VOICE = true, re-run scripts/align_captions.py.
const VOICE = staticFile("voiceover.mp3");
const HAS_VOICE = true;

// MultiHopper palette: deep navy + Solana purple #9945FF / green #14F195 accent.
const BG = "#07080d";
const ACCENT = "#9945FF"; // Solana purple
const ACCENT2 = "#14F195"; // Solana green
const RED = "#ff5470"; // error / critical
const AMBER = "#fbbf24"; // warning
const MUTED = "#64748b";
const LINE = "rgba(255,255,255,0.10)";

const FONT = '"Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif';
const MONO = '"Cascadia Code", "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace';

// ---- Word-by-word caption pill (bottom-center) ----
const WordCaption: React.FC<{ text: string; durationInFrames: number }> = ({ text, durationInFrames }) => {
  const frame = useCurrentFrame();
  const fin = 5;
  const fout = 4;
  const opacity = Math.min(
    interpolate(frame, [0, fin], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(frame, [durationInFrames - fout, durationInFrames], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const scale = interpolate(frame, [0, fin], [0.92, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const y = interpolate(frame, [0, fin], [12, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70 }}>
      <div
        style={{
          opacity,
          transform: `translateY(${y}px) scale(${scale})`,
          backgroundColor: "rgba(8,10,18,0.78)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: `1px solid ${LINE}`,
          padding: "16px 38px",
          borderRadius: 18,
          boxShadow: "0 10px 40px -10px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.06)",
          maxWidth: "86%",
        }}
      >
        <span
          style={{
            fontFamily: FONT,
            fontSize: 46,
            fontWeight: 700,
            letterSpacing: -0.4,
            color: "#ffffff",
            textShadow: "0 3px 18px rgba(0,0,0,0.8)",
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ---- Terminal window ----
type LineKind = "prompt" | "header" | "label" | "hash" | "plain" | "json" | "tx" | "ok" | "err" | "warn";
type TermLine = { text: string; kind?: LineKind };

const lineColor: Record<LineKind, string> = {
  prompt: ACCENT,
  header: ACCENT2,
  label: ACCENT,
  hash: ACCENT2,
  plain: "#94a3b8",
  json: "#cbd5e1",
  tx: ACCENT2,
  ok: ACCENT2,
  err: RED,
  warn: AMBER,
};

const TerminalFrame: React.FC<{
  title?: string;
  lines: TermLine[];
  perLine?: number;
  startOffset?: number;
  fontSize?: number;
}> = ({ title = "multihopper — python run_transfer.py", lines, perLine = 0.4, startOffset = 0.2, fontSize = 26 }) => {
  const frame = useCurrentFrame();
  const fps = 30;
  const visible = (i: number) => {
    const startF = (startOffset + i * perLine) * fps;
    return frame >= startF;
  };
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", backgroundColor: BG }}>
      <div
        style={{
          width: "84%",
          height: "80%",
          borderRadius: 16,
          overflow: "hidden",
          border: `1px solid ${LINE}`,
          backgroundColor: "#0b0e16",
          boxShadow: "0 30px 80px -20px rgba(0,0,0,0.8), 0 0 0 1px rgba(153,69,255,0.06)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* title bar */}
        <div
          style={{
            height: 46,
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "0 18px",
            borderBottom: `1px solid ${LINE}`,
            backgroundColor: "#0e1320",
          }}
        >
          <span style={{ width: 13, height: 13, borderRadius: 9, backgroundColor: "#ff5f56" }} />
          <span style={{ width: 13, height: 13, borderRadius: 9, backgroundColor: "#ffbd2e" }} />
          <span style={{ width: 13, height: 13, borderRadius: 9, backgroundColor: "#27c93f" }} />
          <span style={{ marginLeft: 16, color: MUTED, fontFamily: FONT, fontSize: 18 }}>{title}</span>
        </div>
        {/* body */}
        <div style={{ flex: 1, padding: "22px 28px", overflow: "hidden" }}>
          <pre style={{ margin: 0, fontFamily: MONO, fontSize, lineHeight: 1.5, color: "#cbd5e1", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {lines.map((l, i) =>
              visible(i) ? (
                <div key={i} style={{ color: lineColor[l.kind ?? "plain"], marginBottom: 4 }}>
                  {l.text}
                  {i === lines.length - 1 && frame > (startOffset + (lines.length - 1) * perLine) * fps ? (
                    <span style={{ color: ACCENT }}>▋</span>
                  ) : null}
                </div>
              ) : null,
            )}
          </pre>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---- Shot 1: Title card (0-10s) ----
const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const opOut = interpolate(frame, [270, 292], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const y = interpolate(frame, [0, 20], [30, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        justifyContent: "center",
        alignItems: "center",
        opacity: Math.min(op, opOut),
        backgroundImage: "radial-gradient(1100px 600px at 50% -10%, rgba(153,69,255,0.20), transparent 60%)",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 26, transform: `translateY(${y}px)` }}>
        <div
          style={{
            fontSize: 138,
            fontWeight: 800,
            backgroundImage: "linear-gradient(120deg, #9945FF 0%, #b06bff 55%, #14F195 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            letterSpacing: -3,
          }}
        >
          MultiHopper
        </div>
        <div style={{ fontSize: 40, color: "#e2e8f0", fontWeight: 700, textAlign: "center", maxWidth: 1500 }}>
          Break It Before Users Do — Agentic Flow Bugs &amp; Fixes
        </div>
        <div style={{ fontSize: 24, color: MUTED, fontFamily: MONO }}>
          Responsible devnet testing · 18 findings · Superteam Earn
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---- Shot 2: Agentic flow diagram (10-20s) ----
const FlowDiagram: React.FC = () => {
  const frame = useCurrentFrame();
  const steps = [
    { label: "create", sub: "POST /transfers" },
    { label: "prepare", sub: "POST /:id/prepare" },
    { label: "sign / broadcast", sub: "strict order · 5 txs" },
    { label: "confirm-broadcast ×2", sub: "double-fund guard" },
    { label: "monitor", sub: "GET /:id poll" },
  ];
  const reveal = (i: number) => interpolate(frame, [i * 22, i * 22 + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const arrow = (i: number) => interpolate(frame, [i * 22 + 14, i * 22 + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        justifyContent: "center",
        alignItems: "center",
        backgroundImage: "radial-gradient(900px 500px at 50% -10%, rgba(153,69,255,0.14), transparent 60%)",
      }}
    >
      <div style={{ fontSize: 22, color: MUTED, letterSpacing: 4, textTransform: "uppercase", marginBottom: 50 }}>
        Documented agent flow
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {steps.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                opacity: reveal(i),
                transform: `translateY(${(1 - reveal(i)) * 18}px)`,
                width: 250,
                padding: "22px 18px",
                borderRadius: 14,
                border: `1px solid ${i === 4 ? "rgba(255,84,112,0.4)" : "rgba(153,69,255,0.4)"}`,
                background: i === 4 ? "rgba(255,84,112,0.05)" : "rgba(153,69,255,0.05)",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 26, fontWeight: 700, color: "#fff" }}>{s.label}</div>
              <div style={{ fontSize: 15, color: MUTED, marginTop: 8, fontFamily: MONO }}>{s.sub}</div>
            </div>
            {i < steps.length - 1 ? (
              <div style={{ fontSize: 38, color: ACCENT2, opacity: arrow(i) }}>→</div>
            ) : null}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 54, fontSize: 20, color: AMBER, fontFamily: MONO, opacity: arrow(4) }}>
        terminal state never reached · reproduced on devnet
      </div>
    </AbsoluteFill>
  );
};

// ---- Shot 10: Findings summary (91-101s) ----
const FindingsSummary: React.FC = () => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const rows = [
    { sev: "Critical", count: "1", items: "F1 rescue false promise · Custom 3012", color: RED },
    { sev: "High", count: "5", items: "F2 500/SQL leak · F13 webhook verifier · F16 amount · F18 never settles · F8 MCP", color: AMBER },
    { sev: "Medium", count: "8", items: "F3 F4 F5 F7 F9 F12 F15 F17", color: ACCENT },
    { sev: "Low / Doc", count: "4", items: "F6 F10 F11 + notes", color: MUTED },
  ];
  const vis = (i: number) => interpolate(frame, [i * 24, i * 24 + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        justifyContent: "center",
        alignItems: "center",
        opacity: op,
        backgroundImage: "radial-gradient(1000px 600px at 50% 120%, rgba(153,69,255,0.16), transparent 60%)",
      }}
    >
      <div style={{ fontSize: 96, fontWeight: 800, color: "#fff", letterSpacing: -2, marginBottom: 8 }}>
        18 <span style={{ color: ACCENT2 }}>findings</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 18, maxWidth: 1500, width: "86%" }}>
        {rows.map((r, i) => (
          <div
            key={i}
            style={{
              opacity: vis(i),
              transform: `translateX(${(1 - vis(i)) * -24}px)`,
              display: "flex",
              alignItems: "center",
              gap: 26,
              padding: "20px 26px",
              borderRadius: 12,
              border: `1px solid ${LINE}`,
              background: "rgba(255,255,255,0.03)",
            }}
          >
            <div style={{ width: 130, fontFamily: FONT, fontSize: 30, fontWeight: 800, color: r.color }}>{r.sev}</div>
            <div style={{ width: 70, fontFamily: MONO, fontSize: 40, fontWeight: 800, color: "#fff" }}>{r.count}</div>
            <div style={{ fontFamily: MONO, fontSize: 19, color: "#cbd5e1", flex: 1 }}>{r.items}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 34, fontSize: 22, color: ACCENT2, fontFamily: MONO, opacity: vis(4) }}>
        all devnet-reproduced · all unique vs 6 public competitors
      </div>
    </AbsoluteFill>
  );
};

// ---- Shot 11: Final proof card (101-110s) ----
const FinalCard: React.FC = () => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        justifyContent: "center",
        alignItems: "center",
        opacity: op,
        backgroundImage: "radial-gradient(1100px 600px at 50% 120%, rgba(20,241,149,0.16), transparent 60%)",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
        <div
          style={{
            fontSize: 118,
            fontWeight: 800,
            backgroundImage: "linear-gradient(120deg, #9945FF 0%, #b06bff 55%, #14F195 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            letterSpacing: -2,
          }}
        >
          MultiHopper
        </div>
        <div style={{ display: "flex", gap: 60, marginTop: 8 }}>
          <Stat big="18" small="unique findings" />
          <Stat big="5/5" small="deploy txs confirmed · devnet" />
          <Stat big="0.111" small="SOL locked · rescue failed" />
        </div>
        <div style={{ fontFamily: MONO, fontSize: 24, color: "#fff", marginTop: 14 }}>
          Legit devnet (mh_test_) · reproducible harness · 18 unique findings
        </div>
        <div style={{ fontFamily: MONO, fontSize: 17, color: MUTED, marginTop: 6, textAlign: "center", lineHeight: 1.7 }}>
          repo + report: github.com/yusif/b17-multihopper · all testing on devnet, no live funds
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Stat: React.FC<{ big: string; small: string }> = ({ big, small }) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
    <div style={{ fontSize: 66, fontWeight: 800, color: ACCENT }}>{big}</div>
    <div style={{ fontFamily: MONO, fontSize: 19, color: MUTED }}>{small}</div>
  </div>
);

// ---- Terminal content (REAL devnet evidence) ----

// Shot 3 — happy-path deploy (transfer 476)
const DEPLOY_LINES: TermLine[] = [
  { text: "$ python run_transfer.py", kind: "prompt" },
  { text: "=== MultiHopper agentic transfer (devnet) ===", kind: "header" },
  { text: "base: https://devnet.multihopper.com/api/v1   key: mh_test_••••   wallet: FVBk…8EK5", kind: "plain" },
  { text: "POST /transfers  ->  id=476  status=quote  amount=0.1 SOL  hops=7", kind: "plain" },
  { text: "POST /transfers/476/prepare  ->  4 tx groups (resume: totalSteps=5)", kind: "plain" },
  { text: "signing Versioned v0 + legacy partial_sign (strict order)...", kind: "plain" },
  { text: "", kind: "plain" },
  { text: "broadcast keeperFundingTx      -> confirmed=confirmed", kind: "ok" },
  { text: "  4AkiNVwPBcAhN8FsvDarVcdFHY8L9sZGUCmiadn5XUiJnsF9tFeyy1kq7YCUjrNcYR5TQyYTewn64F52x1pLUpcw", kind: "tx" },
  { text: "broadcast routeInitTxs[0]      -> confirmed=confirmed", kind: "ok" },
  { text: "  3ShSCD5BhwQAxxDEdpcehuVP59Uui4bqqY1PXw5uroZucNCEW8SFnafbhUU3Yuk5eZgNR22WJxbks1DeULdC5wiH", kind: "tx" },
  { text: "broadcast routeInitTxs[1]      -> confirmed=confirmed", kind: "ok" },
  { text: "  jFWjhHDoS4qsY2jsVHmYK9s3eZR78P9AhATxot4syFyZUcp25JGayGLxaGx9SxXbXkw1wrq9p5FymQHsJfftWRr", kind: "tx" },
  { text: "broadcast orchestratorInitTx   -> confirmed=confirmed", kind: "ok" },
  { text: "  2PwKVNUuasxDPgBHnjC3sXR8ppXBxXdXeioVaYFHDuvipBsSF1GKAUsyRrEkQN2q9bXDPs6Br5cYDz1hn4zT75Y7", kind: "tx" },
  { text: "broadcast sessionInitTxs[0]    -> confirmed=confirmed", kind: "ok" },
  { text: "  4WwocT77KpzVLMtvqjxy9U8oLVUn4SVkgqEyWHzR4d8vbWQC1SkEMUuDN2B9SaYn9Z8TTmeT2peHpbkbxeMNoDrDA", kind: "tx" },
  { text: "", kind: "plain" },
  { text: "POST /transfers/476/confirm-broadcast x2  ->  200 / 200", kind: "ok" },
  { text: "5/5 deploy txs confirmed on Solana devnet", kind: "header" },
];

// Shot 4 — STUCK (transfer 476)
const STUCK_LINES: TermLine[] = [
  { text: "$ GET /transfers/476   (poll for terminal state...)", kind: "prompt" },
  { text: "{", kind: "json" },
  { text: '  "id": 476, "status": "active", "phase": "executing",', kind: "json" },
  { text: '  "progress": { "hopsCompleted": 0, "hopsTotal": 5 },   // 0/5', kind: "json" },
  { text: '  "lastError": null,', kind: "json" },
  { text: '  "recovery": null,', kind: "json" },
  { text: '  "completedAt": null,', kind: "json" },
  { text: '  "expiresAt": "2026-06-30T13:13:44.409Z"   <- passed', kind: "warn" },
  { text: "}", kind: "json" },
  { text: "", kind: "plain" },
  { text: "> 30 min elapsed. No hop executes. No error. No recovery.", kind: "err" },
  { text: "F1/F4: stuck hops · hops semantics inconsistent (requested 7, total 5)", kind: "warn" },
];

// Shot 5 — RESCUE false promise (F1, transfer 476)
const RESCUE_LINES: TermLine[] = [
  { text: "$ POST /transfers/476/rescue/prepare", kind: "prompt" },
  { text: '{ "canRescue": true, "rescuableLamports": 111316960,   // 0.111 SOL', kind: "json" },
  { text: '  "rescuableAccounts": ["orchestrator_config", "step_state" x5] }', kind: "json" },
  { text: "-> rescueTxs:[1]   signing sourceOwner keypair...", kind: "plain" },
  { text: "broadcast rescueTx  -> confirmed=confirmed", kind: "ok" },
  { text: "  2kpxgXqPi1mksZYbQgw3jdcPjhX3FbFjsAp3NcCj1yWTArbtKtS1ZT77G1evBydqhE99qxDVhqVz969GQC61ye46", kind: "tx" },
  { text: "$ POST /transfers/476/rescue/confirm", kind: "prompt" },
  { text: "<- 400  MH_083", kind: "err" },
  { text: '"Provided signatures do not match prepared bundle"', kind: "err" },
  { text: "RESCUE_TX_FAILED: InstructionError:[4,{Custom:3012}]", kind: "err" },
  { text: "", kind: "plain" },
  { text: "F1 CRITICAL: canRescue=true is a FALSE PROMISE. Funds locked, no integrator rescue.", kind: "err" },
];

// Shot 6 — NEVER SETTLES (F18, transfer 479)
const NEVER_LINES: TermLine[] = [
  { text: "$ GET /transfers/479   (all hops executed on-chain...)", kind: "prompt" },
  { text: "{", kind: "json" },
  { text: '  "id": 479, "status": "active", "phase": "executing",', kind: "json" },
  { text: '  "progress": { "hopsCompleted": 4, "hopsTotal": 4 },   // 4/4 done', kind: "json" },
  { text: '  "signatures": { "hops": [4 hop sigs] },', kind: "json" },
  { text: '  "completedAt": null, "lastError": null, "recovery": null', kind: "json" },
  { text: "}", kind: "json" },
  { text: "", kind: "plain" },
  { text: "4/4 hops complete. status still active. phase still executing. Never settles.", kind: "err" },
  { text: "F18 HIGH: no API unwrap/settle endpoint. Principal locked in vault.", kind: "warn" },
];

// Shot 7 — WEBHOOK (F13/F14, transfer 479 events)
const WEBHOOK_LINES: TermLine[] = [
  { text: '$ POST /api/v1/webhooks  { url, events:["transfer.completed",...] }', kind: "prompt" },
  { text: '<- 200  { "id":133, "secret":"b2d9430a...", "isActive":true }', kind: "json" },
  { text: '   NO "whsec_" prefix (docs say prefixed)        <- F12', kind: "warn" },
  { text: "", kind: "plain" },
  { text: "delivered event: transfer.quote_created  (transferId 479)", kind: "plain" },
  { text: "headers:", kind: "label" },
  { text: "  x-mh-signature: 2156e337c4a4066b446ac2f55fb4439977f3e05e5bb8a0b9aa84ba6618f28874", kind: "hash" },
  { text: "  x-mh-event: transfer.quote_created", kind: "plain" },
  { text: '   docs say "x-multihopper-signature"          <- F14', kind: "warn" },
  { text: "", kind: "plain" },
  { text: "HMAC-SHA256 over RAW body      -> 2156e337...  MATCH", kind: "ok" },
  { text: "HMAC-SHA256 over parsed JSON   -> 11d7c500...  MISMATCH", kind: "err" },
  { text: "F13 HIGH: docs verifier uses req.body (parsed) -> rejects every webhook", kind: "err" },
];

// Shot 8 — 500 + SQL leak (F2)
const LEAK_LINES: TermLine[] = [
  { text: "$ GET /transfers/476   (valid mh_test_ key)", kind: "prompt" },
  { text: "<- HTTP 500", kind: "err" },
  { text: '{ "statusCode": 500, "error": "Internal Server Error",', kind: "json" },
  { text: '  "message": "Failed query: select \\"api_keys\\".\\"id\\",\\"api_keys\\".\\"integration_id\\",', kind: "json" },
  { text: '            \\"api_keys\\".\\"key_hash\\",...,\\"integrations\\".\\"webhook_url\\",..." }', kind: "json" },
  { text: "re-run seconds later -> 200 OK   (intermittent)", kind: "plain" },
  { text: "F2 HIGH: SQL/schema leak + reliability. No MH_XXX code, no requestId.", kind: "err" },
];

// Shot 9 — AMOUNT MISMATCH (F16)
const AMOUNT_LINES: TermLine[] = [
  { text: '$ POST /transfers  { amountRaw:"100000000", amountTokens:"5.0", tokenDecimals:9 }', kind: "prompt" },
  { text: "   // raw = 0.1 SOL, tokens claims 5.0 SOL  -- inconsistent", kind: "warn" },
  { text: '<- 200  { "status": "quote", "amountRaw": "100000000", "amountTokens": "5.0" }', kind: "json" },
  { text: "   no validation error.", kind: "plain" },
  { text: "   on-chain amount  = amountRaw   (0.1 SOL)", kind: "plain" },
  { text: "   displayed amount = amountTokens (5.0 SOL)  -- WRONG", kind: "err" },
  { text: "F16 HIGH: amountRaw/amountTokens not validated. Fund-safety gap.", kind: "err" },
];

export const MultiHopperDemo: React.FC = () => {
  const { fps, durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {/* Shot 1 — Title (0-13.8s) */}
      <Sequence from={0} durationInFrames={415}>
        <TitleCard />
      </Sequence>

      {/* Shot 2 — Agentic flow diagram (13.8-27.7s) */}
      <Sequence from={415} durationInFrames={415}>
        <FlowDiagram />
      </Sequence>

      {/* Shot 3 — Happy-path deploy (27.7-45.6s) */}
      <Sequence from={830} durationInFrames={539}>
        <TerminalFrame title="multihopper — python run_transfer.py" lines={DEPLOY_LINES} perLine={0.69} startOffset={0.28} fontSize={24} />
      </Sequence>

      {/* Shot 4 — STUCK 476 (45.6-58.1s) */}
      <Sequence from={1369} durationInFrames={373}>
        <TerminalFrame title="multihopper — GET /transfers/476" lines={STUCK_LINES} perLine={0.76} startOffset={0.28} fontSize={26} />
      </Sequence>

      {/* Shot 5 — RESCUE false promise (58.1-76.0s) */}
      <Sequence from={1742} durationInFrames={539}>
        <TerminalFrame title="multihopper — rescue/prepare + rescue/confirm" lines={RESCUE_LINES} perLine={0.69} startOffset={0.28} fontSize={24} />
      </Sequence>

      {/* Shot 6 — NEVER SETTLES 479 (76.0-87.1s) */}
      <Sequence from={2281} durationInFrames={332}>
        <TerminalFrame title="multihopper — GET /transfers/479" lines={NEVER_LINES} perLine={0.69} startOffset={0.28} fontSize={26} />
      </Sequence>

      {/* Shot 7 — WEBHOOK (87.1-105.1s) */}
      <Sequence from={2613} durationInFrames={539}>
        <TerminalFrame title="multihopper — POST /webhooks + delivery" lines={WEBHOOK_LINES} perLine={0.69} startOffset={0.28} fontSize={24} />
      </Sequence>

      {/* Shot 8 — 500 + SQL leak (105.1-116.2s) */}
      <Sequence from={3152} durationInFrames={332}>
        <TerminalFrame title="multihopper — GET /transfers/476 (500)" lines={LEAK_LINES} perLine={0.76} startOffset={0.28} fontSize={26} />
      </Sequence>

      {/* Shot 9 — AMOUNT MISMATCH (116.2-125.9s) */}
      <Sequence from={3484} durationInFrames={290}>
        <TerminalFrame title="multihopper — POST /transfers" lines={AMOUNT_LINES} perLine={0.76} startOffset={0.28} fontSize={26} />
      </Sequence>

      {/* Shot 10 — Findings summary (125.9-139.7s) */}
      <Sequence from={3774} durationInFrames={415}>
        <FindingsSummary />
      </Sequence>

      {/* Shot 11 — Final proof card (139.7-152.0s) */}
      <Sequence from={4189} durationInFrames={371}>
        <FinalCard />
      </Sequence>

      {/* Voiceover (enable when Yusif records public/voiceover.mp3) */}
      {HAS_VOICE ? <Audio src={VOICE} /> : null}

      {/* Word-by-word captions across the whole timeline */}
      {WORDS.map((w, i) => {
        const from = Math.round(w.start * fps);
        const dur = Math.round(w.dur * fps);
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <WordCaption text={w.text} durationInFrames={dur} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
