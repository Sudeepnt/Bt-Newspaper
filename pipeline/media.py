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
    return subprocess.run(cmd, capture_output=True, check=True, timeout=kw.pop("timeout", 120), **kw)


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


def build_media(conn, cfg, feed: dict, out_dir, now_iso: str, synth=synthesize) -> dict:
    """Make audio for each prime item that lacks it. Safe to rerun; stops at the time budget."""
    conn.executescript(ASSETS_SCHEMA)
    out_dir = Path(out_dir)
    stats = {"made": 0, "skipped": 0, "failed": 0, "deferred": 0}
    deadline = time.monotonic() + cfg.media_time_budget_seconds
    for item in sorted(feed["prime"], key=lambda i: i["published_at"], reverse=True):  # newest first
        script = item["script"]
        row = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='audio'", (item["id"],)).fetchone()
        path = out_dir / f"{item['id']}.mp3"
        if row and row["status"] == "ok" and row["script_hash"] == script_hash(script) and path.exists():
            stats["skipped"] += 1
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
    return stats


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
