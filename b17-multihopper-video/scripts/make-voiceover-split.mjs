// Split Yusif's recorded voiceover (public/voiceover-yusif.{wav,mp3,m4a}) by
// silence into 10 segments, ffprobe each, concat (silence-trimmed) -> public/voiceover.mp3
// (replacing the placeholder), and print the per-segment durations so the shot
// timeline in MultiHopperDemo.tsx can be re-aligned to his real pace.
//   node scripts/make-voiceover-split.mjs
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const N = 10; // expected segments (10 paragraphs in the voiceover script)

const findIn = () => {
  for (const ext of ["wav", "mp3", "m4a", "aac"]) {
    const p = resolve(ROOT, `public/voiceover-yusif.${ext}`);
    if (existsSync(p)) return p;
  }
  return null;
};
const IN = findIn();
if (!IN) {
  console.error("Put your recording at: b17-multihopper-video/public/voiceover-yusif.wav (or .mp3/.m4a)");
  process.exit(1);
}
const OUT = resolve(ROOT, "public/voice-yusif");
mkdirSync(OUT, { recursive: true });

console.log("[split] input:", IN);
const total = +execSync(
  `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${IN}"`,
).toString().trim();
console.log("[split] total duration:", total.toFixed(2), "s");

// 1. silence detect (2s pauses between paragraphs show up clearly)
const sd = execSync(`ffmpeg -i "${IN}" -af silencedetect=noise=-35dB:d=0.5 -f null - 2>&1`, {
  encoding: "utf8",
});
const silStarts = [...sd.matchAll(/silence_start: ([\d.]+)/g)].map((m) => +m[1]);
const silEnds = [...sd.matchAll(/silence_end: ([\d.]+)/g)].map((m) => +m[1]);
console.log("[split] silences detected:", silStarts.length);

// cut points = midpoints of each silence
const cuts = silStarts.map((s, i) => ({ mid: (s + silEnds[i]) / 2, len: silEnds[i] - s }));

let boundaries;
if (cuts.length === N - 1) {
  boundaries = [0, ...cuts.map((c) => c.mid), total];
} else if (cuts.length >= N - 1) {
  // pick the (N-1) longest gaps as the paragraph boundaries
  const top = [...cuts].sort((a, b) => b.len - a.len).slice(0, N - 1).map((c) => c.mid).sort((a, b) => a - b);
  boundaries = [0, ...top, total];
} else {
  // fewer pauses than expected — split evenly as a fallback
  boundaries = Array.from({ length: N + 1 }, (_, i) => (total * i) / N);
}
console.log("[split] boundaries (s):", boundaries.map((b) => b.toFixed(2)).join("  "));

// 2. cut segments, trimming ~0.1s of silence off each end
const durs = [];
for (let i = 0; i < N; i++) {
  const s = Math.max(0, boundaries[i] + 0.1);
  const e = Math.max(s + 0.2, boundaries[i + 1] - 0.1);
  const out = resolve(OUT, `seg-${String(i + 1).padStart(2, "0")}.mp3`);
  execSync(`ffmpeg -y -ss ${s} -to ${e} -i "${IN}" -c:a libmp3lame -q:a 2 "${out}" -loglevel error`);
  const d = +execSync(
    `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${out}"`,
  ).toString().trim();
  durs.push(d);
  console.log(`[split] seg ${i + 1}: ${d.toFixed(2)}s`);
}

// 3. concat -> public/voiceover.mp3 (replaces the placeholder used by the composition)
const list = Array.from({ length: N }, (_, i) => `file 'seg-${String(i + 1).padStart(2, "0")}.mp3'`).join("\n");
writeFileSync(resolve(OUT, "list.txt"), list);
execSync(`ffmpeg -y -f concat -safe 0 -i list.txt -c:a libmp3lame -q:a 2 ../voiceover.mp3 -loglevel error`, {
  cwd: OUT,
  stdio: "inherit",
});
console.log("[split] wrote public/voiceover.mp3 (replaced placeholder)");

// 4. print re-aligned shot windows for make_captions.py
let t = 0;
console.log("\n[split] Paste these WINDOWS into scripts/make_captions.py:");
console.log("WINDOWS = [");
for (let i = 0; i < N; i++) {
  const s = t.toFixed(2);
  t += durs[i];
  console.log(`    (${s}, ${t.toFixed(2)}),    # para ${i + 1}`);
}
console.log(`]; // total ${t.toFixed(2)}s -> durationInFrames = ${Math.round(t * 30)}`);
