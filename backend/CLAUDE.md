# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Market Data API

The market data subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, MarketDataSource, create_market_data_source
```

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus properties `change`, `change_percent`, `direction` ("up"/"down"/"flat"), and `to_dict()` for JSON serialization.

- **`PriceCache`** — Thread-safe in-memory store. Key methods:
  - `update(ticker, price, timestamp=None) -> PriceUpdate`
  - `get(ticker) -> PriceUpdate | None`
  - `get_price(ticker) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(ticker)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`MarketDataSource`** — Abstract interface implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` -> `add_ticker()` / `remove_ticker()` -> `stop()`.

- **`create_market_data_source(cache)`** — Factory. Returns `MassiveDataSource` if `MASSIVE_API_KEY` is set, otherwise `SimulatorDataSource`.

### SSE Streaming

```python
from app.market import create_stream_router

router = create_stream_router(price_cache)  # Returns FastAPI APIRouter
# Endpoint: GET /api/stream/prices (text/event-stream)
```

### Seed Data

Default tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Seed prices and per-ticker volatility/drift params are in `app/market/seed_prices.py`.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Demo

```bash
uv run market_data_demo.py   # Live terminal dashboard with simulated prices
```

## Database API

The database layer lives in `app/db/`. It wraps a single shared SQLite connection
to `db/finally.db` (project root), created and seeded lazily on first use — no
separate migration step. Import repository functions directly:

```python
from app.db import (
    get_user, update_cash_balance,
    list_watchlist, add_watchlist_ticker, remove_watchlist_ticker,
    get_position, list_positions, upsert_position, delete_position,
    insert_trade,
    insert_snapshot, list_snapshots,
    insert_chat_message, list_recent_chat_messages,
)
```

Every function takes `user_id: str = "default"` as its last parameter (single-user
app; hardcoded per PLAN.md §7). All timestamps are ISO 8601 UTC strings, all IDs
are UUID4 strings.

- **Users** — `get_user(user_id="default") -> dict | None`; `update_cash_balance(new_balance, user_id="default") -> dict` (raises `LookupError` if the user doesn't exist).
- **Watchlist** — `list_watchlist(user_id="default") -> list[str]`; `add_watchlist_ticker(ticker, user_id="default")` (no-op if already present); `remove_watchlist_ticker(ticker, user_id="default")` (no-op if absent).
- **Positions** — `get_position(ticker, user_id="default") -> dict | None`; `list_positions(user_id="default") -> list[dict]` (ordered by ticker); `upsert_position(ticker, quantity, avg_cost, user_id="default") -> dict` (creates or updates in place — same row, not a duplicate); `delete_position(ticker, user_id="default")` (use when a sell fully closes a position; no-op if absent).
- **Trades** — `insert_trade(ticker, side, quantity, price, user_id="default") -> dict`. `side` must be `"buy"` or `"sell"` — anything else raises `sqlite3.IntegrityError` (CHECK constraint). Append-only log.
- **Portfolio snapshots** — `insert_snapshot(total_value, user_id="default") -> dict`; `list_snapshots(user_id="default", limit=None) -> list[dict]`, chronological order; with `limit`, returns the most recent N snapshots (still chronological) — what the P&L chart wants.
- **Chat messages** — `insert_chat_message(role, content, actions=None, user_id="default") -> dict` (`actions` is any JSON-serializable trades/watchlist-changes payload, stored as JSON and returned as the original Python object, not a string); `list_recent_chat_messages(user_id="default", limit=20) -> list[dict]`, chronological order (the 20-message window is the resolved default from PLAN.md §13 #3 for building LLM conversation history).

### Testing against an isolated database

Don't let tests touch the real `db/finally.db`. Point the module at a temp file
(or `:memory:`) before each test:

```python
from app.db import connection

connection.configure(tmp_path / "test.db")  # or ":memory:"
# ... run test, using the app.db functions normally ...
connection.close()
```

`backend/tests/db/conftest.py` already does this via an autouse fixture, so tests
under `backend/tests/db/` get isolation for free. Note `configure()` opens a
*new* connection under the hood — if you use `":memory:"` directly rather than
through that fixture, calling `configure(":memory:")` more than once in the same
test discards the previous in-memory database.

## Running Database Tests

```bash
uv run --extra dev pytest tests/db -v              # Database layer only
uv run --extra dev ruff check app/db tests/db       # Lint
```

## Chat / LLM API

`POST /api/chat` (`app/routes/chat.py`) is the only route; orchestration lives in
`app/llm/` (`handle_chat_message` is the entry point). Request: `{"message": "..."}`.
Response:

```json
{
  "message": "...",
  "actions": {
    "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10, "status": "executed", "price": 191.23}],
    "watchlist_changes": [{"ticker": "PYPL", "action": "add", "status": "executed"}]
  },
  "portfolio": { /* same shape as GET /api/portfolio */ }
}
```

`actions.trades`/`actions.watchlist_changes` are always present (possibly empty)
and reflect *actual* outcomes, not the LLM's raw proposal — a failed action has
`"status": "failed"` and an `"error"` string instead of `"price"`. On any
failure, a short note is appended to `message` (the LLM's own text is never
rewritten), e.g. `"\n\nNote: AAPL buy failed — insufficient cash."`. Both the
user message and the final assistant message (with any notes) are persisted via
`insert_chat_message`; the assistant row's `actions` column holds the same
`actions` object returned in the response.

The real call goes through LiteLLM -> OpenRouter -> Cerebras
(`openrouter/openai/gpt-oss-120b`, per the `cerebras` skill) with structured
output validated against `app.llm.schema.ChatCompletionResponse`. Malformed/
unparseable model output falls back to a safe canned response instead of
crashing the route (`app/llm/client.py`).

### LLM_MOCK

When the `LLM_MOCK` env var is `"true"`, `handle_chat_message` skips the real
LLM call and uses `app.llm.mock.mock_llm_response` instead — deterministic, no
network call, no API cost. Heuristic: scan the message for an all-caps 1-5
letter word (a "ticker"), ignoring the tokens `I` and `A`. If found and the
message contains `"buy"` (case-insensitive), propose a buy of that ticker for
the first number found in the message (default quantity `1`). Same for
`"sell"`. Otherwise, return a canned analytical message with no trades or
watchlist changes. Proposed trades still go through the normal
`execute_trade` validation — this only fakes the model's proposal, not the
auto-execution/failure-note logic.
