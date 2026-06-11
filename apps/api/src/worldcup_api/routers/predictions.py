from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from worldcup_api.schemas.predictions import (
    MatchPreviewResponse,
    MatchListResponse,
    PredictionListResponse,
    PredictionResponse,
    ScoringRulesSchema,
)
from worldcup_api.services.fixtures import find_prediction_fixture, load_prediction_fixtures, to_match_summary
from worldcup_api.services.sample_predictions import build_prediction, build_predictions
from worldcup_model.ai.match_preview_agent import generate_match_preview

router = APIRouter(tags=["predictions"])


@router.get("/matches/{match_id}/prediction", response_model=PredictionResponse)
def get_prediction(
    match_id: int,
    exact_score: Annotated[int, Query(ge=0)] = 4,
    goal_difference: Annotated[int, Query(ge=0)] = 3,
    correct_result: Annotated[int, Query(ge=0)] = 2,
) -> PredictionResponse:
    prediction = build_prediction(
        match_id,
        ScoringRulesSchema(
            exact_score=exact_score,
            correct_goal_difference=goal_difference,
            correct_result=correct_result,
        ),
    )
    if prediction is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return prediction


@router.get("/matches/{match_id}/preview", response_model=MatchPreviewResponse)
def get_match_preview(match_id: int) -> MatchPreviewResponse:
    fixture = find_prediction_fixture(match_id)
    if fixture is None:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        preview = generate_match_preview(fixture.home_team, fixture.away_team)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI match preview failed") from exc

    return MatchPreviewResponse(**preview.model_dump())


@router.get("/matches", response_model=MatchListResponse)
def list_matches() -> MatchListResponse:
    return MatchListResponse(
        matches=[to_match_summary(fixture) for fixture in load_prediction_fixtures()]
    )


@router.get("/predictions", response_model=PredictionListResponse)
def list_predictions() -> PredictionListResponse:
    return PredictionListResponse(predictions=build_predictions(ScoringRulesSchema()))
