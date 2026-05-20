INFO_RULES = [
    {
        "name": "P/E",
        "field": "pe",
        "thresholds": [
            (40, 2, "P/E very high ({:.1f})"),
            (30, 1, "P/E elevated ({:.1f})"),
        ],
        "missing_penalty": 0.5,
        "missing_msg": "Missing P/E data",
    },
    {
        "name": "Revenue Growth",
        "field": "revenue_growth",
        "thresholds": [
            (0.30, 2, "Strong revenue growth ({:.1%})"),
            (0.15, 1, "Moderate revenue growth ({:.1%})"),
        ],
        "missing_penalty": 0.5,
        "missing_msg": "Missing revenue growth data",
    },
    {
        "name": "P/B",
        "field": "pb",
        "thresholds": [
            (10, 1, "High P/B ({:.1f})"),
        ],
        "missing_penalty": 0.2,
        "missing_msg": "Missing P/B data",
    },
]

HIST_RULES = [
    {
        "name": "Volatility",
        "field": "volatility",
        "threshold": 0.5,
        "score": 1,
        "reason_msg": "Very high volatility ({:.1%})",
        "missing_penalty": 0.3,
        "missing_msg": "Missing historical data",
    },
    {
        "name": "Momentum",
        "field": "momentum",
        "thresholds": [
            (0.50, 2, "Strong momentum (+{:.1%})"),
            (0.20, 1, "Positive momentum (+{:.1%})"),
        ],
        "missing_penalty": 0.3,
        "missing_msg": "Missing momentum data",
    },
]


def clamp(x, min_v=0, max_v=9):
    return max(min_v, min(x, max_v))


def evaluate_features(features):
    score = 0.0
    reasons = []

    for rule in INFO_RULES:
        value = features.get(rule["field"])
        if value is None:
            score += rule["missing_penalty"]
            reasons.append(rule["missing_msg"])
        else:
            for threshold, points, msg in rule["thresholds"]:
                if value > threshold:
                    score += points
                    reasons.append(msg.format(value))
                    break

    for rule in HIST_RULES:
        value = features.get(rule["field"])
        if value is None:
            score += rule["missing_penalty"]
            reasons.append(rule["missing_msg"])
        else:
            if "threshold" in rule:
                if value > rule["threshold"]:
                    score += rule["score"]
                    reasons.append(rule["reason_msg"].format(value))
            elif "thresholds" in rule:
                for threshold, points, msg in rule["thresholds"]:
                    if value > threshold:
                        score += points
                        reasons.append(msg.format(value))
                        break

    score = clamp(score, 0, 9)
    return int(score), reasons
