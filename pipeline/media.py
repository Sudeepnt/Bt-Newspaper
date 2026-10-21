"""Phase 2a: spoken scripts and audio for prime stories (open-source TTS run as an external command)."""
from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import time
from pathlib import Path

from . import db

log = logging.getLogger(__name__)

ASSETS_SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    article_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,                 -- 'audio'
    path        TEXT,
    script_hash TEXT,                          -- audio is rebuilt when the script text changes
    duration_s  REAL,
    status      TEXT NOT NULL,                 -- ok | failed
    attempts    INTEGER NOT NULL DEFAULT 0,
    error       TEXT,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (article_id, kind)
);
"""


def make_script(item: dict, max_chars: int = 600) -> str:
    """Deterministic, extractive spoken script built from our own short summary (no LLM)."""
    def sentence(text):
        text = re.sub(r"\s+", " ", text or "").strip()
        return text if not text or text[-1] in ".!?" else text + "."
    parts = [sentence(item["category"]), sentence(item["headline"]), sentence(item["summary"]),
             f"Source: {item['source']}."]
    script = " ".join(p for p in parts if p)
    return script if len(script) <= max_chars else script[: max_chars - 1].rsplit(" ", 1)[0] + "."


def script_hash(script: str) -> str:
    return hashlib.sha1(script.encode()).hexdigest()[:12]


def _run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, check=True, timeout=kw.pop("timeout", 120), **kw)
    except subprocess.CalledProcessError as e:  # surface the tool's own message, not just the command line
        raise RuntimeError(f"{Path(cmd[0]).name} exited {e.returncode}: "
                           f"{(e.stderr or b'').decode(errors='replace').strip()[-200:]}") from None


def synthesize(script: str, out_mp3: Path, cfg) -> float:
    """TTS -> wav -> mp3 via a temp file, then atomic rename. Returns duration in seconds."""
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    wav, tmp = out_mp3.with_suffix(".wav.tmp"), out_mp3.with_suffix(".mp3.tmp")
    try:
        cmd = [a.replace("{wav}", str(wav)) for a in cfg.tts_command]
        _run(cmd, input=script.encode(), timeout=cfg.tts_timeout_seconds)
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-f", "mp3", "-b:a", "64k", str(tmp)])
        out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", str(tmp)]).stdout
        os.replace(tmp, out_mp3)
        return round(float(out.strip()), 2)
    finally:
        wav.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)


def build_media(conn, cfg, feed: dict, out_dir, now_iso: str, synth=synthesize, fetch_images=True) -> dict:
    """Make audio for each prime item that lacks it. Safe to rerun; stops at the time budget."""
    conn.executescript(ASSETS_SCHEMA)
    out_dir = Path(out_dir)
    stats = {"made": 0, "skipped": 0, "failed": 0, "deferred": 0}
    video_cache = []  # presenter frames, built once per run
    deadline = time.monotonic() + cfg.media_time_budget_seconds
    for item in sorted(feed["prime"], key=lambda i: i["published_at"], reverse=True):  # newest first
        script = item["script"]
        row = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='audio'", (item["id"],)).fetchone()
        path = out_dir / f"{item['id']}.mp3"
        if row and row["status"] == "ok" and row["script_hash"] == script_hash(script) and path.exists():
            stats["skipped"] += 1
            if cfg.avatar_enabled:
                _video(conn, cfg, item, path, out_dir, now_iso, video_cache, fetch_images)
            continue
        same_script = row and row["script_hash"] == script_hash(script)
        if row and row["status"] == "failed" and same_script and row["attempts"] >= cfg.media_max_attempts:
            stats["failed"] += 1
            continue
        if time.monotonic() >= deadline:
            stats["deferred"] += 1
            continue
        attempts = (row["attempts"] if same_script and row else 0) + 1
        try:
            duration = synth(script, path, cfg)
            status, err = "ok", None
        except Exception as e:  # one bad story must not stop the rest
            duration, status, err = None, "failed", f"{type(e).__name__}: {e}"[:300]
            log.warning("audio failed for %s: %s", item["id"], err)
        with db.transaction(conn):
            conn.execute(
                "INSERT INTO assets(article_id,kind,path,script_hash,duration_s,status,attempts,error,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(article_id,kind) DO UPDATE SET path=excluded.path,"
                " script_hash=excluded.script_hash, duration_s=excluded.duration_s, status=excluded.status,"
                " attempts=excluded.attempts, error=excluded.error, updated_at=excluded.updated_at",
                (item["id"], "audio", path.name, script_hash(script), duration, status, attempts, err, now_iso))
        stats["made" if status == "ok" else "failed"] += 1
        if status == "ok" and cfg.avatar_enabled:
            _video(conn, cfg, item, path, out_dir, now_iso, video_cache, fetch_images)
    return stats


def _video(conn, cfg, item, audio, out_dir, now_iso, cache, fetch_images=True) -> None:
    """Presenter video for one story; same skip/retry rules as audio, keyed on the script hash."""
    from . import avatar  # Pillow/numpy only needed when avatar_enabled
    root = Path(__file__).resolve().parent.parent
    resolve = lambda p: Path(p) if Path(p).is_absolute() else root / p
    h = script_hash(item["script"])
    path = out_dir / f"{item['id']}.mp4"
    row = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='video'", (item["id"],)).fetchone()
    same = row and row["script_hash"] == h
    if same and row["status"] == "ok" and path.exists():
        return
    if same and row["status"] == "failed" and row["attempts"] >= cfg.media_max_attempts:
        return
    try:
        if not cache:
            cache.append(avatar.Presenter(resolve(cfg.avatar_image), tuple(cfg.avatar_size)))
        shot = _monitor_image(item, cfg, out_dir, resolve, fetch_images)
        avatar.render_video(audio, path, cache[0], item["headline"], shot, item.get("image_credit") or "",
                            cfg.avatar_channel, resolve(cfg.avatar_font), seed=item["id"])
        status, err = "ok", None
    except Exception as e:
        status, err = "failed", f"{type(e).__name__}: {e}"[:300]
        log.warning("video failed for %s: %s", item["id"], err)
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO assets(article_id,kind,path,script_hash,duration_s,status,attempts,error,updated_at)"
            " VALUES(?,?,?,?,NULL,?,?,?,?) ON CONFLICT(article_id,kind) DO UPDATE SET path=excluded.path,"
            " script_hash=excluded.script_hash, status=excluded.status, attempts=excluded.attempts,"
            " error=excluded.error, updated_at=excluded.updated_at",
            (item["id"], "video", path.name, h, status, (row["attempts"] if same else 0) + 1, err, now_iso))


def attach_media(conn, cfg, feed: dict) -> None:
    """Add audio_url / duration_s to prime items that have finished audio."""
    conn.executescript(ASSETS_SCHEMA)
    base = cfg.audio_base_url.rstrip("/")
    for item in feed["prime"]:
        r = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='audio' AND status='ok'",
                         (item["id"],)).fetchone()
        ok = r and r["script_hash"] == script_hash(item["script"])
        item["audio_url"] = f"{base}/{r['path']}" if ok else None
        item["duration_s"] = r["duration_s"] if ok else None
        v = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='video' AND status='ok'",
                         (item["id"],)).fetchone()
        vok = v and v["script_hash"] == script_hash(item["script"])
        if cfg.avatar_enabled:
            item["video_url"] = f"{base}/{v['path']}" if vok else None


def _monitor_image(item, cfg, out_dir, resolve, fetch):
    """The story image for the on-screen monitor: downloaded once, or a local fallback if that fails."""
    from PIL import Image
    cached = Path(out_dir) / "images" / f"{item['id']}.img"
    if fetch and item.get("image_url"):
        try:
            if not cached.exists():
                import httpx
                r = httpx.get(item["image_url"], timeout=cfg.http_timeout_seconds, follow_redirects=True,
                              headers={"User-Agent": cfg.user_agent})
                r.raise_for_status()
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(r.content)
            return Image.open(cached).convert("RGB")
        except Exception as e:
            cached.unlink(missing_ok=True)
            log.info("monitor image for %s unavailable (%s); using fallback", item["id"], type(e).__name__)
    fallbacks = cfg.avatar_fallback_images
    return Image.open(resolve(fallbacks[int(item["id"], 16) % len(fallbacks)])).convert("RGB")
