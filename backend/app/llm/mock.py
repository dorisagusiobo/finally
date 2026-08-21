"""Deterministic mock LLM responses for LLM_MOCK=true (PLAN.md §9).

Heuristic (documented here and in backend/CLAUDE.md for the Integration
Tester): scan the message for an all-caps 1-5 letter word (excluding "I" and
"A", which read as English words rather than tickers) to use as a ticker. If
one is found and the message contains "buy" (case-insensitive), propose a buy
of that ticker at the first number found in the message (default quantity 1).
Same for "sell" -> a sell proposal. Otherwise, return a canned analytical
message with no trades or watchlist changes. No LLM call, no randomness.
"""

from __future__ import annotations

import re

from .schema import ChatCompletionResponse, TradeProposal

_TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")
_QUANTITY_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")
_IGNORED_TOKENS = {"I", "A"}

_CANNED_MESSAGE = (
    "Your portfolio looks steady right now. Let me know if you'd like a "
    "deeper look at any position, or if you want to place a trade."
)


def _extract_ticker(message: str) -> str | None:
    for match in _TICKER_RE.finditer(message):
        token = match.group(0)
        if token not in _IGNORED_TOKENS:
            return token
    return None


def _extract_quantity(message: str) -> float:
    match = _QUANTITY_RE.search(message)
    return float(match.group(1)) if match else 1.0


def mock_llm_response(message: str) -> ChatCompletionResponse:
    lowered = message.lower()
    ticker = _extract_ticker(message)

    if ticker and "buy" in lowered:
        quantity = _extract_quantity(message)
        return ChatCompletionResponse(
            message=f"Buying {quantity:g} shares of {ticker}.",
            trades=[TradeProposal(ticker=ticker, side="buy", quantity=quantity)],
        )
    if ticker and "sell" in lowered:
        quantity = _extract_quantity(message)
        return ChatCompletionResponse(
            message=f"Selling {quantity:g} shares of {ticker}.",
            trades=[TradeProposal(ticker=ticker, side="sell", quantity=quantity)],
        )

    return ChatCompletionResponse(message=_CANNED_MESSAGE)
