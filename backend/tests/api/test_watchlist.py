from __future__ import annotations

from app.db.schema import SEED_TICKERS


def test_get_watchlist_default(client):
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    tickers = {entry["ticker"] for entry in body["watchlist"]}
    assert tickers == set(SEED_TICKERS)
    for entry in body["watchlist"]:
        assert entry["price"] is not None
        assert entry["direction"] in ("up", "down", "flat")


def test_add_ticker(client):
    response = client.post("/api/watchlist", json={"ticker": "PYPL"})
    assert response.status_code == 200
    body = response.json()
    tickers = {entry["ticker"] for entry in body["watchlist"]}
    assert "PYPL" in tickers

    pypl = next(entry for entry in body["watchlist"] if entry["ticker"] == "PYPL")
    assert pypl["price"] is not None


def test_add_ticker_idempotent(client):
    client.post("/api/watchlist", json={"ticker": "PYPL"})
    response = client.post("/api/watchlist", json={"ticker": "PYPL"})
    assert response.status_code == 200
    tickers = [entry["ticker"] for entry in response.json()["watchlist"]]
    assert tickers.count("PYPL") == 1


def test_remove_ticker(client):
    client.post("/api/watchlist", json={"ticker": "PYPL"})
    response = client.delete("/api/watchlist/PYPL")
    assert response.status_code == 200
    tickers = {entry["ticker"] for entry in response.json()["watchlist"]}
    assert "PYPL" not in tickers


def test_remove_ticker_not_present_is_noop(client):
    response = client.delete("/api/watchlist/NOTREAL")
    assert response.status_code == 200
    tickers = {entry["ticker"] for entry in response.json()["watchlist"]}
    assert tickers == set(SEED_TICKERS)
