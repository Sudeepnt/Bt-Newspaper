"""Stage 5: write feed.json from the selections table."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .db import SLOTS


def build_feed(conn, cfg, generated_at: str) -> dict:
    feed = {"generated_at": generated_at, "slots": dict(cfg.slots)}
    for slot in SLOTS:
        rows = conn.execute(
            "SELECT a.* FROM selections s JOIN articles a ON a.id = s.article_id"
            " WHERE s.slot=? ORDER BY s.rank", (slot,)).fetchall()
        items = []
        for r in rows:
            item = {
                "id": r["id"], "headline": r["title"], "summary": r["summary"],
                "source": r["source"], "category": r["category"], "link": r["canonical_url"],
                "image_url": r["image_url"], "image_credit": r["image_credit"],
                "published_at": r["published_at"],
            }
            if slot == "prime":
                item["script"] = None  # Phase 2 fills this in
            items.append(item)
        feed[slot] = items
    return feed


def write_feed(feed: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)  # readers never see a half-written file
    return path
