"""Fixtures for db tests — every test gets an isolated temp-file database."""

from __future__ import annotations

import pytest

from app.db import connection


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """Point the db module at a fresh temp-file database for the duration of the test."""
    connection.configure(tmp_path / "test.db")
    yield
    connection.close()
