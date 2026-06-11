from typing import Annotated
from datetime import UTC, datetime
import hashlib
import json
import logging
import os
from time import perf_counter

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

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
logger = logging.getLogger("uvicorn.error")
AI_PREVIEW_CACHE_TTL_SECONDS = 60 * 60 * 24 * 14
AI_PREVIEW_CACHE_VERSION = "v2"


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
    started_at = perf_counter()
    logger.info("AI preview requested for match_id=%s", match_id)
    fixture = find_prediction_fixture(match_id)
    if fixture is None:
        logger.warning("AI preview match not found match_id=%s", match_id)
        raise HTTPException(status_code=404, detail="Match not found")

    cache_key = _ai_preview_cache_key(
        match_id=match_id,
        source_match_id=fixture.source_match_id,
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        match_date=fixture.date,
    )
    cached = _read_cached_preview(cache_key)
    if cached is not None:
        logger.info("AI preview cache hit match_id=%s elapsed=%.2fs", match_id, perf_counter() - started_at)
        return cached

    try:
        preview = generate_match_preview(
            fixture.home_team,
            fixture.away_team,
            match_date=fixture.date,
            stage=fixture.group_name or fixture.stage,
            venue=fixture.venue,
        )
        response = MatchPreviewResponse(**preview.model_dump())
        _write_cached_preview(cache_key, response)
    except RuntimeError as exc:
        logger.warning("AI preview failed match_id=%s error=%s", match_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("AI preview unexpected failure match_id=%s", match_id)
        raise HTTPException(status_code=502, detail="AI match preview failed") from exc

    logger.info("AI preview completed match_id=%s elapsed=%.2fs", match_id, perf_counter() - started_at)
    return response


@router.get("/matches", response_model=MatchListResponse)
def list_matches() -> MatchListResponse:
    return MatchListResponse(
        matches=[to_match_summary(fixture) for fixture in load_prediction_fixtures()]
    )


@router.get("/predictions", response_model=PredictionListResponse)
def list_predictions() -> PredictionListResponse:
    return PredictionListResponse(predictions=build_predictions(ScoringRulesSchema()))


def _ai_preview_cache_key(
    *,
    match_id: int,
    source_match_id: str,
    home_team: str,
    away_team: str,
    match_date: datetime,
) -> str:
    model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    web_search = os.environ.get("OPENROUTER_USE_WEB_SEARCH", "true").lower()
    fingerprint = hashlib.sha256(
        "|".join(
            [
                AI_PREVIEW_CACHE_VERSION,
                str(match_id),
                source_match_id,
                home_team,
                away_team,
                match_date.isoformat(),
                model,
                web_search,
            ]
        ).encode()
    ).hexdigest()[:24]
    return f"ai-preview:{fingerprint}"


def _read_cached_preview(cache_key: str) -> MatchPreviewResponse | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key)
        if not payload:
            return None
        return MatchPreviewResponse.model_validate_json(payload)
    except ValidationError as exc:
        logger.warning("AI preview cache payload invalid key=%s error=%s", cache_key, exc)
        return None
    except Exception as exc:
        logger.warning("AI preview cache read failed key=%s error=%s", cache_key, exc)
        return None


def _write_cached_preview(cache_key: str, preview: MatchPreviewResponse) -> None:
    client = _redis_client()
    if client is None:
        return
    payload = preview.model_dump_json()
    cache_record = json.dumps(
        {
            "cached_at": datetime.now(UTC).isoformat(),
            "preview": json.loads(payload),
        }
    )
    try:
        client.setex(cache_key, AI_PREVIEW_CACHE_TTL_SECONDS, payload)
        client.setex(f"{cache_key}:meta", AI_PREVIEW_CACHE_TTL_SECONDS, cache_record)
    except Exception as exc:
        logger.warning("AI preview cache write failed key=%s error=%s", cache_key, exc)


def _redis_client():
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return None
    try:
        from redis import Redis

        return Redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
    except Exception as exc:
        logger.warning("Redis client unavailable for AI preview cache: %s", exc)
        return None
