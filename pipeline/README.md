# BOUGHT newspaper pipeline (Phase 1)

Standalone Python service. Every 30 minutes it pulls trusted RSS/news-sitemap sources, dedupes, scores
(no LLM, no paid APIs) and writes `out/feed.json` with three lists: `prime`, `cards`, `glance`.
We store only headline, source, canonical link, image URL + credit, and a short summary we generate
ourselves (first 2 sentences of the feed blurb, max 300 chars). Article bodies are never stored.

## Setup (Ubuntu VPS)

```sh
sudo apt install -y python3 python3-venv          # Python 3.9+ works
cd /opt/bought                                      # the project root (parent of pipeline/)
python3 -m venv pipeline/.venv
pipeline/.venv/bin/pip install -r pipeline/requirements.txt
```

Always run from the project root (the folder that contains `pipeline/`).

## Run

```sh
pipeline/.venv/bin/python -m pipeline run            # one full cycle (live network)
pipeline/.venv/bin/python -m pipeline show           # print the current selection
pipeline/.venv/bin/python -m pipeline run --dry-run  # saved fixtures, fixed clock, no network
pipeline/.venv/bin/python -m pipeline show --dry-run
pipeline/.venv/bin/python -m pytest pipeline         # tests (pip install -r requirements-dev.txt)
```

`--dry-run` writes to `data/dry_run.db` and `out/dry_run/feed.json`, so it never touches live data.
Exit code is 1 only if *every* source failed; individual source failures are printed as warnings.

## Cron (example, not installed)

```cron
*/30 * * * * cd /opt/bought && flock -n /tmp/bought-pipeline.lock pipeline/.venv/bin/python -m pipeline run >> pipeline/data/run.log 2>&1
```

`flock` stops two runs overlapping. A run is safe to repeat or kill half-way: each stage is one SQLite
transaction, articles are keyed by canonical URL (`INSERT OR IGNORE`), selection is recomputed from scratch,
and `feed.json` is replaced atomically. Items whose article-page lookup failed transiently are skipped and
retried on the next run. Serve `out/feed.json` however you like (e.g. nginx static file); the pipeline
does not serve it.

## Adding a source

Append to `sources.yaml`:

```yaml
  - name: Example Wire          # unique; also names the dry-run fixture (tests/fixtures/example-wire.xml)
    type: rss                   # rss | sitemap (Google News sitemap, not a sitemap index)
    url: https://example.com/rss.xml
    weight: 4                   # 1-5; drives score and wins duplicates
    category: Technology        # free text; the 40% per-slot cap applies per category
```

Check the site's terms/robots before adding. A source answering 401/402/403/451 is logged as blocked
and skipped, with its `fetch_state.last_error` recorded; we do not try to get around it.

## Settings (`config.yaml`)

Slot sizes (`slots`: prime 25 / cards 25 / glance 10 — **unconfirmed numbers**), `filtered_size` (50),
`max_age_hours` (48), `category_cap` (0.4), `dedupe_jaccard` (0.7), og:image fallback limits, user agent
(**set a real contact address in `user_agent`**).

## How selection works

1. Ingest: parse items, canonicalize URLs (strip `utm_*` and other tracking params), take image from
   `media:content` / thumbnail / enclosure / inline `<img>`, else `og:image` from the article page
   (robots.txt honoured, 1.5 s per-host delay, 512 KB cap). Items older than 48 h or without a title are not stored.
2. Reject items with no image (`reject_reason=no_image`); expire items older than 48 h.
3. Dedupe near-identical titles (token Jaccard ≥ 0.7 on stopword-stripped, lightly stemmed tokens); the
   higher-weight source wins, then the earlier-published.
4. `score = source_weight*2 + recency_bonus (0–5, linear over 48 h)`. The top 50 are picked greedily with a
   category-balance bonus (up to +2 for categories below an even share of the 50).
5. Slots: **prime** = best-ranked; **cards** = next best, preferring stories not in prime and reusing prime
   stories only to fill the slot; **glance** = newest of the 50. No category exceeds 40% of any slot, no
   story appears twice in a slot. If a slot cannot be filled under these rules it is left short and
   `run` prints a warning.

Tables: `articles` (status: new / selected_prime / selected_card / selected_glance / rejected / expired),
`selections` (one row per slot, since a story can be in several slots; `articles.status` shows the
strongest one), `fetch_state` (ETag/Last-Modified, last error). `feed.json` prime items carry
`"script": null` until Phase 2.

## Audio for prime stories (Phase 2a, optional)

Needs `ffmpeg` and a TTS command. Install Piper in a separate venv and download a voice:

    python3 -m venv /opt/piper && /opt/piper/bin/pip install piper-tts
    cd /opt/voices && /opt/piper/bin/python -m piper.download_voices en_US-lessac-medium

Then in `config.yaml` set `media_enabled: true` and
`tts_command: ["/opt/piper/bin/piper","--model","/opt/voices/en_US-lessac-medium.onnx","--output_file","{wav}"]`.
`run` then writes MP3s to `out/media/<id>.mp3` and adds `audio_url` and `duration_s` to prime items in `feed.json`.
Serve `out/media/` at `audio_base_url`. Reruns skip finished audio.
