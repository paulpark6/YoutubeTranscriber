"""
Parse YouTube video IDs from various URL formats.

Supported formats:
  - https://www.youtube.com/watch?v=VIDEO_ID
  - https://youtu.be/VIDEO_ID
  - https://www.youtube.com/shorts/VIDEO_ID
  - Raw 11-character video ID
"""

import re
from urllib.parse import urlparse, parse_qs

# YouTube video IDs are always exactly 11 characters: letters, digits, - and _
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _is_valid_video_id(candidate: str) -> bool:
    return bool(_VIDEO_ID_RE.match(candidate))


def parse_video_id(url: str) -> str:
    """
    Extract a YouTube video ID from a URL or raw ID string.

    Args:
        url: A YouTube URL (any supported format) or an 11-character video ID.

    Returns:
        The 11-character video ID string.

    Raises:
        ValueError: If the input cannot be resolved to a valid video ID.
    """
    url = url.strip()

    if not url:
        raise ValueError("URL must not be empty.")

    # Raw 11-character video ID (no slashes or dots — not a URL)
    if _is_valid_video_id(url):
        return url

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError(f"Could not parse URL: {url!r}")

    hostname = parsed.hostname or ""
    # Normalise: strip leading "www." so both "www.youtube.com" and
    # "youtube.com" match the same branch.
    hostname = hostname.removeprefix("www.")

    # --- youtu.be/VIDEO_ID ---
    if hostname == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
        if _is_valid_video_id(video_id):
            return video_id
        raise ValueError(
            f"Could not extract a valid video ID from youtu.be URL: {url!r}"
        )

    # --- youtube.com variants ---
    if hostname in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        path = parsed.path.rstrip("/")

        # /shorts/VIDEO_ID
        if path.startswith("/shorts/"):
            video_id = path.split("/shorts/", 1)[1].split("/")[0]
            if _is_valid_video_id(video_id):
                return video_id
            raise ValueError(
                f"Could not extract a valid video ID from YouTube Shorts URL: {url!r}"
            )

        # /watch?v=VIDEO_ID
        if path == "/watch":
            qs = parse_qs(parsed.query)
            candidates = qs.get("v", [])
            if candidates and _is_valid_video_id(candidates[0]):
                return candidates[0]
            raise ValueError(
                f"Missing or invalid 'v' query parameter in YouTube URL: {url!r}"
            )

        # /embed/VIDEO_ID  (bonus — handle embedded player URLs gracefully)
        if path.startswith("/embed/"):
            video_id = path.split("/embed/", 1)[1].split("/")[0]
            if _is_valid_video_id(video_id):
                return video_id

        raise ValueError(
            f"Unrecognised YouTube URL path. Expected /watch?v=, /shorts/, or "
            f"/embed/ — got: {url!r}"
        )

    raise ValueError(
        f"Not a recognised YouTube URL. Expected youtube.com or youtu.be — got: {url!r}"
    )
