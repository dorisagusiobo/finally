"""Real LLM call via LiteLLM -> OpenRouter -> Cerebras (per the `cerebras` skill)."""

from __future__ import annotations

import logging

from litellm import completion

from .schema import ChatCompletionResponse

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

_FALLBACK_MESSAGE = "Sorry, I had trouble processing that request. Could you rephrase it?"


def call_llm(messages: list[dict[str, str]]) -> ChatCompletionResponse:
    """Call the model, requesting structured output matching ChatCompletionResponse.

    If the model returns malformed/unparseable JSON, falls back to a safe
    empty-actions response rather than raising — a bad completion must never
    crash the /api/chat route.
    """
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatCompletionResponse,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    raw = response.choices[0].message.content
    try:
        return ChatCompletionResponse.model_validate_json(raw)
    except (ValueError, TypeError):
        logger.exception("Failed to parse LLM structured output: %r", raw)
        return ChatCompletionResponse(message=_FALLBACK_MESSAGE)
