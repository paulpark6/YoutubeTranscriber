"""
Shared pytest fixtures for the backend test suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """A TestClient that exercises the full FastAPI app."""
    return TestClient(app)
