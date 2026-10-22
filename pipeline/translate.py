"""Translated headlines and summaries for the page's language picker (offline, via a `translate_command`).

For each language in `translate_languages` the unique English texts (headline, summary) of the issue that are not yet in
the cache are sent to the translator in ONE call (JSON list in, JSON list out), and the results are cached by a hash of
the text, so a rerun only translates what is new. The page loads `translations/<locale>.json` ({id: {headline, summary}})
only when a reader picks that language; the feed lists which languages exist as `translations_available`.
Audio and video stay in English.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from pathlib import Path

log = logging.getLogger(__name__)

# the picker's locale -> the translator's language code
M2M = {"zh-CN": "zh", "hi-IN": "hi", "es-ES": "es", "fr-FR": "fr", "pt-BR": "pt", "ru-RU": "ru",
       "ja-JP": "ja", "fil": "tl", "nb": "no", "sr": "sr", "he": "he"}


def lang_code(locale: str) -> str:
    return M2M.get(locale, locale.split("-")[0])


def _key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def _items(feed: dict) -> list:
    return [i for slot in ("prime", "cards", "glance") for i in feed.get(slot, [])]


def _texts(feed: dict) -> list:
    seen, out = set(), []
    for item in _items(feed):
        for t in (item["headline"], item.get("summary", "")):
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def _call(cfg, locale: str, texts: list) -> list:
    cmd = [a.replace("{lang}", lang_code(locale)) for a in cfg.translate_command]
    res = subprocess.run(cmd, input=json.dumps(texts).encode(), capture_output=True, timeout=cfg.translate_timeout_seconds)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode(errors="replace")[-300:] or f"translator exited {res.returncode}")
    out = json.loads(res.stdout.decode())
    if not isinstance(out, list) or len(out) != len(texts):
        raise RuntimeError("translator must return a JSON list with one string per input")
    return [str(x) for x in out]


def build_translations(cfg, feed: dict, out_dir, cache_path, now_monotonic=time.monotonic) -> dict:
    cache_path, out_dir = Path(cache_path), Path(out_dir)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    texts, started = _texts(feed), now_monotonic()
    stats = {"languages": 0, "translated": 0, "failed": 0, "deferred": 0}
    for locale in cfg.translate_languages:
        have = cache.setdefault(locale, {})
        missing = [t for t in texts if _key(t) not in have]
        if missing:
            if now_monotonic() - started > cfg.translate_time_budget_seconds:
                stats["deferred"] += 1
                continue
            try:
                for t, tr in zip(missing, _call(cfg, locale, missing)):
                    have[_key(t)] = tr
                stats["translated"] += len(missing)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = cache_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(cache, ensure_ascii=False))
                os.replace(tmp, cache_path)                      # saved per language: a crash keeps what was done
            except Exception as e:
                log.warning("translation to %s failed: %s", locale, str(e)[:200])
                stats["failed"] += 1
                continue
        stats["languages"] += 1
    return stats


def attach_translations(cfg, feed: dict, out_dir, cache_path) -> list:
    """Write translations/<locale>.json for every language whose texts are all cached; list them in the feed."""
    cache_path, out_dir = Path(cache_path), Path(out_dir)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    available = []
    for locale in cfg.translate_languages:
        have = cache.get(locale, {})
        data = {}
        for item in _items(feed):
            h, s = have.get(_key(item["headline"])), have.get(_key(item.get("summary", "")), "")
            if h is None:
                break
            data[item["id"]] = {"headline": h, "summary": s}
        else:
            target = out_dir / "translations" / f"{locale}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False))
            os.replace(tmp, target)
            available.append(locale)
    feed["translations_available"] = available
    return available
