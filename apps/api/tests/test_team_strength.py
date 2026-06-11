from datetime import date

import pytest

from worldcup_api.services.team_strength import (
    BASE_ELO,
    HistoricalMatch,
    canonical_team_name,
    compute_elo_ratings,
    estimate_lambdas,
    parse_international_results_csv,
    parse_openfootball_historical_payload,
    rating_source_note,
)


def test_parse_openfootball_payload_uses_completed_full_time_matches() -> None:
    payload = {
        "name": "World Cup Test",
        "matches": [
            {
                "num": 1,
                "round": "Group A",
                "date": "2000-06-01",
                "team1": "West Germany",
                "team2": "USA",
                "score": {"ft": [2, 0]},
            },
            {
                "num": 2,
                "round": "Group A",
                "date": "2000-06-02",
                "team1": "France",
                "team2": "Mexico",
                "score": {"ft": [None, None]},
            },
        ],
    }

    matches = parse_openfootball_historical_payload(2000, payload)

    assert matches == [
        HistoricalMatch(
            source_match_id="openfootball-2000-1",
            date=date(2000, 6, 1),
            tournament="World Cup Test",
            stage="Group A",
            home_team="Germany",
            away_team="United States",
            home_score=2,
            away_score=0,
        )
    ]


def test_parse_international_results_csv_uses_broader_match_history() -> None:
    payload = "\n".join(
        [
            "date,home_team,away_team,home_score,away_score,tournament,city,country,neutral",
            "2024-03-23,France,Germany,0,2,Friendly,Lyon,France,FALSE",
            "2024-06-14,Germany,Scotland,5,1,UEFA Euro,Berlin,Germany,FALSE",
        ]
    )

    matches = parse_international_results_csv(payload)

    assert [match.tournament for match in matches] == ["Friendly", "UEFA Euro"]
    assert matches[0].neutral is False
    assert matches[1].home_team == "Germany"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("USA", "United States"),
        ("West Germany", "Germany"),
        ("Côte d'Ivoire", "Ivory Coast"),
        ("Czechoslovakia", "Czechia"),
    ],
)
def test_canonical_team_name_normalizes_historical_names(source: str, expected: str) -> None:
    assert canonical_team_name(source) == expected


def test_compute_elo_ratings_updates_chronologically() -> None:
    matches = [
        HistoricalMatch(
            source_match_id="later",
            date=date(2000, 6, 2),
            tournament="World Cup Test",
            stage="Group",
            home_team="A",
            away_team="B",
            home_score=0,
            away_score=0,
        ),
        HistoricalMatch(
            source_match_id="earlier",
            date=date(2000, 6, 1),
            tournament="World Cup Test",
            stage="Group",
            home_team="A",
            away_team="B",
            home_score=3,
            away_score=0,
        ),
    ]

    ratings = compute_elo_ratings(matches)

    assert ratings["A"] > BASE_ELO
    assert ratings["B"] < BASE_ELO
    assert ratings["A"] + ratings["B"] == pytest.approx(BASE_ELO * 2)


def test_competitive_matches_move_elo_more_than_friendlies() -> None:
    ratings = compute_elo_ratings(
        [
            HistoricalMatch(
                source_match_id="friendly",
                date=date(2024, 1, 1),
                tournament="Friendly",
                stage="Friendly",
                home_team="A",
                away_team="B",
                home_score=1,
                away_score=0,
            ),
            HistoricalMatch(
                source_match_id="world-cup",
                date=date(2024, 1, 1),
                tournament="FIFA World Cup",
                stage="FIFA World Cup",
                home_team="C",
                away_team="D",
                home_score=1,
                away_score=0,
            ),
        ]
    )

    assert ratings["C"] - BASE_ELO > ratings["A"] - BASE_ELO


def test_old_results_decay_toward_neutral_before_recent_matches() -> None:
    ratings = compute_elo_ratings(
        [
            HistoricalMatch(
                source_match_id="old",
                date=date(1930, 1, 1),
                tournament="FIFA World Cup",
                stage="FIFA World Cup",
                home_team="A",
                away_team="B",
                home_score=5,
                away_score=0,
            ),
            HistoricalMatch(
                source_match_id="recent",
                date=date(2024, 1, 1),
                tournament="FIFA World Cup",
                stage="FIFA World Cup",
                home_team="B",
                away_team="A",
                home_score=1,
                away_score=0,
            ),
        ]
    )

    assert ratings["B"] > ratings["A"]


def test_estimate_lambdas_follow_elo_gap() -> None:
    stronger_home, weaker_away = estimate_lambdas(1700, 1500)
    weaker_home, stronger_away = estimate_lambdas(1500, 1700)

    assert stronger_home > weaker_away
    assert weaker_home < stronger_away


def test_rating_source_note_reports_neutral_fallback_for_unknown_team() -> None:
    note = rating_source_note("Germany", "Cape Verde Islands", 1680, None)

    assert "Neutral 1500 Elo fallback" in note
    assert "Cape Verde Islands" in note
