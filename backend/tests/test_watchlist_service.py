"""Unit tests for app.watchlist, isolated from the API layer."""

from __future__ import annotations

import pytest

from app.db import connection, upsert_position
from app.market import PriceCache
from app.market.simulator import SimulatorDataSource
from app.watchlist import add_ticker, get_watchlist_with_prices, remove_ticker


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    connection.configure(tmp_path / "test.db")
    yield
    connection.close()


@pytest.fixture
async def source():
    cache = PriceCache()
    src = SimulatorDataSource(price_cache=cache)
    await src.start(["AAPL"])
    yield src, cache
    await src.stop()


async def test_add_ticker_adds_to_db_and_cache(source):
    src, cache = source
    await add_ticker(src, "PYPL")
    assert cache.get("PYPL") is not None
    assert "PYPL" in src.get_tickers()


async def test_remove_ticker_removes_from_db_and_cache(source):
    src, cache = source
    await add_ticker(src, "PYPL")
    await remove_ticker(src, "PYPL")
    assert cache.get("PYPL") is None
    assert "PYPL" not in src.get_tickers()


async def test_remove_ticker_keeps_cache_entry_if_position_held(source):
    src, cache = source
    upsert_position("AAPL", 10, 100.0)  # open position on AAPL

    await remove_ticker(src, "AAPL")

    # Removed from the watchlist itself...
    tickers = {entry["ticker"] for entry in get_watchlist_with_prices(cache)}
    assert "AAPL" not in tickers
    # ...but still live in the price cache and simulator, since a position is open.
    assert cache.get("AAPL") is not None
    assert "AAPL" in src.get_tickers()


async def test_get_watchlist_with_prices_missing_price_is_none():
    cache = PriceCache()
    from app.db import add_watchlist_ticker

    add_watchlist_ticker("ZZZZ")

    entries = get_watchlist_with_prices(cache)
    zzzz = next(entry for entry in entries if entry["ticker"] == "ZZZZ")
    assert zzzz == {
        "ticker": "ZZZZ",
        "price": None,
        "previous_price": None,
        "change": None,
        "change_percent": None,
        "direction": None,
    }
