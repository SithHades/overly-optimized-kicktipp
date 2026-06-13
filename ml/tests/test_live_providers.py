from datetime import UTC

from worldcup_model.data.live.providers import OpenFootballWorldCupProvider, _enrich_from_openfootball
from worldcup_model.data.live.schemas import FixtureStatus, LiveFixture, LiveIngestResult
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


def test_football_data_fixture_enrichment_uses_openfootball_venue_and_score(monkeypatch) -> None:
    date = parse_openfootball_datetime("2026-06-11", "13:00 UTC-6")
    football_data_fixture = LiveFixture(
        source="football-data-org",
        source_match_id="537327",
        date=date,
        stage="GROUP_STAGE",
        group_name="GROUP_A",
        home_team="Mexico",
        away_team="South Africa",
        status=FixtureStatus.finished,
    )
    openfootball_fixture = LiveFixture(
        source="openfootball-worldcup-json",
        source_match_id="1",
        date=date,
        stage="Matchday 1",
        group_name="Group A",
        home_team="Mexico",
        away_team="South Africa",
        venue="Mexico City",
        city="Mexico City",
        home_score=2,
        away_score=0,
        status=FixtureStatus.finished,
    )

    monkeypatch.setattr(
        OpenFootballWorldCupProvider,
        "fetch",
        lambda self: LiveIngestResult(
            provider="openfootball-worldcup-json",
            fetched_at=date,
            fixtures=[openfootball_fixture],
        ),
    )

    enriched, warnings = _enrich_from_openfootball([football_data_fixture], timeout_seconds=1)

    assert enriched[0].venue == "Mexico City"
    assert enriched[0].home_score == 2
    assert enriched[0].away_score == 0
    assert warnings == ["Enriched 1 fixtures with OpenFootball venue/score data."]
