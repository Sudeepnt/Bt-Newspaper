from datetime import datetime, timedelta, timezone

from pipeline.scoring import base_score, pick_filtered, pick_slot, recency_bonus

NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


def test_recency_bonus_scale():
    assert recency_bonus(NOW, NOW, 48) == 5.0
    assert recency_bonus(NOW - timedelta(hours=24), NOW, 48) == 2.5
    assert recency_bonus(NOW - timedelta(hours=48), NOW, 48) == 0.0
    assert recency_bonus(NOW - timedelta(hours=100), NOW, 48) == 0.0
    assert recency_bonus(NOW + timedelta(hours=3), NOW, 48) == 5.0  # clock skew


def test_base_score_weight_dominates_small_age_differences():
    assert base_score(5, NOW, NOW, 48) == 15.0
    assert base_score(3, NOW - timedelta(hours=24), NOW, 48) == 8.5
    assert base_score(5, NOW - timedelta(hours=24), NOW, 48) > base_score(3, NOW, NOW, 48)


def cand(i, cat, score, hour=0):
    return {"id": f"{i}", "category": cat, "score": score, "published_at": f"2026-10-20T{hour:02d}:00:00Z"}


def test_balance_bonus_lifts_underrepresented_category():
    cands = [cand(f"a{i}", "A", 10) for i in range(6)] + [cand("b0", "B", 9)]
    ids = [c["id"] for c in pick_filtered(cands, 4, max_bonus=2.0)]
    assert "b0" in ids[:2]  # B beats the 2nd A once A already holds its even share


def test_no_bonus_when_zero():
    cands = [cand(f"a{i}", "A", 10 - i * 0.1) for i in range(6)] + [cand("b0", "B", 5)]
    assert [c["id"] for c in pick_filtered(cands, 3, 0.0)] == ["a0", "a1", "a2"]


def test_slot_category_cap_forty_percent():
    ordered = [cand(f"a{i}", "A", 10) for i in range(20)] + [cand(f"b{i}", "B", 5) for i in range(20)]
    out = pick_slot(ordered, 10, 0.4)
    assert sum(c["category"] == "A" for c in out) == 4 and len(out) == 8  # B capped too: short slot


def test_slot_no_duplicates_and_prefers_unused_then_reuses():
    ordered = [cand(f"{c}{i}", c, 1) for i in range(4) for c in "ABC"]
    used = {"A0", "B0", "C0"}
    out = pick_slot(ordered, 12, 1.0, prefer_not_in=used)
    ids = [c["id"] for c in out]
    assert len(ids) == len(set(ids)) == 12
    assert set(ids[:9]).isdisjoint(used) and set(ids[9:]) == used  # reuse only to fill


def test_slot_zero_size():
    assert pick_slot([cand("a", "A", 1)], 0, 0.4) == []
