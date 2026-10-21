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
    # Phase 2a: audio for prime stories. tts_command reads the script on stdin and writes {wav}.
    media_enabled: bool = False
    tts_command: tuple = ()
    tts_timeout_seconds: float = 120
    audio_base_url: str = "/media"
    media_time_budget_seconds: float = 900     # keeps a 30-min cron from overlapping itself
    media_max_attempts: int = 3
    script_max_chars: int = 600
    # The daily podcast: every story in one narrated episode (needs media_enabled for the TTS engine).
    podcast_enabled: bool = False
    podcast_stories: int = 50
    podcast_speed: float = 1.0
    podcast_gap_seconds: float = 0.7
    podcast_time_budget_seconds: float = 1500
    # Translations for the page's language picker. translate_command reads a JSON list on stdin and prints a JSON list
    # ({lang} is replaced by the language code); see translate_m2m.py. Locales are the picker's, e.g. hi-IN, es-ES, ar.
    translate_languages: tuple = ()
    translate_command: tuple = ()
    translate_timeout_seconds: float = 1800
    translate_time_budget_seconds: float = 3000
    # Badges on stories (see badges.py). Off by default; the "most" badges need engagement_file from the page's collector.
    badges_enabled: bool = False
    badges_exclusive_sources: tuple = ()
    badges_new_hours: float = 3
    badges_min_events: int = 30
    badges_max_per_type: int = 3           # AI / New go to the first few stories only, so badges stay special
    engagement_file: str = ""
    # Phase 2b: presenter video (needs media_enabled). Paths are relative to the project root.
    avatar_enabled: bool = False
    avatar_image: str = "pipeline/assets/presenter_cutout.png"   # transparent PNG, 1280x720 design space
    avatar_size: tuple = (1280, 720)           # 16:9 news frame, the native design size (no downscaling)
    avatar_font: str = "public/assets/font-0.ttf"
    avatar_channel: str = "BOUGHT."
    avatar_cutaway_chance: float = 0.6         # share of stories where the visual goes full screen and she steps out
    # A look per category = which host and which set: {category: {character: photo|anime|mascot, style: studio|channel|funky}}.
    # Empty = every video uses the original photo presenter in the blue studio. Unlisted categories rotate through the looks.
    avatar_looks: dict = field(default_factory=dict)
    avatar_fallback_keywords: dict = field(default_factory=lambda: {   # stand-in picture -> words that pick it
        "public/assets/swipe-data-center.jpg": ["chip", "chips", "chipmakers", "processors", "data", "cloud", "server",
                                                "servers", "capacity", "computing", "quantum", "semiconductor", "network", "operating",
                                                "system", "systems", "linux"],
        "public/assets/swipe-robotics.jpg": ["ai", "robot", "robots", "agent", "agents", "model", "models", "machine",
                                             "automation", "autonomous", "humanoid", "software"],
        "public/assets/swipe-founders.jpg": ["startup", "startups", "founder", "founders", "funding", "raises", "investors",
                                             "venture", "company", "launches", "product"],
        "public/assets/swipe-battery.jpg": ["battery", "batteries", "charging", "energy", "electric", "ev", "power",
                                            "solar", "grid", "bus", "buses"],
        "public/assets/swipe-rocket.jpg": ["satellite", "satellites", "space", "rocket", "orbit", "launch", "broadband",
                                           "geopolitics", "defense", "security", "cybersecurity"],
    })
    avatar_fallback_images: tuple = ("public/assets/swipe-data-center.jpg", "public/assets/swipe-robotics.jpg",
                                     "public/assets/swipe-founders.jpg", "public/assets/swipe-battery.jpg",
                                     "public/assets/swipe-rocket.jpg")


def load_config(path=None) -> Config:
    path = Path(path) if path else PKG_DIR / "config.yaml"
    raw = yaml.safe_load(path.read_text()) or {}
    unknown = set(raw) - set(Config.__dataclass_fields__)
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    if isinstance(raw.get("tts_command"), list):
        raw["tts_command"] = tuple(map(str, raw["tts_command"]))
    for key in ("translate_languages", "translate_command"):
        if isinstance(raw.get(key), list):
            raw[key] = tuple(map(str, raw[key]))
    if isinstance(raw.get("badges_exclusive_sources"), list):
        raw["badges_exclusive_sources"] = tuple(map(str, raw["badges_exclusive_sources"]))
    if isinstance(raw.get("avatar_fallback_images"), list):
        raw["avatar_fallback_images"] = tuple(raw["avatar_fallback_images"])
    if isinstance(raw.get("avatar_size"), list):
        raw["avatar_size"] = tuple(raw["avatar_size"])
    cfg = Config(**raw)
    if set(cfg.slots) != {"prime", "cards", "glance"} or any(
        not isinstance(n, int) or n < 0 for n in cfg.slots.values()
    ):
        raise ConfigError("slots must define non-negative ints for prime, cards, glance")
    if not 0 < cfg.category_cap <= 1:
        raise ConfigError("category_cap must be in (0, 1]")
    for cat, look in cfg.avatar_looks.items():
        if not isinstance(look, dict) or look.get("character") not in ("photo", "anime", "mascot") \
                or look.get("style") not in ("studio", "channel", "funky"):
            raise ConfigError(f"avatar_looks[{cat!r}] needs character: photo|anime|mascot and style: studio|channel|funky")
    if cfg.avatar_enabled and not cfg.media_enabled:
        raise ConfigError("avatar_enabled needs media_enabled (the video is driven by the audio)")
    if cfg.translate_languages and not cfg.translate_command:
        raise ConfigError("translate_languages needs translate_command")
    if cfg.podcast_enabled and not cfg.tts_command:
        raise ConfigError("podcast_enabled needs tts_command")
    if cfg.media_enabled and not cfg.tts_command:
        raise ConfigError("media_enabled needs tts_command")
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
