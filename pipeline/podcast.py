"""The daily podcast: every story of the issue read aloud as ONE episode, with chapter times for the player.

Stages (all retry-safe and idempotent):
  1. a spoken script per story (headline + short summary + source, with natural transitions; no article text),
  2. one TTS call per script, cached as a 24 kHz mono WAV keyed by a hash of the script, voice and speed,
  3. when every segment exists: join them with short gaps into media/podcast.mp3 and write media/podcast.json.
The feed gets `podcast: {audio_url, duration_s, chapters:[{id,title,category,start,end}]}` once the episode matches
the current stories. Segments are synthesised until the time budget runs out; the next run carries on.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import tempfile
import time
import wave
from datetime import datetime
from pathlib import Path

from .media import _run
from .text import spoken_summary

log = logging.getLogger(__name__)
RATE = 24000


def episode_items(feed: dict, count: int) -> list:
    """Prime, then cards, then glance, until `count` stories."""
    items = [i for slot in ("prime", "cards", "glance") for i in feed.get(slot, [])]
    return items[:count]


def _sentence(text: str) -> str:
    text = " ".join(str(text).split()).strip()
    return text if not text or text[-1] in ".!?" else text + "."


def intro_script(feed: dict, total: int) -> str:
    try:
        when = datetime.strptime(feed["generated_at"][:10], "%Y-%m-%d")
        day = f"{when.strftime('%A')}, {when.strftime('%B')} {when.day}"
    except (KeyError, ValueError):
        day = "today"
    return (f"This is your Bought brief for {day}. {total} stories, from the top. Here we go.")


def outro_script(total: int) -> str:
    return f"And that was all {total}. You're up to date. Thanks for listening, and see you tomorrow."


def story_script(item: dict, number: int, previous_category: str, max_chars: int = 600) -> str:
    cat = item.get("category", "")
    if number == 1:
        lead = f"First up, {cat}." if cat else "First up."
    elif cat and cat != previous_category:
        lead = f"Now, {cat}."
    else:
        lead = "Next."
    parts = [f"Story {number}.", lead, _sentence(item["headline"]), _sentence(spoken_summary(item["headline"], item.get("summary", "")))]
    if item.get("source"):
        parts.append(f"From {item['source']}.")
    text = " ".join(p for p in parts if p)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return text


def _hash(*parts) -> str:
    return hashlib.sha1("\x1f".join(map(str, parts)).encode()).hexdigest()[:16]


def _wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def _synthesize(script: str, wav_out: Path, cfg, speed: float) -> None:
    """TTS -> a 24 kHz mono 16-bit WAV, whatever the engine writes; atomic."""
    wav_out.parent.mkdir(parents=True, exist_ok=True)
    tmp_raw, tmp_out = wav_out.with_suffix(".raw.wav"), wav_out.with_suffix(".tmp.wav")
    try:
        voice = cfg.tts_voices[0] if cfg.tts_voices else ""      # one steady voice for the whole episode
        cmd = [a.replace("{wav}", str(tmp_raw)).replace("{speed}", str(speed)).replace("{voice}", voice) for a in cfg.tts_command]
        _run(cmd, input=script.encode(), timeout=cfg.tts_timeout_seconds)
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp_raw), "-ar", str(RATE), "-ac", "1",
              "-sample_fmt", "s16", str(tmp_out)])
        os.replace(tmp_out, wav_out)
    finally:
        tmp_raw.unlink(missing_ok=True)
        tmp_out.unlink(missing_ok=True)


def _plan(cfg, feed: dict) -> list:
    """[(key, script, meta)] in play order: intro, every story, outro."""
    items = episode_items(feed, cfg.podcast_stories)
    plan = [("intro", intro_script(feed, len(items)), None)]
    previous = ""
    for n, item in enumerate(items, 1):
        plan.append((item["id"], story_script(item, n, previous, cfg.script_max_chars), item))
        previous = item.get("category", "")
    plan.append(("outro", outro_script(len(items)), None))
    return plan


def _manifest(cfg, plan) -> str:
    return _hash(cfg.podcast_gap_seconds, *[_hash(k, s, cfg.podcast_speed, *cfg.tts_command) for k, s, _ in plan])


def build_podcast(cfg, feed: dict, out_dir, cache_dir, now_monotonic=time.monotonic) -> dict:
    out_dir, cache_dir = Path(out_dir), Path(cache_dir)
    plan = _plan(cfg, feed)
    manifest = _manifest(cfg, plan)
    meta_path = out_dir / "podcast.json"
    if meta_path.exists() and json.loads(meta_path.read_text()).get("manifest") == manifest and (out_dir / "podcast.mp3").exists():
        return {"segments": len(plan), "new": 0, "complete": True, "built": False}
    started, new = now_monotonic(), 0
    wavs = {}
    for key, script, _ in plan:
        h = _hash(key, script, cfg.podcast_speed, *cfg.tts_command)
        wav, tag = cache_dir / f"{key}.wav", cache_dir / f"{key}.hash"
        if not (wav.exists() and tag.exists() and tag.read_text() == h):
            if now_monotonic() - started > cfg.podcast_time_budget_seconds:
                continue                                   # out of time: the next run carries on from here
            try:
                _synthesize(script, wav, cfg, cfg.podcast_speed)
                tag.write_text(h)
                new += 1
            except Exception as e:                         # one bad story must not stop the episode being retried
                log.warning("podcast segment %s failed: %s", key, str(e)[:200])
                continue
        wavs[key] = wav
    if len(wavs) < len(plan):
        return {"segments": len(plan), "new": new, "complete": False, "built": False, "have": len(wavs)}
    out_dir.mkdir(parents=True, exist_ok=True)
    gap = cache_dir / "gap.wav"
    with wave.open(str(gap), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(b"\0\0" * int(RATE * cfg.podcast_gap_seconds))
    chapters, t = [], 0.0
    lines = []
    for key, script, item in plan:
        dur = _wav_seconds(wavs[key])
        if item is not None:
            chapters.append({"id": item["id"], "title": item["headline"], "category": item.get("category", ""),
                             "start": round(t, 2), "end": round(t + dur, 2)})
        lines.append("file '" + str(wavs[key]).replace("'", "'\\''") + "'")
        lines.append("file '" + str(gap).replace("'", "'\\''") + "'")
        t += dur + cfg.podcast_gap_seconds
    total = round(t - cfg.podcast_gap_seconds, 2)
    mp3_tmp = out_dir / "podcast.mp3.tmp"
    with tempfile.TemporaryDirectory() as tmp:
        listing = Path(tmp) / "list.txt"
        listing.write_text("\n".join(lines[:-1]) + "\n")       # no gap after the outro
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
              "-ac", "1", "-b:a", "80k", "-f", "mp3", str(mp3_tmp)])
    os.replace(mp3_tmp, out_dir / "podcast.mp3")
    meta_path.write_text(json.dumps({"manifest": manifest, "duration_s": total, "chapters": chapters}, indent=2) + "\n")
    return {"segments": len(plan), "new": new, "complete": True, "built": True, "duration_s": total}


def attach_podcast(cfg, feed: dict, out_dir) -> bool:
    """Put the episode in the feed, but only if it was built from exactly these stories."""
    out_dir = Path(out_dir)
    meta_path = out_dir / "podcast.json"
    if not (meta_path.exists() and (out_dir / "podcast.mp3").exists()):
        return False
    meta = json.loads(meta_path.read_text())
    if meta.get("manifest") != _manifest(cfg, _plan(cfg, feed)):
        return False
    feed["podcast"] = {"audio_url": f"{cfg.audio_base_url.rstrip('/')}/podcast.mp3", "duration_s": meta["duration_s"],
                       "chapters": meta["chapters"]}
    return True
