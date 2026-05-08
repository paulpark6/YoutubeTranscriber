"""
Shared pytest fixtures and helpers for the backend test suite.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Shared video ID constants
# ---------------------------------------------------------------------------

RICK_ROLL_VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_ID_2 = "9bZkp7q19f0"

URL_1 = f"https://youtu.be/{RICK_ROLL_VIDEO_ID}"
URL_2 = f"https://youtu.be/{VIDEO_ID_2}"


# ---------------------------------------------------------------------------
# Segment factory
# ---------------------------------------------------------------------------

def make_segment(start: float, text: str) -> MagicMock:
    """Create a mock transcript segment matching the youtube-transcript-api shape."""
    seg = MagicMock()
    seg.start = start
    seg.text = text
    return seg


def fake_segments() -> list[MagicMock]:
    """Return a small, reproducible list of mock transcript segments."""
    return [
        make_segment(0.0, "Hello"),
        make_segment(5.0, "World"),
    ]


# ---------------------------------------------------------------------------
# Mock-wiring helper
# ---------------------------------------------------------------------------

def setup_mock(mock_api_cls: MagicMock, segments: list[MagicMock] | None = None) -> MagicMock:
    """
    Wire *mock_api_cls* so that:

        YouTubeTranscriptApi().list(video_id).find_transcript([lang]).fetch()

    returns *segments* (defaults to ``fake_segments()``).
    """
    mock_instance = mock_api_cls.return_value
    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = segments if segments is not None else fake_segments()
    mock_instance.list.return_value.find_transcript.return_value = mock_transcript
    return mock_instance


# ---------------------------------------------------------------------------
# TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client() -> TestClient:
    """
    A fresh TestClient for each test function.

    Scope is ``"function"`` (not ``"session"``) so that mock state leaking from
    one test cannot affect the next.
    """
    return TestClient(app)
