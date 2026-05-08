# backend/app/routers/ — description

HTTP-facing endpoint handlers. One file per resource. Routers should stay thin: parse the request, call into `services/`, and shape the response. Business logic does not live here.

## Files

### `__init__.py`

Empty package marker — no exports.

### `transcript.py`

Defines the `/api` router and the single `POST /api/transcript` endpoint. Orchestrates the per-URL pipeline: parse video ID → fetch transcript → format → collect into a `dict[filename, text]`. Decides response shape (single-URL `.txt`, batch `.zip`, all-failed `HTTP 400`).

Depended on by `app/main.py`, which calls `app.include_router(router)`.

#### Module-level objects

- `router: APIRouter` — created with `prefix="/api"` and `tags=["transcript"]`. Registered in `main.py`. Inherits from FastAPI's `APIRouter`.
- `logger: logging.Logger` — module logger; emits warnings on per-URL failures so partial-batch errors are observable in logs without aborting the request.

#### Functions

**`post_transcript(request: TranscriptSchema) -> StreamingResponse`** *(async, decorated with `@router.post("/transcript")`)*

- Purpose: fetch and return YouTube transcripts as a downloadable file. Single URL → `.txt`; multiple URLs → `.zip`; partial failures → `.zip` with `_errors.txt`; all failed → `HTTP 400`.
- Inherits / called by: registered on `router`. Called by HTTP clients (the React frontend, or any caller of `POST /api/transcript`).
- Effect: iterates `request.urls`. For each URL: parses the video ID (catches `ValueError`), fetches the transcript (catches `ValueError`/`RuntimeError`), formats it, picks a filename (`request.filename` only honored if exactly one URL; otherwise the video ID; duplicates suffixed `_1`, `_2`, …), and stores it. After the loop: if nothing succeeded → `HTTPException(400)`; else if exactly one URL succeeded with no errors → `text/plain` `StreamingResponse`; else → `application/zip` `StreamingResponse` (with `_errors.txt` appended when there are errors). Sets `Content-Disposition` so the browser can pick the download filename.
- Use case: the only user-facing endpoint of the app. The React form posts here.
- Limitations:
  - URLs are processed sequentially in a synchronous loop inside an `async` function — large batches block the event loop (no `asyncio.gather`, no thread offload). `youtube_transcript_api` is a blocking library.
  - No request-size limit beyond `min_length=1` on `urls` (Pydantic). A request with 1000 URLs will be attempted serially.
  - Error messages contain the raw URL string, which is fine for the frontend but means malformed inputs may surface in logs verbatim.
  - The `_errors.txt` filename is hardcoded — if a batch happens to contain a video whose sanitized ID equals `_errors`, the error file would collide (extremely unlikely given video ID charset, but worth knowing).
