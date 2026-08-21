"""FastAPI application entrypoint for FinAlly.

Single worker process only (PLAN.md §13 #9) — the in-memory PriceCache and the
market data source's background task both assume one process, and SQLite
doesn't handle multiple concurrent writers well.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import insert_snapshot, list_positions, list_watchlist
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.portfolio import get_portfolio_state
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.portfolio import router as portfolio_router
from app.routes.watchlist import router as watchlist_router

logger = logging.getLogger(__name__)

SNAPSHOT_INTERVAL_SECONDS = 30
STATIC_DIR = Path(__file__).parent / "static"

# Created at import time (not inside lifespan) because create_stream_router()
# needs a reference to the same cache instance at router-registration time,
# which happens before the app starts. Constructing it is just an empty dict —
# no background work begins until market_source.start() runs in lifespan.
price_cache = PriceCache()


async def _snapshot_loop() -> None:
    """Record a portfolio value snapshot every 30s, for the P&L chart."""
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
        try:
            portfolio = get_portfolio_state(price_cache)
            insert_snapshot(portfolio["total_value"])
        except Exception:
            logger.exception("Portfolio snapshot failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    market_source = create_market_data_source(price_cache)
    tickers = set(list_watchlist()) | {p["ticker"] for p in list_positions()}
    await market_source.start(list(tickers))

    app.state.price_cache = price_cache
    app.state.market_source = market_source

    snapshot_task = asyncio.create_task(_snapshot_loop(), name="portfolio-snapshot-loop")

    yield

    snapshot_task.cancel()
    try:
        await snapshot_task
    except asyncio.CancelledError:
        pass
    await market_source.stop()


app = FastAPI(title="FinAlly", lifespan=lifespan)

# Registered before the static mount so /api/* isn't shadowed by the catch-all.
app.include_router(health_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(chat_router)
app.include_router(create_stream_router(price_cache))

if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
