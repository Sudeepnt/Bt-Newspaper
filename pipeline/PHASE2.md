# Phase 2: spoken prime stories

## Status
- **2a script + audio: built and tested** (`media.py`). Every prime item gets a `script`, and once audio exists,
  `audio_url` and `duration_s`. Verified end to end with Piper (`en_US-lessac-medium`): 25 stories in ~28 s on a
  laptop (about 1 s per story); not yet timed on the 2 vCPU VPS.
- **2b avatar video: built as the cheap option 1** (`avatar.py`, `avatar_enabled`). The presenter photo
  (`public/assets/ai-presenter.jpg`) gets a 2D mouth-flap driven by speech loudness, muxed with the audio into an
  MP4 (1100x500, H.264/AAC). ~0.5 s per story on CPU. It is stylised, **not true lip-sync**; real lip-sync
  (Wav2Lip etc.) still needs a GPU and a licence check. Demo page: `public/live.html`.
- Engine is any command set as `tts_command` in `config.yaml` (script on stdin, writes `{wav}`), so Piper or
  Kokoro can be swapped without code changes. Audio is rebuilt only when the script text changes; failures are
  retried up to `media_max_attempts`, and the feed stays valid without audio.
- **Licence flag:** `piper-tts` 1.8.0 (pip) is **GPL-3.0-or-later**, as is its voice tooling. We run it as a separate
  process and do not link or bundle it, but confirm that is acceptable to you. Each voice model has its own
  licence too (lessac: check its model card before shipping). Kokoro-82M (Apache-2.0) is the non-GPL fallback.

## Original plan

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
