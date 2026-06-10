import os
from pathlib import Path

from pydantic import BaseModel

from worldcup_model.data.live.postgres import upsert_fixtures
from worldcup_model.data.live.providers import FootballDataWorldCupProvider, OpenFootballWorldCupProvider
from worldcup_model.data.live.snapshot import write_frontend_fixture_export, write_snapshot


class LiveIngestJobResult(BaseModel):
    provider: str
    fixture_count: int
    snapshot_path: str
    frontend_export_path: str
    postgres_upserts: int | None = None
    warnings: list[str] = []


def main(provider: str | None = None) -> dict:
    repo_root = Path(os.environ.get("WORLDCUPQUANT_ROOT", Path.cwd()))
    selected_provider = provider or os.environ.get("LIVE_FIXTURE_PROVIDER", "openfootball")

    ingest_provider = _build_provider(selected_provider)
    result = ingest_provider.fetch()

    snapshot_path = Path(os.environ.get("LIVE_FIXTURE_SNAPSHOT", repo_root / "data/processed/live_fixtures.json"))
    frontend_export_path = Path(
        os.environ.get("LIVE_FIXTURE_FRONTEND_EXPORT", repo_root / "apps/web/public/live-fixtures.json")
    )
    write_snapshot(result, snapshot_path)
    write_frontend_fixture_export(result.fixtures, frontend_export_path)

    database_url = os.environ.get("DATABASE_URL")
    upserts = upsert_fixtures(database_url, result.fixtures) if database_url else None

    return LiveIngestJobResult(
        provider=result.provider,
        fixture_count=len(result.fixtures),
        snapshot_path=str(snapshot_path),
        frontend_export_path=str(frontend_export_path),
        postgres_upserts=upserts,
        warnings=result.warnings,
    ).model_dump()


def _build_provider(provider: str):
    match provider:
        case "openfootball":
            return OpenFootballWorldCupProvider(
                url=os.environ.get(
                    "OPENFOOTBALL_WORLDCUP_URL",
                    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
                )
            )
        case "football-data":
            token = os.environ["FOOTBALL_DATA_API_TOKEN"]
            return FootballDataWorldCupProvider(api_token=token)
        case _:
            raise ValueError(f"Unsupported live fixture provider: {provider}")


if __name__ == "__main__":
    print(main())
