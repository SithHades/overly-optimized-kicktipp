import os
from dataclasses import dataclass

from worldcup_api.services.team_strength import ensure_elo_ratings
from worldcup_api.services.tournament_tips import refresh_tournament_tips
from worldcup_model.data.live.postgres import upsert_fixtures
from worldcup_model.jobs.ingest_live_fixtures import _build_provider


@dataclass(frozen=True)
class FixtureIngestResult:
    provider: str
    fixture_count: int
    postgres_upserts: int
    elo_team_count: int
    tournament_tip_count: int
    warnings: list[str]


def run_fixture_ingest(provider: str | None = None) -> FixtureIngestResult:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    selected_provider = provider or os.environ.get("LIVE_FIXTURE_PROVIDER", "football-data")
    ingest_provider = _build_provider(selected_provider)
    result = ingest_provider.fetch()
    upserts = upsert_fixtures(database_url, result.fixtures)
    elo_result = ensure_elo_ratings(database_url)
    tournament_tips = refresh_tournament_tips(database_url)

    return FixtureIngestResult(
        provider=result.provider,
        fixture_count=len(result.fixtures),
        postgres_upserts=upserts,
        elo_team_count=elo_result.team_count,
        tournament_tip_count=tournament_tips["tip_count"],
        warnings=result.warnings,
    )
