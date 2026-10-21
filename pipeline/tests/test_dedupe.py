from pipeline.dedupe import find_duplicates


def row(id, title, weight, published="2026-10-20T10:00:00Z"):
    return {"id": id, "title": title, "source_weight": weight, "published_at": published}


def test_keeps_higher_weight_source():
    rows = [row("low", "Chip stocks climb as suppliers raise forecasts", 2),
            row("high", "Chip stocks climb after strong supplier forecasts", 5)]
    assert find_duplicates(rows, 0.7) == {"low": "high"}


def test_tie_prefers_earlier_published():
    rows = [row("late", "Founders test ideas using prototypes before launch", 3, "2026-10-20T11:00:00Z"),
            row("early", "Founders test ideas with prototypes before launch", 3, "2026-10-20T09:00:00Z")]
    assert find_duplicates(rows, 0.7) == {"late": "early"}


def test_different_stories_survive():
    rows = [row("a", "Chip stocks climb on supplier forecasts", 3),
            row("b", "Chip shortage slows some AI training projects", 3)]
    assert find_duplicates(rows, 0.7) == {}


def test_short_titles_only_match_exactly():
    rows = [row("a", "Fed holds rates", 3), row("b", "Fed holds", 3)]
    assert find_duplicates(rows, 0.7) == {}
    assert find_duplicates([row("a", "Fed holds!", 3), row("b", "fed HOLDS", 3)], 0.7) != {}


def test_threshold_boundary():
    a, b = "alpha beta gamma delta epsilon", "alpha beta gamma delta zeta"  # jaccard 4/6
    rows = [row("a", a, 3), row("b", b, 2)]
    assert find_duplicates(rows, 0.66) == {"b": "a"}
    assert find_duplicates(rows, 0.7) == {}
