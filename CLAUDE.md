# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Always read PLAN.md first

Before starting any task in this repo, **read `PLAN.md`**. It is the single source of truth for MVP scope, build order, and what is currently in progress. Every task in this repo either:

- Advances a `[ ]` or `[~]` item in `PLAN.md` toward `[x]`, or
- Is out of scope for MVP (push back on the user before doing it).

When you complete work that satisfies a checkbox, **propose the checkbox flip in chat and wait for the user's explicit approval before editing PLAN.md**. See "PLAN.md update protocol" below.

If you finish work that's not represented in `PLAN.md`, that's a smell. Either propose adding it as a new checkbox, or stop and confirm scope with the user.

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

## Description files — keep in sync with code

Each directory in the backend has a `*_description.md` file that documents the files, functions, and invariants in that directory. These are:

- `backend/backend_description.md`
- `backend/app/backend_app_description.md`
- `backend/app/routers/backend_app_routers_description.md`
- `backend/app/schemas/backend_app_schemas_description.md`
- `backend/app/services/backend_app_services_description.md`
- `backend/tests/backend_tests_description.md`

**Any time you add, remove, rename, or meaningfully change a file, function, argument, return type, exception, or invariant in `backend/`, you must also update the description file for that directory.** This applies to agents too — `backend-agent` must update the relevant description file(s) as part of the same PR/commit as the code change.

What to update:
- Added a file → add a new `### filename.py` section.
- Removed a file → delete its section.
- Renamed a function or argument → update the function entry.
- Changed behavior, exception handling, or a key limitation → update the relevant bullet under that function.
- Added a new limitation or known edge case → add it under "Limitations".

Do **not** update description files for: pure test-only changes that don't alter the public interface, comment/whitespace-only edits, or changes to planning docs.

## Reference files

- `transcribe.py` (repo root) is the original CLI prototype. It is not used by the web app and not imported anywhere — kept for reference only.
- `PLAN.md` (repo root) is the MVP checklist — what is done, in progress, and left before shipping. See "PLAN.md update protocol" below.

## Agents

This repo has four subagents defined in `.claude/agents/`. Each owns a specific area; respect the boundaries.

| Agent | Owns (may edit) | Off-limits | Use when |
|---|---|---|---|
| `backend-agent` | `backend/**` | `frontend/**`, `mdfiles/**` (does not exist anymore — historical) | Any FastAPI / Python / server-side work |
| `frontend-engineer` | `frontend/**` | `backend/**`, planning docs | Any React / TS / UI work |
| `code-reviewer` | (read-only) | Never edits | Final review pass before a feature is "done" — bugs, security, FE/BE contract mismatches |
| `project-planner` | `PLAN.md`, `README.md` | `backend/**`, `frontend/**` | Updating the MVP checklist or coordinating multi-agent work. Never writes application code |

### Picking the right agent

- Touches files the user sees in the browser → `frontend-engineer`
- Touches files that run on the server → `backend-agent`
- Touches `PLAN.md` or planning docs → `project-planner`
- Final check before merging a feature → `code-reviewer`
- A change spans frontend and backend → start with `project-planner` to align scope, then run frontend and backend agents in parallel, then `code-reviewer`

### Cross-agent handoff

When a frontend feature depends on backend behavior (or vice versa), the agents do **not** talk directly — the main session coordinates:

1. The first agent finishes its half and reports the contract it expects (endpoint shape, payload, headers, etc.).
2. The main session passes that contract to the second agent in the prompt.
3. After both halves are in, run `code-reviewer` with a prompt like *"verify that `frontend/src/api/transcript.ts` matches the request/response shape of `backend/app/routers/transcript.py`"*.

If an agent needs to verify integration end-to-end (e.g. "does the download button actually trigger a real download"), do that from the main session with both servers running — agents should not start servers or run integration loops on their own.

### Agent memory

Each agent has a memory store at `.claude/agent-memory/<agent-name>/`. Memory is for **non-derivable** facts (user preferences, past incidents, surprising decisions). It is **not** a status tracker — do not use it to record what was built, what changed, or current project state. That belongs in `PLAN.md`, in the code itself, or in `git log`.

## PLAN.md update protocol

`PLAN.md` is the MVP checklist. Whenever a change to scope, structure, or a checklist item is warranted, follow this protocol — never edit `PLAN.md` silently:

1. **Propose in chat first.** State the exact diff you want to apply (which checkbox flips, which line is added/removed/reworded) and the reason.
2. **Wait for explicit user confirmation.** Do not infer approval from silence or from approval of an unrelated action. The user must say yes to the `PLAN.md` change specifically.
3. **Apply the edit only after confirmation**, then show the user the resulting section.
4. **If the user is not satisfied**, revise and re-propose. Do not move on until the user agrees the plan reflects reality.

When to trigger this protocol:
- A checklist item moves between `[ ]` / `[~]` / `[x]`.
- A new feature, phase, or section is added.
- A decision changes (e.g. host choice, auth direction).
- The actual code drifts from what `PLAN.md` says is built — flag it and propose a correction.
- A user instruction implies new scope not on the checklist — pause, propose a new checkbox under the right Stage, get approval, then proceed.

Do **not** trigger this protocol for: pure bug fixes, refactors with no behavior change, doc typos in other files. Those don't move the MVP checklist.
