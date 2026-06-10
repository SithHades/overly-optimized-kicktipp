import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SampleFixture:
    id: int
    date: datetime
    stage: str
    home_team: str
    away_team: str
    lambda_home: float
    lambda_away: float


def _find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "data/sample/fixtures.json").exists():
            return path
    raise FileNotFoundError("Could not find data/sample/fixtures.json")


def load_sample_fixtures() -> list[SampleFixture]:
    repo_root = _find_repo_root(Path(__file__).resolve())
    raw = json.loads((repo_root / "data/sample/fixtures.json").read_text())
    return [
        SampleFixture(
            id=item["id"],
            date=datetime.fromisoformat(item["date"].replace("Z", "+00:00")),
            stage=item["stage"],
            home_team=item["home_team"],
            away_team=item["away_team"],
            lambda_home=float(item["lambda_home"]),
            lambda_away=float(item["lambda_away"]),
        )
        for item in raw
    ]
