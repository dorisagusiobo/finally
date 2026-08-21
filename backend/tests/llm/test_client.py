"""Structured-output parsing tests for app.llm.client.call_llm.

These stub out litellm.completion entirely — no network calls, no API key
needed. Covers: valid full schema, schema with missing optional fields, and
malformed/garbage model output (must fall back gracefully, not raise).
"""

from __future__ import annotations

from app.llm.client import call_llm
from app.llm.schema import ChatCompletionResponse


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


def test_call_llm_parses_full_valid_response(monkeypatch):
    content = (
        '{"message": "Bought it.", '
        '"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 5}], '
        '"watchlist_changes": [{"ticker": "PYPL", "action": "add"}]}'
    )
    monkeypatch.setattr("app.llm.client.completion", lambda **kwargs: _FakeResponse(content))

    result = call_llm([{"role": "user", "content": "hi"}])

    assert isinstance(result, ChatCompletionResponse)
    assert result.message == "Bought it."
    assert result.trades[0].ticker == "AAPL"
    assert result.watchlist_changes[0].ticker == "PYPL"


def test_call_llm_missing_optional_fields_default_to_none(monkeypatch):
    content = '{"message": "All good, no changes needed."}'
    monkeypatch.setattr("app.llm.client.completion", lambda **kwargs: _FakeResponse(content))

    result = call_llm([{"role": "user", "content": "hi"}])

    assert result.message == "All good, no changes needed."
    assert result.trades is None
    assert result.watchlist_changes is None


def test_call_llm_explicit_null_arrays(monkeypatch):
    content = '{"message": "Nothing to do.", "trades": null, "watchlist_changes": null}'
    monkeypatch.setattr("app.llm.client.completion", lambda **kwargs: _FakeResponse(content))

    result = call_llm([{"role": "user", "content": "hi"}])

    assert result.trades is None
    assert result.watchlist_changes is None


def test_call_llm_malformed_json_falls_back_without_raising(monkeypatch):
    monkeypatch.setattr("app.llm.client.completion", lambda **kwargs: _FakeResponse("not json at all"))

    result = call_llm([{"role": "user", "content": "hi"}])

    assert isinstance(result, ChatCompletionResponse)
    assert result.trades is None
    assert result.watchlist_changes is None
    assert result.message
