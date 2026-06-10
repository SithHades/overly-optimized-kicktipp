from dataclasses import dataclass


@dataclass(frozen=True)
class EloConfig:
    base_rating: float = 1500.0
    k_factor: float = 24.0
    home_advantage: float = 60.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_rating(rating: float, opponent_rating: float, actual_score: float, k_factor: float) -> float:
    return rating + k_factor * (actual_score - expected_score(rating, opponent_rating))
