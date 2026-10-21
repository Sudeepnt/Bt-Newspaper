"""LiveFetcher against httpx.MockTransport: no real network."""
import httpx
import pytest

from pipeline.config import load_config, load_sources
from pipeline.ingest import LiveFetcher, ingest_source, iso
from pipeline.runner import FIXTURES, fixture_now
from pipeline import db

CFG = load_config()
CFG = type(CFG)(**{**CFG.__dict__, "og_min_interval_seconds": 0, "fetch_attempts": 2})
SRC = load_sources()[0]


def fetcher(handler):
    f = LiveFetcher(CFG, httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True))
    return f


def test_blocked_source_raises_clear_error_and_is_recorded(tmp_path):
    f = fetcher(lambda r: httpx.Response(403))
    conn = db.connect(tmp_path / "x.db")
    st = ingest_source(conn, SRC, f, CFG, fixture_now())
    assert "blocks or requires auth" in st["error"]
    assert conn.execute("SELECT last_error FROM fetch_state").fetchone()[0] == st["error"]


def test_retries_5xx_then_succeeds(monkeypatch):
    monkeypatch.setattr("pipeline.ingest.time.sleep", lambda s: None)
    calls = []
    body = (FIXTURES / "placeholder-technology.xml").read_bytes()

    def h(r):
        calls.append(1)
        return httpx.Response(503) if len(calls) == 1 else httpx.Response(200, content=body, headers={"etag": "v1"})

    res = fetcher(h).fetch(SRC, None)
    assert len(calls) == 2 and res.etag == "v1"


def test_conditional_get_sends_validators_and_handles_304():
    seen = {}

    def h(r):
        seen.update(r.headers)
        return httpx.Response(304)

    state = {"etag": "v1", "last_modified": "Mon, 19 Oct 2026 10:00:00 GMT"}
    assert fetcher(h).fetch(SRC, state).not_modified
    assert seen["if-none-match"] == "v1" and "if-modified-since" in seen


def page(html, status=200):
    def h(r):
        if r.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private/")
        return httpx.Response(status, text=html)
    return h


def test_og_image_found_relative_resolved_and_robots_respected():
    f = fetcher(page('<html><head><meta property="og:image" content="/img/a.jpg"></head><body>'))
    assert f.og_image("https://example.com/news/1") == ("https://example.com/img/a.jpg", True)
    assert f.og_image("https://example.com/private/1") == (None, True)  # disallowed: not fetched


def test_og_transient_failure_is_retryable_but_404_is_final():
    assert fetcher(page("", 503)).og_image("https://example.com/n")[1] is False
    assert fetcher(page("", 404)).og_image("https://example.com/n") == (None, True)


def test_og_failure_leaves_item_out_so_next_run_retries(tmp_path):
    feed = (FIXTURES / "placeholder-technology.xml").read_bytes()

    def h(r):
        if r.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        if r.url.path.endswith("technology.xml"):
            return httpx.Response(200, content=feed)
        return httpx.Response(503)  # article pages are down

    conn = db.connect(tmp_path / "o.db")
    st = ingest_source(conn, SRC, fetcher(h), CFG, fixture_now())
    n = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert st["new"] == n and n == 13  # 16 items - 2 expired-age - 1 imageless-and-unreachable
