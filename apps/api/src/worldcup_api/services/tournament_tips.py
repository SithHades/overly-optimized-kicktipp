from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import Any

from sqlalchemy import create_engine, text

from worldcup_api.services.team_strength import MODEL_VERSION, estimate_lambdas, strength_score
from worldcup_model.data.live.postgres import _ensure_live_schema
from worldcup_model.models.poisson import outcome_probabilities, score_distribution

TOP_SCORER_CANDIDATES: list[dict[str, Any]] = [
    {"player": "Kylian Mbappe", "team": "France", "role_score": 1.0},
    {"player": "Harry Kane", "team": "England", "role_score": 0.98},
    {"player": "Erling Haaland", "team": "Norway", "role_score": 0.99},
    {"player": "Vinicius Junior", "team": "Brazil", "role_score": 0.86},
    {"player": "Rodrygo", "team": "Brazil", "role_score": 0.78},
    {"player": "Lionel Messi", "team": "Argentina", "role_score": 0.84},
    {"player": "Julian Alvarez", "team": "Argentina", "role_score": 0.78},
    {"player": "Cristiano Ronaldo", "team": "Portugal", "role_score": 0.8},
    {"player": "Alvaro Morata", "team": "Spain", "role_score": 0.72},
    {"player": "Cody Gakpo", "team": "Netherlands", "role_score": 0.7},
    {"player": "Romelu Lukaku", "team": "Belgium", "role_score": 0.7},
    {"player": "Darwin Nunez", "team": "Uruguay", "role_score": 0.68},
]


@dataclass(frozen=True)
class DbMatch:
    id: int
    date: datetime
    group_name: str | None
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: str


def refresh_tournament_tips(database_url: str, create_pre_tournament: bool = True) -> dict[str, Any]:
    tips = build_tournament_tips(database_url)
    engine = create_engine(database_url)
    with engine.begin() as connection:
        _ensure_live_schema(connection)
        if create_pre_tournament:
            existing = connection.execute(
                text("SELECT COUNT(*) FROM tournament_tips WHERE phase = 'pre_tournament'")
            ).scalar_one()
            if int(existing) == 0:
                _upsert_tips(connection, "pre_tournament", tips)

        _upsert_tips(connection, "current", tips)

    return {
        "model_version": MODEL_VERSION,
        "tip_count": len(tips),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def read_tournament_tips(database_url: str) -> dict[str, Any]:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        _ensure_live_schema(connection)
        rows = connection.execute(
            text(
                """
                SELECT phase, question_key, question_label, answer, confidence, generated_at,
                       model_version, source_state
                FROM tournament_tips
                ORDER BY phase, question_key
                """
            )
        ).mappings()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["phase"]].append(
                {
                    "question_key": row["question_key"],
                    "question_label": row["question_label"],
                    "answer": row["answer"],
                    "confidence": row["confidence"],
                    "generated_at": row["generated_at"],
                    "model_version": row["model_version"],
                    "source_state": row["source_state"],
                }
            )
        return {"phases": dict(grouped)}


def build_tournament_tips(database_url: str) -> list[dict[str, Any]]:
    matches = _load_matches(database_url)
    group_winners = _project_group_winners(matches)
    team_scores = _project_team_scores(matches, group_winners)
    semifinalists = sorted(team_scores.items(), key=lambda item: item[1], reverse=True)[:4]
    winner = semifinalists[0] if semifinalists else ("TBD", 0.0)
    top_scorer = _project_top_scorer(team_scores)

    tips: list[dict[str, Any]] = []
    tips.append(
        {
            "question_key": "top_scorer",
            "question_label": "Which player scores the most goals?",
            "answer": top_scorer,
            "confidence": top_scorer.get("confidence", 0.0),
            "source_state": {"candidate_count": len(TOP_SCORER_CANDIDATES)},
        }
    )
    tips.append(
        {
            "question_key": "semifinalists",
            "question_label": "Which 4 teams reach the semifinals?",
            "answer": {
                "teams": [
                    {"team": team, "projection_score": round(score, 3)}
                    for team, score in semifinalists
                ]
            },
            "confidence": _spread_confidence([score for _, score in semifinalists]),
            "source_state": {"team_count": len(team_scores)},
        }
    )
    tips.append(
        {
            "question_key": "tournament_winner",
            "question_label": "Who wins the tournament?",
            "answer": {"team": winner[0], "projection_score": round(winner[1], 3)},
            "confidence": min(0.95, max(0.1, winner[1] / 140.0)),
            "source_state": {"team_count": len(team_scores)},
        }
    )

    for group_name, projected in sorted(group_winners.items()):
        tips.append(
            {
                "question_key": f"group_winner_{group_name.lower().replace(' ', '_')}",
                "question_label": f"Who wins {group_name}?",
                "answer": {
                    "group": group_name,
                    "team": projected["team"],
                    "projection_points": round(projected["points"], 3),
                },
                "confidence": projected["confidence"],
                "source_state": {"group": group_name},
            }
        )

    return tips


def _load_matches(database_url: str) -> list[DbMatch]:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        _ensure_live_schema(connection)
        rows = connection.execute(
            text(
                """
                SELECT m.id, m.date, m.group_name, home_team.name AS home_team,
                       away_team.name AS away_team, m.home_score, m.away_score, m.status
                FROM matches m
                JOIN teams home_team ON home_team.id = m.home_team_id
                JOIN teams away_team ON away_team.id = m.away_team_id
                WHERE m.date IS NOT NULL
                ORDER BY m.date ASC, m.id ASC
                """
            )
        ).mappings()
        return [
            DbMatch(
                id=row["id"],
                date=row["date"],
                group_name=row["group_name"],
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_score=row["home_score"],
                away_score=row["away_score"],
                status=row["status"] or "scheduled",
            )
            for row in rows
        ]


def _project_group_winners(matches: list[DbMatch]) -> dict[str, dict[str, Any]]:
    points_by_group: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    group_matches = [match for match in matches if match.group_name and _is_group_team(match.home_team)]
    for match in group_matches:
        assert match.group_name is not None
        table = points_by_group[match.group_name]
        table.setdefault(match.home_team, 0.0)
        table.setdefault(match.away_team, 0.0)

        if match.status == "finished" and match.home_score is not None and match.away_score is not None:
            home_points, away_points = _actual_points(match.home_score, match.away_score)
        else:
            lambda_home, lambda_away = estimate_lambdas(match.home_team, match.away_team)
            outcomes = outcome_probabilities(score_distribution(lambda_home, lambda_away))
            home_points = 3 * outcomes.home_win + outcomes.draw
            away_points = 3 * outcomes.away_win + outcomes.draw
        table[match.home_team] += home_points
        table[match.away_team] += away_points

    winners: dict[str, dict[str, Any]] = {}
    for group_name, table in points_by_group.items():
        ranked = sorted(
            table.items(),
            key=lambda item: (item[1], _strength(item[0])),
            reverse=True,
        )
        if not ranked:
            continue
        runner_up_points = ranked[1][1] if len(ranked) > 1 else 0.0
        winners[group_name] = {
            "team": ranked[0][0],
            "points": ranked[0][1],
            "confidence": min(0.95, max(0.1, 0.45 + (ranked[0][1] - runner_up_points) / 6)),
        }
    return winners


def _project_team_scores(
    matches: list[DbMatch],
    group_winners: dict[str, dict[str, Any]],
) -> dict[str, float]:
    teams = {
        team
        for match in matches
        for team in (match.home_team, match.away_team)
        if _is_group_team(team)
    }
    group_winner_teams = {item["team"] for item in group_winners.values()}
    scores: dict[str, float] = {}
    for team in teams:
        current_points = _current_group_points(team, matches)
        winner_bonus = 8.0 if team in group_winner_teams else 0.0
        scores[team] = _strength(team) + current_points * 2.0 + winner_bonus
    return scores


def _project_top_scorer(team_scores: dict[str, float]) -> dict[str, Any]:
    current_goals = _fetch_current_scorer_goals()
    scored_candidates: list[dict[str, Any]] = []
    for candidate in TOP_SCORER_CANDIDATES:
        goals = current_goals.get(candidate["player"], 0)
        team_score = team_scores.get(candidate["team"], _strength(candidate["team"]))
        projection_score = team_score * candidate["role_score"] + goals * 18
        scored_candidates.append(
            {
                "player": candidate["player"],
                "team": candidate["team"],
                "current_goals": goals,
                "projection_score": round(projection_score, 3),
            }
        )

    best = max(scored_candidates, key=lambda item: item["projection_score"])
    second = sorted(scored_candidates, key=lambda item: item["projection_score"], reverse=True)[1]
    best["confidence"] = min(
        0.9,
        max(0.1, 0.35 + (best["projection_score"] - second["projection_score"]) / 40),
    )
    return best


def _fetch_current_scorer_goals() -> dict[str, int]:
    token = os.environ.get("FOOTBALL_DATA_API_TOKEN")
    if not token:
        return {}

    try:
        import httpx

        response = httpx.get(
            "https://api.football-data.org/v4/competitions/WC/scorers",
            headers={"X-Auth-Token": token},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return {}

    scorers: dict[str, int] = {}
    for item in payload.get("scorers", []):
        player = item.get("player") or {}
        name = player.get("name")
        goals = item.get("goals")
        if name and isinstance(goals, int):
            scorers[name] = goals
    return scorers


def _current_group_points(team: str, matches: list[DbMatch]) -> float:
    points = 0.0
    for match in matches:
        if match.status != "finished" or match.home_score is None or match.away_score is None:
            continue
        if match.home_team == team:
            points += _actual_points(match.home_score, match.away_score)[0]
        elif match.away_team == team:
            points += _actual_points(match.home_score, match.away_score)[1]
    return points


def _actual_points(home_score: int, away_score: int) -> tuple[int, int]:
    if home_score > away_score:
        return 3, 0
    if home_score < away_score:
        return 0, 3
    return 1, 1


def _upsert_tips(connection, phase: str, tips: list[dict[str, Any]]) -> None:
    for tip in tips:
        connection.execute(
            text(
                """
                INSERT INTO tournament_tips (
                  phase, question_key, question_label, answer, confidence,
                  generated_at, model_version, source_state
                )
                VALUES (
                  :phase, :question_key, :question_label, CAST(:answer AS jsonb),
                  :confidence, now(), :model_version, CAST(:source_state AS jsonb)
                )
                ON CONFLICT (phase, question_key)
                DO UPDATE SET
                  question_label = excluded.question_label,
                  answer = excluded.answer,
                  confidence = excluded.confidence,
                  generated_at = excluded.generated_at,
                  model_version = excluded.model_version,
                  source_state = excluded.source_state
                """
            ),
            {
                "phase": phase,
                "question_key": tip["question_key"],
                "question_label": tip["question_label"],
                "answer": _json_dumps(tip["answer"]),
                "confidence": tip["confidence"],
                "model_version": MODEL_VERSION,
                "source_state": _json_dumps(tip["source_state"]),
            },
        )


def _json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, default=str)


def _strength(team: str) -> float:
    return strength_score(team)


def _is_group_team(team: str) -> bool:
    if team == "TBD":
        return False
    return not (team.startswith("W") or team.startswith("L") or team[:1].isdigit())


def _spread_confidence(scores: list[float]) -> float:
    if len(scores) < 2:
        return 0.1
    return min(0.9, max(0.1, 0.3 + (max(scores) - min(scores)) / 80))
