"""LLM chat integration for FinAlly (PLAN.md §9).

Public API: `handle_chat_message`, the orchestration entry point the chat
route calls.
"""

from __future__ import annotations

from .service import handle_chat_message

__all__ = ["handle_chat_message"]
