from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone

from . import db
from .config import ConfigError, load_config, load_sources
from .ingest import parse_iso
from .runner import ROOT, fixture_now, paths, run_cycle


def _add_common(p):
    p.add_argument("--dry-run", action="store_true",
                   help="use saved fixtures (tests/fixtures), a fixed clock, and separate dry_run files")
    p.add_argument("--config", help="path to config.yaml")
    p.add_argument("--sources", help="path to sources.yaml")


def cmd_run(args) -> int:
    cfg, sources = load_config(args.config), load_sources(args.sources)
    result = run_cycle(cfg, sources, dry_run=args.dry_run)
    failed = [n for n, s in result["ingest"].items() if s["error"]]
    sel = result["selection"]
    print(f"ingested {sum(s['new'] for s in result['ingest'].values())} new | "
          f"duplicates rejected {result['duplicates_rejected']} | candidates {sel['candidates']} | "
          f"filtered {sel['filtered']} | prime {sel['prime']} cards {sel['cards']} glance {sel['glance']}")
    for slot, want in cfg.slots.items():
        if sel[slot] < want:
            print(f"WARNING: slot '{slot}' has {sel[slot]} of {want} (not enough eligible stories)")
    if failed:
        print(f"WARNING: {len(failed)} source(s) failed: {', '.join(failed)}")
    if result["media"]:
        print("audio: " + ", ".join(f"{k} {v}" for k, v in result["media"].items()))
    if result.get("podcast"):
        print("podcast: " + ", ".join(f"{k} {v}" for k, v in result["podcast"].items()))
    print(f"feed: {result['feed']}")
    return 0 if len(failed) < len(sources) else 1  # exit 1 only if every source failed


def cmd_show(args) -> int:
    cfg = load_config(args.config)
    db_path, _ = paths(args.dry_run)
    if not db_path.exists():
        print(f"no database at {db_path}; run `python -m pipeline run` first", file=sys.stderr)
        return 1
    now = fixture_now() if args.dry_run else datetime.now(timezone.utc)
    conn = db.connect(db_path)
    for slot in db.SLOTS:
        rows = conn.execute(
            "SELECT s.rank, a.score, a.category, a.source, a.published_at, a.title FROM selections s"
            " JOIN articles a ON a.id=s.article_id WHERE s.slot=? ORDER BY s.rank", (slot,)).fetchall()
        print(f"\n== {slot.upper()} ({len(rows)}/{cfg.slots[slot]}) ==")
        for r in rows:
            age = (now - parse_iso(r["published_at"])).total_seconds() / 3600
            print(f"{r['rank']:>2}. [{r['score']:5.2f}] {r['category'][:20]:<20} {r['source'][:22]:<22}"
                  f" {age:4.0f}h  {r['title'][:70]}")
    counts = conn.execute("SELECT status, COUNT(*) n FROM articles GROUP BY status ORDER BY status").fetchall()
    print("\nstatus counts: " + ", ".join(f"{r['status']}={r['n']}" for r in counts))
    return 0


def cmd_clip(args) -> int:
    from .clip import make_clip
    cfg = load_config(args.config)
    res = make_clip(args.spec, cfg, dry_run=args.dry_run)
    print(f"clip: {res['mp4']} ({res['duration_s']}s)" + (f" -> attached to feed item {res['attached_to']}" if res["attached_to"] else ""))
    print(f"laughs at {res['laughs']} | cutaways at {res['cutaways']}")
    return 0


def cmd_badges(args) -> int:
    """Recompute the badges on the current feed.json from the latest engagement counts (cheap: no ingest, no media)."""
    import json
    from .badges import assign_badges
    cfg = load_config(args.config)
    feed_path = paths(args.dry_run)[1]
    feed = json.loads(feed_path.read_text())
    counts = assign_badges(cfg, feed)
    feed_path.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("badges: " + (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"))
    return 0


def cmd_podcast(args) -> int:
    """Build (or finish building) the podcast episode for the current feed.json, without a new ingest."""
    import json
    from .podcast import attach_podcast, build_podcast
    cfg = load_config(args.config)
    if not cfg.tts_command:
        raise ConfigError("podcast needs tts_command")
    feed_path = paths(args.dry_run)[1]
    feed = json.loads(feed_path.read_text())
    cache = ROOT / "data" / ("podcast_dry_run" if args.dry_run else "podcast")
    res = build_podcast(cfg, feed, feed_path.parent / "media", cache)
    attached = attach_podcast(cfg, feed, feed_path.parent / "media")
    if attached:
        feed_path.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("podcast: " + ", ".join(f"{k} {v}" for k, v in res.items()) + (" -> attached to feed" if attached else ""))
    return 0 if res["complete"] else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_common(sub.add_parser("run", help="one full cycle"))
    _add_common(sub.add_parser("show", help="print the current selection"))
    _add_common(sub.add_parser("badges", help="refresh the story badges from the latest engagement counts"))
    _add_common(sub.add_parser("podcast", help="narrate every story into one episode (uses the existing feed.json)"))
    pc = sub.add_parser("clip", help="render a produced clip from a spec file (see pipeline/clips/)")
    pc.add_argument("spec")
    _add_common(pc)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        return {"run": cmd_run, "show": cmd_show, "clip": cmd_clip, "podcast": cmd_podcast, "badges": cmd_badges}[args.cmd](args)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
