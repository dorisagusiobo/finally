"""Watchlist routes — thin wrappers over app.watchlist."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app import watchlist as watchlist_service

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistAddRequest(BaseModel):
    ticker: str


@router.get("")
async def get_watchlist(request: Request) -> dict:
    watchlist = watchlist_service.get_watchlist_with_prices(request.app.state.price_cache)
    return {"watchlist": watchlist}


@router.post("")
async def add_to_watchlist(request: Request, body: WatchlistAddRequest) -> dict:
    await watchlist_service.add_ticker(request.app.state.market_source, body.ticker)
    watchlist = watchlist_service.get_watchlist_with_prices(request.app.state.price_cache)
    return {"watchlist": watchlist}


@router.delete("/{ticker}")
async def remove_from_watchlist(request: Request, ticker: str) -> dict:
    await watchlist_service.remove_ticker(request.app.state.market_source, ticker)
    watchlist = watchlist_service.get_watchlist_with_prices(request.app.state.price_cache)
    return {"watchlist": watchlist}
