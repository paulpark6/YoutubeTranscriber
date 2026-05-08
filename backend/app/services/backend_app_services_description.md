# backend/app/services/ — description

Pure business logic. No FastAPI imports, no HTTP concerns. Routers call into these modules and remain thin. Each module is independently testable.

## Files

### `__init__.py`

Empty package marker — no exports.

### `url_parser.py`

Extracts a YouTube video ID from any supported URL format or raw 11-character ID.

Depended on by `routers/transcript.py` (`parse_video_id` is called once per URL in the request).

#### Module-level objects

- `_VIDEO_ID_RE: re.Pattern` — matches exactly 11 characters of `[A-Za-z0-9_-]`. The canonical YouTube video ID shape.

#### Functions

**`_is_valid_video_id(candidate: str) -> bool`** *(private)*

- Purpose: predicate — does the string match the canonical 11-char video ID regex?
- Inherits / called by: standalone helper. Called by `parse_video_id` at multiple decision points.
- Effect: returns `True`/`False`.
- Use case: tells the parser when a path segment or query value is a usable video ID.
- Limitations: regex-only — does not check that the ID actually exists on YouTube.

**`parse_video_id(url: str) -> str`**

- Purpose: turn any supported YouTube URL or raw 11-char ID into the canonical video ID.
- Inherits / called by: standalone. Called by `routers/transcript.py::post_transcript` once per `request.urls` entry.
- Effect: strips whitespace; if the input is already an 11-char ID, returns it; otherwise calls `urlparse` and matches against `youtu.be`, `youtube.com`/`m.youtube.com`/`music.youtube.com` (handling `/watch?v=`, `/shorts/`, `/embed/`). Strips `www.` prefix. Raises `ValueError` with a specific message on every failure mode.
- Use case: the request pipeline converts user-pasted URLs into IDs before calling `youtube-transcript-api`.
- Limitations:
  - **Scheme-less URLs are not handled.** Inputs like `youtube.com/watch?v=…` (no `https://`) cause `urlparse` to return `hostname = ""`, so the function falls through to the final `ValueError`. This is the cause of the 6 currently-failing tests in `test_url_parser.py` — see Backend-issue2 in `Current_plan.md`.
  - URL shortener redirects are not followed.
  - Playlist URLs (`/playlist?list=…`) and channel URLs (`/@handle`) are intentionally rejected.
  - Live URLs (`/live/VIDEO_ID`) are not supported.

### `transcript.py`

Wraps the `youtube-transcript-api` library and provides filename sanitization. Translates upstream library exceptions into user-friendly `ValueError` / `RuntimeError`.

Depended on by `routers/transcript.py` (uses `fetch_transcript` and `sanitize_filename`).

> Note: this file is named `transcript.py` (not renamed in Backend-issue1). The schema sibling was renamed to `transcript_schema.py` to disambiguate.

#### Module-level objects

- `logger: logging.Logger` — module logger; emits an `exception(...)` traceback for unexpected fetch failures.

#### Functions

**`fetch_transcript(video_id: str, language: str = "en") -> list[dict[str, Any]]`**

- Purpose: fetch the transcript for a video ID and return a list of plain dicts (so callers don't depend on `youtube-transcript-api`'s internal types).
- Inherits / called by: standalone. Called by `routers/transcript.py::post_transcript`.
- Effect: instantiates `YouTubeTranscriptApi`, calls `.list(video_id).find_transcript([language]).fetch()`, and converts each `FetchedTranscript` segment into `{"start": float, "text": str}`. Catches `NoTranscriptFound`, `TranscriptsDisabled`, `VideoUnavailable` and re-raises as `ValueError` with a user-facing message; catches everything else, logs a traceback, and re-raises as `RuntimeError`.
- Use case: the per-URL fetch step in the request pipeline.
- Limitations:
  - Network call — slow and blocking. Called from inside an `async` route function but never offloaded to a thread, so it blocks the event loop.
  - No retry / backoff — transient network errors surface as `RuntimeError` immediately.
  - The router catches `(ValueError, RuntimeError)` together; adding any new exception type here requires updating the router's `except` clause too (see `CLAUDE.md` "Key invariants").
  - The `language` argument doesn't fall back to other available languages if the requested one is missing.

**`sanitize_filename(name: str) -> str`**

- Purpose: strip or replace characters that are unsafe for filenames across Windows / macOS / Linux.
- Inherits / called by: standalone. Called by `routers/transcript.py::post_transcript` for both user-supplied `filename` and for video IDs before they go into a ZIP.
- Effect: replaces `<>:"/\\|?*` and control chars with `_`; collapses runs of whitespace/underscores; strips leading/trailing `_` and `.`; truncates to 200 chars; falls back to `"transcript"` if the result is empty.
- Use case: prevents path traversal and OS-level filename errors when writing the response file or ZIP entry.
- Limitations:
  - Doesn't reject Windows reserved names (`CON`, `PRN`, `NUL`, `COM1`–`COM9`, etc.). Sanitized output `"CON"` is still a Windows reserved name.
  - Truncation at 200 chars is byte-naive — multi-byte UTF-8 characters could be counted as one but occupy more bytes on disk on some filesystems.
  - Aggressive collapse: `"hello world"` becomes `"hello_world"`, which may surprise users who expect spaces preserved.

### `transcript_format.py`

Pure formatting — turns a list of segment dicts into one display-ready string.

Depended on by `routers/transcript.py` (uses `format_transcript`).

#### Functions

**`_format_time(seconds: float) -> str`** *(private)*

- Purpose: convert seconds to `MM:SS`.
- Inherits / called by: standalone. Called by `format_transcript` when timestamps are enabled.
- Effect: returns `f"{minutes:02d}:{secs:02d}"`.
- Use case: prefix per-line timestamps in the formatted transcript.
- Limitations: no hours bucket — a 1h 5m video shows `65:00`, not `01:05:00`.

**`format_transcript(segments: list[dict[str, Any]], include_timestamps: bool = True) -> str`**

- Purpose: format raw transcript segments into a human-readable string with one segment per line.
- Inherits / called by: standalone. Called by `routers/transcript.py::post_transcript` after a successful fetch.
- Effect: skips segments with empty `text`; when `include_timestamps=True`, prefixes each line with `[MM:SS]`; joins with `\n`. Returns `""` for empty input.
- Use case: produces the body that goes into the `.txt` response or into a `.zip` entry.
- Limitations:
  - Hardcoded line separator (`\n`) — Windows clients downloading the `.txt` get LF endings, not CRLF.
  - No de-duplication of consecutive identical lines (sometimes happens in auto-generated captions).
  - Uses `segment.get("start", 0)` and `segment.get("text", "")` defensively, but the schema produced by `fetch_transcript` always includes both keys.

### `zip_builder.py`

In-memory ZIP archive builder for batch responses.

Depended on by `routers/transcript.py` (uses `build_zip`).

#### Functions

**`build_zip(files: dict[str, str]) -> bytes`**

- Purpose: build a ZIP archive in memory from `{filename: text_content}` and return raw bytes.
- Inherits / called by: standalone. Called by `routers/transcript.py::post_transcript` when responding with a batch (or partial-failure) ZIP.
- Effect: opens a `BytesIO` buffer, writes a `ZipFile` in `ZIP_DEFLATED` mode, encodes each value as UTF-8 and writes it as the named entry, and returns the buffer's bytes.
- Use case: build the `transcripts.zip` response without writing anything to disk.
- Limitations:
  - Entirely in memory — large batches (many videos, long transcripts) inflate process RSS. No streaming variant.
  - All entries are encoded as UTF-8; binary content is not supported by the type signature (text only).
  - No directory entries / nesting — flat archive only.
  - Caller is responsible for de-duplicating filenames; passing duplicate keys silently drops earlier values (dict semantics).
