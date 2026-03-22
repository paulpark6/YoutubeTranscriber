# Project Plan -- YouTube Transcription Web App

**Last updated:** 2026-03-21 (status updated after Phase 1 build)

## Overview

A web application that downloads YouTube video transcripts. Users paste one or more YouTube URLs into a browser-based form, choose options (language, timestamps), and download the resulting transcript files. The app replaces the existing CLI script (`transcribe.py`) with a full-stack solution.

---

## Phases

### Phase 1 -- Core Web App (CURRENT)

**Status:** Code complete -- tests not yet verified

Build a working FastAPI backend and React frontend that handles single and batch transcript downloads.

| Feature | Status |
|---|---|
| Backend: FastAPI project scaffold | Done |
| Backend: YouTube URL parser (all formats) | Done |
| Backend: Transcript fetch + format service | Done |
| Backend: `POST /api/transcript` endpoint | Done |
| Backend: ZIP packaging for batch downloads | Done |
| Backend: Per-video error handling in batch | Done |
| Backend: CORS middleware | Done |
| Backend: Environment-based config | Done |
| Backend: Unit + integration tests | Done (not yet run) |
| Frontend: Vite + React + TypeScript scaffold | Done |
| Frontend: URL textarea (multi-line input) | Done |
| Frontend: Custom filename field (single URL) | Done |
| Frontend: Language selector dropdown | Done |
| Frontend: Timestamps toggle (default ON) | Done |
| Frontend: Download trigger | Done |
| Frontend: Per-video error display | Done |
| Frontend: Loading state | Done |
| Frontend: Tests | Done (not yet run) |

**Pending before Phase 1 is fully verified:**
- [ ] Run `pytest` in `backend/` and confirm all tests pass
- [ ] Run `npm test` in `frontend/` and confirm all tests pass
- [ ] Run code reviewer checklist from `AGENT_INSTRUCTIONS.md`

### Phase 2 -- Topic Search (FUTURE -- do not build yet)

Search YouTube for videos on a topic, select top N results, and batch transcribe them. Will require YouTube Data API v3 and an API key.

### Phase 3 -- Supabase Integration (FUTURE -- do not build yet)

Save transcripts to a Supabase database. Potential session-based history (no login required). Schema and integration TBD.

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| **FastAPI** for backend | Async-capable, lightweight, built-in OpenAPI docs, Pydantic validation |
| **React + Vite + TypeScript** for frontend | Fast dev server, type safety, widely supported |
| **youtube-transcript-api** (Python) | Already proven in the original script; no API key needed |
| **ZIP for batch results** | Standard format, one download action for multiple files |
| **Env vars for all config** | Enables local dev now and hosted deployment later without code changes |
| **CORS allow-all for now** | Simplifies local development; will tighten for production |
| **Graceful per-video errors** | One bad URL in a batch should not kill the whole request |

---

## API Contract

### `POST /api/transcript`

**Request body (JSON):**

```json
{
  "urls": [
    "https://www.youtube.com/watch?v=abc123",
    "https://youtu.be/def456"
  ],
  "include_timestamps": true,
  "language": "en",
  "filename": "my_transcript"
}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `urls` | `list[str]` | Yes | -- | One or more YouTube URLs or video IDs |
| `include_timestamps` | `bool` | No | `true` | Toggle `[MM:SS]` prefix on each line |
| `language` | `str` | No | `"en"` | Language code for transcript |
| `filename` | `str` | No | `null` | Custom filename; only used when a single URL is provided |

**Response:**

- **Single URL:** Returns a `.txt` file (`Content-Type: text/plain`)
- **Multiple URLs:** Returns a `.zip` file (`Content-Type: application/zip`)
- Each file inside the ZIP is named after the video title (sanitized) or video ID if title unavailable
- If `filename` is provided for a single-URL request, the downloaded file uses that name

**Error handling:**

- If ALL videos fail: return HTTP 400 with JSON error body
- If SOME videos fail in a batch: return the ZIP with successful transcripts plus an `_errors.txt` file summarizing which videos failed and why
- Individual error reasons: invalid URL, no transcript available, unsupported language, network error

**Supported URL formats:**

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- Raw video ID string (11 characters)

---

## Testing Strategy

### Backend

- **Unit tests:**
  - URL parser: all supported formats, edge cases, invalid URLs
  - Transcript formatter: with timestamps, without timestamps, empty transcript
  - Language fallback behavior
  - Filename sanitization
- **Integration tests (FastAPI TestClient):**
  - Single URL request returns `.txt`
  - Batch URL request returns `.zip`
  - Partial failure returns ZIP with `_errors.txt`
  - All-failure returns HTTP 400
  - Mock `youtube-transcript-api` to avoid hitting YouTube in CI

### Frontend

- **React Testing Library:**
  - Form renders with all controls
  - URL textarea accepts multi-line input
  - Timestamps toggle changes state
  - Language dropdown selection works
  - Submit triggers API call with correct payload
  - Error messages display per video
  - Loading spinner shows during request
- **Mock fetch** for all API calls in tests

---

## Deployment Notes

- All config via environment variables (see `.env.example` files in both `backend/` and `frontend/`)
- Backend: `CORS_ORIGINS` env var to restrict allowed origins in production
- Frontend: `VITE_API_URL` env var for the backend URL (no hardcoded `localhost`)
- Backend runs on configurable port (`PORT` env var, default `8000`)
- Frontend dev server proxied to backend in `vite.config.ts`
- Production: frontend builds to static files, can be served by any static host or the backend itself

---

## Risks and Open Questions

| Risk | Mitigation |
|---|---|
| `youtube-transcript-api` rate limits or blocks | Add retry logic; document the limitation |
| Large batch requests could be slow | Consider async processing; for Phase 1, synchronous is fine |
| Video title fetch may require separate API call | Fall back to video ID for filename if title unavailable |
| ZIP in memory for large batches could use significant RAM | Acceptable for Phase 1 scope; stream to disk if needed later |
