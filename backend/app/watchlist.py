"""Watchlist management, wired to both the database and the live price cache.

Non-route module — the LLM Engineer's chat flow (next wave) will call these
directly for AI-driven watchlist changes, same as the routes do.
"""

from __future__ import annotations

from typing import Any

from app.db import (
    DEFAULT_USER_ID,
    add_watchlist_ticker,
    get_position,
    list_watchlist,
    remove_watchlist_ticker,
)
from app.market import MarketDataSource, PriceCache


async def add_ticker(
    market_source: MarketDataSource, ticker: str, user_id: str = DEFAULT_USER_ID
) -> None:
    """Add a ticker to the watchlist and bring it live in the price cache. Idempotent."""
    add_watchlist_ticker(ticker, user_id)
    await market_source.add_ticker(ticker)


async def remove_ticker(
    market_source: MarketDataSource, ticker: str, user_id: str = DEFAULT_USER_ID
) -> None:
    """Remove a ticker from the watchlist. Idempotent.

    The ticker stays live in the price cache if the user still holds an open
    position in it — the cache must always cover watchlist union open positions.
    """
    remove_watchlist_ticker(ticker, user_id)
    if get_position(ticker, user_id) is None:
        await market_source.remove_ticker(ticker)


def get_watchlist_with_prices(
    price_cache: PriceCache, user_id: str = DEFAULT_USER_ID
) -> list[dict[str, Any]]:
    """The watchlist with latest price data from the cache.

    If a ticker has no cached price yet (startup race), price fields are None.
    """
    entries = []
    for ticker in list_watchlist(user_id):
        update = price_cache.get(ticker)
        if update is None:
            entries.append(
                {
                    "ticker": ticker,
                    "price": None,
                    "previous_price": None,
                    "change": None,
                    "change_percent": None,
                    "direction": None,
                }
            )
        else:
            entries.append(
                {
                    "ticker": ticker,
                    "price": update.price,
                    "previous_price": update.previous_price,
                    "change": update.change,
                    "change_percent": update.change_percent,
                    "direction": update.direction,
                }
            )
    return entries
