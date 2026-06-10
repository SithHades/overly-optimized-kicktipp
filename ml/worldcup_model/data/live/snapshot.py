import json
from datetime import datetime
from pathlib import Path

from worldcup_model.data.live.schemas import LiveFixture, LiveIngestResult


def write_snapshot(result: LiveIngestResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def read_snapshot(path: Path) -> LiveIngestResult:
    return LiveIngestResult.model_validate_json(path.read_text(encoding="utf-8"))


def write_frontend_fixture_export(fixtures: list[LiveFixture], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "id": index + 1,
            "source": fixture.source,
            "source_match_id": fixture.source_match_id,
            "date": fixture.date.isoformat(),
            "stage": fixture.stage,
            "group_name": fixture.group_name,
            "home_team": fixture.home_team,
            "away_team": fixture.away_team,
            "venue": fixture.venue,
            "status": fixture.status,
            "home_score": fixture.home_score,
            "away_score": fixture.away_score,
        }
        for index, fixture in enumerate(fixtures)
    ]
    path.write_text(json.dumps({"exported_at": datetime.utcnow().isoformat() + "Z", "fixtures": rows}, indent=2))
