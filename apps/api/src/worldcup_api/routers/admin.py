import os
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel

from worldcup_api.services.tournament_tips import refresh_tournament_tips
from worldcup_api.services.team_strength import ensure_elo_ratings, refresh_elo_ratings
from worldcup_model.data.live.postgres import upsert_fixtures
from worldcup_model.jobs.ingest_live_fixtures import _build_provider

router = APIRouter(tags=["admin"])


class IngestFixturesResponse(BaseModel):
    provider: str
    fixture_count: int
    postgres_upserts: int
    elo_team_count: int
    tournament_tip_count: int
    warnings: list[str]


class RefreshEloResponse(BaseModel):
    model_version: str
    match_count: int
    team_count: int
    fetched_years: list[int]
    skipped_years: list[int]
    top_ratings: list[dict]


@router.post("/admin/ingest-fixtures", response_model=IngestFixturesResponse)
def ingest_fixtures(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    provider: Annotated[str | None, Query()] = None,
) -> IngestFixturesResponse:
    expected_token = os.environ.get("INGEST_ADMIN_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INGEST_ADMIN_TOKEN is not configured",
        )
    if x_admin_token != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured",
        )

    selected_provider = provider or os.environ.get("LIVE_FIXTURE_PROVIDER", "football-data")
    ingest_provider = _build_provider(selected_provider)
    result = ingest_provider.fetch()
    upserts = upsert_fixtures(database_url, result.fixtures)
    elo_result = ensure_elo_ratings(database_url)
    tournament_tips = refresh_tournament_tips(database_url)

    return IngestFixturesResponse(
        provider=result.provider,
        fixture_count=len(result.fixtures),
        postgres_upserts=upserts,
        elo_team_count=elo_result.team_count,
        tournament_tip_count=tournament_tips["tip_count"],
        warnings=result.warnings,
    )


@router.post("/admin/refresh-elo-ratings", response_model=RefreshEloResponse)
def refresh_elo(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    force: Annotated[bool, Query()] = False,
) -> RefreshEloResponse:
    expected_token = os.environ.get("INGEST_ADMIN_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INGEST_ADMIN_TOKEN is not configured",
        )
    if x_admin_token != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured",
        )

    result = refresh_elo_ratings(database_url, force=force)
    refresh_tournament_tips(database_url)
    return RefreshEloResponse(**result.__dict__)
