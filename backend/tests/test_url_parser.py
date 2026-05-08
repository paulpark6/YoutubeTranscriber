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
# Module-level constants — reused across many table rows.
# Using a named constant makes it obvious that 9 rows share the same ID and
# that changes to one propagate everywhere.
# ---------------------------------------------------------------------------
_RICK_ROLL_ID = "dQw4w9WgXcQ"
_FAKE_PLAYLIST = "PLxyz"


# ---------------------------------------------------------------------------
# GLOBAL: real-world URLs that should resolve to a specific video ID.
# Each row is (raw_user_input, expected_video_id).
# ---------------------------------------------------------------------------
REAL_URLS: list[tuple[str, str]] = [
    # Standard watch URLs (desktop, copy-paste from address bar)
    (f"https://www.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    (f"https://youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    # Watch URL with timestamp ("Copy URL at current time")
    ("https://www.youtube.com/watch?v=N5Zk-xH1e0k&t=596s", "N5Zk-xH1e0k"),
    # Watch URL with timestamp + playlist params (mixed)
    (
        f"https://www.youtube.com/watch?v=9bZkp7q19f0&list={_FAKE_PLAYLIST}&t=12s",
        "9bZkp7q19f0",
    ),
    # Watch URL with ?si= tracking param (desktop share link)
    (
        f"https://www.youtube.com/watch?v={_RICK_ROLL_ID}&si=AbCdEfGhIjKlMnOp",
        _RICK_ROLL_ID,
    ),
    # youtu.be share link with ?si= (mobile "Share" button)
    ("https://youtu.be/8vIDZO_w7lY?si=_A4rcB8rw8vjODBI", "8vIDZO_w7lY"),
    # youtu.be with timestamp
    (f"https://youtu.be/{_RICK_ROLL_ID}?t=42", _RICK_ROLL_ID),
    # YouTube Shorts
    ("https://www.youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
    ("https://youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
    # YouTube Music
    (f"https://music.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    # Mobile YouTube
    (f"https://m.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    # Embed URLs
    (f"https://www.youtube.com/embed/{_RICK_ROLL_ID}", _RICK_ROLL_ID),
    # Raw 11-char IDs (just pasted)
    (_RICK_ROLL_ID, _RICK_ROLL_ID),
    ("xS-fX-CL3Ys", "xS-fX-CL3Ys"),  # contains '-' (valid in IDs)
    ("abc-def_ghi", "abc-def_ghi"),  # contains '-' and '_' (both valid)
    # URL / ID with leading/trailing whitespace (paste accident)
    (f"  https://youtu.be/{_RICK_ROLL_ID}  ", _RICK_ROLL_ID),
    (f"  {_RICK_ROLL_ID}  ", _RICK_ROLL_ID),
    # Scheme-less variants — user copied without "https://"
    (f"youtu.be/{_RICK_ROLL_ID}", _RICK_ROLL_ID),
    (f"youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    (f"www.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    (f"m.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    (f"music.youtube.com/watch?v={_RICK_ROLL_ID}", _RICK_ROLL_ID),
    ("www.youtube.com/shorts/aQvpqlSiUIQ", "aQvpqlSiUIQ"),
]


# ---------------------------------------------------------------------------
# GLOBAL: inputs that should raise ValueError.
# Each row is (raw_user_input, expected_error_substring).
# Substring match is case-insensitive.
# Every row provides a non-empty substring so there is a real message contract;
# "not a recognised" / "unrecognised" covers generic fallthrough cases.
# ---------------------------------------------------------------------------
INVALID_URLS: list[tuple[str, str]] = [
    # Empty / whitespace
    ("", "must not be empty"),
    ("   ", "must not be empty"),
    # Tab-only and newline-only inputs are whitespace — same branch
    ("\t", "must not be empty"),
    ("\n", "must not be empty"),
    # Wrong-length raw IDs
    ("dQw4w9WgXc", "not a recognised YouTube URL"),  # 10 chars
    ("dQw4w9WgXcQQ", "not a recognised YouTube URL"),  # 12 chars
    # Watch URL: missing or invalid `v` param
    (
        f"https://www.youtube.com/watch?list={_FAKE_PLAYLIST}",
        "Missing or invalid 'v' query parameter",
    ),
    (
        "https://www.youtube.com/watch?v=tooshort",
        "Missing or invalid 'v' query parameter",
    ),
    # youtu.be: invalid path (too short)
    ("https://youtu.be/bad", "youtu.be URL"),
    # youtu.be: empty path (no video at all)
    ("https://youtu.be/", "youtu.be URL"),
    # Shorts: invalid path (too long / illegal chars)
    ("https://www.youtube.com/shorts/toolong_id_here!", "Shorts URL"),
    # Embed: invalid path (too short) — embed branch must raise a clear error
    ("https://www.youtube.com/embed/tooshort", "embed"),
    # Non-YouTube domain
    ("https://vimeo.com/123456789", "not a recognised YouTube URL"),
    # Random text (not a URL, not 11 chars)
    ("not_a_url_at_all_and_not_11", "not a recognised YouTube URL"),
    # YouTube channel URL (not a video)
    ("https://www.youtube.com/channel/UCxxxxxx", "unrecognised YouTube URL path"),
    # Just the YouTube domain — no video selected
    ("https://www.youtube.com/", "unrecognised YouTube URL path"),
    # Channel handle URL — no video
    ("https://www.youtube.com/@MrBeast", "unrecognised YouTube URL path"),
    # Search results URL — no video
    (
        "https://www.youtube.com/results?search_query=cats",
        "unrecognised YouTube URL path",
    ),
    # Playlist URL (playlist support is a separate feature ticket)
    (
        f"https://www.youtube.com/playlist?list={_FAKE_PLAYLIST}",
        "unrecognised YouTube URL path",
    ),
    # Garbage with an 11-char substring buried inside.
    # The raw-ID gate (_is_valid_video_id) only runs on the stripped input; an
    # ID embedded in a longer string is NOT extracted — the input is not 11 chars.
    (f"xxxxxxhello world {_RICK_ROLL_ID} blahxx", "not a recognised YouTube URL"),
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
    """Each invalid input raises ValueError with a matching message substring."""
    with pytest.raises(ValueError) as exc_info:
        parse_video_id(raw_input)
    assert expected_error_substring.lower() in str(exc_info.value).lower()
