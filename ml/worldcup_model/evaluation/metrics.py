from math import log


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have equal length")
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes, strict=True)) / len(probabilities)


def multiclass_log_loss(probabilities: list[list[float]], actual_indexes: list[int]) -> float:
    if len(probabilities) != len(actual_indexes):
        raise ValueError("probabilities and actual_indexes must have equal length")
    epsilon = 1e-15
    total = 0.0
    for row, actual_index in zip(probabilities, actual_indexes, strict=True):
        p = min(max(row[actual_index], epsilon), 1.0 - epsilon)
        total -= log(p)
    return total / len(probabilities)
