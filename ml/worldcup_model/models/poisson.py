from dataclasses import dataclass
from math import exp, factorial

ScoreDistribution = dict[tuple[int, int], float]


@dataclass(frozen=True)
class OutcomeProbabilities:
    home_win: float
    draw: float
    away_win: float


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0:
        return 0.0
    return (lam**k * exp(-lam)) / factorial(k)


def score_distribution(lambda_home: float, lambda_away: float, max_goals: int = 7) -> ScoreDistribution:
    distribution: ScoreDistribution = {}
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            distribution[(home_goals, away_goals)] = poisson_pmf(home_goals, lambda_home) * poisson_pmf(
                away_goals, lambda_away
            )

    total_mass = sum(distribution.values())
    return {score: probability / total_mass for score, probability in distribution.items()}


def outcome_probabilities(distribution: ScoreDistribution) -> OutcomeProbabilities:
    home_win = sum(p for (home, away), p in distribution.items() if home > away)
    draw = sum(p for (home, away), p in distribution.items() if home == away)
    away_win = sum(p for (home, away), p in distribution.items() if home < away)
    return OutcomeProbabilities(home_win=home_win, draw=draw, away_win=away_win)


def top_scores(
    distribution: ScoreDistribution,
    limit: int = 5,
) -> list[tuple[tuple[int, int], float]]:
    return sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:limit]
