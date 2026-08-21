"""Tests for watchlist repository functions."""

from __future__ import annotations

from app.db import add_watchlist_ticker, list_watchlist, remove_watchlist_ticker
from app.db.schema import SEED_TICKERS


def test_list_watchlist_returns_seed_tickers():
    tickers = list_watchlist()

    assert set(tickers) == set(SEED_TICKERS)
    assert len(tickers) == len(SEED_TICKERS)


def test_add_watchlist_ticker():
    add_watchlist_ticker("PYPL")

    assert "PYPL" in list_watchlist()


def test_add_watchlist_ticker_duplicate_is_noop():
    add_watchlist_ticker("PYPL")
    add_watchlist_ticker("PYPL")

    assert list_watchlist().count("PYPL") == 1


def test_remove_watchlist_ticker():
    remove_watchlist_ticker("AAPL")

    assert "AAPL" not in list_watchlist()


def test_remove_watchlist_ticker_not_present_does_not_raise():
    remove_watchlist_ticker("NOPE")  # should not raise

    assert set(list_watchlist()) == set(SEED_TICKERS)


def test_watchlist_scoped_by_user():
    add_watchlist_ticker("PYPL", user_id="other")

    assert "PYPL" not in list_watchlist()
    assert list_watchlist(user_id="other") == ["PYPL"]
