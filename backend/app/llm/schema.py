"""Structured-output schema for the LLM chat completion (PLAN.md §9)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TradeProposal(BaseModel):
    ticker: str
    side: str
    quantity: float


class WatchlistChangeProposal(BaseModel):
    ticker: str
    action: str


class ChatCompletionResponse(BaseModel):
    """What the LLM returns for a single chat turn.

    `trades`/`watchlist_changes` are nullable — the model may omit them or
    send an explicit `null` for "nothing to do here". Callers normalize a
    `None` to `[]` (see `service.handle_chat_message`).
    """

    message: str
    trades: list[TradeProposal] | None = Field(default=None)
    watchlist_changes: list[WatchlistChangeProposal] | None = Field(default=None)
