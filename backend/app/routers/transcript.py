"""
POST /api/transcript endpoint.

Behaviour:
  - Single URL  -> StreamingResponse (.txt)
  - Multiple URLs -> StreamingResponse (.zip)
  - Batch with some failures -> .zip containing successful files + _errors.txt
  - All failures -> HTTP 400 JSON
"""

import io
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.transcript import TranscriptRequest
from app.services.transcript import (
    fetch_transcript,
    sanitize_filename,
)
from app.services.transcript_format import format_transcript
from app.services.url_parser import parse_video_id
from app.services.zip_builder import build_zip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transcript"])


@router.post("/transcript")
async def post_transcript(request: TranscriptRequest) -> StreamingResponse:
    """
    Fetch and return YouTube transcripts as a downloadable file.

    - Single URL: returns a .txt file.
    - Multiple URLs: returns a .zip archive.
    - Partial batch failures: .zip includes _errors.txt.
    - All URLs fail: HTTP 400 with a JSON error body.
    """
    successful: dict[str, str] = {}  # filename (with ext) -> formatted text
    errors: list[str] = []           # human-readable error lines

    for raw_url in request.urls:
        raw_url = raw_url.strip()
        if not raw_url:
            continue

        # --- Parse video ID ---
        try:
            video_id = parse_video_id(raw_url)
        except ValueError as exc:
            errors.append(f"{raw_url}: {exc}")
            logger.warning("URL parse failure for %r: %s", raw_url, exc)
            continue

        # --- Fetch transcript ---
        try:
            segments = fetch_transcript(video_id, language=request.language)
        except (ValueError, RuntimeError) as exc:
            errors.append(f"{raw_url}: {exc}")
            logger.warning("Transcript fetch failure for video '%s': %s", video_id, exc)
            continue

        # --- Format ---
        text = format_transcript(segments, include_timestamps=request.include_timestamps)

        # --- Determine filename ---
        if len(request.urls) == 1 and request.filename:
            base = sanitize_filename(request.filename)
        else:
            base = sanitize_filename(video_id)

        filename = f"{base}.txt"
        # Avoid duplicate filenames in a batch by appending an index suffix.
        if filename in successful:
            idx = 1
            while f"{base}_{idx}.txt" in successful:
                idx += 1
            filename = f"{base}_{idx}.txt"

        successful[filename] = text

    # --- All failed ---
    if not successful:
        error_detail = "; ".join(errors) if errors else "No valid URLs provided."
        raise HTTPException(status_code=400, detail=error_detail)

    # --- Single URL success ---
    if len(request.urls) == 1 and not errors:
        filename, content = next(iter(successful.items()))
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    # --- Batch (or single URL that had errors) -> ZIP ---
    zip_files: dict[str, str] = dict(successful)

    if errors:
        error_lines = ["The following videos could not be transcribed:", ""]
        error_lines.extend(f"  - {line}" for line in errors)
        zip_files["_errors.txt"] = "\n".join(error_lines)

    zip_bytes = build_zip(zip_files)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="transcripts.zip"',
        },
    )
