# backend/app/schemas/ — description

Pydantic models that define the JSON contract for request/response bodies. Schemas are the single source of truth for what the API accepts; routers depend on them.

## Files

### `__init__.py`

Empty package marker — no exports.

### `transcript_schema.py`

Defines `TranscriptSchema`, the request body for `POST /api/transcript`.

Depended on by `app/routers/transcript.py`. The frontend mirrors this shape in `frontend/src/api/transcript.ts` (TypeScript interface also named `TranscriptSchema`); changes here may require a corresponding TS update.

#### Classes

**`TranscriptSchema(BaseModel)`**

- Purpose: validate the incoming JSON for `POST /api/transcript`. FastAPI uses it both to parse the body and to generate the OpenAPI schema.
- Inherits: `pydantic.BaseModel` — gets validation, JSON serialization, and OpenAPI schema generation for free.
- Used by: `post_transcript` in `routers/transcript.py` declares it as the body type, so FastAPI auto-validates incoming requests.
- Fields:
  - `urls: list[str]` — required, `min_length=1`. One or more YouTube URLs or 11-char video IDs.
  - `include_timestamps: bool = True` — when `True`, each transcript line is prefixed with `[MM:SS]`.
  - `language: str = "en"` — BCP-47 language code passed to `youtube_transcript_api`.
  - `filename: str | None = None` — custom base filename (no extension). Only honored when `len(urls) == 1`; ignored for batches.
- Use case: a frontend form posts `{"urls": [...], "language": "en", "include_timestamps": true}` and FastAPI rejects malformed bodies before the route function runs.
- Limitations:
  - No URL-format validation at the schema layer — that's deferred to `services/url_parser.py::parse_video_id`. Schema accepts any string.
  - No upper bound on `len(urls)`; a malicious caller could submit a huge list (see also the router's "no batch-size limit" limitation).
  - `language` is a free-form string; invalid codes only surface at fetch time as `NoTranscriptFound`.
  - `filename` is not sanitized at the schema layer — `services/transcript.py::sanitize_filename` strips unsafe characters before use, but schema-level rejection of obviously bad inputs (e.g. path traversal) is not done here.
