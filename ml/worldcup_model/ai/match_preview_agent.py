from datetime import datetime
import os

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
    match_date: datetime | None = None,
    stage: str | None = None,
    venue: str | None = None,
    client: OpenRouterStructuredClient | None = None,
) -> MatchPreview:
    llm = client or OpenRouterStructuredClient()
    use_web_search = os.environ.get("OPENROUTER_USE_WEB_SEARCH", "true").lower() in {"1", "true", "yes"}
    fixture_context = [
        f"Fixture: {home_team} vs {away_team}",
        f"Date: {match_date.isoformat() if match_date else 'unknown'}",
        f"Stage: {stage or 'unknown'}",
        f"Venue: {venue or 'unknown'}",
        "Competition context: 2026 FIFA World Cup fixture feed from this application.",
    ]
    return llm.complete_structured(
        [
            {
                "role": "system",
                "content": (
                    "Create a sourced football match preview for a future World Cup fixture. "
                    "Return only valid JSON for the requested schema. Do not wrap JSON in Markdown. "
                    "Use web search for current tactical, squad, and availability context when available. "
                    "Do not reject the task because the public schedule is incomplete; use the fixture context "
                    "provided by the application. Do not invent injuries or lineup facts. "
                    "If current availability is unclear, say that explicitly in injury_watch. "
                    "Do not put Markdown links in narrative fields; put plain absolute URLs only in source_urls."
                ),
            },
            {
                "role": "user",
                "content": "\n".join(
                    [
                        *fixture_context,
                        "Produce concise tactical_preview, 3-5 key_factors, upset_scenario, injury_watch, source_urls, and confidence.",
                    ]
                ),
            },
        ],
        MatchPreview,
        use_web_search=use_web_search,
    )
