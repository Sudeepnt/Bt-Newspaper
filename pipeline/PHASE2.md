# Phase 2 plan (not started): spoken prime stories

Goal: for each `prime` item, produce `script` (text), an audio file, and an avatar video, all with
open-source tools on a 2 vCPU / 8 GB, no-GPU VPS. Nothing here is built or benchmarked yet.

## 1. Script (no LLM)
Template + extractive text from our own 300-char summary: "<Category>. <headline>. <summary>. Source: <name>."
~15–25 s each. Stored in `feed.json` `script` and a new `scripts` table. Fully deterministic, so idempotent.

## 2. TTS (CPU)
Candidates: **Piper** (fast on CPU; check which repo/version: the older rhasspy/piper was MIT, the newer
piper1-gpl is GPL-3, and each *voice* has its own license) or **Kokoro-82M** (Apache-2.0, small, CPU-capable,
higher quality, slower). Plan: benchmark both on 20 scripts, pick by real-time factor and licence.
Output WAV -> MP3/AAC with ffmpeg (LGPL build). One file per story id, skipped if it already exists.
Also gives the podcast edition real audio (replaces the simulated timings in the prototype).

## 3. Avatar video — the hard part
Neural talking-head models (Wav2Lip, SadTalker, MuseTalk, LivePortrait) generally need a GPU, and several have
non-commercial weights or dependencies (verify each before use). On this VPS they would take minutes per
second of video, if they run at all. Options, cheapest first:
1. **2D mouth-shape avatar:** Rhubarb Lip Sync (MIT) turns audio into mouth-shape cues; ffmpeg/Pillow composite
   pre-drawn mouth frames on a fixed illustrated presenter. Realistic runtime on CPU, no model weights.
2. **Pre-render offline** on a rented/own GPU or a laptop, upload MP4s; VPS only schedules and serves.
3. Neural model on CPU for a handful of stories only (slow; needs measurement).
Recommendation: start with option 1 to ship; decide on 2 only if quality is not enough.

## 4. Pipeline changes
New stage after `select`: for each prime id without assets -> script -> audio -> video, each step writing to
`out/media/<id>.*` and recording state in an `assets` table (id, kind, path, status, error). Retry-safe by file
existence + status. `feed.json` gains `audio_url`, `video_url`, `duration_s` for prime items.
Queue only the 25 prime stories, newest first, with a per-run time budget so a 30-min cron never overlaps.

## 5. Open questions for you
- Is a stylised/illustrated presenter acceptable, or must it look like a real person?
- Where are media files hosted (same VPS, object storage, CDN)?
- Is a GPU (rented by the hour) acceptable for batch pre-rendering?
