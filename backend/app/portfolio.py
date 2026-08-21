"""Portfolio valuation and trade execution.

Reusable, non-route functions: the trade routes call these directly, and the
LLM Engineer's chat flow (next wave) will call `execute_trade` for
auto-executed trades rather than duplicating validation logic.
"""

from __future__ import annotations

from typing import Any

from app.db import (
    DEFAULT_USER_ID,
    delete_position,
    get_position,
    get_user,
    insert_snapshot,
    insert_trade,
    list_positions,
    update_cash_balance,
    upsert_position,
)
from app.market import PriceCache

VALID_SIDES = ("buy", "sell")


def get_portfolio_state(price_cache: PriceCache, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    """Current cash balance, positions (with live valuation), and totals.

    Matches the GET /api/portfolio response shape exactly.
    """
    user = get_user(user_id)
    cash_balance = user["cash_balance"] if user else 0.0

    positions = []
    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    for pos in list_positions(user_id):
        ticker = pos["ticker"]
        quantity = pos["quantity"]
        avg_cost = pos["avg_cost"]
        current_price = price_cache.get_price(ticker)
        if current_price is None:
            current_price = avg_cost  # No live price yet — fall back to cost basis

        market_value = current_price * quantity
        unrealized_pnl = (current_price - avg_cost) * quantity
        unrealized_pnl_percent = (current_price - avg_cost) / avg_cost * 100 if avg_cost else 0.0

        positions.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_percent": round(unrealized_pnl_percent, 2),
            }
        )
        total_market_value += market_value
        total_unrealized_pnl += unrealized_pnl

    return {
        "cash_balance": round(cash_balance, 2),
        "positions": positions,
        "total_value": round(cash_balance + total_market_value, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
    }


def execute_trade(
    price_cache: PriceCache,
    ticker: str,
    side: str,
    quantity: float,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Validate and execute a market order at the current cached price.

    Returns {"trade": <inserted trade row>, "portfolio": <get_portfolio_state shape>}.
    Raises ValueError with a human-readable message on any validation failure
    (insufficient cash, overselling, unknown ticker, bad side/quantity) —
    callers turn this into a 400 response.
    """
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side {side!r}: must be 'buy' or 'sell'.")
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

    price = price_cache.get_price(ticker)
    if price is None:
        raise ValueError(f"No current price available for {ticker!r}.")

    user = get_user(user_id)
    if user is None:
        raise ValueError(f"No user with id {user_id!r}.")
    cash_balance = user["cash_balance"]

    position = get_position(ticker, user_id)
    amount = round(quantity * price, 2)

    if side == "buy":
        if amount > cash_balance:
            raise ValueError(
                f"Insufficient cash: buying {quantity} {ticker} costs ${amount:.2f}, "
                f"only ${cash_balance:.2f} available."
            )
        if position:
            new_quantity = position["quantity"] + quantity
            new_avg_cost = (
                position["quantity"] * position["avg_cost"] + quantity * price
            ) / new_quantity
            upsert_position(ticker, new_quantity, new_avg_cost, user_id)
        else:
            upsert_position(ticker, quantity, price, user_id)
        update_cash_balance(round(cash_balance - amount, 2), user_id)
    else:
        held = position["quantity"] if position else 0.0
        if quantity > held:
            raise ValueError(
                f"Cannot sell {quantity} shares of {ticker}: only {held} held."
            )
        remaining = held - quantity
        if remaining <= 0:
            delete_position(ticker, user_id)
        else:
            upsert_position(ticker, remaining, position["avg_cost"], user_id)
        update_cash_balance(round(cash_balance + amount, 2), user_id)

    trade = insert_trade(ticker, side, quantity, price, user_id)
    portfolio = get_portfolio_state(price_cache, user_id)
    insert_snapshot(portfolio["total_value"], user_id)

    return {"trade": trade, "portfolio": portfolio}
