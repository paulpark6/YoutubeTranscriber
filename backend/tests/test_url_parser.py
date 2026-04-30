"""
Unit tests for backend/app/services/url_parser.py

Real-world URL samples are kept in two global tables — REAL_URLS for inputs
that should resolve to a video ID, and INVALID_URLS for inputs that should
raise ValueError. Tests parametrize over those tables so every change to
parser behaviour is reflected as a single-row edit, not scattered code.
"""

import pytest

from app.services.url_parser import parse_video_id


# ---------------------------------------------------------------------------
# GLOBAL: real-world URLs that should resolve to a specific video ID.
# Each row is (raw_user_input, expected_video_id).
# ---------------------------------------------------------------------------
REAL_URLS: list[tuple[str, str]] = [
    # Standard watch URLs (desktop, copy-paste from address bar)
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    # Watch URL with timestamp ("Copy URL at current time")
    ("https://www.youtube.com/watch?v=N5Zk-xH1e0k&t=596s", "N5Zk-xH1e0k"),
    # Watch URL with timestamp + playlist params (mixed)
    ("https://www.youtube.com/watch?v=9bZkp7q19f0&list=PLxyz&t=12s", "9bZkp7q19f0"),
    # youtu.be share link with ?si= (mobile "Share" button)
    ("https://youtu.be/8vIDZO_w7lY?si=_A4rcB8rw8vjODBI", "8vIDZO_w7lY"),
    # youtu.be with timestamp
    ("https://youtu.be/dQw4w9WgXcQ?t=42", "dQw4w9WgXcQ"),
    # YouTube Shorts
    ("https://www.youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
    ("https://youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
    # YouTube Music
    ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    # Mobile YouTube
    ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    # Embed URLs
    ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    # Raw 11-char IDs (just pasted)
    ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("xS-fX-CL3Ys", "xS-fX-CL3Ys"),  # contains '-' (valid in IDs)
    ("abc-def_ghi", "abc-def_ghi"),  # contains '-' and '_' (both valid)
    # URL / ID with leading/trailing whitespace (paste accident)
    ("  https://youtu.be/dQw4w9WgXcQ  ", "dQw4w9WgXcQ"),
    ("  dQw4w9WgXcQ  ", "dQw4w9WgXcQ"),
    # Scheme-less variants — user copied without "https://"
    ("youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("music.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("www.youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
]


# ---------------------------------------------------------------------------
# GLOBAL: inputs that should raise ValueError.
# Each row is (raw_user_input, expected_error_substring).
# An empty substring means "any ValueError message is acceptable".
# Substring match is case-insensitive.
# ---------------------------------------------------------------------------
INVALID_URLS: list[tuple[str, str]] = [
    # Empty / whitespace
    ("", "must not be empty"),
    ("   ", "must not be empty"),
    # Wrong-length raw IDs
    ("dQw4w9WgXc", "Not a recognised YouTube URL"),     # 10 chars
    ("dQw4w9WgXcQQ", "Not a recognised YouTube URL"),   # 12 chars
    # Watch URL: missing or invalid `v` param
    ("https://www.youtube.com/watch?list=PLxyz", "Missing or invalid 'v' query parameter"),
    ("https://www.youtube.com/watch?v=tooshort", "Missing or invalid 'v' query parameter"),
    # youtu.be: invalid path
    ("https://youtu.be/bad", "youtu.be URL"),
    # Shorts: invalid path
    ("https://www.youtube.com/shorts/toolong_id_here!", "Shorts URL"),
    # Non-YouTube domain
    ("https://vimeo.com/123456789", "Not a recognised YouTube URL"),
    # Random text (not a URL, not 11 chars)
    ("not_a_url_at_all_and_not_11", ""),
    # YouTube channel URL (not a video)
    ("https://www.youtube.com/channel/UCxxxxxx", ""),
    # Just the YouTube domain — no video selected
    ("https://www.youtube.com/", ""),
    # Channel handle URL — no video
    ("https://www.youtube.com/@MrBeast", ""),
    # Search results URL — no video
    ("https://www.youtube.com/results?search_query=cats", ""),
    # Playlist URL (playlist support is a separate feature ticket)
    ("https://www.youtube.com/playlist?list=PLxyz", ""),
    # Garbage with an 11-char substring buried inside — must NOT be scraped out
    ("xxxxxxhello world dQw4w9WgXcQ blahxx", ""),
]


# ---------------------------------------------------------------------------
# Parametrized tests over the global tables.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw_input, expected_id", REAL_URLS)
def test_real_url_extracts_expected_id(raw_input: str, expected_id: str) -> None:
    """Each real-world URL in REAL_URLS resolves to its expected video ID."""
    assert parse_video_id(raw_input) == expected_id


@pytest.mark.parametrize("raw_input, expected_error_substring", INVALID_URLS)
def test_invalid_url_raises_value_error(
    raw_input: str, expected_error_substring: str
) -> None:
    """Each input in INVALID_URLS raises ValueError; if a substring is given, it appears in the message."""
    with pytest.raises(ValueError) as exc_info:
        parse_video_id(raw_input)
    if expected_error_substring:
        assert expected_error_substring.lower() in str(exc_info.value).lower()
