import os
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel

from worldcup_api.services.live_ingest import run_fixture_ingest
from worldcup_api.services.team_strength import refresh_elo_ratings
from worldcup_api.services.tournament_tips import refresh_tournament_tips

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

    result = run_fixture_ingest(provider)

    return IngestFixturesResponse(
        provider=result.provider,
        fixture_count=result.fixture_count,
        postgres_upserts=result.postgres_upserts,
        elo_team_count=result.elo_team_count,
        tournament_tip_count=result.tournament_tip_count,
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
