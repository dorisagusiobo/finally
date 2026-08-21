"""Connection management for the FinAlly SQLite database.

A single connection is reused for the lifetime of the process — this is a
single-worker asyncio app (per PLAN.md §13), so there's no need for connection
pooling or multi-process locking. The database file and schema are created
lazily on first use.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from .schema import init_schema, seed_if_empty

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = str(_PROJECT_ROOT / "db" / "finally.db")

_db_path: str = os.environ.get("FINALLY_DB_PATH", _DEFAULT_DB_PATH)
_conn: sqlite3.Connection | None = None


def configure(db_path: str | Path) -> None:
    """Point the module at a different database file (or ``:memory:``).

    Closes any existing connection so the next call to `get_connection` opens
    a fresh one at the new path. Intended for tests; production code should
    rely on the default path (overridable via the `FINALLY_DB_PATH` env var).
    """
    global _db_path
    close()
    _db_path = str(db_path)


def get_connection() -> sqlite3.Connection:
    """Return the shared connection, creating and initializing it on first use."""
    global _conn
    if _conn is None:
        if _db_path != ":memory:":
            Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(_db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        seed_if_empty(conn)
        _conn = conn
    return _conn


def close() -> None:
    """Close the shared connection, if open. Safe to call when already closed."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
