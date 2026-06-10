from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from worldcup_api.schemas.predictions import MatchSummary, TeamSide
from worldcup_api.services.sample_data import load_sample_fixtures
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
    lambda_home: float
    lambda_away: float


TEAM_ATTACK_PRIORS: dict[str, tuple[float, float]] = {
    "Argentina": (1.85, 0.82),
    "Brazil": (1.9, 0.8),
    "France": (1.82, 0.85),
    "Spain": (1.72, 0.9),
    "England": (1.7, 0.92),
    "Portugal": (1.68, 0.96),
    "Germany": (1.64, 1.02),
    "Netherlands": (1.62, 1.02),
    "Belgium": (1.58, 1.08),
    "Uruguay": (1.52, 1.04),
    "Croatia": (1.44, 1.1),
    "Mexico": (1.36, 1.16),
    "USA": (1.34, 1.17),
    "Japan": (1.32, 1.15),
    "Morocco": (1.3, 1.08),
}


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
    )


def _load_live_fixtures() -> list[PredictionFixture]:
    snapshot_path = _find_repo_root(Path(__file__).resolve()) / "data/processed/live_fixtures.json"
    if not snapshot_path.exists():
        return []

    result = read_snapshot(snapshot_path)
    fixtures: list[PredictionFixture] = []
    for index, fixture in enumerate(result.fixtures, start=1):
        lambda_home, lambda_away = _estimate_lambdas(fixture.home_team, fixture.away_team)
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
                      m.venue,
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
                lambda_home, lambda_away = _estimate_lambdas(row["home_team"], row["away_team"])
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
                        lambda_home=lambda_home,
                        lambda_away=lambda_away,
                    )
                )
            return fixtures
    except SQLAlchemyError:
        return []


def _estimate_lambdas(home_team: str, away_team: str) -> tuple[float, float]:
    home_attack, home_defense = TEAM_ATTACK_PRIORS.get(home_team, (1.2, 1.2))
    away_attack, away_defense = TEAM_ATTACK_PRIORS.get(away_team, (1.2, 1.2))
    lambda_home = max(0.25, (home_attack + away_defense) / 2)
    lambda_away = max(0.25, (away_attack + home_defense) / 2)
    return lambda_home, lambda_away


def _find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "README.md").exists() and (path / "data").exists():
            return path
    raise FileNotFoundError("Could not find repository root")
