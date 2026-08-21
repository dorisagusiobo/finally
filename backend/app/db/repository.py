"""Repository functions — the public data-access API for the FinAlly database.

Every function operates on the shared connection from `connection.py` and the
hardcoded single user ("default") unless a different `user_id` is passed. Each
call commits its own writes immediately (no cross-call transactions), which is
fine for a single-writer, single-user app.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .connection import get_connection

DEFAULT_USER_ID = "default"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


# --- users -------------------------------------------------------------------


def get_user(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
    """Fetch a user's profile (id, cash_balance, created_at), or None if unknown."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_cash_balance(new_balance: float, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    """Set a user's cash balance. Raises LookupError if the user doesn't exist."""
    conn = get_connection()
    with conn:
        cursor = conn.execute(
            "UPDATE users SET cash_balance = ? WHERE id = ?", (new_balance, user_id)
        )
    if cursor.rowcount == 0:
        raise LookupError(f"No user with id {user_id!r}")
    return get_user(user_id)  # type: ignore[return-value]


# --- watchlist -----------------------------------------------------------------


def list_watchlist(user_id: str = DEFAULT_USER_ID) -> list[str]:
    """Tickers on the user's watchlist, ordered by when they were added."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at", (user_id,)
    ).fetchall()
    return [row["ticker"] for row in rows]


def add_watchlist_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> None:
    """Add a ticker to the watchlist. No-op if already present."""
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, ticker, _now()),
        )


def remove_watchlist_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> None:
    """Remove a ticker from the watchlist. No-op if not present."""
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker))


# --- positions -----------------------------------------------------------------


def get_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
    """Fetch a single position, or None if the user holds no shares of it."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_positions(user_id: str = DEFAULT_USER_ID) -> list[dict[str, Any]]:
    """All open positions for the user, ordered by ticker."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM positions WHERE user_id = ? ORDER BY ticker", (user_id,)
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def upsert_position(
    ticker: str, quantity: float, avg_cost: float, user_id: str = DEFAULT_USER_ID
) -> dict[str, Any]:
    """Create or update a position. An existing row (UNIQUE(user_id, ticker)) is updated in place."""
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, ticker) DO UPDATE SET
                quantity = excluded.quantity,
                avg_cost = excluded.avg_cost,
                updated_at = excluded.updated_at
            """,
            (str(uuid.uuid4()), user_id, ticker, quantity, avg_cost, _now()),
        )
    return get_position(ticker, user_id)  # type: ignore[return-value]


def delete_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> None:
    """Remove a position (e.g. a sell that fully closes it). No-op if not present."""
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker))


# --- trades ----------------------------------------------------------------------


def insert_trade(
    ticker: str, side: str, quantity: float, price: float, user_id: str = DEFAULT_USER_ID
) -> dict[str, Any]:
    """Append a trade to the (append-only) trade log.

    `side` must be 'buy' or 'sell' — enforced by a CHECK constraint, which raises
    `sqlite3.IntegrityError` for anything else.
    """
    conn = get_connection()
    trade_id = str(uuid.uuid4())
    executed_at = _now()
    with conn:
        conn.execute(
            """
            INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trade_id, user_id, ticker, side, quantity, price, executed_at),
        )
    return {
        "id": trade_id,
        "user_id": user_id,
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": price,
        "executed_at": executed_at,
    }


# --- portfolio snapshots -------------------------------------------------------------


def insert_snapshot(total_value: float, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    """Record a portfolio value snapshot (for the P&L chart)."""
    conn = get_connection()
    snapshot_id = str(uuid.uuid4())
    recorded_at = _now()
    with conn:
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (snapshot_id, user_id, total_value, recorded_at),
        )
    return {
        "id": snapshot_id,
        "user_id": user_id,
        "total_value": total_value,
        "recorded_at": recorded_at,
    }


def list_snapshots(
    user_id: str = DEFAULT_USER_ID, limit: int | None = None
) -> list[dict[str, Any]]:
    """Portfolio value snapshots in chronological order (oldest first).

    With `limit`, returns only the most recent `limit` snapshots (still in
    chronological order), which is what a P&L chart wants.
    """
    conn = get_connection()
    if limit is None:
        rows = conn.execute(
            "SELECT * FROM portfolio_snapshots WHERE user_id = ? ORDER BY recorded_at",
            (user_id,),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]

    rows = conn.execute(
        """
        SELECT * FROM (
            SELECT * FROM portfolio_snapshots WHERE user_id = ?
            ORDER BY recorded_at DESC LIMIT ?
        )
        ORDER BY recorded_at
        """,
        (user_id, limit),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


# --- chat messages -----------------------------------------------------------------


def _row_to_chat_message(row: sqlite3.Row) -> dict[str, Any]:
    data = _row_to_dict(row)
    data["actions"] = json.loads(data["actions"]) if data["actions"] is not None else None
    return data


def insert_chat_message(
    role: str,
    content: str,
    actions: list[Any] | dict[str, Any] | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Store a chat message. `actions` (trades/watchlist changes) is stored as JSON."""
    conn = get_connection()
    message_id = str(uuid.uuid4())
    created_at = _now()
    actions_json = json.dumps(actions) if actions is not None else None
    with conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, user_id, role, content, actions_json, created_at),
        )
    return {
        "id": message_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "actions": actions,
        "created_at": created_at,
    }


def list_recent_chat_messages(
    user_id: str = DEFAULT_USER_ID, limit: int = 20
) -> list[dict[str, Any]]:
    """The most recent `limit` chat messages, in chronological order (oldest first)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM (
            SELECT * FROM chat_messages WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        )
        ORDER BY created_at
        """,
        (user_id, limit),
    ).fetchall()
    return [_row_to_chat_message(row) for row in rows]
