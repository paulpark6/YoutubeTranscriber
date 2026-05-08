# backend/tests/ — description

Pytest suite for the backend. Mix of unit tests (services) and integration tests (router via FastAPI's `TestClient`). `youtube-transcript-api` is **mocked everywhere** — no real network calls.

Run from `backend/` with the venv activated:

```bash
python -m pytest tests/ -v
```

Current state: **96 passed, 0 failed.**

## Files

### `__init__.py`

Empty package marker — no exports.

### `conftest.py`

Shared pytest fixtures and helpers used across all test files.

#### Constants

- `RICK_ROLL_VIDEO_ID = "dQw4w9WgXcQ"` — canonical test video ID
- `VIDEO_ID_2 = "9bZkp7q19f0"` — second test video ID for batch tests
- `URL_1`, `URL_2` — `youtu.be/` URLs for the above IDs

#### Helpers

**`make_segment(start, text) -> MagicMock`** — creates a mock transcript segment matching the library's API shape.

**`fake_segments() -> list[MagicMock]`** — returns a reproducible two-segment list (0.0/"Hello", 5.0/"World").

**`setup_mock(mock_api_cls, segments) -> MagicMock`** — wires a patched `YouTubeTranscriptApi` so that `api.list(id).find_transcript([lang]).fetch()` returns `segments`.

#### Fixtures

**`client() -> TestClient`** *(scope=`function`)*

- Purpose: provide a fresh FastAPI `TestClient` per test function.
- Scope is `"function"` (not `"session"`) so that mock state from one test cannot leak into the next.
- Used by: `test_transcript_router.py` (injected via pytest parameter name).

### `test_url_parser.py`

Unit tests for `app/services/url_parser.py::parse_video_id`. Uses two parametrize tables — `REAL_URLS` (input → expected ID) and `INVALID_URLS` (input → expected error substring).

**Currently testing:**

- All supported URL shapes (`watch?v=`, `youtu.be/`, `shorts/`, `embed/`), with desktop/`m.`/`music.` subdomains, with timestamps, with playlist params, with `?si=` share params.
- Raw 11-char IDs, including those containing `-` and `_`.
- Whitespace tolerance (leading/trailing spaces, tab-only, newline-only).
- Scheme-less variants (`youtu.be/...`, `youtube.com/...`, `www.youtube.com/...`, `m.youtube.com/...`, `music.youtube.com/...`, `www.youtube.com/shorts/...`).
- Wrong-length IDs (10 and 12 chars).
- Missing `v` param, invalid `youtu.be` path, empty `youtu.be` path, invalid Shorts path, invalid embed path.
- Non-YouTube domains, channel URLs, handle URLs, search URLs, playlist URLs, garbage.
- Substring match for ID inside random text (must not be scraped out).
- All `INVALID_URLS` rows assert a non-empty error substring — no empty-string assertions that pass any message.
- Module-level constants `_RICK_ROLL_ID` and `_FAKE_PLAYLIST` to avoid repeating literals.

### `test_transcript_service.py`

Unit tests for `app/services/transcript.py` (`fetch_transcript`, `sanitize_filename`), plus `transcript_format.py::format_transcript` and `zip_builder.py::build_zip`. Uses `unittest.mock.patch` to substitute `YouTubeTranscriptApi`. All `youtube_transcript_api._errors` imports are at module level.

**Currently testing:**

- `fetch_transcript`: success path returns `[{"start", "text"}]` dicts; verifies `list(video_id)` is called with the right `video_id` (`assert_called_once_with`); each upstream exception (`NoTranscriptFound`, `TranscriptsDisabled`, `VideoUnavailable`) → `ValueError`; unexpected exception → `RuntimeError`. Default language is `"en"`. Returns `[]` for empty segments.
- `format_transcript`: with/without timestamps, empty input, empty/whitespace text segments, zero-padded timestamps, >1h timestamp behavior (documents the "no hours bucket" design), default `include_timestamps=True`.
- `sanitize_filename`: plain name unchanged, illegal characters replaced, spaces → underscore, leading/trailing underscores stripped, leading/trailing dots stripped, tabs and newlines replaced, truncation at exactly 200 chars pinned with `len == 200`, empty fallback to `"transcript"`, all-illegal-chars fallback asserts `result == "transcript"`, slashes replaced.
- `build_zip`: returns `bytes`, contains the expected entries, content matches, empty dict produces a valid empty ZIP, UTF-8 unicode round-trips.

### `test_transcript_router.py`

Integration tests for `POST /api/transcript`. Uses the `client` fixture and patches `app.services.transcript.YouTubeTranscriptApi`. Module-level constants `_VIDEO_ID_1`, `_VIDEO_ID_2`, `_URL_1`, `_URL_2` are used throughout to keep ID/URL coupling explicit.

**Currently testing:**

- **Single URL:** returns `text/plain`, includes `[MM:SS]` by default, `include_timestamps=False` strips them, custom `filename` honored, `language` param passed through to `find_transcript` (also asserts `status_code == 200`), path traversal in `filename` is sanitized (no `/` in disposition).
- **Multiple URLs:** returns `application/zip` with `transcripts.zip` filename (`"application/zip" in content-type`), ZIP contains one `.txt` per URL, custom `filename` ignored for batches, duplicate video IDs get `_1` suffix, mixed empty + valid URLs produce a ZIP with only the non-empty URL files.
- **Partial failure:** ZIP includes `_errors.txt`, error text contains the specific failed video ID (not an overly-permissive `or`), `_errors.txt` starts with the documented header line.
- **All-failure:** HTTP 400 with `detail` in the JSON body, `"No valid URLs provided"` for all-whitespace input, all-invalid-URLs → 400.
- **Input validation:** missing `urls` → 422; empty `urls` list → 422; malformed JSON body with `Content-Type: application/json` → 422.
- **CORS:** actual POST with `Origin: http://localhost:5173` returns `access-control-expose-headers: Content-Disposition`, confirming the key invariant from CLAUDE.md.
