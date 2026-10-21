from pipeline.text import jaccard, short_summary, title_tokens


def test_summary_is_first_two_sentences_and_plain_text():
    raw = "<p>First point. Second point &amp; more.</p><p>Third sentence is dropped.</p>"
    assert short_summary(raw) == "First point. Second point & more."


def test_summary_capped_at_300_chars_on_word_boundary():
    out = short_summary("word " * 200)
    assert len(out) <= 300 and out.endswith("…") and "  " not in out


def test_summary_empty():
    assert short_summary("") == "" and short_summary("<img src=x>") == ""


def test_title_tokens_ignore_case_punctuation_stopwords_plurals():
    assert title_tokens("The AI Agents: new tools!") == title_tokens("AI agent new tool")


def test_jaccard():
    a, b = title_tokens("chip stocks climb"), title_tokens("chip stocks fall")
    assert jaccard(a, a) == 1.0 and jaccard(a, b) == 0.5 and jaccard(a, frozenset()) == 0.0
