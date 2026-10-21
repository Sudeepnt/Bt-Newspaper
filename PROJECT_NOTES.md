# BOUGHT — Project Notes (read this instead of re-exploring the code)

Written 2026-10-20 from a one-time read of both repos. Re-check the code only for details not covered here.

## The big picture

| | **Bought** (main product) | **Bt-Newspaper** (design prototype) |
|---|---|---|
| Repo | github.com/Sudeepnt/Bought | github.com/Sudeepnt/Bt-Newspaper |
| Local path | `./Bought/` (nested git repo) | `./` (this folder's root) |
| Stack | React 19 + Vinext (App Router-compatible, **not** Next.js) + Vite, Nitro → Vercel | Plain static HTML/CSS/JS, no build, no deps |
| Purpose | Video "broadcast" marketplace/auction + magazine archive | Mobile newspaper + podcast UI, designed *before* merging into Bought |

**Strategy:** the daily newspaper is the hook that brings readers to the site; the broadcast (video upload) side is the product. Bt-Newspaper is where the newspaper UX gets designed and polished; once final, it gets ported into Bought. Brand name inside the prototype: "Bought. Spotlight".

**Bought → Bt-Newspaper link:** the prototype contains "Bought Spotlight" placements (a presenter image + quote, `assets/bought-spotlight-placement.webp`) that preview how a Bought broadcast would be promoted inside the newspaper feed.

---

## 1. Bt-Newspaper (root of this folder)

Run: `python3 -m http.server 8000 --directory public` → http://localhost:8000/. Deploy: Vercel serves `public/` (`vercel.json`: framework null, no build, outputDirectory `public`).

Pages
- `/` (`public/index.html`) — Newspaper edition, dated "Tuesday, October 13, 2026". Sticky masthead ("Bought." wordmark, date, language picker), a Newspaper/Podcast view switch, a story list, then an end-of-issue completion section.
- `/podcast.html` — Podcast edition of the same issue (`podcast.css`, `podcast.js`).

Files
- `stories.js` (755 lines, the core): hardcoded `sampleStories` array (`category, title, deck, happened, matters, image, imageAlt, imagePosition`). Renders:
  - story cards (`renderStory`), image-swipe carousel (`renderImageCarousel`, drag/touch/pointer handlers), "glances" list (`renderGlances`)
  - `renderSpotlightPlacement(n)` — Bought Spotlight ad-like blocks, inserted after story index 4 and 9 and at the end
  - full-story overlay (`openFullStory` / `closeFullStory`, Esc to close)
  - Save (localStorage key `bought-spotlight-saved-2026-10-13`), copy, and share (Web Share API) per story, with `#action-feedback` toast
- `language.js` — language picker: 10 popular languages first (English, Mandarin, Hindi, Spanish, Arabic, French, Bengali, Portuguese, Russian, Japanese), then ~48 others alphabetically. UI only so far; **no real translation is wired**.
- `completion.js` — "You are up to date" ending: canvas-drawn layered mountains with drifting fog (3 canvases `mountain-far/mid/near`), animated per-category counts (`data-final-count`), respects `prefers-reduced-motion`. Issue totals shown: 50 stories — Technology 8, AI 8, Tech Business 12, Founders & Startups 10, Product Launches 8, Tech Geopolitics 4.
- `podcast.js` — `headlineData` `[category, title, startSecond]` list, play/pause, speed button, progress bar, elapsed time. Audio is simulated/prototype.
- `styles.css` (497 lines), `podcast.css`; assets in `public/assets/` (swipe-*.jpg images, fonts: Newsreader + DM Sans, ai-presenter.jpg, podcast-earth.jpg).

Design language: warm paper background `#efece5`, Newsreader serif editorial look, newspaper rules, mobile-first (viewport-fit=cover).

Content shape per story: **deck** (summary) + **What happened** + **Why it matters**.

Recent git history: "Add bottom rule to Spotlight placements", "Add Spotlight preview placements to newspaper", "Deploy BOUGHT Spotlight as static Vercel site".

---

## 2. Bought (`./Bought/`)

Run: `npm ci && cp .env.example .env && npm run dev`. Scripts: `build`, `test` (`tsx --test tests/*.test.ts`), `typecheck`, `lint` (oxlint), `format` (oxfmt), `preflight:production`. Node ≥ 22.13. Without credentials the `/broadcast` form shows but sign-in/upload is disabled.

### Services
- **Supabase** — auth (email code sign-in), Postgres, Realtime, private thumbnail storage. Migrations in `supabase/migrations/` (apply in filename order): paid drop pipeline, capture mode, optimized public snapshot, English transcription, web push, finalized categories, push RPC hardening, free daily upload limit, free public current auction.
- **Mux** — direct uploads (UpChunk, resumable, bytes never touch the server), signed playback, auto captions + translation (10 featured languages pre-generated, others on demand).
- **Stripe / Razorpay** — optional paid "boost" in USD to rank higher; webhooks verify raw-body signature + amount + currency. Publishing itself is now **free**.
- **Upstash Redis** — atomic write rate limits (fail closed).
- Web Push (VAPID) notifications, `public/notifications-sw.js`.
- Env vars (see `.env.example`): `APP_ORIGIN, VAPID_*, SUPABASE_*, STRIPE_*, RAZORPAY_*, MUX_*, UPSTASH_*, CRON_SECRET`. Never prefix secrets with `NEXT_PUBLIC_`/`VITE_`.

### Routes (`app/`)
`/` (today's market/leaderboard, 799 lines) · `/broadcast` (record & upload) · `/review` (moderator queue) · `/categories` (2722 lines, biggest) · `/magazine` and `/magazine/[slug]` (The BOUGHT Review archive) · `/profile` · `/watchlist` · `/chat` · `/search` + `/search/[type]/[id]` · `/how-it-works` · `/terms` · `/capture-test` · `/drop` (stub). API: single catch-all `app/api/bought/[...path]/route.ts` → `handleApi` (config, drops, uploads, webhooks for stripe/razorpay/mux, `cron`, market snapshot).

### Key code
- `components/`: `drop-recorder`, `screen-recorder`, `capture-preflight` (camera/mic + MediaPipe face detect), `drop-player` (Mux player), `magazine-issue-reader`, `market-chrome`/`market-topbar`, sign-in modal steps (category, goals), `add-funds-modal`, `bought-provider`.
- `lib/`: `magazine.ts` (issue data), `recording-*` (compositor, retention, capabilities, guidance), `local-recording` (IndexedDB recovery copy), `direct-messages`, `market-notifications`, `search`, `caption-languages`, `drop-domain`; `lib/server/` = `api, config, providers, security, transcription, webhooks, push-notifications`.
- `tests/` covers api routing, DMs, drop DB (PGlite), domain, recording, push, webhooks/providers, preflight.
- `public/mediapipe/` = face-detector WASM + model; `public/magazine/*.pdf` = generated issues; `scripts/generate_magazine_pdfs.py` builds the PDFs (also into `output/pdf/`).
- `vercel.json`: strict CSP/security headers, long cache for `/mediapipe`, `/brand`, `/magazine`; daily cron `0 0 * * *` → `/api/bought/cron`.

### Business rules to remember
- Each account: **3 new Mux uploads per UTC day**; broadcasts up to 2 min (imports up to 250 MB MP4/MOV/WebM).
- Flow: record → upload to Mux + thumbnail to Supabase → Mux processing + English transcript → **human moderator** approves (`bought_moderator: true` in server-managed app metadata) → public. No auto-approval.
- Auction: market open **00:00–12:00 UTC**, order frozen at 12:00 UTC, exposure until 00:00. Rank = higher paid amount, then earliest payment confirmation, then `dropId`. Late finishers roll to next auction. DB clock is authoritative.
- Refund/dispute removes the public entry.
- Categories (rooms) seen in magazine: Beef, Chaos, Confessions, The Ask, Building, The Rant, Hiring, Indian D2C, Money I Set On Fire, Unpopular Opinion, Pitch, Wrong, Agency Row.

### Magazine ("The BOUGHT Review") — the existing newspaper-ish side in Bought
- After each 12:00 UTC lock, the next day's issue is published: one **ALL #1 cover** + one cover per category leader, permanent archive. Types in `lib/magazine.ts`: `MagazineIssue {slug, number, date, person, category, title, image, tone(blue|red|orange|green|charcoal), views, opens}`; exports `latestIssue`, `categoryIssues`, `dailyEditions`, `historyIssues`, `roomIssues`. Currently sample/static data (issue 05 "The Cost of Being Seen", Ananya Rao, 09 Sep 2026). Rendered as PDFs.
- This is **leaderboard/people-focused** (winners' covers), whereas Bt-Newspaper is a **news-focused** daily feed (tech stories). Merging them = adding the news feed/podcast as the reader-facing hook, with Spotlight placements linking to Bought broadcasts.

---

## Integration notes / likely next steps
- Bt-Newspaper is framework-free; porting into Bought means converting `stories.js` rendering into React components (new route, e.g. `/` or `/news`) and moving `sampleStories`/`headlineData` to real data (Supabase table or API route).
- Styling: prototype uses its own `styles.css` (paper `#efece5`, Newsreader/DM Sans); check Bought's `app/globals.css` for conflicts before porting.
- Bought's CSP (`vercel.json`) is strict (`default-src 'self'`) — remote images/fonts need allowlisting.
- Language picker and podcast audio in the prototype are placeholders; Bought already has Mux captions/translation infra and a language list (`lib/caption-languages.ts`) that could be reused.
- `Bought/` is a nested git repo inside the Bt-Newspaper repo working tree; don't `git add` it from the parent.

---

## 3. `pipeline/` (added 2026-10-20) — newspaper content pipeline, Phase 1
Standalone Python service (own venv, `pipeline/README.md` has everything): RSS/news-sitemap sources
(`sources.yaml`) -> SQLite (`data/news.db`) -> dedupe -> score/select -> `out/feed.json` {prime, cards, glance}.
Settings in `pipeline/config.yaml` (slots 25/25/10 unconfirmed). `python -m pipeline run|show [--dry-run]`,
tests `pytest pipeline`. Phase 2 (TTS/avatar) is only planned in `pipeline/PHASE2.md`. Licenses: `pipeline/LICENSES.md`.
Run commands from the project root.
