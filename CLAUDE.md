# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All backend commands assume the venv is activated (`source venv/bin/activate` from repo root) and you are in the `backend/` directory. The backend imports use `app.*` paths, so `uvicorn` and `pytest` must be run from `backend/` (not the repo root) for imports to resolve.

```bash
# Backend dev server (port 8000, hot reload)
cd backend && uvicorn app.main:app --reload --port 8000

# Backend tests
cd backend && python -m pytest tests/ -v

# Run a single backend test
cd backend && python -m pytest tests/test_url_parser.py::test_function_name -v

# Frontend dev server (port 5173, proxies /api → :8000)
cd frontend && npm run dev

# Frontend tests (vitest, jsdom)
cd frontend && npm run test

# Frontend production build
cd frontend && npm run build   # runs `tsc && vite build` — type errors fail the build
```

Both servers must run concurrently for the app to function — frontend at `http://localhost:5173`, backend at `http://localhost:8000`. The Vite dev server proxies `/api` to the backend (see `frontend/vite.config.ts`), so the frontend uses relative `/api/...` paths and does not need a base URL in dev.

## Architecture

The app has a single user-facing endpoint: **`POST /api/transcript`** (defined in `backend/app/routers/transcript.py`). The request flow is:

1. **Frontend** (`frontend/src/components/TranscriptForm.tsx`) splits the textarea on newlines, builds a `TranscriptRequest`, and POSTs JSON to `/api/transcript` via `frontend/src/api/transcript.ts`.
2. **Router** iterates over each URL, calling `parse_video_id()` then `fetch_transcript()` then `format_transcript()`. Per-URL failures are collected as error strings rather than aborting the whole request.
3. **Response shape depends on outcome:**
   - **Single URL, success** → `StreamingResponse` of `text/plain` (one `.txt`).
   - **Multiple URLs, or single URL with batch errors** → `application/zip` containing each successful transcript plus an `_errors.txt` listing failures.
   - **All URLs failed** → HTTP 400 with `detail` containing `; `-joined error messages.
4. **Frontend `downloadTranscript`** reads `Content-Disposition` to pick the download filename, creates a blob URL, and triggers a synthetic `<a>` click to save the file.

### Key invariants

- `Content-Disposition` must be in the CORS `expose_headers` list (`backend/app/main.py`), otherwise the frontend cannot read the filename in browsers.
- `app/services/transcript.py::fetch_transcript` translates `youtube_transcript_api` exceptions (`NoTranscriptFound`, `TranscriptsDisabled`, `VideoUnavailable`) into user-facing `ValueError` messages, and wraps everything else as `RuntimeError`. The router catches **both** `(ValueError, RuntimeError)` — adding new exception types here requires updating the router too.
- `sanitize_filename` is applied to user-supplied `filename` AND to video IDs before writing into a ZIP. Video IDs (`[A-Za-z0-9_-]{11}`) survive sanitization unchanged; custom filenames may not.
- A custom `filename` is only honored when there is exactly one URL — for multi-URL batches each file is named after its video ID. Duplicate filenames in a batch get `_1`, `_2`, … suffixes.
- `parse_video_id` accepts a raw 11-char ID, `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, and `youtube.com/embed/`. Adding new URL formats means updating both `url_parser.py` and `test_url_parser.py`.
- `CORS_ORIGINS` in `backend/app/config.py` is a hardcoded list (currently only `http://localhost:5173`). Update it when deploying or when the frontend dev port changes.

### Code organization rules

- New API endpoints → `backend/app/routers/` (one file per resource), and register the router in `app/main.py`.
- Business logic → `backend/app/services/`. Routers should stay thin and delegate.
- Pydantic request/response models → `backend/app/schemas/`.
- New React components → `frontend/src/components/`. Frontend API client functions → `frontend/src/api/`.

## Reference files

- `transcribe.py` (repo root) is the original CLI prototype. It is not used by the web app and not imported anywhere — kept for reference only.
- The loose `*.txt` files at the repo root (e.g., `2JEzjfs6Kew.txt`) are sample transcript outputs from manual runs; they are not test fixtures.
- `mdfiles/` contains the original planning docs (`PROJECT_PLAN.md`, `PROJECT_STRUCTURE.md`, `AGENT_INSTRUCTIONS.md`). `PROJECT_STRUCTURE.md` lists `.env.example` files and `pydantic-settings`/`python-dotenv` dependencies that the actual code does not use — trust the code over those docs when they conflict.
