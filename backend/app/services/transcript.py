"""
Core transcript logic: fetch and sanitize filenames.
"""

import logging
import re
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)


def fetch_transcript(video_id: str, language: str = "en") -> list[dict[str, Any]]:
    """
    Fetch the transcript for a YouTube video.

    Args:
        video_id: 11-character YouTube video ID.
        language:  BCP-47 language code (e.g. "en", "es").

    Returns:
        List of segment dicts, each with at least ``start`` (float) and
        ``text`` (str) keys.

    Raises:
        ValueError: For invalid video IDs or unavailable transcripts, with a
                    user-friendly message.
        RuntimeError: For unexpected network or library errors.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript = api.list(video_id).find_transcript([language]).fetch()
        # The API returns FetchedTranscript objects; convert to plain dicts so
        # callers have no dependency on the library's internal types.
        return [{"start": segment.start, "text": segment.text} for segment in transcript]

    except NoTranscriptFound:
        raise ValueError(
            f"No transcript found for video '{video_id}' in language '{language}'. "
            "Try a different language code or check that the video has captions."
        )
    except TranscriptsDisabled:
        raise ValueError(
            f"Transcripts are disabled for video '{video_id}'. "
            "The video owner has turned off captions."
        )
    except VideoUnavailable:
        raise ValueError(
            f"Video '{video_id}' is unavailable. "
            "It may be private, deleted, or region-locked."
        )
    except Exception as exc:
        logger.exception("Unexpected error fetching transcript for video '%s'", video_id)
        raise RuntimeError(
            f"An unexpected error occurred while fetching the transcript for '{video_id}'. "
            "Please try again later."
        ) from exc


def sanitize_filename(name: str) -> str:
    """
    Strip or replace characters that are unsafe for filenames across common OSes.

    Replaces runs of unsafe characters with underscores, strips leading/trailing
    whitespace and dots, and truncates to 200 characters to avoid path-length issues.

    Args:
        name: Raw filename (without extension).

    Returns:
        A safe, non-empty filename string.
    """
    # Remove or replace characters that are problematic on Windows, macOS, or Linux.
    # Keep alphanumerics, spaces, hyphens, underscores, and parentheses.
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Collapse multiple consecutive underscores/spaces into a single underscore
    sanitized = re.sub(r"[\s_]+", "_", sanitized)
    # Strip leading/trailing underscores and dots (dots at start hide files on Unix)
    sanitized = sanitized.strip("_.")
    # Truncate to a safe length
    sanitized = sanitized[:200]
    # Fall back if the result is empty
    if not sanitized:
        sanitized = "transcript"
    return sanitized
