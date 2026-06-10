from datetime import UTC

from worldcup_model.data.live.providers import OpenFootballWorldCupProvider
from worldcup_model.data.live.timeparse import parse_openfootball_datetime


def test_parse_openfootball_datetime_converts_to_utc() -> None:
    parsed = parse_openfootball_datetime("2026-06-11", "13:00 UTC-6")

    assert parsed.tzinfo == UTC
    assert parsed.isoformat() == "2026-06-11T19:00:00+00:00"


def test_openfootball_match_normalization() -> None:
    provider = OpenFootballWorldCupProvider()
    fixture = provider._fixture_from_match(
        "World Cup 2026",
        {
            "round": "Matchday 1",
            "date": "2026-06-11",
            "time": "13:00 UTC-6",
            "team1": "Mexico",
            "team2": "South Africa",
            "group": "Group A",
            "ground": "Mexico City",
        },
    )

    assert fixture.home_team == "Mexico"
    assert fixture.away_team == "South Africa"
    assert fixture.group_name == "Group A"
    assert fixture.date.isoformat() == "2026-06-11T19:00:00+00:00"
