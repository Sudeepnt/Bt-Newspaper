"""Text helpers: HTML stripping, our own short summaries, title normalisation."""
from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser

MAX_SUMMARY_CHARS = 300

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])["”’)]*\s+(?=["“‘(]?[A-Z0-9])')
_WS = re.compile(r"\s+")
STOPWORDS = frozenset(
    "a an the to of in on for and or is are was were be as at by with from its it "
    "this that after over into than amid says say said".split()
)


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("p", "br", "div", "li"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def strip_html(value: str) -> str:
    if not value:
        return ""
    s = _Stripper()
    try:
        s.feed(value)
        s.close()
        text = "".join(s.parts)
    except Exception:  # malformed markup: fall back to a crude strip
        text = re.sub(r"<[^>]+>", " ", value)
    return _WS.sub(" ", html.unescape(text)).strip()


def short_summary(raw: str, sentences: int = 2, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Extractive summary: first `sentences` sentences of the feed blurb, <= max_chars."""
    text = strip_html(raw)
    if not text:
        return ""
    picked = " ".join(_SENTENCE_SPLIT.split(text)[:sentences]).strip()
    if len(picked) <= max_chars:
        return picked
    cut = picked[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut + "…"


def clean_title(raw: str) -> str:
    return _WS.sub(" ", strip_html(raw)).strip()


def title_tokens(title: str) -> frozenset:
    """Normalised, stopword-free, lightly stemmed tokens for near-duplicate matching."""
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    out = set()
    for tok in re.findall(r"[a-z0-9]+", t):
        if tok in STOPWORDS:
            continue
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        out.add(tok)
    return frozenset(out)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
