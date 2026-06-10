from worldcup_api.schemas.predictions import (
    PredictionResponse,
    RecommendedTip,
    ScoreProbability,
    ScoringRulesSchema,
)
from worldcup_api.services.fixtures import find_prediction_fixture, to_match_summary
from worldcup_model.models.poisson import outcome_probabilities, score_distribution, top_scores
from worldcup_model.models.tippspiel import ScoringRules, expected_tippspiel_points


def build_prediction(
    match_id: int,
    scoring_rules: ScoringRulesSchema,
) -> PredictionResponse | None:
    fixture = find_prediction_fixture(match_id)
    if fixture is None:
        return None

    distribution = score_distribution(fixture.lambda_home, fixture.lambda_away, max_goals=7)
    outcomes = outcome_probabilities(distribution)
    rules = ScoringRules(
        correct_result=scoring_rules.correct_result,
        correct_goal_difference=scoring_rules.correct_goal_difference,
        exact_score=scoring_rules.exact_score,
    )
    best_tip = expected_tippspiel_points(distribution, rules, max_pick_goals=5)

    return PredictionResponse(
        match=to_match_summary(fixture),
        p_home_win=outcomes.home_win,
        p_draw=outcomes.draw,
        p_away_win=outcomes.away_win,
        lambda_home=fixture.lambda_home,
        lambda_away=fixture.lambda_away,
        most_likely_scores=[
            ScoreProbability(score=f"{home}-{away}", p=probability)
            for (home, away), probability in top_scores(distribution, limit=5)
        ],
        recommended_tip=RecommendedTip(
            score=f"{best_tip.pick[0]}-{best_tip.pick[1]}",
            expected_points=best_tip.expected_points,
            explanation=(
                "Optimized for expected scoring-rule points across the full score distribution, "
                "not just the single most likely scoreline."
            ),
        ),
        model_notes=[
            f"Fixture source: {fixture.source}. Lambdas are baseline priors until historical training is wired.",
            "Tipp recommendation is deterministic and scoring-rule aware.",
        ],
    )
