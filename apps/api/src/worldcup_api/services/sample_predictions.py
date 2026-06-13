from worldcup_api.schemas.predictions import (
    ModelContext,
    PredictionResponse,
    PredictionConfidence,
    RecommendedTip,
    ScoreProbability,
    ScoringRulesSchema,
    TeamRating,
)
from worldcup_api.services.fixtures import PredictionFixture, find_prediction_fixture, load_prediction_fixtures, to_match_summary
from worldcup_api.services.team_strength import (
    MODEL_TRAINING_STATUS,
    MODEL_VERSION,
    model_elo,
    rating_known,
    rating_source_note,
    rating_tier,
    strength_score,
)
from worldcup_model.models.poisson import outcome_probabilities, score_distribution, top_scores
from worldcup_model.models.tippspiel import ScoringRules, expected_tippspiel_points, score_points


def build_prediction(
    match_id: int,
    scoring_rules: ScoringRulesSchema,
) -> PredictionResponse | None:
    fixture = find_prediction_fixture(match_id)
    if fixture is None:
        return None

    return build_prediction_for_fixture(fixture, scoring_rules)


def build_predictions(scoring_rules: ScoringRulesSchema) -> list[PredictionResponse]:
    return [
        build_prediction_for_fixture(fixture, scoring_rules)
        for fixture in load_prediction_fixtures()
        if fixture.home_team != "TBD" and fixture.away_team != "TBD"
    ]


def build_prediction_for_fixture(
    fixture: PredictionFixture,
    scoring_rules: ScoringRulesSchema,
) -> PredictionResponse:
    distribution = score_distribution(fixture.lambda_home, fixture.lambda_away, max_goals=7)
    outcomes = outcome_probabilities(distribution)
    rules = ScoringRules(
        correct_result=scoring_rules.correct_result,
        correct_goal_difference=scoring_rules.correct_goal_difference,
        exact_score=scoring_rules.exact_score,
    )
    best_tip = expected_tippspiel_points(distribution, rules, max_pick_goals=5)
    actual_score = _actual_score(fixture)
    actual_points = score_points(best_tip.pick, actual_score, rules) if actual_score else None
    confidence = _prediction_confidence(outcomes.home_win, outcomes.draw, outcomes.away_win)
    home_rating = _team_rating(fixture.home_team, fixture.home_elo)
    away_rating = _team_rating(fixture.away_team, fixture.away_elo)

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
            actual_points=actual_points,
            actual_score=f"{actual_score[0]}-{actual_score[1]}" if actual_score else None,
            explanation=(
                "Optimized for expected scoring-rule points across the full score distribution, "
                "not just the single most likely scoreline."
            ),
        ),
        home_rating=home_rating,
        away_rating=away_rating,
        rating_delta=home_rating.model_elo - away_rating.model_elo,
        confidence=confidence,
        model_context=ModelContext(
            model_version=MODEL_VERSION,
            data_source=f"{fixture.source} fixtures saved in Postgres, then scored on demand.",
            training_status=MODEL_TRAINING_STATUS,
            rating_source=rating_source_note(
                fixture.home_team,
                fixture.away_team,
                fixture.home_elo,
                fixture.away_elo,
            ),
            explanation=[
                "Each team rating is fitted from completed historical international matches.",
                "The rating gap is converted into expected goals for a Poisson score model.",
                "The 1X2 probabilities come from the full scoreline distribution.",
                "The recommended Tipp maximizes expected points under the configured scoring rules.",
            ],
        ),
        model_notes=[
            f"Fixture source: {fixture.source}.",
            f"Model Elo: {fixture.home_team} {home_rating.model_elo}, {fixture.away_team} {away_rating.model_elo}.",
            MODEL_TRAINING_STATUS,
        ],
    )


def _team_rating(team: str, rating: float | None) -> TeamRating:
    return TeamRating(
        team=team,
        model_elo=model_elo(team, rating),
        strength_score=strength_score(team, rating),
        tier=rating_tier(team, rating),
        known_rating=rating_known(rating),
    )


def _actual_score(fixture: PredictionFixture) -> tuple[int, int] | None:
    if fixture.status != "finished":
        return None
    if fixture.home_score is None or fixture.away_score is None:
        return None
    return fixture.home_score, fixture.away_score


def _prediction_confidence(home_win: float, draw: float, away_win: float) -> PredictionConfidence:
    strongest = max(home_win, draw, away_win)
    margin = strongest - sorted([home_win, draw, away_win], reverse=True)[1]
    score = min(1.0, max(0.0, strongest * 0.7 + margin * 1.2))
    if strongest >= 0.58 or margin >= 0.2:
        label = "High"
    elif strongest >= 0.44 or margin >= 0.1:
        label = "Medium"
    else:
        label = "Low"

    return PredictionConfidence(
        label=label,
        score=score,
        reason=(
            f"Best outcome is {strongest:.0%}; gap to the next outcome is {margin:.0%}. "
            "Football scorelines are noisy, so close 1X2 markets should remain low confidence."
        ),
    )
