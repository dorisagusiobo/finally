"""Chat route — thin wrapper over app.llm.handle_chat_message."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.llm import handle_chat_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(request: Request, body: ChatRequest) -> dict:
    return await handle_chat_message(
        request.app.state.price_cache,
        request.app.state.market_source,
        body.message,
    )
