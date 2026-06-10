from fastapi import APIRouter, HTTPException

from worldcup_api.schemas.predictions import MatchListResponse, PredictionResponse, ScoringRulesSchema
from worldcup_api.services.fixtures import load_prediction_fixtures, to_match_summary
from worldcup_api.services.sample_predictions import build_prediction

router = APIRouter(tags=["predictions"])


@router.get("/matches/{match_id}/prediction", response_model=PredictionResponse)
def get_prediction(match_id: int) -> PredictionResponse:
    prediction = build_prediction(match_id, ScoringRulesSchema())
    if prediction is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return prediction


@router.get("/matches", response_model=MatchListResponse)
def list_matches() -> MatchListResponse:
    return MatchListResponse(
        matches=[to_match_summary(fixture) for fixture in load_prediction_fixtures()]
    )
