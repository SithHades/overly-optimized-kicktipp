from worldcup_model.models.poisson import score_distribution
from worldcup_model.models.tippspiel import ScoringRules, expected_tippspiel_points, score_points


def test_score_points_exact_score_takes_precedence() -> None:
    rules = ScoringRules(correct_result=2, correct_goal_difference=3, exact_score=4)

    assert score_points((2, 1), (2, 1), rules) == 4


def test_score_points_goal_difference_beats_result_only() -> None:
    rules = ScoringRules(correct_result=2, correct_goal_difference=3, exact_score=4)

    assert score_points((2, 1), (3, 2), rules) == 3
    assert score_points((1, 0), (3, 2), rules) == 3
    assert score_points((2, 0), (3, 2), rules) == 2


def test_expected_tippspiel_points_returns_candidate_pick() -> None:
    distribution = score_distribution(lambda_home=1.64, lambda_away=1.08)
    recommendation = expected_tippspiel_points(distribution, ScoringRules(), max_pick_goals=5)

    assert 0 <= recommendation.pick[0] <= 5
    assert 0 <= recommendation.pick[1] <= 5
    assert recommendation.expected_points > 0
