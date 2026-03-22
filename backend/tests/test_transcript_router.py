"""
Integration tests for POST /api/transcript.

youtube-transcript-api is mocked — no real network calls are made.
"""

import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# Patch target: the YouTubeTranscriptApi as used inside the service module.
_API_TARGET = "app.services.transcript.YouTubeTranscriptApi"


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

        resp = _post(client, {"urls": ["https://youtu.be/dQw4w9WgXcQ"]})

        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert ".txt" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_txt_content_includes_timestamps_by_default(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(client, {"urls": ["https://youtu.be/dQw4w9WgXcQ"]})

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
                "urls": ["https://youtu.be/dQw4w9WgXcQ"],
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
                "urls": ["https://youtu.be/dQw4w9WgXcQ"],
                "filename": "my_custom_name",
            },
        )

        assert resp.status_code == 200
        assert "my_custom_name.txt" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_language_parameter_passed_through(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        _post(
            client,
            {
                "urls": ["https://youtu.be/dQw4w9WgXcQ"],
                "language": "es",
            },
        )

        # Verify find_transcript was called with the requested language
        mock_api_cls.return_value.list.return_value.find_transcript.assert_called_once_with(["es"])


# ---------------------------------------------------------------------------
# Multiple URLs — success
# ---------------------------------------------------------------------------

class TestMultipleUrls:
    @patch(_API_TARGET)
    def test_returns_zip_file(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ]
            },
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert "transcripts.zip" in resp.headers["content-disposition"]

    @patch(_API_TARGET)
    def test_zip_contains_txt_for_each_url(self, mock_api_cls, client: TestClient):
        _setup_mock(mock_api_cls)

        resp = _post(
            client,
            {
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ]
            },
        )

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
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ],
                "filename": "should_be_ignored",
            },
        )

        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        assert not any("should_be_ignored" in n for n in names)


# ---------------------------------------------------------------------------
# Partial failure
# ---------------------------------------------------------------------------

class TestPartialFailure:
    @patch(_API_TARGET)
    def test_zip_includes_errors_txt_on_partial_failure(self, mock_api_cls, client: TestClient):
        from youtube_transcript_api._errors import NoTranscriptFound

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

        resp = _post(
            client,
            {
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ]
            },
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
        assert "_errors.txt" in names

    @patch(_API_TARGET)
    def test_errors_txt_lists_failed_url(self, mock_api_cls, client: TestClient):
        from youtube_transcript_api._errors import TranscriptsDisabled

        call_count = 0

        def find_transcript_side_effect(langs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_t = MagicMock()
                mock_t.fetch.return_value = _fake_segments()
                return mock_t
            raise TranscriptsDisabled("9bZkp7q19f0")

        mock_api_cls.return_value.list.return_value.find_transcript.side_effect = find_transcript_side_effect

        resp = _post(
            client,
            {
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ]
            },
        )

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            errors_content = zf.read("_errors.txt").decode("utf-8")

        assert "9bZkp7q19f0" in errors_content or "youtu.be" in errors_content


# ---------------------------------------------------------------------------
# All failures
# ---------------------------------------------------------------------------

class TestAllFailure:
    @patch(_API_TARGET)
    def test_returns_400_when_all_urls_fail(self, mock_api_cls, client: TestClient):
        from youtube_transcript_api._errors import VideoUnavailable

        mock_api_cls.return_value.list.return_value.find_transcript.return_value.fetch.side_effect = VideoUnavailable("vid")

        resp = _post(
            client,
            {
                "urls": [
                    "https://youtu.be/dQw4w9WgXcQ",
                    "https://youtu.be/9bZkp7q19f0",
                ]
            },
        )

        assert resp.status_code == 400

    @patch(_API_TARGET)
    def test_400_body_contains_detail(self, mock_api_cls, client: TestClient):
        from youtube_transcript_api._errors import VideoUnavailable

        mock_api_cls.return_value.list.return_value.find_transcript.return_value.fetch.side_effect = VideoUnavailable("vid")

        resp = _post(client, {"urls": ["https://youtu.be/dQw4w9WgXcQ"]})

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
