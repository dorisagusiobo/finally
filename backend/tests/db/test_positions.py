"""Tests for position repository functions."""

from __future__ import annotations

from app.db import delete_position, get_position, list_positions, upsert_position


def test_get_position_missing_returns_none():
    assert get_position("AAPL") is None


def test_upsert_position_creates():
    position = upsert_position("AAPL", quantity=10, avg_cost=190.0)

    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 10
    assert position["avg_cost"] == 190.0
    assert get_position("AAPL")["quantity"] == 10


def test_upsert_position_existing_updates_not_duplicates():
    first = upsert_position("AAPL", quantity=10, avg_cost=190.0)
    second = upsert_position("AAPL", quantity=15, avg_cost=195.0)

    assert first["id"] == second["id"]
    assert second["quantity"] == 15
    assert second["avg_cost"] == 195.0
    assert len(list_positions()) == 1


def test_list_positions_ordered_by_ticker():
    upsert_position("TSLA", quantity=1, avg_cost=250.0)
    upsert_position("AAPL", quantity=1, avg_cost=190.0)

    tickers = [p["ticker"] for p in list_positions()]
    assert tickers == ["AAPL", "TSLA"]


def test_delete_position():
    upsert_position("AAPL", quantity=10, avg_cost=190.0)

    delete_position("AAPL")

    assert get_position("AAPL") is None


def test_delete_position_not_present_does_not_raise():
    delete_position("NOPE")  # should not raise

    assert list_positions() == []
