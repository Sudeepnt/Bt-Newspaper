"""Fetch sources, parse items, store new articles. Re-running never duplicates rows."""
from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from calendar import timegm
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import feedparser
import httpx

from .db import article_id, transaction
from .text import clean_title, short_summary
from .urls import canonicalize_url

log = logging.getLogger(__name__)
MAX_PAGE_BYTES = 512 * 1024
IMG_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.I)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class Item:
    title: str
    link: str
    published: Optional[datetime]
    summary: str
    image_url: Optional[str] = None
    image_credit: Optional[str] = None


@dataclass
class FetchResult:
    content: Optional[bytes] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    not_modified: bool = False


# ---------- parsing ----------

def _http_url(value) -> Optional[str]:
    value = (value or "").strip()
    return value if value.startswith(("http://", "https://")) else None


def _entry_image(entry) -> tuple:
    """(image_url, credit) from media:content, media:thumbnail, enclosures, or inline <img>."""
    best, best_w = None, -1
    for m in entry.get("media_content", []) or []:
        url = _http_url(m.get("url"))
        if url and (m.get("medium") == "image" or str(m.get("type", "")).startswith("image/")
                    or not m.get("type") and not m.get("medium")):
            w = int(m.get("width") or 0) if str(m.get("width") or "0").isdigit() else 0
            if w > best_w:
                best, best_w = url, w
    if not best:
        for m in entry.get("media_thumbnail", []) or []:
            if _http_url(m.get("url")):
                best = m["url"].strip()
                break
    if not best:
        for link in entry.get("links", []) or []:
            if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image/"):
                best = _http_url(link.get("href"))
                if best:
                    break
    if not best:
        blob = " ".join(
            [entry.get("summary", "") or ""] + [c.get("value", "") for c in entry.get("content", []) or []]
        )
        m = IMG_RE.search(blob)
        best = _http_url(m.group(1)) if m else None
    credit = None
    for c in entry.get("media_credit", []) or []:
        if isinstance(c, dict) and c.get("content"):
            credit = c["content"].strip()
            break
    return best, credit


def parse_feed(content: bytes, source, now: datetime) -> list:
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"unparseable feed: {parsed.bozo_exception}")
    items = []
    for e in parsed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime.fromtimestamp(timegm(t), timezone.utc) if t else None
        image, credit = _entry_image(e)
        raw_summary = e.get("summary") or (e.get("content") or [{}])[0].get("value", "")
        items.append(Item(
            title=clean_title(e.get("title", "")), link=(e.get("link") or "").strip(),
            published=published, summary=short_summary(raw_summary),
            image_url=image, image_credit=credit,
        ))
    return items


_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}


def parse_sitemap(content: bytes, source, now: datetime) -> list:
    """Google News sitemap: <url><loc/><news:news><news:title/><news:publication_date/></news:news>."""
    root = ET.fromstring(content)
    if root.tag.endswith("sitemapindex"):
        raise ValueError("sitemap index not supported: point at a news sitemap")
    items = []
    for u in root.findall("sm:url", _NS):
        title = u.findtext("news:news/news:title", default="", namespaces=_NS)
        pub = u.findtext("news:news/news:publication_date", default="", namespaces=_NS).strip()
        try:
            published = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None
            if published and published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except ValueError:
            published = None
        items.append(Item(
            title=clean_title(title), link=(u.findtext("sm:loc", default="", namespaces=_NS) or "").strip(),
            published=published, summary="",
            image_url=_http_url(u.findtext("image:image/image:loc", default="", namespaces=_NS)),
        ))
    return items


# ---------- fetchers ----------

class _OgParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.image = None

    def handle_starttag(self, tag, attrs):
        if tag != "meta" or self.image:
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        if a.get("property", a.get("name", "")).lower() in ("og:image", "og:image:url", "twitter:image"):
            self.image = a.get("content", "").strip() or None


class LiveFetcher:
    """HTTP access with timeouts, retries, robots.txt, and a per-host delay for page fetches."""

    def __init__(self, cfg, client: Optional[httpx.Client] = None):
        self.cfg = cfg
        self.client = client or httpx.Client(
            headers={"User-Agent": cfg.user_agent}, timeout=cfg.http_timeout_seconds,
            follow_redirects=True,
        )
        self._robots: dict = {}
        self._last_hit: dict = {}

    def fetch(self, source, state) -> FetchResult:
        headers = {}
        if state and state["etag"]:
            headers["If-None-Match"] = state["etag"]
        if state and state["last_modified"]:
            headers["If-Modified-Since"] = state["last_modified"]
        last_exc = None
        for attempt in range(self.cfg.fetch_attempts):
            try:
                r = self.client.get(source.url, headers=headers)
                if r.status_code == 304:
                    return FetchResult(not_modified=True)
                if r.status_code in (403, 401, 402, 451):
                    raise PermissionError(f"HTTP {r.status_code}: source blocks or requires auth/payment")
                if r.status_code == 429 or r.status_code >= 500:
                    raise httpx.HTTPStatusError(f"HTTP {r.status_code}", request=r.request, response=r)
                r.raise_for_status()
                return FetchResult(r.content, r.headers.get("etag"), r.headers.get("last-modified"))
            except PermissionError:
                raise
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(2 ** attempt)
        raise last_exc  # type: ignore[misc]

    def _wait_for_host(self, host: str) -> None:
        wait = self._last_hit.get(host, 0) + self.cfg.og_min_interval_seconds - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_hit[host] = time.monotonic()

    def _allowed(self, url: str):
        """True/False, or None if robots.txt could not be checked (retry later)."""
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            try:
                self._wait_for_host(parts.netloc)
                r = self.client.get(origin + "/robots.txt")
                if r.status_code >= 500:
                    self._robots[origin] = None
                elif r.status_code >= 400:
                    rp.parse([])  # no robots.txt: everything allowed
                    self._robots[origin] = rp
                else:
                    rp.parse(r.text.splitlines())
                    self._robots[origin] = rp
            except httpx.HTTPError:
                self._robots[origin] = None
        rp = self._robots[origin]
        return None if rp is None else rp.can_fetch(self.cfg.user_agent, url)

    def og_image(self, page_url: str) -> tuple:
        """(image_url or None, checked_ok). checked_ok=False means 'try again next run'."""
        allowed = self._allowed(page_url)
        if allowed is None:
            return None, False
        if not allowed:
            return None, True
        try:
            self._wait_for_host(urlsplit(page_url).netloc)
            with self.client.stream("GET", page_url) as r:
                if r.status_code >= 500 or r.status_code == 429:
                    return None, False
                if r.status_code >= 400:
                    return None, True
                buf = b""
                for chunk in r.iter_bytes():
                    buf += chunk
                    if len(buf) >= MAX_PAGE_BYTES or b"</head>" in buf.lower():
                        break
            p = _OgParser()
            p.feed(buf.decode("utf-8", "ignore"))
            return (_http_url(urljoin(page_url, p.image)) if p.image else None), True
        except httpx.HTTPError:
            return None, False

    def close(self):
        self.client.close()


class FixtureFetcher:
    """Dry-run fetcher: reads tests/fixtures/<source slug>.xml and never touches the network."""

    def __init__(self, fixtures_dir):
        self.dir = Path(fixtures_dir)

    def fetch(self, source, state) -> FetchResult:
        f = self.dir / f"{source.slug}.xml"
        if not f.exists():
            raise FileNotFoundError(f"no fixture for {source.name}: {f.name}")
        return FetchResult(f.read_bytes())

    def og_image(self, page_url):
        return None, True

    def close(self):
        pass


# ---------- orchestration ----------

def ingest_source(conn, source, fetcher, cfg, now: datetime) -> dict:
    stats = {"seen": 0, "new": 0, "skipped": 0, "error": None}
    state = conn.execute("SELECT * FROM fetch_state WHERE source=?", (source.name,)).fetchone()
    try:
        res = fetcher.fetch(source, state)
        if res.not_modified:
            _mark_fetch(conn, source.name, now, None, state["etag"], state["last_modified"])
            return stats
        parse = parse_feed if source.type == "rss" else parse_sitemap
        items = parse(res.content, source, now)[: cfg.max_items_per_source]
    except Exception as exc:  # one broken source must not stop the cycle
        stats["error"] = f"{type(exc).__name__}: {exc}"
        log.warning("source %s failed: %s", source.name, stats["error"])
        _mark_fetch(conn, source.name, now, stats["error"], state["etag"] if state else None,
                    state["last_modified"] if state else None)
        return stats

    cutoff = now - timedelta(hours=cfg.max_age_hours)
    og_budget = cfg.og_max_per_source if cfg.og_fallback else 0
    rows = []
    for it in items:
        stats["seen"] += 1
        try:
            url = canonicalize_url(it.link)
        except ValueError:
            stats["skipped"] += 1
            continue
        published = min(it.published or now, now)  # undated or future-dated -> now
        if not it.title or published < cutoff:
            stats["skipped"] += 1
            continue
        aid = article_id(url)
        if conn.execute("SELECT 1 FROM articles WHERE id=?", (aid,)).fetchone():
            continue
        image, credit = it.image_url, it.image_credit
        if not image and og_budget > 0:
            og_budget -= 1
            image, ok = fetcher.og_image(url)
            if not ok:  # transient failure: leave it out so the next run retries
                stats["skipped"] += 1
                continue
        rows.append((aid, url, source.name, source.category, source.weight, it.title, it.summary,
                     image, (credit or source.name) if image else None, iso(published), iso(now)))

    with transaction(conn):
        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO articles (id, canonical_url, source, category, source_weight,"
            " title, summary, image_url, image_credit, published_at, fetched_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        stats["new"] = conn.total_changes - before
        _mark_fetch(conn, source.name, now, None, res.etag, res.last_modified, in_tx=True)
    return stats


def _mark_fetch(conn, name, now, error, etag, last_modified, in_tx=False):
    def write():
        conn.execute(
            "INSERT INTO fetch_state (source, etag, last_modified, last_ok_at, last_error)"
            " VALUES (?,?,?,?,?) ON CONFLICT(source) DO UPDATE SET etag=excluded.etag,"
            " last_modified=excluded.last_modified,"
            " last_ok_at=CASE WHEN excluded.last_error IS NULL THEN excluded.last_ok_at ELSE last_ok_at END,"
            " last_error=excluded.last_error",
            (name, etag, last_modified, None if error else iso(now), error))
    if in_tx:
        write()
    else:
        with transaction(conn):
            write()


def ingest_all(conn, sources, fetcher, cfg, now: datetime) -> dict:
    return {s.name: ingest_source(conn, s, fetcher, cfg, now) for s in sources}
