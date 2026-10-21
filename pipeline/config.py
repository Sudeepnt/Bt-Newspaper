"""Load and validate config.yaml / sources.yaml."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent
SOURCE_TYPES = ("rss", "sitemap")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    name: str
    type: str
    url: str
    weight: int
    category: str

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")


@dataclass(frozen=True)
class Config:
    user_agent: str = "BoughtNewsBot/0.1"
    http_timeout_seconds: float = 15
    fetch_attempts: int = 3
    max_items_per_source: int = 60
    max_age_hours: float = 48
    filtered_size: int = 50
    slots: dict = field(default_factory=lambda: {"prime": 25, "cards": 25, "glance": 10})
    category_cap: float = 0.4
    category_balance_max_bonus: float = 2.0
    dedupe_jaccard: float = 0.7
    og_fallback: bool = True
    og_min_interval_seconds: float = 1.5
    og_max_per_source: int = 15


def load_config(path=None) -> Config:
    path = Path(path) if path else PKG_DIR / "config.yaml"
    raw = yaml.safe_load(path.read_text()) or {}
    unknown = set(raw) - set(Config.__dataclass_fields__)
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    cfg = Config(**raw)
    if set(cfg.slots) != {"prime", "cards", "glance"} or any(
        not isinstance(n, int) or n < 0 for n in cfg.slots.values()
    ):
        raise ConfigError("slots must define non-negative ints for prime, cards, glance")
    if not 0 < cfg.category_cap <= 1:
        raise ConfigError("category_cap must be in (0, 1]")
    return cfg


def load_sources(path=None) -> list:
    path = Path(path) if path else PKG_DIR / "sources.yaml"
    raw = yaml.safe_load(path.read_text()) or {}
    out, seen = [], set()
    for i, s in enumerate(raw.get("sources") or []):
        try:
            src = Source(
                name=str(s["name"]).strip(), type=str(s["type"]).strip().lower(),
                url=str(s["url"]).strip(), weight=int(s["weight"]),
                category=str(s["category"]).strip(),
            )
        except KeyError as e:
            raise ConfigError(f"sources[{i}] is missing {e}") from None
        if src.type not in SOURCE_TYPES:
            raise ConfigError(f"{src.name}: type must be one of {SOURCE_TYPES}")
        if not 1 <= src.weight <= 5:
            raise ConfigError(f"{src.name}: weight must be 1-5")
        if not src.name or not src.category or not src.url.startswith(("http://", "https://")):
            raise ConfigError(f"sources[{i}]: name, category and an http(s) url are required")
        if src.name in seen:
            raise ConfigError(f"duplicate source name: {src.name}")
        seen.add(src.name)
        out.append(src)
    return out
