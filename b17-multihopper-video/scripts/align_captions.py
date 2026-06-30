#!/usr/bin/env python3
"""Word-level align the demo voiceover with faster-whisper (GPU),
then collapse into comfortable 1-2 word caption chunks.

Input : b17-multihopper-video/public/voiceover.mp3  (the ACTUAL audio in the video)
Output: b17-multihopper-video/src/words.ts          (WORDS array: {start, dur, text})
        b17-multihopper-video/scripts/words.json    (raw words + chunks, for inspection)

Chunking rules (comfortable, not flickery, not a wall of text):
  - max 2 words per chunk
  - a lone function word (the/a/of/and/...) is merged with the neighbor word
  - min chunk duration 0.28s (~8 frames @30fps) so a word is readable
  - chunks never overlap (end clamped to next start)
"""
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "public" / "voiceover.mp3"
OUT_TS = ROOT / "src" / "words.ts"
OUT_JSON = ROOT / "scripts" / "words.json"
FPS = 30.0
MIN_DUR = 0.28          # seconds, min visibility per chunk
MAX_CHUNK_DUR = 1.20    # seconds, hard cap (rarely hit at 1-2 words)

FUNC = {
    "a","an","the","of","to","in","on","at","by","for","from","with","and","but","or",
    "nor","yet","so","as","is","are","was","were","be","been","being","it","its","our",
    "no","not","than","then","that","this","these","those","we","you","he","she","they",
    "them","his","her","their","my","your","i","me","him","us","do","did","does","done",
    "has","had","have","can","could","will","would","shall","should","may","might","must",
    "just","now","here","there","up","down","out","off","over","into","onto","each","every",
    "all","any","some","such","which","who","whom","whose","what","when","where","how","why",
    "if","because","while","once","also","very","too","more","most","much","many","one","two",
    "five","e.g","ie","vs",
}


def transcribe(path: Path):
    from faster_whisper import WhisperModel
    last_err = None
    for ct in ("float16", "int8_float16", "int8"):
        try:
            model = WhisperModel("small", device="cuda", compute_type=ct)
            print(f"[whisper] model=small device=cuda compute_type={ct}", flush=True)
            break
        except Exception as e:  # pragma: no cover
            last_err = e
            print(f"[whisper] compute_type={ct} failed: {e}", flush=True)
    else:
        print(f"[whisper] CUDA unavailable, falling back to CPU: {last_err}", flush=True)
        model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, info = model.transcribe(
        str(path),
        language="en",
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    words = []
    for s in segs:
        for w in (s.words or []):
            txt = (w.word or "").strip()
            txt = txt.strip().strip(",;:()")
            if not txt:
                continue
            words.append({"word": txt, "start": float(w.start), "end": float(w.end)})
    return words, round(info.duration, 3)


def is_func(w: str) -> bool:
    w = w.lower().strip(".,;:!?\"'()")
    return w in FUNC


def chunk(words):
    """Greedy 1-2 word chunks. A word is merged with a neighbor when:
       - either is a function word (avoid a lone "the"/"a" flashing), OR
       - the first word is shorter than MIN_DUR (force a partner so it's readable).
       Max 2 words. Pauses between words are kept as natural boundaries (gap>0.40s)."""
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        w0 = words[i]
        cur = [w0]
        cur_end = w0["end"]
        cur_start = w0["start"]
        if i + 1 < n:
            w1 = words[i + 1]
            gap = w1["start"] - cur_end
            cur_dur = cur_end - cur_start
            merged_dur = w1["end"] - cur_start
            want = (
                (is_func(w0["word"]) or is_func(w1["word"]) or cur_dur < MIN_DUR)
                and gap <= 0.40
                and merged_dur <= MAX_CHUNK_DUR
            )
            if want:
                cur.append(w1)
                cur_end = w1["end"]
                i += 2
            else:
                i += 1
        else:
            i += 1
        chunks.append(finalize(cur, words, i))
    return chunks


def finalize(cur, words, next_i):
    start = cur[0]["start"]
    end = cur[-1]["end"]
    text = " ".join(c["word"] for c in cur)
    next_start = words[next_i]["start"] if next_i < len(words) else 9999.0
    # hold the caption for at least MIN_DUR by filling the following pause
    # (no overlap with the next chunk — at most touch its start).
    target_end = max(end, start + MIN_DUR)
    if target_end > next_start:
        target_end = max(end, next_start - 0.005)
    dur = round(target_end - start, 3)
    if dur < 1 / FPS:
        dur = round(1 / FPS, 3)
    return {"start": round(start, 3), "dur": dur, "text": text}


def main():
    if not AUDIO.exists():
        sys.exit(f"missing audio: {AUDIO}")
    words, dur = transcribe(AUDIO)
    print(f"[align] {len(words)} words, audio={dur}s", flush=True)
    if not words:
        sys.exit("no words transcribed")
    chunks = chunk(words)
    # stats
    durs = [c["dur"] for c in chunks]
    print(f"[align] {len(chunks)} chunks | dur min/mean/max = "
          f"{min(durs):.2f}/{sum(durs)/len(durs):.2f}/{max(durs):.2f}s | "
          f"1-word={sum(1 for c in chunks if ' ' not in c['text'])}, "
          f"2-word={sum(1 for c in chunks if ' ' in c['text'])}", flush=True)
    print(f"[align] first 8: {chunks[:8]}", flush=True)
    print(f"[align] last 5: {chunks[-5:]}", flush=True)

    OUT_JSON.write_text(json.dumps(
        {"audio_duration": dur, "words": words, "chunks": chunks}, indent=2), encoding="utf-8")
    print(f"[align] wrote {OUT_JSON}", flush=True)

    # emit words.ts
    lines = ["// Auto-generated by scripts/align_captions.py — word-level synced captions.",
             "// 1-2 word chunks, timed to the actual voiceover (faster-whisper, GPU).",
             f"// {len(chunks)} chunks over {dur}s of narration.",
             "export const WORDS: { start: number; dur: number; text: string }[] = ["]
    for c in chunks:
        t = c["text"].replace('"', '\\"')
        lines.append(f"  {{ start: {c['start']}, dur: {c['dur']}, text: \"{t}\" }},")
    lines.append("];")
    OUT_TS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[align] wrote {OUT_TS}", flush=True)


if __name__ == "__main__":
    main()
