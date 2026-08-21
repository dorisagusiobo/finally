from __future__ import annotations


def test_get_portfolio_empty(client):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "cash_balance": 10000.0,
        "positions": [],
        "total_value": 10000.0,
        "total_unrealized_pnl": 0.0,
    }


def test_buy_trade_success(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    trade = body["trade"]
    assert trade["ticker"] == "AAPL"
    assert trade["side"] == "buy"
    assert trade["quantity"] == 10
    price = trade["price"]
    assert price > 0

    portfolio = body["portfolio"]
    assert portfolio["cash_balance"] == round(10000.0 - 10 * price, 2)
    assert len(portfolio["positions"]) == 1
    position = portfolio["positions"][0]
    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 10
    assert position["avg_cost"] == price


def test_buy_insufficient_cash(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1_000_000, "side": "buy"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "insufficient" in body["error"].lower() or "cash" in body["error"].lower()

    # No side effects on failure
    portfolio = client.get("/api/portfolio").json()
    assert portfolio["cash_balance"] == 10000.0
    assert portfolio["positions"] == []


def test_sell_without_position_fails(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "sell"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False


def test_sell_more_than_held_fails(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "buy"})

    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "sell"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"][0]["quantity"] == 5


def test_sell_partial_keeps_avg_cost(client):
    buy = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    ).json()
    buy_price = buy["trade"]["price"]

    sell = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 4, "side": "sell"}
    ).json()
    assert sell["success"] is True

    position = sell["portfolio"]["positions"][0]
    assert position["quantity"] == 6
    assert position["avg_cost"] == buy_price


def test_sell_to_zero_deletes_position(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "buy"})
    sell = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "sell"}
    ).json()

    assert sell["success"] is True
    assert sell["portfolio"]["positions"] == []


def test_weighted_average_cost_on_second_buy(client):
    buy1 = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    ).json()
    buy2 = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "buy"}
    ).json()

    price1 = buy1["trade"]["price"]
    price2 = buy2["trade"]["price"]
    expected_avg = (10 * price1 + 5 * price2) / 15

    position = buy2["portfolio"]["positions"][0]
    assert position["quantity"] == 15
    assert abs(position["avg_cost"] - expected_avg) < 0.01


def test_trade_records_snapshot(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})

    history = client.get("/api/portfolio/history").json()
    assert len(history["snapshots"]) >= 1
    assert "total_value" in history["snapshots"][-1]
    assert "recorded_at" in history["snapshots"][-1]


def test_portfolio_history_empty_initially(client):
    history = client.get("/api/portfolio/history").json()
    assert history == {"snapshots": []}
