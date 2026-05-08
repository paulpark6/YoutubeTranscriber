# PLAN.md — MVP checklist

**This is the single source of truth for what is built, in progress, and left before MVP ships.**

Claude must always read this file at the start of any task. Whenever a checkbox moves between states, propose the change in chat first and wait for explicit user approval before editing. See "PLAN.md update protocol" in `CLAUDE.md`.

Legend: `[x]` done · `[~]` in progress · `[ ]` not started

Build order is sequential by Stage but checkboxes within a stage can be done in any order. Move to the next Stage only when the current one is fully `[x]`.

---

## Stage 1 — Backend hardening

- [x] `services/url_parser.py` — `watch?v=`, `youtu.be/`, `shorts/`, `embed/`, raw 11-char ID, scheme-less URLs (issue #4)
- [x] `services/transcript.py` — `fetch_transcript`, `sanitize_filename`
- [x] `services/transcript_format.py` — `format_transcript`
- [x] `services/zip_builder.py` — in-memory ZIP for batch downloads
- [x] `routers/transcript.py` — `POST /api/transcript` with single→.txt, batch→.zip, partial→.zip+`_errors.txt`, all-fail→HTTP 400
- [x] `schemas/transcript_schema.py` — `TranscriptSchema` request model
- [x] Pytest unit + integration tests (79 passing)
- [x] Close GitHub issue #5 — improve `test_url_parser.py` (xfail markers, embed error, hardcoded values)
- [x] Close GitHub issue #6 — improve `test_transcript_service.py` (split files, mock contract drift, default-language test, etc.)
- [x] Close GitHub issue #7 — improve `test_transcript_router.py` (CORS expose-headers test, duplicate-ID suffix, path traversal, etc.)
- [ ] Add Ruff to backend (`backend/pyproject.toml` config + run in CI)

## Stage 2 — Supabase + rate-limit + abuse system

- [ ] Provision Supabase project; capture `SUPABASE_URL` + `SUPABASE_KEY`
- [ ] Schema: `blocked_ips`, `ip_request_log`, `feature_votes` tables
- [ ] Wire backend to Supabase via Python client; env vars on Render
- [ ] Per-IP rate limiting: 20 req/min → HTTP 429 + `Retry-After: 60`
- [ ] Global rate limiting: 300 req/min ceiling
- [ ] Auto-block: >5 rate-limit violations / hour → permanent block, persisted in `blocked_ips`
- [ ] Blocked IPs receive HTTP 403 with contact info in body
- [ ] Discord webhook ping fires on every auto-block event
- [ ] Admin endpoint to manually unblock an IP (for support-ticket appeals)
- [ ] `feature_votes` table backs the static future-plans voting (per-IP toggle)

## Stage 3 — Frontend redesign + states

- [x] Vite + React + TypeScript scaffold
- [x] `TranscriptForm` baseline (URL textarea, filename input, language selector, timestamps toggle, submit)
- [x] `LanguageSelector`, `ErrorMessage`, `LoadingSpinner` components
- [x] `api/transcript.ts` — POST `/api/transcript`, blob-URL download, filename from `Content-Disposition`
- [ ] Tailwind + shadcn/ui CLI setup (`components.json`, Tailwind config)
- [ ] Light/dark mode toggle: default to OS preference, persist user override in localStorage
- [ ] Rebuild form UI with shadcn components, Wealthsimple-newer aesthetic (sans-serif, sharp, minimal)
- [ ] Polished state: empty (title + subtitle + how-it-works)
- [ ] Polished state: loading (button text + inline spinner + cold-start message after 5s)
- [ ] Polished state: error (per-error-type messages: bad URL / no transcript / rate limited / partial batch)
- [ ] Polished state: success (toast + form reset + "transcribe another" affordance)
- [ ] Static "Future plans" section listing the 7 features with per-IP upvote/downvote (toggle pattern)
- [ ] Cookie consent banner (GDPR)
- [ ] Privacy Policy page
- [ ] Terms of Service page
- [ ] Footer: mailto link, Discord invite link, in-app feedback form (→ Discord webhook only)
- [ ] Favicon, page title, OpenGraph metadata
- [ ] Accessibility: semantic HTML, ARIA labels, focus states, color contrast, reduced-motion
- [ ] Footer credit to `youtube-transcript-api`
- [ ] `LICENSE` file (MIT)

## Stage 4 — Frontend testing

- [x] Vitest tests for `TranscriptForm` baseline (8 passing)
- [ ] Frontend integration tests for `TranscriptForm` with mocked backend (~5–10 tests covering form state, error rendering, success, rate-limited UI)
- [ ] Playwright installed + configured
- [ ] E2E test 1 — happy path: paste URL → submit → `.txt` downloads
- [ ] E2E test 2 — batch path: paste 2 URLs → submit → `.zip` downloads with 2 entries
- [ ] E2E test 3 — error path: paste bad URL → submit → error message visible, no download
- [ ] E2E tests structured to support `E2E_MODE=mock` (CI default) and `E2E_MODE=real` (nightly)

## Stage 5 — CI/CD pipeline

- [ ] `.github/workflows/ci.yml` — backend pytest + Ruff, frontend vitest + tsc + build + eslint/prettier, E2E in mocked mode, all run in parallel
- [ ] `.github/workflows/nightly.yml` — same E2E tests in real-YouTube mode, runs at 03:00 UTC daily
- [ ] Pre-push git hook in `.githooks/pre-push` running fast subset (pytest + vitest + tsc)
- [ ] `scripts/install-hooks.sh` to set `core.hooksPath = .githooks`
- [ ] Branch protection rule on `main`: cannot merge unless `ci.yml` is green
- [ ] README documents how to install hooks + skip them with `--no-verify` if needed

## Stage 6 — Deployment

- [ ] Backend deployed to Render free tier; `Dockerfile` or build command set; uvicorn start command
- [ ] Frontend deployed to Vercel free tier; framework preset = Vite
- [ ] Render env vars: `SUPABASE_URL`, `SUPABASE_KEY`, `DISCORD_WEBHOOK_URL`, `CORS_ORIGINS`
- [ ] Vercel env var: `VITE_API_URL` pointing at Render backend
- [ ] Production `CORS_ORIGINS` updated in `backend/app/config.py` (or read from env)
- [ ] cron-job.org or UptimeRobot pinger hits `/health` every 14 minutes
- [ ] Vercel Analytics enabled
- [ ] Manual prod smoke test: single URL, batch URL, partial-failure batch, rate-limit hit, blocked-IP simulation

## Stage 7 — Launch

- [ ] README updated with production URL, screenshot, "How to use," "Tech stack" sections
- [ ] Final read-through of Privacy + Terms pages
- [ ] Share / portfolio link / tweet
- [ ] Watch Render + Vercel logs for the first 24h

---

## Future phases (not in MVP)

Headline-only. Detailed scoping happens when each phase actually starts. Trigger for all = "when motivated to return to this app."

- **Phase 2 — Foundation (Cluster X).** Auth (Supabase Auth: signup/login/password reset/email verification/GDPR delete), transcript history (save user transcripts to Supabase, "your transcripts" page), custom domain + DNS, real observability (Axiom or similar with alerting). ~3–6 weeks.
- **Phase 3 — Free signed-in features (Cluster Y).** Transcript count tracker, in-place history search, mobile-optimized layout, email forwarding for feedback (Resend). ~1–2 weeks. Depends on Phase 2.
- **Phase 4 — Paid features (Cluster Z).** Stripe integration (pricing/checkout/webhooks/cancel/sub UI), tier-gating middleware, AI summary, per-video chatbot, LLM usage tracking. ~4–8 weeks. Depends on Phase 2.
- **Phase 5 — Integrations (Cluster W).** Notion integration, in-place YouTube search bar, topic search (YouTube Data API v3 batch-transcribe top N). ~2–4 weeks per integration; ship one at a time. Depends on Phase 4.
