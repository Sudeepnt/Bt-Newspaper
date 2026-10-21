# Dependency licenses

All runtime dependencies are open source; none needs an API key or a paid service. Versions are those
installed when this was written (license text taken from each package's own metadata).

## Direct

| Package | Version | License | Use |
|---|---|---|---|
| feedparser | 6.0.12 | BSD-2-Clause | RSS/Atom parsing |
| httpx | 0.28.1 | BSD-3-Clause | HTTP client |
| PyYAML | 6.0.3 | MIT | config files |
| pytest (dev only) | 8.4.2 | MIT | tests |

Everything else is the Python standard library (sqlite3, xml.etree, html.parser, urllib.robotparser).

## Transitive (runtime)

| Package | License |
|---|---|
| httpcore | BSD-3-Clause |
| h11 | MIT |
| anyio | MIT |
| idna | BSD-3-Clause |
| certifi | **MPL-2.0** (file-level copyleft; fine to use unmodified as a dependency) |
| sgmllib3k (via feedparser) | BSD |
| typing_extensions | PSF-2.0 (Python < 3.11 only) |
| exceptiongroup | MIT (Python < 3.11 only) |
| sniffio | MIT OR Apache-2.0 (per upstream; metadata was not installed here, re-check) |

Dev-only transitives (pytest): iniconfig MIT, pluggy MIT, packaging Apache-2.0 OR BSD-2-Clause,
pygments BSD-2-Clause, tomli MIT.

Not verified: licenses of newer versions pulled by a fresh `pip install` on the VPS. Re-run
`pip-licenses` (or read each package's metadata) after upgrading.

## Phase 2a (optional, external programs; not in requirements.txt)

| Tool | Licence | Notes |
|---|---|---|
| piper-tts 1.8.0 | **GPL-3.0-or-later** | installed in its own venv, run as a subprocess |
| Piper voice en_US-lessac-medium | check model card | per-voice licence, not verified here |
| ffmpeg / ffprobe | LGPL-2.1+ or GPL (build dependent) | used as a subprocess; use an LGPL build |
