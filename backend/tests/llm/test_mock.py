from __future__ import annotations

from app.llm.mock import mock_llm_response


def test_mock_buy_detected():
    result = mock_llm_response("Buy 10 AAPL please")
    assert result.trades[0].ticker == "AAPL"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 10


def test_mock_sell_detected():
    result = mock_llm_response("Sell 3 TSLA now")
    assert result.trades[0].ticker == "TSLA"
    assert result.trades[0].side == "sell"
    assert result.trades[0].quantity == 3


def test_mock_buy_default_quantity_is_one():
    result = mock_llm_response("Buy some GOOGL")
    assert result.trades[0].quantity == 1.0


def test_mock_no_ticker_returns_canned_response():
    result = mock_llm_response("What do you think about the market today?")
    assert result.trades is None
    assert result.watchlist_changes is None
    assert len(result.message) > 0


def test_mock_ignores_pronoun_tokens():
    result = mock_llm_response("I want to buy A share of something")
    assert result.trades is None


def test_mock_is_deterministic():
    a = mock_llm_response("Buy 10 AAPL")
    b = mock_llm_response("Buy 10 AAPL")
    assert a.model_dump() == b.model_dump()
