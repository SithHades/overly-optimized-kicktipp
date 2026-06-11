from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from io import StringIO
from math import log
from typing import Any

import httpx
from sqlalchemy import create_engine, text

from worldcup_model.data.live.postgres import _ensure_live_schema
from worldcup_model.models.elo import expected_score

MODEL_VERSION = "historical-international-elo-v2"
MODEL_TRAINING_STATUS = (
    "Fitted from historical men's international matches with recency decay, home-field adjustment, "
    "and tournament-importance weights."
)
RATING_SOURCE = "Historical international match results fetched from martj42/international_results."
INTERNATIONAL_RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
BASE_ELO = 1500.0
K_FACTOR = 32.0
ANNUAL_ELO_DECAY = 0.035
HOME_FIELD_ELO = 55.0

WORLD_CUP_YEARS = [
    1930,
    1934,
    1938,
    1950,
    1954,
    1958,
    1962,
    1966,
    1970,
    1974,
    1978,
    1982,
    1986,
    1990,
    1994,
    1998,
    2002,
    2006,
    2010,
    2014,
    2018,
    2022,
]

TEAM_ALIASES = {
    "USA": "United States",
    "United States of America": "United States",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Cape Verde": "Cape Verde Islands",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "DR Congo": "Congo DR",
    "Czech Republic": "Czechia",
    "Curacao": "Curaçao",
    "Soviet Union": "Russia",
    "West Germany": "Germany",
    "German DR": "Germany",
    "Yugoslavia": "Serbia",
    "Serbia and Montenegro": "Serbia",
    "Czechoslovakia": "Czechia",
}


@dataclass(frozen=True)
class HistoricalMatch:
    source_match_id: str
    date: date
    tournament: str
    stage: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    neutral: bool = True


@dataclass(frozen=True)
class EloRefreshResult:
    match_count: int
    team_count: int
    fetched_years: list[int]
    skipped_years: list[int]
    top_ratings: list[dict[str, Any]]
    model_version: str = MODEL_VERSION


def refresh_elo_ratings(database_url: str, force: bool = False) -> EloRefreshResult:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        _ensure_live_schema(connection)
        active = connection.execute(
            text("SELECT COUNT(*) FROM model_runs WHERE model_type = :model_type AND is_active = true"),
            {"model_type": MODEL_VERSION},
        ).scalar_one()
        if int(active) > 0 and not force:
            ratings = _read_current_ratings(connection)
            return EloRefreshResult(
                match_count=0,
                team_count=len(ratings),
                fetched_years=[],
                skipped_years=[],
                top_ratings=_top_ratings(ratings),
            )

    matches, fetched_years, skipped_years = fetch_historical_international_matches()
    ratings = compute_elo_ratings(matches)

    with engine.begin() as connection:
        _ensure_live_schema(connection)
        connection.execute(
            text("UPDATE model_runs SET is_active = false WHERE model_type = :model_type"),
            {"model_type": MODEL_VERSION},
        )
        for team, rating in ratings.items():
            connection.execute(
                text(
                    """
                    INSERT INTO teams (name, current_elo)
                    VALUES (:name, :current_elo)
                    ON CONFLICT (name)
                    DO UPDATE SET current_elo = excluded.current_elo
                    """
                ),
                {"name": team, "current_elo": rating},
            )
        connection.execute(
            text(
                """
                INSERT INTO model_runs (train_data_until, model_type, metrics, is_active)
                VALUES (:train_data_until, :model_type, CAST(:metrics AS jsonb), true)
                """
            ),
            {
                "train_data_until": max(match.date for match in matches),
                "model_type": MODEL_VERSION,
                "metrics": _json_dumps(
                    {
                        "match_count": len(matches),
                        "team_count": len(ratings),
                        "fetched_years": fetched_years,
                        "skipped_years": skipped_years,
                        "rating_source": RATING_SOURCE,
                        "annual_elo_decay": ANNUAL_ELO_DECAY,
                        "base_k_factor": K_FACTOR,
                        "home_field_elo": HOME_FIELD_ELO,
                    }
                ),
            },
        )

    return EloRefreshResult(
        match_count=len(matches),
        team_count=len(ratings),
        fetched_years=fetched_years,
        skipped_years=skipped_years,
        top_ratings=_top_ratings(ratings),
    )


def ensure_elo_ratings(database_url: str) -> EloRefreshResult:
    return refresh_elo_ratings(database_url, force=False)


def fetch_historical_international_matches(
    url: str = INTERNATIONAL_RESULTS_URL,
    timeout_seconds: float = 30.0,
) -> tuple[list[HistoricalMatch], list[int], list[int]]:
    try:
        response = httpx.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("No historical international matches could be fetched") from exc

    matches = parse_international_results_csv(response.text)
    if not matches:
        raise RuntimeError("No historical international matches could be parsed")

    fetched_years = sorted({match.date.year for match in matches})
    return sorted(matches, key=lambda match: (match.date, match.source_match_id)), fetched_years, []


def parse_international_results_csv(payload: str) -> list[HistoricalMatch]:
    matches: list[HistoricalMatch] = []
    reader = csv.DictReader(StringIO(payload))
    for index, row in enumerate(reader, start=1):
        try:
            match_date = date.fromisoformat(row["date"])
            home_score = int(row["home_score"])
            away_score = int(row["away_score"])
        except (KeyError, TypeError, ValueError):
            continue

        home_team = row.get("home_team")
        away_team = row.get("away_team")
        tournament = row.get("tournament")
        if not home_team or not away_team or not tournament:
            continue

        neutral_value = str(row.get("neutral") or "TRUE").strip().upper()
        matches.append(
            HistoricalMatch(
                source_match_id=f"international-results-{match_date.isoformat()}-{index}",
                date=match_date,
                tournament=tournament,
                stage=tournament,
                home_team=canonical_team_name(home_team),
                away_team=canonical_team_name(away_team),
                home_score=home_score,
                away_score=away_score,
                neutral=neutral_value == "TRUE",
            )
        )
    return matches


def fetch_historical_world_cup_matches(
    years: list[int] | None = None,
    url_template: str = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/{year}/worldcup.json",
    timeout_seconds: float = 20.0,
) -> tuple[list[HistoricalMatch], list[int], list[int]]:
    matches: list[HistoricalMatch] = []
    fetched_years: list[int] = []
    skipped_years: list[int] = []

    for year in years or WORLD_CUP_YEARS:
        url = url_template.format(year=year)
        try:
            response = httpx.get(url, timeout=timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError:
            skipped_years.append(year)
            continue

        payload = response.json()
        year_matches = parse_openfootball_historical_payload(year, payload)
        if year_matches:
            matches.extend(year_matches)
            fetched_years.append(year)
        else:
            skipped_years.append(year)

    if not matches:
        raise RuntimeError("No historical World Cup matches could be fetched")

    return sorted(matches, key=lambda match: (match.date, match.source_match_id)), fetched_years, skipped_years


def parse_openfootball_historical_payload(year: int, payload: dict[str, Any]) -> list[HistoricalMatch]:
    tournament = str(payload.get("name") or f"World Cup {year}")
    matches: list[HistoricalMatch] = []
    for index, item in enumerate(payload.get("matches", []), start=1):
        score = item.get("score") or {}
        full_time = score.get("ft")
        if not isinstance(full_time, list) or len(full_time) < 2:
            continue
        if full_time[0] is None or full_time[1] is None:
            continue

        home_team = item.get("team1")
        away_team = item.get("team2")
        match_date = item.get("date")
        if not home_team or not away_team or not match_date:
            continue

        matches.append(
            HistoricalMatch(
                source_match_id=f"openfootball-{year}-{item.get('num') or index}",
                date=date.fromisoformat(match_date),
                tournament=tournament,
                stage=str(item.get("round") or "Unknown"),
                home_team=canonical_team_name(str(home_team)),
                away_team=canonical_team_name(str(away_team)),
                home_score=int(full_time[0]),
                away_score=int(full_time[1]),
                neutral=True,
            )
        )
    return matches


def compute_elo_ratings(matches: list[HistoricalMatch]) -> dict[str, float]:
    ratings: dict[str, float] = {}
    last_year: int | None = None
    for match in sorted(matches, key=lambda item: (item.date, item.source_match_id)):
        if last_year is not None and match.date.year > last_year:
            ratings = _decay_ratings(ratings, match.date.year - last_year)
        last_year = match.date.year

        home_rating = ratings.get(match.home_team, BASE_ELO)
        away_rating = ratings.get(match.away_team, BASE_ELO)
        home_advantage = 0.0 if match.neutral else HOME_FIELD_ELO
        actual_home = _actual_score(match.home_score, match.away_score)
        expected_home = expected_score(home_rating + home_advantage, away_rating)
        multiplier = _margin_multiplier(match.home_score, match.away_score)
        importance = _match_importance_multiplier(match.tournament, match.stage)
        delta = K_FACTOR * multiplier * importance * (actual_home - expected_home)
        ratings[match.home_team] = home_rating + delta
        ratings[match.away_team] = away_rating - delta
    return ratings


def canonical_team_name(team: str) -> str:
    return TEAM_ALIASES.get(team, team)


def model_elo(team: str, rating: float | None = None) -> int:
    return round(rating if rating is not None else BASE_ELO)


def strength_score(team: str, rating: float | None = None) -> float:
    return (model_elo(team, rating) - BASE_ELO) / 8


def rating_tier(team: str, rating: float | None = None) -> str:
    elo = model_elo(team, rating)
    if elo >= 1775:
        return "favorite"
    if elo >= 1675:
        return "contender"
    if elo >= 1575:
        return "solid"
    if elo >= 1475:
        return "outsider"
    return "long shot"


def rating_known(rating: float | None = None) -> bool:
    return rating is not None


def estimate_lambdas(home_elo: float | None, away_elo: float | None) -> tuple[float, float]:
    home_rating = home_elo if home_elo is not None else BASE_ELO
    away_rating = away_elo if away_elo is not None else BASE_ELO
    rating_delta = (home_rating - away_rating) / 400.0
    lambda_home = 1.28 + rating_delta * 0.55
    lambda_away = 1.12 - rating_delta * 0.48
    return max(0.45, min(2.7, lambda_home)), max(0.35, min(2.5, lambda_away))


def rating_source_note(home_team: str, away_team: str, home_elo: float | None, away_elo: float | None) -> str:
    unknown = [
        team
        for team, rating in [(home_team, home_elo), (away_team, away_elo)]
        if rating is None
    ]
    if unknown:
        return f"{RATING_SOURCE} Neutral {BASE_ELO:.0f} Elo fallback used for teams without international match history: {', '.join(unknown)}."
    return RATING_SOURCE


def _read_current_ratings(connection) -> dict[str, float]:
    rows = connection.execute(
        text("SELECT name, current_elo FROM teams WHERE current_elo IS NOT NULL")
    ).mappings()
    return {row["name"]: float(row["current_elo"]) for row in rows}


def _top_ratings(ratings: dict[str, float], limit: int = 12) -> list[dict[str, Any]]:
    return [
        {"team": team, "elo": round(rating, 1)}
        for team, rating in sorted(ratings.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def _actual_score(home_score: int, away_score: int) -> float:
    if home_score > away_score:
        return 1.0
    if home_score < away_score:
        return 0.0
    return 0.5


def _margin_multiplier(home_score: int, away_score: int) -> float:
    margin = abs(home_score - away_score)
    if margin <= 1:
        return 1.0
    return 1.0 + min(log(margin), 1.6) * 0.35


def _decay_ratings(ratings: dict[str, float], years_elapsed: int) -> dict[str, float]:
    retention = (1.0 - ANNUAL_ELO_DECAY) ** years_elapsed
    return {
        team: BASE_ELO + (rating - BASE_ELO) * retention
        for team, rating in ratings.items()
    }


def _match_importance_multiplier(tournament: str, stage: str) -> float:
    label = f"{tournament} {stage}".lower()
    if "fifa world cup" in label and "qualification" not in label:
        return 1.35
    if "world cup" in label and "qualification" not in label:
        return 1.35
    if "qualification" in label or "qualifier" in label:
        return 1.05
    if any(
        competition in label
        for competition in [
            "uefa euro",
            "copa américa",
            "copa america",
            "african cup of nations",
            "afc asian cup",
            "concacaf championship",
            "concacaf gold cup",
            "ofc nations cup",
        ]
    ):
        return 1.15
    if "nations league" in label or "confederations cup" in label:
        return 0.95
    if "friendly" in label:
        return 0.55
    return 0.8


def _json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, default=str)
