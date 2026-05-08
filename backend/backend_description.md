# backend/ — description

The Python/FastAPI server that powers `POST /api/transcript`. Imports use the `app.*` path, so `uvicorn` and `pytest` must be run from this folder (not the repo root).

## Subfolders

- **`app/`** — application source: routers, schemas, services, plus `main.py` (FastAPI entry point) and `config.py` (CORS).
- **`tests/`** — pytest suite: unit tests for services, integration tests for the router, plus shared fixtures.

## Files

### `requirements.txt`

Pinned production + test dependencies:

- `fastapi==0.115.6`, `uvicorn[standard]==0.32.1` — web framework + ASGI server.
- `youtube-transcript-api==1.2.3` — the upstream library that fetches captions.
- `pytest==8.3.4`, `pytest-asyncio==0.24.0`, `httpx==0.28.1` — test runner, async test support, HTTP client used by FastAPI's `TestClient`.

No functions to document — this is a dependency manifest.

## Run commands

```bash
# from backend/ with venv activated:
uvicorn app.main:app --reload --port 8000   # dev server
python -m pytest tests/ -v                  # full test suite
```
