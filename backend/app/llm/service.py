"""Chat orchestration: prompt -> LLM -> auto-execute -> persist (PLAN.md §9).

Single completion, no second LLM pass (PLAN.md §13 #1): the LLM's own
`message` text is never rewritten. If any proposed action fails validation, a
short factual note is appended to it. The persisted/returned `actions` object
reflects actual outcomes, not the LLM's raw proposal (PLAN.md §13 #2).
"""

from __future__ import annotations

import os
from typing import Any

from app.db import DEFAULT_USER_ID, insert_chat_message, list_recent_chat_messages
from app.market import MarketDataSource, PriceCache
from app.portfolio import execute_trade, get_portfolio_state
from app.watchlist import add_ticker, get_watchlist_with_prices, remove_ticker

from .client import call_llm
from .mock import mock_llm_response
from .prompts import build_messages
from .schema import ChatCompletionResponse


def _is_mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "false").strip().lower() == "true"


async def _apply_trades(
    price_cache: PriceCache,
    completion: ChatCompletionResponse,
    user_id: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for proposal in completion.trades or []:
        action: dict[str, Any] = {
            "ticker": proposal.ticker,
            "side": proposal.side,
            "quantity": proposal.quantity,
        }
        try:
            result = execute_trade(
                price_cache, proposal.ticker, proposal.side, proposal.quantity, user_id
            )
            action["status"] = "executed"
            action["price"] = result["trade"]["price"]
        except ValueError as exc:
            action["status"] = "failed"
            action["error"] = str(exc)
        actions.append(action)
    return actions


async def _apply_watchlist_changes(
    market_source: MarketDataSource,
    completion: ChatCompletionResponse,
    user_id: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for change in completion.watchlist_changes or []:
        action: dict[str, Any] = {"ticker": change.ticker, "action": change.action}
        try:
            if change.action == "add":
                await add_ticker(market_source, change.ticker, user_id)
            elif change.action == "remove":
                await remove_ticker(market_source, change.ticker, user_id)
            else:
                raise ValueError(
                    f"Invalid watchlist action {change.action!r}: must be 'add' or 'remove'."
                )
            action["status"] = "executed"
        except ValueError as exc:
            action["status"] = "failed"
            action["error"] = str(exc)
        actions.append(action)
    return actions


def _append_failure_notes(
    message: str, trade_actions: list[dict[str, Any]], watchlist_actions: list[dict[str, Any]]
) -> str:
    notes = []
    for a in trade_actions:
        if a["status"] == "failed":
            notes.append(f"{a['ticker']} {a['side']} failed — {a['error']}")
    for a in watchlist_actions:
        if a["status"] == "failed":
            notes.append(f"{a['ticker']} watchlist {a['action']} failed — {a['error']}")
    if not notes:
        return message
    return message + "\n\nNote: " + "; ".join(notes) + "."


async def handle_chat_message(
    price_cache: PriceCache,
    market_source: MarketDataSource,
    user_message: str,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    portfolio = get_portfolio_state(price_cache, user_id)
    watchlist = get_watchlist_with_prices(price_cache, user_id)
    history = list_recent_chat_messages(user_id=user_id)

    if _is_mock_mode():
        completion = mock_llm_response(user_message)
    else:
        messages = build_messages(portfolio, watchlist, history, user_message)
        completion = call_llm(messages)

    trade_actions = await _apply_trades(price_cache, completion, user_id)
    watchlist_actions = await _apply_watchlist_changes(market_source, completion, user_id)

    final_message = _append_failure_notes(completion.message, trade_actions, watchlist_actions)
    actions = {"trades": trade_actions, "watchlist_changes": watchlist_actions}

    insert_chat_message(role="user", content=user_message, actions=None, user_id=user_id)
    insert_chat_message(role="assistant", content=final_message, actions=actions, user_id=user_id)

    return {
        "message": final_message,
        "actions": actions,
        "portfolio": get_portfolio_state(price_cache, user_id),
    }
