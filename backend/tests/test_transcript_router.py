"""
Integration tests for POST /api/transcript.

youtube-transcript-api is mocked — no real network calls are made.
"""

import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable


# Patch target: the YouTubeTranscriptApi as used inside the service module.
_API_TARGET = "app.services.transcript.YouTubeTranscriptApi"

# ---------------------------------------------------------------------------
# Module-level URL / ID constants — prevents silent typos and makes coupling
# between URL literals and bare ID assertions explicit.
# ---------------------------------------------------------------------------

_VIDEO_ID_1 = "dQw4w9WgXcQ"
_VIDEO_ID_2 = "9bZkp7q19f0"
_URL_1 = f"https://youtu.be/{_VIDEO_ID_1}"
_URL_2 = f"https://youtu.be/{_VIDEO_ID_2}"


def _make_segment(start: float, text: str) -> MagicMock:
    seg = MagicMock()
    seg.start = start
    seg.text = text
    return seg


def _fake_segments() -> list[MagicMock]:
    return [
        _make_segment(0.0, "Hello"),
        _make_segment(5.0, "World"),
    ]


def _setup_mock(mock_api_cls: MagicMock, segments: list[MagicMock] | None = None) -> MagicMock:
    """Wire mock so api.list().find_transcript().fetch() returns segments."""
    mock_instance = mock_api_cls.return_value
    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = segments if segments is not None else _fake_segments()
    mock_instance.list.return_value.find_transcript.return_value = mock_transcript
    return mock_instance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post(client: TestClient, payload: dict) -> "Response":  # noqa: F821
    return client.post("/api/transcript", json=payload)


# ---------------------------------------------------------------------------
# Single URL — success
# ---------------------------------------------------------------------------

class TestSingleUrl:
    @patch(_API_TARGET)
    def test_returns_txt_file(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1]})

        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert ".txt" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_txt_content_includes_timestamps_by_default(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1]})

        assert resp.status_code == 200
        body = resp.text
        assert "[00:00]" in body
        assert "Hello" in body

    @patch(_API_TARGET)
    def test_txt_content_no_timestamps(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [_URL_1],
                "include_timestamps": False,
            },
        )

        assert resp.status_code == 200
        body = resp.text
        assert "[" not in body
        assert "Hello" in body

    @patch(_API_TARGET)
    def test_custom_filename_honoured(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [_URL_1],
                "filename": "my_custom_name",
            },
        )

        assert resp.status_code == 200
        assert "my_custom_name.txt" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_language_parameter_passed_through(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [_URL_1],
                "language": "es",
            },
        )

        assert resp.status_code == 200
        # Verify find_transcript was called with the requested language
        mock_api_cls.return_value.list.return_value.find_transcript.assert_called_once_with(["es"])

    @patch(_API_TARGET)
    def test_filename_with_path_traversal_is_sanitized(self, mock_api_cls, client: TestClient):
        """
        A filename containing path separators must have them removed so no path
        traversal is possible via Content-Disposition. Slashes are the critical
        risk — sanitize_filename replaces '/' and ':' with '_'. Note that '.'
        characters within a filename are kept (they are valid), so '..' survives
        as '..' inside a name, but since '/' is stripped it cannot cause traversal.
        """
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [_URL_1],
                "filename": "evil/../name",
            },
        )

        assert resp.status_code == 200
        disposition = resp.headers["content-disposition"]
        # No slash may appear in the sanitized filename — that's the traversal vector.
        assert "evil/name" not in disposition
        assert "/" not in disposition.split("filename=", 1)[-1]


# ---------------------------------------------------------------------------
# Multiple URLs — success
# ---------------------------------------------------------------------------

class TestMultipleUrls:
    @patch(_API_TARGET)
    def test_returns_zip_file(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]
        assert "transcripts.zip" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_zip_contains_txt_for_each_url(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        txt_files = [n for n in names if n.endswith(".txt")]
        assert len(txt_files) == 2

    @patch(_API_TARGET)
    def test_custom_filename_ignored_for_multiple_urls(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [_URL_1, _URL_2],
                "filename": "should_be_ignored",
            },
        )

        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        assert not any("should_be_ignored" in n for n in names)

    @patch(_API_TARGET)
    def test_duplicate_video_id_gets_suffixed(self, mock_api_cls, client: TestClient):
        """Two identical URLs produce <id>.txt and <id>_1.txt — not a single overwritten file."""
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1, _URL_1]})

        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        assert f"{_VIDEO_ID_1}.txt" in names
        assert f"{_VIDEO_ID_1}_1.txt" in names

    @patch(_API_TARGET)
    def test_mixed_empty_and_valid_urls_returns_two_file_zip(self, mock_api_cls, client: TestClient):
        """Empty URL entries are stripped; the ZIP has one file per non-empty URL."""
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": [_URL_1, "", _URL_2]})

        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        txt_files = [n for n in names if n.endswith(".txt")]
        assert len(txt_files) == 2


# ---------------------------------------------------------------------------
# Partial failure
# ---------------------------------------------------------------------------

class TestPartialFailure:
    @patch(_API_TARGET)
    def test_zip_includes_errors_txt_on_partial_failure(self, mock_api_cls, client: TestClient):
        call_count = 0

        def find_transcript_side_effect(langs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_t = MagicMock()
                mock_t.fetch.return_value = _fake_segments()
                return mock_t
            raise NoTranscriptFound("vid2", ["en"], MagicMock())

        mock_api_cls.return_value.list.return_value.find_transcript.side_effect = find_transcript_side_effect

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        assert "_errors.txt" in names

    @patch(_API_TARGET)
    def test_errors_txt_lists_failed_url(self, mock_api_cls, client: TestClient):
        call_count = 0

        def find_transcript_side_effect(langs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_t = MagicMock()
                mock_t.fetch.return_value = _fake_segments()
                return mock_t
            raise TranscriptsDisabled(_VIDEO_ID_2)

        mock_api_cls.return_value.list.return_value.find_transcript.side_effect = find_transcript_side_effect

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            errors_content = zf.read("_errors.txt").decode("utf-8")

        # The failed video ID must appear in the error file — not just any content.
        assert _VIDEO_ID_2 in errors_content

    @patch(_API_TARGET)
    def test_errors_txt_contains_header_line(self, mock_api_cls, client: TestClient):
        """_errors.txt must begin with the documented header line."""
        call_count = 0

        def find_transcript_side_effect(langs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_t = MagicMock()
                mock_t.fetch.return_value = _fake_segments()
                return mock_t
            raise VideoUnavailable(_VIDEO_ID_2)

        mock_api_cls.return_value.list.return_value.find_transcript.side_effect = find_transcript_side_effect

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            errors_content = zf.read("_errors.txt").decode("utf-8")

        assert "The following videos could not be transcribed:" in errors_content


# ---------------------------------------------------------------------------
# All failures
# ---------------------------------------------------------------------------

class TestAllFailure:
    @patch(_API_TARGET)
    def test_returns_400_when_all_urls_fail(self, mock_api_cls, client: TestClient):
        mock_api_cls.return_value.list.return_value.find_transcript.return_value.fetch.side_effect = VideoUnavailable("vid")

        resp = _post(client, {"urls": [_URL_1, _URL_2]})

        assert resp.status_code == 400

    @patch(_API_TARGET)
    def test_400_body_contains_detail(self, mock_api_cls, client: TestClient):
        mock_api_cls.return_value.list.return_value.find_transcript.return_value.fetch.side_effect = VideoUnavailable("vid")

        resp = _post(client, {"urls": [_URL_1]})

        assert resp.status_code == 400
        body = resp.json()
        assert "detail" in body

    def test_returns_400_for_all_invalid_urls(self, client: TestClient):
        resp = _post(
            client,
            {"urls": ["not-a-url-at-all-longerthan11", "also-not-valid-long"]}
        )
        assert resp.status_code == 400

    def test_returns_400_for_empty_urls(self, client: TestClient):
        resp = _post(client, {"urls": ["   ", "   "]})
        assert resp.status_code == 400
        # Confirm the error message is the expected fallback, not an internal trace
        body = resp.json()
        assert "detail" in body
        assert "No valid URLs provided" in body["detail"]


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_missing_urls_field_returns_422(self, client: TestClient):
        resp = _post(client, {"include_timestamps": True})
        assert resp.status_code == 422

    def test_empty_urls_list_returns_422(self, client: TestClient):
        resp = _post(client, {"urls": []})
        assert resp.status_code == 422

    def test_malformed_json_returns_422(self, client: TestClient):
        """A request body that is not valid JSON must yield a 422 Unprocessable Entity."""
        resp = client.post(
            "/api/transcript",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------

class TestCors:
    @patch(_API_TARGET)
    def test_cors_exposes_content_disposition(self, mock_api_cls, client: TestClient):
        """
        Content-Disposition must be in access-control-expose-headers on the actual
        response so that browsers running on a different origin can read the filename.
        This is a key invariant documented in CLAUDE.md — a misconfiguration in
        main.py would silently break production downloads.

        The expose_headers value is returned on the actual cross-origin response
        (not the preflight), so we send a POST with an Origin header to verify it.
        """
        _setup_mock(mock_api_cls)

        resp = client.post(
            "/api/transcript",
            json={"urls": [_URL_1]},
            headers={"Origin": "http://localhost:5173"},
        )

        assert resp.status_code == 200
        expose = resp.headers.get("access-control-expose-headers", "")
        assert "Content-Disposition" in expose
