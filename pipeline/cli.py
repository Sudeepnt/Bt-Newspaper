from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone

from . import db
from .config import ConfigError, load_config, load_sources
from .ingest import parse_iso
from .runner import fixture_now, paths, run_cycle


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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_common(sub.add_parser("run", help="one full cycle"))
    _add_common(sub.add_parser("show", help="print the current selection"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        return {"run": cmd_run, "show": cmd_show}[args.cmd](args)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
