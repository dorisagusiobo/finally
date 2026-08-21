"""API tests for POST /api/chat, using LLM_MOCK=true (no real API calls).

Mock heuristic under test lives in app/llm/mock.py — see its docstring.
"""

from __future__ import annotations

from app.db import list_recent_chat_messages


def test_chat_canned_response_has_no_actions(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post(
        "/api/chat", json={"message": "What do you think about my portfolio?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["actions"] == {"trades": [], "watchlist_changes": []}
    assert body["message"]
    assert body["portfolio"]["cash_balance"] == 10000.0


def test_chat_buy_trade_executes(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post("/api/chat", json={"message": "Buy 5 AAPL"})

    assert response.status_code == 200
    body = response.json()
    trade = body["actions"]["trades"][0]
    assert trade == {
        "ticker": "AAPL",
        "side": "buy",
        "quantity": 5,
        "status": "executed",
        "price": trade["price"],
    }
    assert trade["price"] > 0
    assert "Note:" not in body["message"]

    portfolio = body["portfolio"]
    assert portfolio["cash_balance"] < 10000.0
    assert any(p["ticker"] == "AAPL" for p in portfolio["positions"])


def test_chat_buy_trade_insufficient_cash_appends_note(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post("/api/chat", json={"message": "Buy 1000000 AAPL"})

    assert response.status_code == 200
    body = response.json()
    trade = body["actions"]["trades"][0]
    assert trade["status"] == "failed"
    assert "error" in trade
    assert "Note:" in body["message"]
    assert body["portfolio"]["cash_balance"] == 10000.0


def test_chat_sell_without_position_fails_with_note(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post("/api/chat", json={"message": "Sell 5 AAPL"})

    assert response.status_code == 200
    body = response.json()
    trade = body["actions"]["trades"][0]
    assert trade["status"] == "failed"
    assert "Note:" in body["message"]


def test_chat_persists_user_and_assistant_messages(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    client.post("/api/chat", json={"message": "Buy 5 AAPL"})

    messages = list_recent_chat_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Buy 5 AAPL"
    assert messages[0]["actions"] is None
    assert messages[1]["role"] == "assistant"
    assert messages[1]["actions"]["trades"][0]["ticker"] == "AAPL"


def test_chat_response_always_has_both_action_keys(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post("/api/chat", json={"message": "hello"})

    body = response.json()
    assert "trades" in body["actions"]
    assert "watchlist_changes" in body["actions"]
