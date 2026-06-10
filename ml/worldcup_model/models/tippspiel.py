from dataclasses import dataclass

from worldcup_model.models.poisson import ScoreDistribution


@dataclass(frozen=True)
class ScoringRules:
    correct_result: int = 2
    correct_goal_difference: int = 3
    exact_score: int = 4


@dataclass(frozen=True)
class TipRecommendation:
    pick: tuple[int, int]
    expected_points: float


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def score_points(
    pick: tuple[int, int],
    actual: tuple[int, int],
    rules: ScoringRules,
) -> int:
    if pick == actual:
        return rules.exact_score

    pick_diff = pick[0] - pick[1]
    actual_diff = actual[0] - actual[1]

    if pick_diff == actual_diff:
        return rules.correct_goal_difference

    if _sign(pick_diff) == _sign(actual_diff):
        return rules.correct_result

    return 0


def expected_points_for_pick(
    pick: tuple[int, int],
    distribution: ScoreDistribution,
    rules: ScoringRules,
) -> float:
    return sum(
        probability * score_points(pick, actual_score, rules)
        for actual_score, probability in distribution.items()
    )


def expected_tippspiel_points(
    distribution: ScoreDistribution,
    rules: ScoringRules,
    max_pick_goals: int = 5,
) -> TipRecommendation:
    candidates: list[TipRecommendation] = []
    for pick_home in range(max_pick_goals + 1):
        for pick_away in range(max_pick_goals + 1):
            pick = (pick_home, pick_away)
            candidates.append(
                TipRecommendation(
                    pick=pick,
                    expected_points=expected_points_for_pick(pick, distribution, rules),
                )
            )

    return max(candidates, key=lambda item: item.expected_points)
