"""SQLite storage. Every stage is a single transaction so reruns are safe."""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path

STATUSES = ("new", "selected_prime", "selected_card", "selected_glance", "rejected", "expired")
SLOTS = ("prime", "cards", "glance")
SLOT_STATUS = {"prime": "selected_prime", "cards": "selected_card", "glance": "selected_glance"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id            TEXT PRIMARY KEY,            -- sha1(canonical_url)[:16], stable across rebuilds
    canonical_url TEXT NOT NULL UNIQUE,
    source        TEXT NOT NULL,
    category      TEXT NOT NULL,
    source_weight INTEGER NOT NULL,
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL DEFAULT '',
    image_url     TEXT,
    image_credit  TEXT,
    published_at  TEXT NOT NULL,               -- ISO-8601 UTC
    fetched_at    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'new',
    score         REAL,
    reject_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE TABLE IF NOT EXISTS selections (        -- an article may appear in several slots
    slot       TEXT NOT NULL,
    rank       INTEGER NOT NULL,
    article_id TEXT NOT NULL REFERENCES articles(id),
    PRIMARY KEY (slot, article_id)
);
CREATE TABLE IF NOT EXISTS fetch_state (
    source        TEXT PRIMARY KEY,
    etag          TEXT,
    last_modified TEXT,
    last_ok_at    TEXT,
    last_error    TEXT
);
"""


def article_id(canonical_url: str) -> str:
    return hashlib.sha1(canonical_url.encode()).hexdigest()[:16]


def connect(path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)  # we manage transactions
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()
