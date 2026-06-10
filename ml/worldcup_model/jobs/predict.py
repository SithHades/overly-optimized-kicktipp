from worldcup_model.models.poisson import outcome_probabilities, score_distribution, top_scores
from worldcup_model.models.tippspiel import ScoringRules, expected_tippspiel_points


def main(lambda_home: float = 1.5, lambda_away: float = 1.1) -> dict[str, object]:
    distribution = score_distribution(lambda_home, lambda_away)
    outcomes = outcome_probabilities(distribution)
    tip = expected_tippspiel_points(distribution, ScoringRules())
    return {
        "p_home_win": outcomes.home_win,
        "p_draw": outcomes.draw,
        "p_away_win": outcomes.away_win,
        "top_scores": [
            {"score": f"{home}-{away}", "p": probability}
            for (home, away), probability in top_scores(distribution)
        ],
        "recommended_tip": {
            "score": f"{tip.pick[0]}-{tip.pick[1]}",
            "expected_points": tip.expected_points,
        },
    }
