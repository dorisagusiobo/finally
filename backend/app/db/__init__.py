"""Database layer for FinAlly — SQLite persistence for users, watchlist,
positions, trades, portfolio snapshots, and chat history.

The database is lazily initialized (schema created + seeded) on first use of
`get_connection()`, which every repository function below calls internally.
"""

from __future__ import annotations

from .connection import close, configure, get_connection
from .repository import (
    DEFAULT_USER_ID,
    add_watchlist_ticker,
    delete_position,
    get_position,
    get_user,
    insert_chat_message,
    insert_snapshot,
    insert_trade,
    list_positions,
    list_recent_chat_messages,
    list_snapshots,
    list_watchlist,
    remove_watchlist_ticker,
    update_cash_balance,
    upsert_position,
)

__all__ = [
    "DEFAULT_USER_ID",
    "add_watchlist_ticker",
    "close",
    "configure",
    "delete_position",
    "get_connection",
    "get_position",
    "get_user",
    "insert_chat_message",
    "insert_snapshot",
    "insert_trade",
    "list_positions",
    "list_recent_chat_messages",
    "list_snapshots",
    "list_watchlist",
    "remove_watchlist_ticker",
    "update_cash_balance",
    "upsert_position",
]
