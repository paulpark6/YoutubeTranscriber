# PLAN.md — MVP checklist

This is the single source of truth for what is built, what is in progress, and what is left before the MVP ships. Claude must propose changes here in chat first and wait for explicit user approval before editing this file (see "PLAN.md update protocol" in CLAUDE.md).

Legend: `[x]` done · `[~]` in progress · `[ ]` not started

---

## Frontend

- [x] Vite + React + TypeScript scaffold
- [x] `TranscriptForm` — URL textarea, filename input, language selector, timestamps toggle, submit
- [x] `LanguageSelector`, `ErrorMessage`, `LoadingSpinner` components
- [x] `api/transcript.ts` — POST `/api/transcript`, blob-URL download, filename from `Content-Disposition`
- [x] Vitest tests for `TranscriptForm`
- [ ] Production build deployed to a static host

## Backend

- [x] FastAPI app with CORS middleware
- [x] `services/url_parser.py` — `watch?v=`, `youtu.be/`, `shorts/`, `embed/`, raw 11-char ID
- [x] `services/transcript.py` — `fetch_transcript`, `format_transcript`, `sanitize_filename`
- [x] `services/zip_builder.py` — in-memory ZIP for batch downloads
- [x] `routers/transcript.py` — `POST /api/transcript` (single→.txt, batch→.zip, partial→.zip+`_errors.txt`, all-fail→HTTP 400)
- [x] Pytest unit + integration tests
- [ ] Production deployment target chosen and configured

## Auth

- [ ] Decide whether MVP needs auth (Phase 1 is anonymous)
- [ ] If yes: provider, session model, protected routes

## Database

- [ ] Decide whether MVP needs persistence (Phase 1 is stateless)
- [ ] If yes (Phase 3 plan): Supabase schema, connection config, migrations
- [ ] Session-based history (no login) — design TBD

## Hosting

- [ ] Backend host chosen (e.g. Fly.io / Render / Railway)
- [ ] Frontend host chosen (e.g. Vercel / Netlify / same host as backend)
- [ ] Production `CORS_ORIGINS` updated in `backend/app/config.py`
- [ ] Production API base URL wired into frontend build

## Shipping

- [ ] CI: backend pytest on PR
- [ ] CI: frontend vitest + `tsc` on PR
- [ ] README updated with production URL
- [ ] Smoke test on prod: single URL, batch URL, partial-failure batch

---

## Future phases (not in MVP)

- **Phase 2 — Topic search:** YouTube Data API v3 integration to search by topic and batch transcribe top N results. Requires API key.
- **Phase 3 — Supabase:** Persist transcripts; optional session history without login.
