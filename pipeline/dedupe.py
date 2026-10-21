"""Stage 3: reject exact-URL (handled by UNIQUE) and near-duplicate titles."""
from __future__ import annotations

from .db import transaction
from .text import jaccard, title_tokens


def find_duplicates(rows, threshold: float) -> dict:
    """rows: dicts with id, title, source_weight, published_at. Returns {loser_id: winner_id}.

    The keeper is the higher-weight source; ties go to the earlier published, then lower id.
    Winners are transitive-safe: a loser is never used as a winner for later comparisons.
    """
    ordered = sorted(rows, key=lambda r: (-r["source_weight"], r["published_at"], r["id"]))
    kept, losers = [], {}
    for r in ordered:
        toks = title_tokens(r["title"])
        match = next(
            (k for k, kt in kept
             if toks == kt or (len(toks) >= 3 and len(kt) >= 3 and jaccard(toks, kt) >= threshold)),
            None,
        )
        if match is None:
            kept.append((r, toks))
        else:
            losers[r["id"]] = match["id"]
    return losers


def dedupe(conn, cfg) -> int:
    rows = [dict(r) for r in conn.execute(
        "SELECT id, title, source_weight, published_at FROM articles"
        " WHERE status NOT IN ('rejected','expired')")]
    losers = find_duplicates(rows, cfg.dedupe_jaccard)
    with transaction(conn):
        conn.executemany(
            "UPDATE articles SET status='rejected', reject_reason=? WHERE id=?",
            [(f"duplicate_of:{w}", l) for l, w in losers.items()])
    return len(losers)
