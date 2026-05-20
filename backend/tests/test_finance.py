import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from finance import get_stock_data


def test_stock_data_returns_three_values():
    result = get_stock_data("AAPL")
    assert len(result) == 3


def test_stock_data_shape():
    info, hist, price = get_stock_data("MSFT")
    assert isinstance(info, dict)
    assert price is None or isinstance(price, (int, float))
