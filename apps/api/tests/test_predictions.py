from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from worldcup_api.main import app


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
