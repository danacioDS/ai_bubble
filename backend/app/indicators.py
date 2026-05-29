from .domain.features import extract_features
from .domain.scoring import evaluate_features


def bubble_score(info, hist=None):
    if not info:
        return 0, ["No financial data available"]
    features = extract_features(info, hist)
    return evaluate_features(features)
