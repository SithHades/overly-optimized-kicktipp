import os
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel

from worldcup_api.services.tournament_tips import refresh_tournament_tips
from worldcup_model.data.live.postgres import upsert_fixtures
from worldcup_model.jobs.ingest_live_fixtures import _build_provider

router = APIRouter(tags=["admin"])


class IngestFixturesResponse(BaseModel):
    provider: str
    fixture_count: int
    postgres_upserts: int
    tournament_tip_count: int
    warnings: list[str]


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
    tournament_tips = refresh_tournament_tips(database_url)

    return IngestFixturesResponse(
        provider=result.provider,
        fixture_count=len(result.fixtures),
        postgres_upserts=upserts,
        tournament_tip_count=tournament_tips["tip_count"],
        warnings=result.warnings,
    )
