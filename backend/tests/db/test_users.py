"""Tests for user repository functions."""

from __future__ import annotations

import pytest

from app.db import get_user, update_cash_balance


def test_get_user_returns_seeded_default():
    user = get_user()

    assert user["id"] == "default"
    assert user["cash_balance"] == 10000.0
    assert user["created_at"]


def test_get_user_unknown_returns_none():
    assert get_user("nobody") is None


def test_update_cash_balance_updates_and_returns_user():
    updated = update_cash_balance(12345.67)

    assert updated["cash_balance"] == 12345.67
    assert get_user()["cash_balance"] == 12345.67


def test_update_cash_balance_unknown_user_raises():
    with pytest.raises(LookupError):
        update_cash_balance(100.0, user_id="nobody")
