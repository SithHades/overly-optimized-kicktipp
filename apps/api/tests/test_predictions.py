from fastapi.testclient import TestClient

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
