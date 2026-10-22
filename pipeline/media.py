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
from .text import spoken_summary

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
    parts = [sentence(item["category"]), sentence(item["headline"]),
             sentence(spoken_summary(item["headline"], item["summary"])),
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


def pick_voice(rank, cfg) -> str:
    """The voice for the story at this place in the feed: the voices take turns, so neighbours never sound alike."""
    voices = cfg.tts_voices
    return voices[(rank or 0) % len(voices)] if voices else ""


def synthesize(script: str, out_mp3: Path, cfg, speed=None, voice: str = "") -> float:
    """TTS -> wav -> mp3 via a temp file, then atomic rename. Returns duration in seconds."""
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    wav, tmp = out_mp3.with_suffix(".wav.tmp"), out_mp3.with_suffix(".mp3.tmp")
    try:
        speed = cfg.tts_speed if speed is None else speed
        cmd = [a.replace("{wav}", str(wav)).replace("{speed}", str(speed)).replace("{voice}", voice) for a in cfg.tts_command]
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
    video_cache = {}  # presenters, built once per run (one per look)
    ticker = [i["headline"] for i in feed["prime"]]
    ranks = {i["id"]: n for n, i in enumerate(feed["prime"])}   # place in the feed: the top stories share one look
    deadline = time.monotonic() + cfg.media_time_budget_seconds
    for item in sorted(feed["prime"], key=lambda i: i["published_at"], reverse=True):  # newest first
        script = item["script"]
        voice = pick_voice(ranks[item["id"]], cfg)
        key = script_hash(script + "|" + voice) if voice else script_hash(script)
        row = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='audio'", (item["id"],)).fetchone()
        path = out_dir / f"{item['id']}.mp3"
        if row and row["status"] == "ok" and row["script_hash"] == key and path.exists():
            stats["skipped"] += 1
            if cfg.avatar_enabled:
                _video(conn, cfg, item, path, out_dir, now_iso, video_cache, fetch_images, ticker, ranks[item["id"]])
            continue
        same_script = row and row["script_hash"] == key
        if row and row["status"] == "failed" and same_script and row["attempts"] >= cfg.media_max_attempts:
            stats["failed"] += 1
            continue
        if time.monotonic() >= deadline:
            stats["deferred"] += 1
            continue
        attempts = (row["attempts"] if same_script and row else 0) + 1
        try:
            duration = synth(script, path, cfg, voice=voice) if voice else synth(script, path, cfg)
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
                (item["id"], "audio", path.name, key, duration, status, attempts, err, now_iso))
        stats["made" if status == "ok" else "failed"] += 1
        if status == "ok" and cfg.avatar_enabled:
            _video(conn, cfg, item, path, out_dir, now_iso, video_cache, fetch_images, ticker, ranks[item["id"]])
    return stats


def _poster(avatar, path) -> None:
    """A missing still must never fail a finished video: the page falls back to loading the video's first frame."""
    try:
        avatar.extract_poster(path)
    except Exception as e:
        log.warning("poster failed for %s: %s", path.name, e)


RENDER_VERSION = "2"   # bump when the look of every video changes (v2: no photo credit on the picture, name strap)


def video_hash(item, cfg, rank=None) -> str:
    """Changes when the script or the story's look changes, so a new look re-renders its video."""
    from .styles import pick_look
    return script_hash(item["script"] + "|" + "|".join(pick_look(item, cfg, rank)) + "|" + cfg.avatar_name
                       + "|" + RENDER_VERSION + str(cfg.avatar_credit_on_video) + "|" + pick_voice(rank, cfg))


def _subhead(item, limit=96) -> str:
    """The last sentence of the summary, for the channel set's sub-line."""
    sentences = [s.strip() for s in item.get("summary", "").replace("? ", ". ").split(". ") if s.strip()]
    text = (sentences[-1] if sentences else "").rstrip(".") + "."
    return text if len(text) <= limit else text[:limit - 3].rsplit(" ", 1)[0] + "..."


def _video(conn, cfg, item, audio, out_dir, now_iso, cache, fetch_images=True, ticker=(), rank=None) -> None:
    """Presenter video for one story; same skip/retry rules as audio, keyed on the script hash and look."""
    from . import avatar  # Pillow/numpy only needed when avatar_enabled
    from .styles import build_presenter, pick_look, render_styled
    root = Path(__file__).resolve().parent.parent
    resolve = lambda p: Path(p) if Path(p).is_absolute() else root / p
    h = video_hash(item, cfg, rank)
    look = pick_look(item, cfg, rank)
    path = out_dir / f"{item['id']}.mp4"
    row = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='video'", (item["id"],)).fetchone()
    same = row and row["script_hash"] == h
    if same and row["status"] == "ok" and path.exists():
        _poster(avatar, path)                           # videos rendered before posters existed get theirs now
        return
    if same and row["status"] == "failed" and row["attempts"] >= cfg.media_max_attempts:
        return
    try:
        if look not in cache:
            cache[look] = build_presenter(look[0], look[1], cfg, resolve)
        shot = _monitor_image(item, cfg, out_dir, resolve, fetch_images)
        credit = (item.get("image_credit") or "") if cfg.avatar_credit_on_video else ""
        if look[1] == "studio":
            avatar.render_video(audio, path, cache[look], item["headline"], shot, credit, cfg.avatar_channel,
                                resolve(cfg.avatar_font), seed=item["id"], cutaway_chance=cfg.avatar_cutaway_chance,
                                journalist=(cfg.avatar_name, cfg.avatar_name_tag))
        else:
            render_styled(look[1], audio, path, cache[look], item["headline"], shot, credit, cfg.avatar_channel,
                          resolve(cfg.avatar_font), seed=item["id"], cutaway_chance=cfg.avatar_cutaway_chance,
                          category=item.get("category", ""), ticker=[t for t in ticker if t != item["headline"]][:8],
                          script=item["script"], subhead=_subhead(item), journalist=(cfg.avatar_name, cfg.avatar_name_tag))
        path.with_suffix(".jpg").unlink(missing_ok=True)     # a new render needs a new still, not the old video's
        _poster(avatar, path)
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
    for rank, item in enumerate(feed["prime"]):
        r = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='audio' AND status='ok'",
                         (item["id"],)).fetchone()
        voice = pick_voice(rank, cfg)
        ok = r and r["script_hash"] == (script_hash(item["script"] + "|" + voice) if voice else script_hash(item["script"]))
        item["audio_url"] = f"{base}/{r['path']}" if ok else None
        item["duration_s"] = r["duration_s"] if ok else None
        v = conn.execute("SELECT * FROM assets WHERE article_id=? AND kind='video' AND status='ok'",
                         (item["id"],)).fetchone()
        vok = v and v["script_hash"] == video_hash(item, cfg, rank)
        if cfg.avatar_enabled:
            item["video_url"] = f"{base}/{v['path']}" if vok else None
            item["poster_url"] = f"{base}/{Path(v['path']).with_suffix('.jpg').name}" if vok else None


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
    return Image.open(resolve(_pick_fallback(item, cfg))).convert("RGB")


def _pick_fallback(item, cfg) -> str:
    """Best-matching stand-in picture: most keyword hits in headline/summary/category, else a stable pick."""
    text = " ".join(str(item.get(k) or "") for k in ("headline", "summary", "category")).lower()
    words = set(re.findall(r"[a-z0-9]+", text))
    best, score = None, 0
    for image, keywords in cfg.avatar_fallback_keywords.items():
        hits = sum(1 for k in keywords if k in words or (len(k) > 4 and k in text))
        if hits > score:
            best, score = image, hits
    pool = cfg.avatar_fallback_images
    return best or pool[int(item["id"], 16) % len(pool)]
