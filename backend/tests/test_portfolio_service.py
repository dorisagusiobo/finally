"""Unit tests for app.portfolio, isolated from the API layer."""

from __future__ import annotations

import pytest

from app.db import connection
from app.market import PriceCache
from app.portfolio import execute_trade, get_portfolio_state


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    connection.configure(tmp_path / "test.db")
    yield
    connection.close()


@pytest.fixture
def price_cache():
    cache = PriceCache()
    cache.update("AAPL", 100.0)
    return cache


def test_get_portfolio_state_no_positions(price_cache):
    state = get_portfolio_state(price_cache)
    assert state == {
        "cash_balance": 10000.0,
        "positions": [],
        "total_value": 10000.0,
        "total_unrealized_pnl": 0.0,
    }


def test_execute_trade_buy_updates_cash_and_position(price_cache):
    result = execute_trade(price_cache, "AAPL", "buy", 10)
    assert result["trade"]["price"] == 100.0
    assert result["portfolio"]["cash_balance"] == 9000.0
    assert result["portfolio"]["positions"][0]["quantity"] == 10
    assert result["portfolio"]["positions"][0]["avg_cost"] == 100.0


def test_execute_trade_buy_insufficient_cash_raises(price_cache):
    with pytest.raises(ValueError, match="[Ii]nsufficient"):
        execute_trade(price_cache, "AAPL", "buy", 1000)


def test_execute_trade_sell_more_than_held_raises(price_cache):
    execute_trade(price_cache, "AAPL", "buy", 5)
    with pytest.raises(ValueError):
        execute_trade(price_cache, "AAPL", "sell", 10)


def test_execute_trade_sell_to_zero_deletes_position(price_cache):
    execute_trade(price_cache, "AAPL", "buy", 5)
    result = execute_trade(price_cache, "AAPL", "sell", 5)
    assert result["portfolio"]["positions"] == []
    assert result["portfolio"]["cash_balance"] == 10000.0


def test_execute_trade_unknown_ticker_raises():
    empty_cache = PriceCache()
    with pytest.raises(ValueError, match="[Nn]o current price"):
        execute_trade(empty_cache, "ZZZZ", "buy", 1)


def test_execute_trade_invalid_side_raises(price_cache):
    with pytest.raises(ValueError):
        execute_trade(price_cache, "AAPL", "hold", 1)


def test_execute_trade_weighted_avg_cost(price_cache):
    execute_trade(price_cache, "AAPL", "buy", 10)  # @ 100.0
    price_cache.update("AAPL", 200.0)
    result = execute_trade(price_cache, "AAPL", "buy", 10)  # @ 200.0

    position = result["portfolio"]["positions"][0]
    assert position["quantity"] == 20
    assert position["avg_cost"] == 150.0
