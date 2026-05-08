"""
Unit tests for backend/app/services/transcript.py

youtube-transcript-api is mocked throughout — no real network calls.

Note: format_transcript, sanitize_filename, and build_zip tests live here
alongside fetch_transcript tests for historical reasons; they test
transcript_format.py, transcript.py, and zip_builder.py respectively.
"""

import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.services.transcript import (
    fetch_transcript,
    sanitize_filename,
)
from app.services.transcript_format import format_transcript
from app.services.zip_builder import build_zip

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_FAKE_VIDEO_ID = "vid"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_segment(start: float, text: str) -> MagicMock:
    """Create a mock transcript segment object matching the library's API."""
    seg = MagicMock()
    seg.start = start
    seg.text = text
    return seg


# ---------------------------------------------------------------------------
# fetch_transcript
# ---------------------------------------------------------------------------

def _setup_fetch_mock(mock_api_cls: MagicMock, segments: list | None = None, side_effect=None) -> MagicMock:
    """Wire mock so api.list().find_transcript().fetch() returns segments or raises side_effect."""
    mock_transcript = mock_api_cls.return_value.list.return_value.find_transcript.return_value
    if side_effect is not None:
        mock_transcript.fetch.side_effect = side_effect
    else:
        mock_transcript.fetch.return_value = segments or []
    return mock_api_cls.return_value


class TestFetchTranscript:
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_list_of_dicts(self, mock_api_cls):
        _setup_fetch_mock(mock_api_cls, segments=[
            _make_segment(0.0, "Hello"),
            _make_segment(3.5, "World"),
        ])

        result = fetch_transcript("dQw4w9WgXcQ", language="en")

        assert result == [
            {"start": 0.0, "text": "Hello"},
            {"start": 3.5, "text": "World"},
        ]
        mock_api_cls.return_value.list.assert_called_once_with("dQw4w9WgXcQ")
        mock_api_cls.return_value.list.return_value.find_transcript.assert_called_once_with(["en"])

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_default_language_is_en(self, mock_api_cls):
        """fetch_transcript with no language arg defaults to 'en'."""
        _setup_fetch_mock(mock_api_cls, segments=[_make_segment(0.0, "Hi")])

        fetch_transcript(_FAKE_VIDEO_ID)

        mock_api_cls.return_value.list.return_value.find_transcript.assert_called_once_with(["en"])

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_empty_list_for_empty_segments(self, mock_api_cls):
        """fetch_transcript returns [] when the API returns no segments."""
        _setup_fetch_mock(mock_api_cls, segments=[])

        result = fetch_transcript(_FAKE_VIDEO_ID, language="en")

        assert result == []

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_value_error_on_no_transcript_found(self, mock_api_cls):
        _setup_fetch_mock(mock_api_cls, side_effect=NoTranscriptFound(_FAKE_VIDEO_ID, ["en"], MagicMock()))

        with pytest.raises(ValueError, match="No transcript found"):
            fetch_transcript(_FAKE_VIDEO_ID, language="en")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_value_error_on_transcripts_disabled(self, mock_api_cls):
        _setup_fetch_mock(mock_api_cls, side_effect=TranscriptsDisabled(_FAKE_VIDEO_ID))

        with pytest.raises(ValueError, match="disabled"):
            fetch_transcript(_FAKE_VIDEO_ID)

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_value_error_on_video_unavailable(self, mock_api_cls):
        _setup_fetch_mock(mock_api_cls, side_effect=VideoUnavailable(_FAKE_VIDEO_ID))

        with pytest.raises(ValueError, match="unavailable"):
            fetch_transcript(_FAKE_VIDEO_ID)

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_runtime_error_on_unexpected_exception(self, mock_api_cls):
        _setup_fetch_mock(mock_api_cls, side_effect=ConnectionError("network down"))

        with pytest.raises(RuntimeError, match="unexpected error"):
            fetch_transcript(_FAKE_VIDEO_ID)


# ---------------------------------------------------------------------------
# format_transcript
# ---------------------------------------------------------------------------

class TestFormatTranscript:
    def test_with_timestamps(self):
        segments = [
            {"start": 0.0, "text": "Hello"},
            {"start": 65.0, "text": "World"},
        ]
        result = format_transcript(segments, include_timestamps=True)
        assert result == "[00:00] Hello\n[01:05] World"

    def test_without_timestamps(self):
        segments = [
            {"start": 0.0, "text": "Hello"},
            {"start": 65.0, "text": "World"},
        ]
        result = format_transcript(segments, include_timestamps=False)
        assert result == "Hello\nWorld"

    def test_empty_segments_returns_empty_string(self):
        assert format_transcript([], include_timestamps=True) == ""
        assert format_transcript([], include_timestamps=False) == ""

    def test_skips_segments_with_empty_text(self):
        segments = [
            {"start": 0.0, "text": ""},
            {"start": 1.0, "text": "   "},
            {"start": 2.0, "text": "Hello"},
        ]
        result = format_transcript(segments, include_timestamps=False)
        assert result == "Hello"

    def test_timestamp_zero_padding(self):
        segments = [{"start": 5.0, "text": "Hi"}]
        result = format_transcript(segments, include_timestamps=True)
        assert result == "[00:05] Hi"

    def test_timestamp_over_one_hour(self):
        # 3661 seconds = 1 hour, 1 minute, 1 second
        # format_time shows total minutes, not hours:minutes:seconds — this is an
        # intentional design choice (no hours bucket). See CLAUDE.md architecture notes.
        segments = [{"start": 3661.0, "text": "Late"}]
        result = format_transcript(segments, include_timestamps=True)
        assert result == "[61:01] Late"

    def test_default_include_timestamps_is_true(self):
        segments = [{"start": 0.0, "text": "Hi"}]
        result = format_transcript(segments)
        assert "[00:00]" in result


# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_plain_name_unchanged_structure(self):
        result = sanitize_filename("my_video")
        assert result == "my_video"

    def test_replaces_illegal_characters(self):
        result = sanitize_filename('vi<de>o: "name"')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result

    def test_collapses_spaces_to_underscore(self):
        result = sanitize_filename("hello world")
        assert " " not in result
        assert result == "hello_world"

    def test_strips_leading_trailing_underscores_and_dots(self):
        result = sanitize_filename("___name___")
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_strips_leading_dot(self):
        """Leading dots create hidden files on Unix — they must be stripped."""
        assert not sanitize_filename(".hidden").startswith(".")
        assert not sanitize_filename("...name...").startswith(".")

    def test_strips_trailing_dot(self):
        """Trailing dots are problematic on Windows — they must be stripped."""
        assert not sanitize_filename("name.").endswith(".")
        assert not sanitize_filename("name...").endswith(".")

    def test_truncates_long_names(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_truncates_to_exactly_200_chars(self):
        """A name of exactly 200+ chars truncates to exactly 200."""
        long_name = "a" * 250
        result = sanitize_filename(long_name)
        assert len(result) == 200

    def test_empty_string_falls_back(self):
        result = sanitize_filename("")
        assert result == "transcript"

    def test_only_illegal_chars_falls_back(self):
        # All illegal chars are replaced and stripped → empty → fallback to "transcript"
        result = sanitize_filename('<>:"/\\|?*')
        assert result == "transcript"

    def test_slashes_replaced(self):
        result = sanitize_filename("path/to/file")
        assert "/" not in result

    def test_tab_and_newline_replaced(self):
        """Control characters (\t, \n) are treated as illegal and replaced."""
        result = sanitize_filename("my\tvideo\nname")
        assert "\t" not in result
        assert "\n" not in result


# ---------------------------------------------------------------------------
# build_zip
# ---------------------------------------------------------------------------

class TestBuildZip:
    def test_returns_bytes(self):
        result = build_zip({"hello.txt": "Hello, world!"})
        assert isinstance(result, bytes)

    def test_zip_contains_correct_files(self):
        files = {
            "a.txt": "Content A",
            "b.txt": "Content B",
        }
        zip_bytes = build_zip(files)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "a.txt" in names
            assert "b.txt" in names

    def test_zip_file_content_matches(self):
        files = {"transcript.txt": "Hello\nWorld"}
        zip_bytes = build_zip(files)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            content = zf.read("transcript.txt").decode("utf-8")
        assert content == "Hello\nWorld"

    def test_empty_dict_produces_valid_zip(self):
        zip_bytes = build_zip({})
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.namelist() == []

    def test_unicode_content_encoded_as_utf8(self):
        files = {"trans.txt": "日本語テキスト"}
        zip_bytes = build_zip(files)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            content = zf.read("trans.txt").decode("utf-8")
        assert content == "日本語テキスト"
