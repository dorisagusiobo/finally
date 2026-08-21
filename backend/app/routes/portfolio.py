"""Portfolio and trade routes — thin wrappers over app.portfolio."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import list_snapshots
from app.portfolio import execute_trade, get_portfolio_state

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str


@router.get("")
async def get_portfolio(request: Request) -> dict:
    return get_portfolio_state(request.app.state.price_cache)


@router.post("/trade")
async def trade(request: Request, body: TradeRequest) -> JSONResponse:
    try:
        result = execute_trade(
            request.app.state.price_cache, body.ticker, body.side, body.quantity
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})

    return JSONResponse(
        content={"success": True, "trade": result["trade"], "portfolio": result["portfolio"]}
    )


@router.get("/history")
async def history() -> dict:
    return {"snapshots": list_snapshots()}
