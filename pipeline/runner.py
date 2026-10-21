"""One full cycle: ingest -> filter/expire -> dedupe -> score/select -> feed.json."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from . import db
from .dedupe import dedupe
from .ingest import FixtureFetcher, LiveFetcher, ingest_all, iso
from .output import build_feed, write_feed
from .scoring import prefilter, select

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "tests" / "fixtures"


def paths(dry_run: bool) -> tuple:
    if dry_run:
        return ROOT / "data" / "dry_run.db", ROOT / "out" / "dry_run" / "feed.json"
    return ROOT / "data" / "news.db", ROOT / "out" / "feed.json"


def fixture_now() -> datetime:
    """Dry runs use a fixed clock so the saved fixtures never go stale."""
    text = (FIXTURES / "NOW").read_text().strip()
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def run_cycle(cfg, sources, dry_run=False, now=None, db_path=None, out_path=None, fetcher=None) -> dict:
    default_db, default_out = paths(dry_run)
    db_path, out_path = db_path or default_db, out_path or default_out
    if dry_run:
        now = now or fixture_now()
        if db_path == default_db and Path(db_path).exists():
            for suffix in ("", "-wal", "-shm"):
                Path(str(db_path) + suffix).unlink(missing_ok=True)  # start dry runs clean
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    fetcher = fetcher or (FixtureFetcher(FIXTURES) if dry_run else LiveFetcher(cfg))
    conn = db.connect(db_path)
    try:
        ingest_stats = ingest_all(conn, sources, fetcher, cfg, now)
        prefilter(conn, cfg, now)
        dupes = dedupe(conn, cfg)
        sel = select(conn, cfg, now)
        feed = build_feed(conn, cfg, iso(now))
        write_feed(feed, out_path)
    finally:
        fetcher.close()
        conn.close()
    for name, st in ingest_stats.items():
        log.info("ingest %-24s seen=%d new=%d skipped=%d%s", name, st["seen"], st["new"], st["skipped"],
                 f" ERROR {st['error']}" if st["error"] else "")
    return {"ingest": ingest_stats, "duplicates_rejected": dupes, "selection": sel,
            "db": str(db_path), "feed": str(out_path)}
