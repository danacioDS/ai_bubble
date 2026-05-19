import numpy as np

FACTORS = {
    "pe": {"weight": 2, "missing_penalty": 0.5},
    "growth": {"weight": 2, "missing_penalty": 0.5},
    "pb": {"weight": 1, "missing_penalty": 0.2},
    "volatility": {"weight": 1, "missing_penalty": 0.3},
    "momentum": {"weight": 2, "missing_penalty": 0.3},
}


def clamp(x, min_v=0, max_v=10):
    return max(min_v, min(x, max_v))


def bubble_score(info: dict, hist=None):
    score = 0
    reasons = []

    if not info:
        return 0, ["No financial data available"]

    # ---------------------
    # P/E
    # ---------------------
    pe = info.get("trailingPE")

    if pe is None:
        score += FACTORS["pe"]["missing_penalty"]
        reasons.append("Missing P/E data")
    else:
        if pe > 40:
            score += 2 * FACTORS["pe"]["weight"]
            reasons.append(f"P/E very high ({pe:.1f})")
        elif pe > 30:
            score += 1 * FACTORS["pe"]["weight"]
            reasons.append(f"P/E elevated ({pe:.1f})")

    # ---------------------
    # GROWTH
    # ---------------------
    growth = info.get("revenueGrowth")

    if growth is None:
        score += FACTORS["growth"]["missing_penalty"]
        reasons.append("Missing revenue growth data")
    else:
        if growth > 0.3:
            score += 2 * FACTORS["growth"]["weight"]
            reasons.append(f"Strong revenue growth ({growth:.1%})")
        elif growth > 0.15:
            score += 1 * FACTORS["growth"]["weight"]
            reasons.append(f"Moderate revenue growth ({growth:.1%})")

    # ---------------------
    # P/B
    # ---------------------
    pb = info.get("priceToBook")

    if pb is None:
        score += FACTORS["pb"]["missing_penalty"]
        reasons.append("Missing P/B data")
    else:
        if pb > 10:
            score += 1 * FACTORS["pb"]["weight"]
            reasons.append(f"High P/B ({pb:.1f})")

    # ---------------------
    # VOLATILITY
    # ---------------------
    if hist is None or hist.empty:
        score += FACTORS["volatility"]["missing_penalty"]
        reasons.append("Missing historical data")
    else:
        try:
            returns = hist["Close"].pct_change().dropna()

            if len(returns) > 10:
                vol = returns.std() * np.sqrt(252)

                if vol > 0.6:
                    score += 1 * FACTORS["volatility"]["weight"]
                    reasons.append(f"Very high volatility ({vol:.1%})")

        except Exception:
            reasons.append("Volatility calculation error")

    # ---------------------
    # MOMENTUM
    # ---------------------
    if hist is None or hist.empty:
        score += FACTORS["momentum"]["missing_penalty"]
        reasons.append("Missing momentum data")
    else:
        try:
            if len(hist) > 20:
                momentum = hist["Close"].iloc[-1] / hist["Close"].iloc[-20] - 1

                if momentum > 0.5:
                    score += 2 * FACTORS["momentum"]["weight"]
                    reasons.append(f"Strong momentum (+{momentum:.1%})")
                elif momentum > 0.2:
                    score += 1 * FACTORS["momentum"]["weight"]
                    reasons.append(f"Positive momentum (+{momentum:.1%})")

        except Exception:
            reasons.append("Momentum calculation error")

    # ---------------------
    # FINAL SCORE (NORMALIZED)
    # ---------------------
    score = clamp(score, 0, 10)

    return int(score), reasons
