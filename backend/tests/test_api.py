import os
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["RATE_LIMIT_MAX"] = "1000"
os.environ["RATE_LIMIT_WINDOW"] = "1"

from app.main import app

client = TestClient(app)


def _make_mock_stock(info_overrides=None):
    info = {
        "shortName": "Apple Inc.",
        "longName": "Apple Inc.",
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "revenueGrowth": 0.15,
        "priceToBook": 45.0,
        "marketCap": 3000000000000,
        "currentPrice": 180.0,
    }
    if info_overrides:
        info.update(info_overrides)

    hist = pd.DataFrame({
        "Date": pd.date_range(end="2024-01-01", periods=200),
        "Close": np.linspace(150, 180, 200),
    })

    mock = MagicMock()
    mock.info = info
    mock.history.return_value = hist
    return mock


@patch("app.finance.yf.Ticker")
def test_stock_endpoint_shape(mock_ticker):
    mock_ticker.return_value = _make_mock_stock()
    res = client.get("/stock/AAPL")
    assert res.status_code == 200

    body = res.json()

    assert "ticker" in body
    assert "name" in body
    assert "price" in body
    assert "metrics" in body
    assert "score" in body
    assert "riskLabel" in body
    assert "reasons" in body
    assert isinstance(body["score"], int)
    assert 0 <= body["score"] <= 9
    assert body["riskLabel"] in ("low", "low/medium", "medium", "medium/high", "high", "very high")


@patch("app.finance.yf.Ticker")
def test_stock_metrics_shape(mock_ticker):
    mock_ticker.return_value = _make_mock_stock()
    res = client.get("/stock/AAPL")

    if res.status_code == 200:
        m = res.json()["metrics"]
        for key in ("pe", "forwardPe", "revenueGrowth", "priceToBook", "marketCap"):
            assert key in m


@patch("app.finance.yf.Ticker")
def test_history_endpoint_shape(mock_ticker):
    mock_ticker.return_value = _make_mock_stock()
    res = client.get("/stock/AAPL/history")
    assert res.status_code == 200

    body = res.json()
    assert "prices" in body
    assert isinstance(body["prices"], list)

    if body["prices"]:
        p = body["prices"][0]
        assert "date" in p
        assert "close" in p


def test_invalid_ticker_returns_400():
    res = client.get("/stock/INVALIDLONG")
    assert res.status_code == 400

    res = client.get("/stock/" + "A" * 20)
    assert res.status_code == 400

    res = client.get("/stock/")
    assert res.status_code == 404

    res = client.get("/stock/BRK.BB")
    assert res.status_code == 400

    res = client.get("/stock/123")
    assert res.status_code == 400


@patch("app.finance.yf.Ticker")
def test_dot_suffix_ticker_accepted(mock_ticker):
    mock_ticker.return_value = _make_mock_stock()
    res = client.get("/stock/BRK.B")
    assert res.status_code != 400


@patch("app.finance.yf.Ticker")
def test_metrics_are_nullable(mock_ticker):
    mock_ticker.return_value = _make_mock_stock({"trailingPE": None, "revenueGrowth": None})
    res = client.get("/stock/AAPL")

    if res.status_code == 200:
        m = res.json()["metrics"]
        nullable = ("pe", "forwardPe", "revenueGrowth", "priceToBook")
        for key in nullable:
            assert m[key] is None or isinstance(m[key], (int, float))


def test_health_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}

    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}
