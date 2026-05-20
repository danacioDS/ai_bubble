import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from indicators import bubble_score


def make_hist(close_prices):
    dates = pd.date_range(end="2024-01-01", periods=len(close_prices), freq="D")
    return pd.DataFrame({"Close": close_prices}, index=dates)


def test_extreme_bubble_case():
    base = np.linspace(100, 110, 180)
    spike = np.linspace(110, 180, 20)
    prices = np.append(base, spike) + np.random.normal(0, 3, 200)
    hist = make_hist(prices)
    score, reasons = bubble_score({
        "trailingPE": 120,
        "priceToBook": 30,
        "revenueGrowth": 0.8,
    }, hist)
    assert score >= 8
    assert any("momentum" in r.lower() for r in reasons)


def test_safe_case():
    score, reasons = bubble_score({
        "trailingPE": 10,
        "priceToBook": 2,
        "revenueGrowth": 0.05,
    })
    assert score == 0


def test_warning_range():
    hist = make_hist(np.linspace(100, 130, 200) + np.random.normal(0, 3, 200))
    score, reasons = bubble_score({
        "trailingPE": 35,
        "revenueGrowth": 0.2,
        "priceToBook": 12,
    }, hist)
    assert 4 <= score <= 5


def test_missing_data_uses_penalties():
    score, reasons = bubble_score({})
    assert score >= 0
    assert len(reasons) >= 1


def test_high_pe_scores():
    score, reasons = bubble_score({
        "trailingPE": 50,
        "revenueGrowth": 0.1,
        "priceToBook": 5,
    })
    assert score >= 2
    assert any("P/E" in r for r in reasons)


def test_high_growth_scores():
    score, reasons = bubble_score({
        "trailingPE": 15,
        "revenueGrowth": 0.4,
        "priceToBook": 3,
    })
    assert score >= 2
    assert any("growth" in r.lower() for r in reasons)


def test_score_bounds():
    for _ in range(100):
        score, reasons = bubble_score({
            "trailingPE": _ * 5,
            "revenueGrowth": _ * 0.05,
            "priceToBook": _ * 2,
        })
        assert 0 <= score <= 9


def test_volatility_momentum_with_hist():
    prices = np.linspace(100, 180, 200) + np.random.normal(0, 2, 200)
    hist = make_hist(prices)

    score, reasons = bubble_score({
        "trailingPE": 30,
        "revenueGrowth": 0.1,
        "priceToBook": 5,
    }, hist)

    assert 0 <= score <= 9
