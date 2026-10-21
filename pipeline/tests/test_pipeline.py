import json
import sqlite3
from datetime import datetime, timezone

from pipeline.config import load_config, load_sources
from pipeline.ingest import FixtureFetcher, parse_feed, parse_sitemap
from pipeline.runner import FIXTURES, fixture_now, run_cycle


def run(tmp_path, cfg=None, name="a"):
    cfg = cfg or load_config()
    return run_cycle(cfg, load_sources(), dry_run=True, db_path=tmp_path / f"{name}.db",
                     out_path=tmp_path / f"{name}.json"), tmp_path / f"{name}.json"


def feed_without_time(path):
    d = json.loads(path.read_text())
    d.pop("generated_at")
    return d


def test_feed_shape_counts_and_rules(tmp_path):
    res, out = run(tmp_path)
    feed = json.loads(out.read_text())
    assert [len(feed[s]) for s in ("prime", "cards", "glance")] == [25, 25, 10]
    for slot, n in (("prime", 25), ("cards", 25), ("glance", 10)):
        ids = [i["id"] for i in feed[slot]]
        assert len(ids) == len(set(ids))  # same story never twice in one slot
        cats = [i["category"] for i in feed[slot]]
        assert max(cats.count(c) for c in set(cats)) <= int(n * 0.4)
    keys = {"id", "headline", "summary", "source", "link", "image_url", "image_credit", "published_at"}
    assert all(keys <= set(i) for s in ("prime", "cards", "glance") for i in feed[s])
    assert all("script" in i for i in feed["prime"]) and not any("script" in i for i in feed["cards"])
    now = fixture_now()
    for i in feed["prime"] + feed["cards"] + feed["glance"]:
        age = (now - datetime.strptime(i["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
        assert age.total_seconds() <= 48 * 3600
        assert i["image_url"] and i["headline"] and len(i["summary"]) <= 300
        assert "utm_" not in i["link"]


def test_rerun_is_idempotent(tmp_path):
    cfg, sources = load_config(), load_sources()
    kw = dict(dry_run=True, db_path=tmp_path / "n.db", out_path=tmp_path / "n.json")
    run_cycle(cfg, sources, **kw)
    first = feed_without_time(tmp_path / "n.json")
    second = run_cycle(cfg, sources, **kw)
    assert feed_without_time(tmp_path / "n.json") == first
    assert all(s["new"] == 0 for s in second["ingest"].values())
    c = sqlite3.connect(tmp_path / "n.db")
    assert c.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 73
    assert c.execute("SELECT COUNT(*) FROM selections").fetchone()[0] == 60


def test_statuses_and_rejections(tmp_path):
    run(tmp_path)
    c = sqlite3.connect(tmp_path / "a.db")
    reasons = dict(c.execute("SELECT reject_reason, COUNT(*) FROM articles WHERE status='rejected'"
                             " GROUP BY reject_reason").fetchall())
    assert reasons.get("no_image") == 5
    assert sum(v for k, v in reasons.items() if k.startswith("duplicate_of")) == 2
    statuses = {r[0] for r in c.execute("SELECT DISTINCT status FROM articles")}
    assert statuses <= {"new", "selected_prime", "selected_card", "selected_glance", "rejected", "expired"}
    # canonical-url uniqueness is enforced by the schema
    assert c.execute("SELECT COUNT(*) - COUNT(DISTINCT canonical_url) FROM articles").fetchone()[0] == 0


def test_slot_split_is_config(tmp_path):
    cfg = load_config()
    cfg = type(cfg)(**{**cfg.__dict__, "slots": {"prime": 5, "cards": 6, "glance": 3}})
    _, out = run(tmp_path, cfg)
    feed = json.loads(out.read_text())
    assert [len(feed[s]) for s in ("prime", "cards", "glance")] == [5, 6, 3]


def test_broken_source_does_not_stop_cycle(tmp_path):
    class Flaky(FixtureFetcher):
        def fetch(self, source, state):
            if source.name == "Placeholder AI":
                raise TimeoutError("boom")
            return super().fetch(source, state)

    res = run_cycle(load_config(), load_sources(), dry_run=True, db_path=tmp_path / "f.db",
                    out_path=tmp_path / "f.json", fetcher=Flaky(FIXTURES))
    assert "boom" in res["ingest"]["Placeholder AI"]["error"]
    assert res["ingest"]["Placeholder Technology"]["new"] > 0
    assert (tmp_path / "f.json").exists()


def test_parse_feed_extracts_image_credit_and_summary():
    src = load_sources()[0]
    items = parse_feed((FIXTURES / "placeholder-technology.xml").read_bytes(), src, fixture_now())
    first = items[0]
    assert first.image_url.startswith("https://example.com/images/") and first.image_credit
    assert first.summary.startswith(first.title) and "<" not in first.summary
    assert "utm_source" in first.link  # raw link; canonicalised later at ingest
    assert items[12].image_url is None  # the fixture item without an image


def test_parse_sitemap_news():
    xml = b"""<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
      xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"><url>
      <loc>https://example.com/a?utm_source=x</loc><news:news><news:title>Hello &amp; world</news:title>
      <news:publication_date>2026-10-20T09:00:00Z</news:publication_date></news:news>
      <image:image><image:loc>https://example.com/i.jpg</image:loc></image:image></url></urlset>"""
    [it] = parse_sitemap(xml, load_sources()[0], fixture_now())
    assert it.title == "Hello & world" and it.image_url == "https://example.com/i.jpg"
    assert it.published == datetime(2026, 10, 20, 9, tzinfo=timezone.utc)
