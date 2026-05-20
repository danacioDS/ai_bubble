from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def test_stock_endpoint_shape():
    res = client.get("/stock/AAPL")
    assert res.status_code == 200

    body = res.json()

    assert "ticker" in body
    assert "name" in body
    assert "price" in body
    assert "metrics" in body
    assert "score" in body
    assert "reasons" in body
    assert isinstance(body["score"], int)
    assert 0 <= body["score"] <= 9


def test_stock_metrics_shape():
    res = client.get("/stock/AAPL")

    if res.status_code == 200:
        m = res.json()["metrics"]
        for key in ("pe", "forwardPe", "revenueGrowth", "priceToBook", "marketCap"):
            assert key in m


def test_history_endpoint_shape():
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
    res = client.get("/stock/" + "A" * 20)
    assert res.status_code == 400


def test_metrics_are_nullable():
    res = client.get("/stock/AAPL")

    if res.status_code == 200:
        m = res.json()["metrics"]
        nullable = ("pe", "forwardPe", "revenueGrowth", "priceToBook")
        for key in nullable:
            assert m[key] is None or isinstance(m[key], (int, float))
