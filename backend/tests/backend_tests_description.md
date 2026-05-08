# backend/tests/ — description

Pytest suite for the backend. Mix of unit tests (services) and integration tests (router via FastAPI's `TestClient`). `youtube-transcript-api` is **mocked everywhere** — no real network calls.

Run from `backend/` with the venv activated:

```bash
python -m pytest tests/ -v
```

Current state at time of writing: **73 passed, 6 failed.** The 6 failures are all in `test_url_parser.py` (scheme-less URL parametrize cases). Tracked as Backend-issue2 in `Current_plan.md`. Per-test-file improvement issues are appended at the bottom of `Current_plan.md`.

## Files

### `__init__.py`

Empty package marker — no exports.

### `conftest.py`

Shared pytest fixtures.

#### Fixtures

**`client() -> TestClient`** *(scope=`session`)*

- Purpose: provide a FastAPI `TestClient` wrapping the real `app` for integration tests.
- Inherits / called by: pytest auto-injects it into any test function that has a `client` parameter. Used by `test_transcript_router.py`.
- Effect: imports `app.main.app` and constructs `TestClient(app)` once per test session.
- Use case: lets integration tests do `client.post("/api/transcript", json=...)` without spinning up uvicorn.
- Limitations: session scope means side effects on `app` (e.g. mutating CORS at runtime) leak across tests. Not a concern today since tests don't mutate `app`.

### `test_url_parser.py`

Unit tests for `app/services/url_parser.py::parse_video_id`. Uses two parametrize tables — `REAL_URLS` (input → expected ID) and `INVALID_URLS` (input → expected error substring).

**Currently testing:**

- All supported URL shapes (`watch?v=`, `youtu.be/`, `shorts/`, `embed/`), with desktop/`m.`/`music.` subdomains, with timestamps, with playlist params, with `?si=` share params.
- Raw 11-char IDs, including those containing `-` and `_`.
- Whitespace tolerance.
- Scheme-less variants (these are the **6 failing** cases).
- Wrong-length IDs (10 and 12 chars).
- Missing `v` param, invalid `youtu.be` path, invalid Shorts path.
- Non-YouTube domains, channel URLs, search URLs, playlist URLs, garbage.
- Substring match for ID inside random text (must not be scraped out).

**Flaws / gaps:** see `Backend-issue-test_url_parser` in `Current_plan.md`.

### `test_transcript_service.py`

Unit tests for `app/services/transcript.py` (`fetch_transcript`, `sanitize_filename`), plus `transcript_format.py::format_transcript` and `zip_builder.py::build_zip`. Uses `unittest.mock.patch` to substitute `YouTubeTranscriptApi`.

**Currently testing:**

- `fetch_transcript`: success path returns `[{"start", "text"}]` dicts; each upstream exception (`NoTranscriptFound`, `TranscriptsDisabled`, `VideoUnavailable`) → `ValueError`; unexpected exception → `RuntimeError`. Verifies `find_transcript([language])` is called with the right list.
- `format_transcript`: with/without timestamps, empty input, empty/whitespace text segments, zero-padded timestamps, >1h timestamp behavior (documents the "no hours bucket" limitation), default `include_timestamps=True`.
- `sanitize_filename`: plain name unchanged, illegal characters replaced, spaces → underscore, leading/trailing underscores stripped, truncation at 200 chars, empty fallback to `"transcript"`, "all illegal" non-empty fallback, slashes replaced.
- `build_zip`: returns `bytes`, contains the expected entries, content matches, empty dict produces a valid empty ZIP, UTF-8 unicode round-trips.

**Flaws / gaps:** see `Backend-issue-test_transcript_service` in `Current_plan.md`.

### `test_transcript_router.py`

Integration tests for `POST /api/transcript`. Uses the `client` fixture and patches `app.services.transcript.YouTubeTranscriptApi`.

**Currently testing:**

- **Single URL:** returns `text/plain`, includes `[MM:SS]` by default, `include_timestamps=False` strips them, custom `filename` honored, `language` param passed through to `find_transcript`.
- **Multiple URLs:** returns `application/zip` with `transcripts.zip` filename, ZIP contains one `.txt` per URL, custom `filename` ignored for batches.
- **Partial failure:** ZIP includes `_errors.txt`, error text references the failed URL/ID.
- **All-failure:** HTTP 400 with `detail` in the JSON body. Also covers all-invalid-URLs and all-whitespace-URLs as 400 (these don't even reach the service).
- **Input validation:** missing `urls` → 422; empty `urls` list → 422 (Pydantic enforces `min_length=1`).

**Flaws / gaps:** see `Backend-issue-test_transcript_router` in `Current_plan.md`.
