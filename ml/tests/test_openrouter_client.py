from worldcup_model.ai.match_preview_agent import MatchPreview
from worldcup_model.ai.openrouter_client import OpenRouterStructuredClient


def test_parse_response_extracts_json_from_markdown_wrapper() -> None:
    client = OpenRouterStructuredClient(api_key="test")

    preview = client.parse_response(
        """
        I found the fixture context.

        ```json
        {
          "fixture": "Germany vs France",
          "tactical_preview": "Both teams can press high, attack in transition, and force the opponent into rushed buildup decisions in central areas.",
          "key_factors": ["Rest defense", "Set pieces"],
          "upset_scenario": "An early goal changes the risk profile.",
          "injury_watch": ["No confirmed current injuries found."],
          "source_urls": [],
          "confidence": 0.61
        }
        ```
        """,
        MatchPreview,
    )

    assert preview.fixture == "Germany vs France"
    assert preview.confidence == 0.61


def test_heal_response_repairs_non_json_output(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "fixture": "Germany vs France",
                              "tactical_preview": "Germany can press high through midfield while France threatens the space behind the full-backs with direct transition runners and quick switches.",
                              "key_factors": ["Press resistance", "Transition defense"],
                              "upset_scenario": "A transition goal decides it.",
                              "injury_watch": [],
                              "source_urls": [],
                              "confidence": 0.57
                            }
                            """
                        }
                    }
                ]
            }

    client = OpenRouterStructuredClient(api_key="test")
    monkeypatch.setattr(client, "_post", lambda body: FakeResponse())

    preview = client._heal_response("Here is the preview: not valid JSON", MatchPreview)

    assert preview is not None
    assert preview.fixture == "Germany vs France"


def test_match_preview_rejects_search_query_text() -> None:
    from pydantic import ValidationError

    try:
        MatchPreview(
            fixture="Mexico vs South Africa",
            tactical_preview=(
                "Mexico national football team current tactics formation 2024 2025 and South Africa "
                "national football team Hugo Broos tactics formation 2024 2025"
            ),
            key_factors=[
                "Mexico national football team injuries squad availability 2024 2025",
                "South Africa national football team Bafana Bafana injuries squad availability 2024 2025",
            ],
            upset_scenario="South Africa national football team Bafana Bafana upsets Mexico",
            injury_watch=[],
            source_urls=[],
            confidence=0.5,
        )
    except ValidationError:
        return

    raise AssertionError("search query text should not validate as a match preview")
