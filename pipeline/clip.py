"""One-off showcase clip from a hand-written spec: sentences with moods, natural pauses, laugh beats.

The automatic pipeline builds scripts from templates; this is for a produced piece (character, pacing and
expressions chosen by a person). Run: python -m pipeline clip SPEC.yaml --dry-run
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from .avatar import FPS, Presenter, render_video
from .media import _run

ROOT = Path(__file__).resolve().parent.parent
RATE = 24000


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def _read_wav(path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1, "TTS must write 16-bit mono WAV"
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if rate != RATE:  # linear resample, enough for joining pieces
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * RATE / rate)), np.arange(len(x)), x)
    return x


def _trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[idx[0]: idx[-1] + 1] if len(idx) else x


def build_audio(spec: dict, cfg, out_mp3: Path):
    """Returns (duration_s, moods per video frame, spoken text, cutaway windows, laugh windows, spoken lines with
    start/end; times in seconds)."""
    pieces, marks, text, cuts, caps = [], [], [], [], []
    pos = 0
    def add(x, mood):
        nonlocal pos
        pieces.append(x)
        marks.append((pos, pos + len(x), mood))
        pos += len(x)
    silence = lambda sec: np.zeros(int(RATE * sec), np.float32)
    add(silence(spec.get("lead_in", 0.35)), "happy")
    with tempfile.TemporaryDirectory() as tmp:
        for n, seg in enumerate(spec["segments"]):
            mood = seg.get("mood", "neutral")
            if seg.get("sound"):                                     # a recorded laugh/chuckle, loudness-matched to her speech
                x = _trim(_read_wav(_resolve(seg["sound"])))
                voiced = np.concatenate(pieces) if pieces else np.zeros(1, np.float32)
                voiced = voiced[np.abs(voiced) > 0.02]
                target = float(np.sqrt((voiced ** 2).mean())) if len(voiced) else 0.1
                x = x * min(target / (float(np.sqrt((x ** 2).mean())) or 1.0) * seg.get("gain", 1.0), 0.95 / (np.abs(x).max() or 1.0))
                add(np.concatenate([x, silence(seg.get("pause", 0.35))]), "laugh")
                continue
            if seg.get("laugh"):                                     # silent laugh beat (visual only)
                add(silence(float(seg["laugh"])), "laugh")
                continue
            wav = Path(tmp) / f"{n}.wav"
            cmd = [a.replace("{wav}", str(wav)).replace("{speed}", str(seg.get("speed", spec.get("speed", 1.0))))
                   for a in cfg.tts_command]
            _run(cmd, input=seg["text"].encode(), timeout=cfg.tts_timeout_seconds)
            start = pos / RATE
            add(_read_wav(wav), mood)
            caps.append((start, pos / RATE, seg["text"]))
            add(silence(seg.get("pause", 0.3)), mood)
            if seg.get("cutaway"):
                cuts.append((start, pos / RATE))
            text.append(seg["text"])
    add(silence(spec.get("tail", 0.6)), "happy")
    audio = np.concatenate(pieces)
    peak = np.abs(audio).max() or 1.0
    audio = audio * (0.89 / peak)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "all.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes((audio * 32767).astype(np.int16).tobytes())
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "128k", str(out_mp3)])
    n_frames = int(len(audio) / RATE * FPS) + 1
    moods = ["neutral"] * n_frames
    for a, b, mood in marks:
        for f in range(int(a / RATE * FPS), min(n_frames, int(b / RATE * FPS) + 1)):
            moods[f] = mood
    laughs = [(round(a / RATE, 2), round(b / RATE, 2)) for a, b, mood in marks if mood == "laugh"]
    return len(audio) / RATE, moods, " ".join(text), cuts, laughs, caps


def _ticker(feed_path, spec):
    """Other prime headlines from the feed, for the scrolling ticker."""
    try:
        feed = json.loads(Path(feed_path).read_text())
        return [i["headline"] for i in feed["prime"] if i["headline"] != spec["headline"]][:8]
    except (OSError, ValueError, KeyError):
        return []


def make_clip(spec_path, cfg, dry_run=True, feed_path=None) -> dict:
    from .runner import paths
    spec = yaml.safe_load(Path(spec_path).read_text())
    feed_path = Path(feed_path) if feed_path else paths(dry_run)[1]
    media = feed_path.parent / "media"
    name = spec["name"]
    mp3, mp4 = media / f"{name}.mp3", media / f"{name}.mp4"
    duration, moods, script, cuts, laughs, caps = build_audio(spec, cfg, mp3)
    from .styles import build_presenter
    presenter = build_presenter(spec.get("character", "photo"), spec.get("style", "studio"), cfg, _resolve)
    shot = Image.open(_resolve(spec["image"])).convert("RGB")
    style = spec.get("style", "studio")
    if style == "studio":
        render_video(mp3, mp4, presenter, spec["headline"], shot, spec.get("credit", ""), cfg.avatar_channel,
                     _resolve(cfg.avatar_font), seed=name, moods=moods, cut_ranges=cuts)
    else:
        from .styles import render_styled
        render_styled(style, mp3, mp4, presenter, spec["headline"], shot, spec.get("credit", ""), cfg.avatar_channel,
                      _resolve(cfg.avatar_font), seed=name, moods=moods, cut_ranges=cuts, category=spec.get("category", ""), subhead=spec.get("subhead", ""),
                      ticker=spec.get("ticker") or _ticker(feed_path, spec), captions=caps, laughs=laughs)
    from .avatar import extract_poster
    mp4.with_suffix(".jpg").unlink(missing_ok=True)                  # the video was just re-rendered: refresh its still
    extract_poster(mp4)
    attached = None
    if spec.get("attach_to") and feed_path.exists():                 # point that feed item at this clip (demo plumbing)
        feed = json.loads(feed_path.read_text())
        for item in feed["prime"]:
            if item["id"] == spec["attach_to"]:
                base = cfg.audio_base_url.rstrip("/")
                item.update(script=script, audio_url=f"{base}/{mp3.name}", video_url=f"{base}/{mp4.name}", poster_url=f"{base}/{mp4.with_suffix('.jpg').name}",
                            duration_s=round(duration, 2))
                attached = item["id"]
        feed_path.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"mp4": str(mp4), "duration_s": round(duration, 2), "attached_to": attached, "script": script,
            "laughs": laughs, "cutaways": [(round(a, 2), round(b, 2)) for a, b in cuts]}
