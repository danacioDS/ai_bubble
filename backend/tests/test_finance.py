from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from .finance import get_stock_data


def _make_mock_ticker():
    info = {
        "shortName": "Microsoft Corp.",
        "currentPrice": 350.0,
    }

    hist = pd.DataFrame({
        "Date": pd.date_range(end="2024-01-01", periods=100),
        "Close": np.linspace(300, 350, 100),
    })

    mock = MagicMock()
    mock.info = info
    mock.history.return_value = hist
    return mock


@patch("app.finance.yf.Ticker")
def test_stock_data_returns_three_values(mock_ticker):
    mock_ticker.return_value = _make_mock_ticker()
    result = get_stock_data("MSFT")
    assert len(result) == 3


@patch("app.finance.yf.Ticker")
def test_stock_data_shape(mock_ticker):
    mock_ticker.return_value = _make_mock_ticker()
    info, hist, price = get_stock_data("MSFT")
    assert isinstance(info, dict)
    assert hist is None or isinstance(hist, pd.DataFrame)
    assert price is None or isinstance(price, (int, float))


@patch("app.finance.yf.Ticker")
def test_stock_data_cache_hit(mock_ticker):
    mock_ticker.return_value = _make_mock_ticker()

    get_stock_data("CACHE_TEST")
    get_stock_data("CACHE_TEST")

    assert mock_ticker.call_count == 1


@patch("app.finance.yf.Ticker")
def test_stock_data_no_data_returns_none(mock_ticker):
    mock = MagicMock()
    mock.info = {}
    mock.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock

    info, hist, price = get_stock_data("NODATA")
    assert info is None
    assert hist is None
    assert price is None
