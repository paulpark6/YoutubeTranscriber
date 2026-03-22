# Project Structure -- YouTube Transcription Web App

**Last updated:** 2026-03-21

---

## Folder Tree

```
YoutubeTranscription/
|
|-- mdfiles/                        # Project planning docs (this folder)
|   |-- PROJECT_PLAN.md             # Overall plan, phases, API contract, status
|   |-- PROJECT_STRUCTURE.md        # This file -- folder layout and file purposes
|   |-- AGENT_INSTRUCTIONS.md       # Task briefs for engineering agents
|
|-- backend/                        # FastAPI backend
|   |-- app/
|   |   |-- __init__.py             # Package init
|   |   |-- main.py                 # FastAPI app creation, CORS setup, router registration
|   |   |-- config.py               # Settings loaded from env vars (pydantic-settings)
|   |   |-- routers/
|   |   |   |-- __init__.py
|   |   |   |-- transcript.py       # POST /api/transcript endpoint
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- transcript.py       # Core logic: fetch transcript, format text, build ZIP
|   |   |   |-- url_parser.py       # Extract video ID from various YouTube URL formats
|   |   |-- schemas/
|   |   |   |-- __init__.py
|   |   |   |-- transcript.py       # Pydantic request/response models
|   |-- tests/
|   |   |-- __init__.py
|   |   |-- conftest.py             # Shared fixtures (TestClient, mocks)
|   |   |-- test_url_parser.py      # URL parser unit tests
|   |   |-- test_transcript_service.py  # Transcript service unit tests
|   |   |-- test_transcript_router.py   # Endpoint integration tests
|   |-- requirements.txt            # Python dependencies
|   |-- .env.example                # Template for backend env vars
|
|-- frontend/                       # React + Vite + TypeScript frontend
|   |-- src/
|   |   |-- App.tsx                 # Root component, layout
|   |   |-- main.tsx                # Vite entry point, renders App
|   |   |-- components/
|   |   |   |-- TranscriptForm.tsx  # Main form: URL input, options, submit button
|   |   |   |-- LanguageSelector.tsx # Language dropdown component
|   |   |   |-- ErrorMessage.tsx    # Displays per-video errors from API
|   |   |   |-- LoadingSpinner.tsx  # Spinner shown during API request
|   |   |-- api/
|   |   |   |-- transcript.ts      # API client: POST to /api/transcript, handle file download
|   |-- tests/
|   |   |-- TranscriptForm.test.tsx # Form behavior tests
|   |-- package.json                # Node dependencies and scripts
|   |-- tsconfig.json               # TypeScript config
|   |-- vite.config.ts              # Vite config (dev proxy, build settings)
|   |-- index.html                  # HTML entry point
|   |-- .env.example                # Template for frontend env vars
|
|-- transcribe.py                   # Original CLI script (kept for reference, not used by the app)
|-- requirements.txt                # Original root requirements (kept for reference)
|-- venv/                           # Python virtual environment (not committed)
```

---

## Naming Conventions

| Area | Convention | Example |
|---|---|---|
| Python files | `snake_case.py` | `url_parser.py` |
| Python classes | `PascalCase` | `TranscriptRequest` |
| Python functions | `snake_case` | `parse_video_id()` |
| TypeScript files | `PascalCase.tsx` for components, `camelCase.ts` for utilities | `TranscriptForm.tsx`, `transcript.ts` |
| React components | `PascalCase` | `LanguageSelector` |
| CSS/styles | TBD -- decide during frontend implementation | -- |
| Test files | `test_*.py` (backend), `*.test.tsx` (frontend) | `test_url_parser.py`, `TranscriptForm.test.tsx` |
| Env vars | `SCREAMING_SNAKE_CASE` | `CORS_ORIGINS`, `VITE_API_URL` |

---

## Where New Files Go

| If you are adding... | Put it in... |
|---|---|
| A new API endpoint | `backend/app/routers/` -- one file per resource |
| Business logic or data processing | `backend/app/services/` |
| A Pydantic model | `backend/app/schemas/` |
| A new React component | `frontend/src/components/` |
| A new API client function | `frontend/src/api/` |
| A backend test | `backend/tests/` |
| A frontend test | `frontend/tests/` |
| Shared types or constants (frontend) | `frontend/src/types/` (create when needed) |
| Utility/helper functions (frontend) | `frontend/src/utils/` (create when needed) |

---

## Key Dependencies

### Backend

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `youtube-transcript-api` | Fetch YouTube transcripts without API key |
| `pydantic` | Request/response validation (included with FastAPI) |
| `pydantic-settings` | Load config from env vars |
| `python-dotenv` | Load `.env` files in dev |
| `pytest` | Test runner |
| `httpx` | Async test client for FastAPI |

### Frontend

| Package | Purpose |
|---|---|
| `react` | UI library |
| `vite` | Build tool and dev server |
| `typescript` | Type safety |
| `@testing-library/react` | Component testing |
| `vitest` | Test runner (integrates with Vite) |

---

## Environment Variables

### Backend (`.env.example`)

```
CORS_ORIGINS=http://localhost:5173
PORT=8000
```

### Frontend (`.env.example`)

```
VITE_API_URL=http://localhost:8000
```
