"""Badges on stories: what a story is, at a glance. Each item gets `badges: [{id, label}]` (at most two, strongest first).

  exclusive      its source is listed in `badges_exclusive_sources` (outlets we have an exclusive arrangement with; we
                 cannot know exclusivity from the feeds themselves, so this is configuration, never a guess)
  most-viewed    the most-played story of the issue  (engagement: views; prime and cards)
  most-read      the most-opened story of the issue  (engagement: reads; any slot)
  most-glanced   the most-seen story in the glance list (engagement: glances; glance slot)
  ai             category AI, or the headline is plainly about AI
  new            published within `badges_new_hours` of the feed time
  AI and New go to at most `badges_max_per_type` stories (the best-ranked ones), so a badge stays a signal.

The "most" badges come from reader counts in `engagement_file` (JSON {article_id: {views, reads, glances}}), written by
the page's collector. A winner needs at least `badges_min_events` of that count, so a quiet day shows none.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

LABELS = {"exclusive": "Exclusive", "most-viewed": "Most viewed", "most-read": "Most read", "most-glanced": "Most glanced",
          "ai": "AI", "new": "New"}
PRIORITY = ("exclusive", "most-viewed", "most-read", "most-glanced", "ai", "new")
MOST = {"most-viewed": ("views", ("prime", "cards")), "most-read": ("reads", ("prime", "cards", "glance")),
        "most-glanced": ("glances", ("glance",))}
AI_HEADLINE = re.compile(r"\b(AI|LLMs?|GPT|chatbots?|agentic|OpenAI|Anthropic)\b|\bgenerative\b|\bAI agents?\b")


def _parse(ts: str):
    return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")


def load_engagement(path) -> dict:
    p = Path(path) if path else None
    if not p or not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}                                           # a half-written file must not break the run


def assign_badges(cfg, feed: dict, engagement: dict | None = None) -> dict:
    engagement = engagement if engagement is not None else load_engagement(cfg.engagement_file)
    try:
        now = _parse(feed["generated_at"])
    except (KeyError, ValueError):
        now = None
    exclusive = {s.lower() for s in cfg.badges_exclusive_sources}
    earned = {}                                             # item id -> set of badge ids
    for slot in ("prime", "cards", "glance"):
        for item in feed.get(slot, []):
            got = earned.setdefault(item["id"], set())
            if item.get("source", "").lower() in exclusive:
                got.add("exclusive")
            if item.get("category") == "AI" or AI_HEADLINE.search(item.get("headline", "")):
                got.add("ai")
            if now and item.get("published_at"):
                try:
                    if 0 <= (now - _parse(item["published_at"])).total_seconds() <= cfg.badges_new_hours * 3600:
                        got.add("new")
                except ValueError:
                    pass
    for badge, (metric, slots) in MOST.items():             # one winner per badge; ties and thin counts win nothing
        pool = [(engagement.get(i["id"], {}).get(metric, 0), i["id"]) for s in slots for i in feed.get(s, [])]
        pool = [p for p in pool if p[0] >= cfg.badges_min_events]
        if pool:
            top = max(p[0] for p in pool)
            winners = [i for c, i in pool if c == top]
            if len(winners) == 1:
                earned[winners[0]].add(badge)
    for badge in ("ai", "new"):                             # only the first few (feed order = ranking) keep these
        holders = list(dict.fromkeys(                       # an article can sit in several slots: count it once
            i["id"] for s in ("prime", "cards", "glance") for i in feed.get(s, []) if badge in earned.get(i["id"], ())))
        for dropped in holders[cfg.badges_max_per_type:]:
            earned[dropped].discard(badge)
    counts = {}
    for slot in ("prime", "cards", "glance"):
        for item in feed.get(slot, []):
            ids = [b for b in PRIORITY if b in earned.get(item["id"], ())][:2]
            item["badges"] = [{"id": b, "label": LABELS[b]} for b in ids]
            for b in ids:
                counts[b] = counts.get(b, 0) + 1
    return counts
