"""Fixtures for API tests — an isolated temp-file database and a TestClient
whose lifespan (market data source start/stop) runs for the duration of the test.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import connection


@pytest.fixture
def client(tmp_path):
    connection.configure(tmp_path / "test.db")

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    connection.close()
