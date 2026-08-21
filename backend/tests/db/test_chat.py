"""Tests for chat message repository functions."""

from __future__ import annotations

from app.db import insert_chat_message, list_recent_chat_messages


def test_insert_chat_message_without_actions():
    message = insert_chat_message("user", "What's my portfolio worth?")

    assert message["role"] == "user"
    assert message["content"] == "What's my portfolio worth?"
    assert message["actions"] is None


def test_insert_chat_message_with_actions_round_trips_as_json():
    actions = {"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}]}

    message = insert_chat_message("assistant", "Bought 10 AAPL for you.", actions=actions)

    assert message["actions"] == actions


def test_list_recent_chat_messages_chronological_order():
    insert_chat_message("user", "first")
    insert_chat_message("assistant", "second")
    insert_chat_message("user", "third")

    contents = [m["content"] for m in list_recent_chat_messages()]
    assert contents == ["first", "second", "third"]


def test_list_recent_chat_messages_respects_limit():
    for i in range(5):
        insert_chat_message("user", f"message {i}")

    recent = list_recent_chat_messages(limit=2)

    assert [m["content"] for m in recent] == ["message 3", "message 4"]


def test_list_recent_chat_messages_parses_stored_actions():
    insert_chat_message("assistant", "done", actions=[{"ticker": "AAPL", "action": "add"}])

    [message] = list_recent_chat_messages()

    assert message["actions"] == [{"ticker": "AAPL", "action": "add"}]
