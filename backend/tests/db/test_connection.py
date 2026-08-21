"""Tests for lazy schema creation, seeding, and idempotent re-init."""

from __future__ import annotations

from app.db import connection
from app.db.schema import SEED_TICKERS


def test_creates_file_and_tables(tmp_path):
    db_path = tmp_path / "nested" / "finally.db"
    connection.configure(db_path)

    conn = connection.get_connection()

    assert db_path.exists()
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {
        "users",
        "watchlist",
        "positions",
        "trades",
        "portfolio_snapshots",
        "chat_messages",
    } <= tables


def test_seeds_default_user_and_watchlist():
    conn = connection.get_connection()

    user_row = conn.execute("SELECT * FROM users WHERE id = 'default'").fetchone()
    assert user_row["cash_balance"] == 10000.0

    tickers = {
        row["ticker"] for row in conn.execute("SELECT ticker FROM watchlist").fetchall()
    }
    assert tickers == set(SEED_TICKERS)


def test_reinit_is_idempotent():
    conn = connection.get_connection()

    from app.db.schema import init_schema, seed_if_empty

    init_schema(conn)
    seed_if_empty(conn)
    init_schema(conn)
    seed_if_empty(conn)

    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    watchlist_count = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]

    assert user_count == 1
    assert watchlist_count == len(SEED_TICKERS)


def test_get_connection_returns_same_instance():
    first = connection.get_connection()
    second = connection.get_connection()

    assert first is second


def test_configure_switches_to_isolated_database(tmp_path):
    connection.get_connection()  # ensure the first db is initialized/seeded

    other_path = tmp_path / "other.db"
    connection.configure(other_path)
    conn = connection.get_connection()

    # Fresh db is independently seeded, not sharing state with the previous one.
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


def test_memory_database_persists_across_calls():
    connection.configure(":memory:")
    conn = connection.get_connection()

    conn.execute("INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES ('x', 'default', 'ZZZ', 'now')")
    conn.commit()

    again = connection.get_connection()
    row = again.execute("SELECT ticker FROM watchlist WHERE id = 'x'").fetchone()
    assert row["ticker"] == "ZZZ"
