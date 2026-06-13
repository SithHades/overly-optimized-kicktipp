from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from worldcup_api.main import app
from worldcup_api.schemas.predictions import ScoringRulesSchema
from worldcup_api.services.fixtures import PredictionFixture
from worldcup_api.services.sample_predictions import build_prediction_for_fixture


def test_prediction_list_includes_model_context(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)

    response = client.get("/api/predictions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["predictions"]
    prediction = payload["predictions"][0]
    assert prediction["home_rating"]["model_elo"] > 0
    assert prediction["away_rating"]["model_elo"] > 0
    assert prediction["confidence"]["label"] in {"Low", "Medium", "High"}
    assert prediction["model_context"]["training_status"]


def test_prediction_endpoint_accepts_scoring_rules(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)

    response = client.get(
        "/api/matches/1/prediction",
        params={"exact_score": 8, "goal_difference": 3, "correct_result": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_tip"]["score"]
    assert payload["recommended_tip"]["expected_points"] > 0
    assert payload["tip_candidates"]
    assert payload["tip_candidates"][0]["expected_points"] > 0
    assert payload["tip_candidates"][0]["exact_probability"] >= 0


def test_match_preview_endpoint_returns_ai_preview(monkeypatch) -> None:
    class FakePreview(BaseModel):
        fixture: str = "Germany vs France"
        tactical_preview: str = (
            "Germany should try to control midfield possession while France looks for fast "
            "transitions behind the full-backs and pressure after turnovers."
        )
        key_factors: list[str] = Field(default_factory=lambda: ["Rest defense", "Set pieces"])
        upset_scenario: str = "An early set-piece goal changes the game state."
        injury_watch: list[str] = Field(default_factory=list)
        source_urls: list[str] = Field(default_factory=list)
        confidence: float = 0.62

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        "worldcup_api.routers.predictions.generate_match_preview",
        lambda home_team, away_team, **_: FakePreview(fixture=f"{home_team} vs {away_team}"),
    )
    client = TestClient(app)

    response = client.get("/api/matches/1/preview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fixture"]
    assert "control midfield" in payload["tactical_preview"]


def test_match_preview_endpoint_uses_cached_preview(monkeypatch) -> None:
    from worldcup_api.routers import predictions
    from worldcup_api.schemas.predictions import MatchPreviewResponse

    cached = MatchPreviewResponse(
        fixture="Cached fixture",
        tactical_preview=(
            "The cached preview describes pressing structure, transition defense, and set-piece "
            "risk in complete football-analysis sentences."
        ),
        key_factors=["Transition defense", "Set pieces"],
        upset_scenario="An early goal lets the underdog defend deeper.",
        injury_watch=[],
        source_urls=[],
        confidence=0.7,
    )

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(predictions, "_read_cached_preview", lambda cache_key: cached)
    monkeypatch.setattr(
        predictions,
        "generate_match_preview",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("cache miss")),
    )
    client = TestClient(app)

    response = client.get("/api/matches/1/preview")

    assert response.status_code == 200
    assert response.json()["fixture"] == "Cached fixture"


def test_finished_prediction_includes_actual_tip_points() -> None:
    from datetime import UTC, datetime

    prediction = build_prediction_for_fixture(
        PredictionFixture(
            id=1,
            source="test",
            source_match_id="test-1",
            date=datetime(2026, 6, 11, 19, 0, tzinfo=UTC),
            stage="GROUP_STAGE",
            group_name="GROUP_A",
            home_team="Mexico",
            away_team="South Africa",
            venue="Mexico City",
            status="finished",
            home_score=1,
            away_score=0,
            home_elo=1800,
            away_elo=1600,
            lambda_home=1.6,
            lambda_away=0.8,
        ),
        ScoringRulesSchema(),
    )

    assert prediction.match.home_score == 1
    assert prediction.match.away_score == 0
    assert prediction.recommended_tip.actual_score == "1-0"
    assert prediction.recommended_tip.actual_points is not None
    assert any(candidate.actual_points is not None for candidate in prediction.tip_candidates)
