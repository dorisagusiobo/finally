"""Tests for the trade log and portfolio snapshot repository functions."""

from __future__ import annotations

import sqlite3

import pytest

from app.db import get_connection, insert_snapshot, insert_trade, list_snapshots


def test_insert_trade_returns_recorded_trade():
    trade = insert_trade("AAPL", "buy", quantity=5, price=190.0)

    assert trade["ticker"] == "AAPL"
    assert trade["side"] == "buy"
    assert trade["quantity"] == 5
    assert trade["price"] == 190.0
    assert trade["executed_at"]

    row = get_connection().execute(
        "SELECT * FROM trades WHERE id = ?", (trade["id"],)
    ).fetchone()
    assert row is not None


def test_insert_trade_rejects_invalid_side():
    with pytest.raises(sqlite3.IntegrityError):
        insert_trade("AAPL", "hold", quantity=5, price=190.0)


def test_insert_snapshot_returns_recorded_snapshot():
    snapshot = insert_snapshot(total_value=10500.0)

    assert snapshot["total_value"] == 10500.0
    assert snapshot["recorded_at"]


def test_list_snapshots_chronological_order():
    insert_snapshot(total_value=10000.0)
    insert_snapshot(total_value=10100.0)
    insert_snapshot(total_value=10200.0)

    values = [s["total_value"] for s in list_snapshots()]
    assert values == [10000.0, 10100.0, 10200.0]


def test_list_snapshots_limit_keeps_most_recent_in_order():
    for value in (10000.0, 10100.0, 10200.0, 10300.0):
        insert_snapshot(total_value=value)

    values = [s["total_value"] for s in list_snapshots(limit=2)]
    assert values == [10200.0, 10300.0]
