from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from worldcup_api.schemas.predictions import MatchSummary, TeamSide
from worldcup_api.services.sample_data import load_sample_fixtures
from worldcup_api.services.team_strength import estimate_lambdas
from worldcup_model.data.live.snapshot import read_snapshot


@dataclass(frozen=True)
class PredictionFixture:
    id: int
    source: str
    source_match_id: str
    date: datetime
    stage: str
    group_name: str | None
    home_team: str
    away_team: str
    venue: str | None
    status: str
    home_score: int | None
    away_score: int | None
    home_elo: float | None
    away_elo: float | None
    lambda_home: float
    lambda_away: float


def load_prediction_fixtures() -> list[PredictionFixture]:
    database = _load_database_fixtures()
    if database:
        return database

    live = _load_live_fixtures()
    if live:
        return live

    return [
        PredictionFixture(
            id=fixture.id,
            source="sample",
            source_match_id=str(fixture.id),
            date=fixture.date,
            stage=fixture.stage,
            group_name=None,
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            venue=None,
            status="scheduled",
            home_score=None,
            away_score=None,
            home_elo=None,
            away_elo=None,
            lambda_home=fixture.lambda_home,
            lambda_away=fixture.lambda_away,
        )
        for fixture in load_sample_fixtures()
    ]


def find_prediction_fixture(match_id: int) -> PredictionFixture | None:
    return next((fixture for fixture in load_prediction_fixtures() if fixture.id == match_id), None)


def to_match_summary(fixture: PredictionFixture) -> MatchSummary:
    return MatchSummary(
        id=fixture.id,
        source=fixture.source,
        source_match_id=fixture.source_match_id,
        date=fixture.date,
        stage=fixture.stage,
        group_name=fixture.group_name,
        home_team=TeamSide(name=fixture.home_team),
        away_team=TeamSide(name=fixture.away_team),
        venue=fixture.venue,
        status=fixture.status,
        home_score=fixture.home_score,
        away_score=fixture.away_score,
    )


def _load_live_fixtures() -> list[PredictionFixture]:
    snapshot_path = _live_fixture_snapshot_path(Path(__file__).resolve())
    if not snapshot_path.exists():
        return []

    result = read_snapshot(snapshot_path)
    fixtures: list[PredictionFixture] = []
    for index, fixture in enumerate(result.fixtures, start=1):
        lambda_home, lambda_away = estimate_lambdas(None, None)
        fixtures.append(
            PredictionFixture(
                id=index,
                source=fixture.source,
                source_match_id=fixture.source_match_id,
                date=fixture.date,
                stage=fixture.stage,
                group_name=fixture.group_name,
                home_team=fixture.home_team,
                away_team=fixture.away_team,
                venue=fixture.venue,
                status=fixture.status.value,
                home_score=fixture.home_score,
                away_score=fixture.away_score,
                home_elo=None,
                away_elo=None,
                lambda_home=lambda_home,
                lambda_away=lambda_away,
            )
        )
    return fixtures


def _load_database_fixtures() -> list[PredictionFixture]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return []

    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                      m.id,
                      m.source,
                      m.source_match_id,
                      m.date,
                      m.stage,
                      m.group_name,
                      home_team.name AS home_team,
                      away_team.name AS away_team,
                      home_team.current_elo AS home_elo,
                      away_team.current_elo AS away_elo,
                      m.venue,
                      m.home_score,
                      m.away_score,
                      m.status
                    FROM matches m
                    JOIN teams home_team ON home_team.id = m.home_team_id
                    JOIN teams away_team ON away_team.id = m.away_team_id
                    WHERE m.date IS NOT NULL
                    ORDER BY m.date ASC, m.id ASC
                    """
                )
            ).mappings()
            fixtures: list[PredictionFixture] = []
            for row in rows:
                home_elo = float(row["home_elo"]) if row["home_elo"] is not None else None
                away_elo = float(row["away_elo"]) if row["away_elo"] is not None else None
                lambda_home, lambda_away = estimate_lambdas(home_elo, away_elo)
                fixtures.append(
                    PredictionFixture(
                        id=row["id"],
                        source=row["source"] or "database",
                        source_match_id=row["source_match_id"] or str(row["id"]),
                        date=row["date"],
                        stage=row["stage"] or "Unknown",
                        group_name=row["group_name"],
                        home_team=row["home_team"],
                        away_team=row["away_team"],
                        venue=row["venue"],
                        status=row["status"] or "scheduled",
                        home_score=row["home_score"],
                        away_score=row["away_score"],
                        home_elo=home_elo,
                        away_elo=away_elo,
                        lambda_home=lambda_home,
                        lambda_away=lambda_away,
                    )
                )
            return fixtures
    except SQLAlchemyError:
        return []


def _live_fixture_snapshot_path(start: Path) -> Path:
    configured_snapshot = os.environ.get("LIVE_FIXTURE_SNAPSHOT")
    if configured_snapshot:
        return Path(configured_snapshot)

    configured_root = os.environ.get("WORLDCUPQUANT_ROOT")
    if configured_root:
        return Path(configured_root) / "data/processed/live_fixtures.json"

    data_root = _find_data_root(start)
    return data_root / "processed/live_fixtures.json"


def _find_data_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "data").exists():
            return path / "data"
    return Path.cwd() / "data"
