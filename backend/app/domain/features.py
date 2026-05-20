import numpy as np


def extract_features(info, hist):
    pe = info.get("trailingPE")
    revenue_growth = info.get("revenueGrowth")
    pb = info.get("priceToBook")
    volatility = _calc_volatility(hist)
    momentum = _calc_momentum(hist)
    return {
        "pe": pe,
        "revenue_growth": revenue_growth,
        "pb": pb,
        "volatility": volatility,
        "momentum": momentum,
    }


def _calc_volatility(hist):
    if hist is None or hist.empty:
        return None
    try:
        returns = hist["Close"].pct_change().dropna()
        if len(returns) > 10:
            return float(returns.std() * np.sqrt(252))
    except Exception:
        pass
    return None


def _calc_momentum(hist):
    if hist is None or hist.empty:
        return None
    try:
        if len(hist) > 20:
            return float(hist["Close"].iloc[-1] / hist["Close"].iloc[-20] - 1)
    except Exception:
        pass
    return None
