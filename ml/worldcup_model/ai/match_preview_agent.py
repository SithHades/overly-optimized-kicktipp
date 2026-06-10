from pydantic import BaseModel, Field

from worldcup_model.ai.openrouter_client import OpenRouterStructuredClient


class MatchPreview(BaseModel):
    fixture: str
    tactical_preview: str
    key_factors: list[str] = Field(default_factory=list)
    upset_scenario: str
    injury_watch: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


def generate_match_preview(
    home_team: str,
    away_team: str,
    *,
    client: OpenRouterStructuredClient | None = None,
) -> MatchPreview:
    llm = client or OpenRouterStructuredClient()
    return llm.complete_structured(
        [
            {
                "role": "system",
                "content": (
                    "Extract current football tactical and availability context for a World Cup match. "
                    "Return only valid structured JSON. Include source URLs when web results provide them. "
                    "Do not invent injuries or lineup facts."
                ),
            },
            {
                "role": "user",
                "content": f"Create a concise current match preview for {home_team} vs {away_team}.",
            },
        ],
        MatchPreview,
        use_web_search=True,
    )
