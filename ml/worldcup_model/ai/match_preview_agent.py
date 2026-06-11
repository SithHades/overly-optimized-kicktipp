from datetime import datetime
import os
import re

from pydantic import BaseModel, Field, field_validator, model_validator

from worldcup_model.ai.openrouter_client import OpenRouterStructuredClient


class MatchPreview(BaseModel):
    fixture: str
    tactical_preview: str
    key_factors: list[str] = Field(default_factory=list)
    upset_scenario: str
    injury_watch: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

    @field_validator("tactical_preview", "upset_scenario")
    @classmethod
    def reject_search_query_text(cls, value: str) -> str:
        if _looks_like_search_query(value):
            raise ValueError("field looks like a search query, not a match preview")
        return value

    @field_validator("key_factors", "injury_watch")
    @classmethod
    def reject_query_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value for value in values if not _looks_like_search_query(value)]
        if values and not cleaned:
            raise ValueError("all items look like search queries")
        return cleaned

    @model_validator(mode="after")
    def require_preview_substance(self) -> "MatchPreview":
        if len(self.tactical_preview.split()) < 18:
            raise ValueError("tactical_preview is too short")
        if len(self.key_factors) < 2:
            raise ValueError("at least two key factors are required")
        return self


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
                    "Do not put Markdown links in narrative fields; put plain absolute URLs only in source_urls. "
                    "Never return search queries as field values. tactical_preview and upset_scenario must be "
                    "complete explanatory sentences."
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


def _looks_like_search_query(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    query_terms = [
        " current tactics ",
        " tactics formation ",
        " injuries squad availability",
        " national football team",
        " 2024 2025",
    ]
    padded = f" {normalized} "
    if sum(term in padded for term in query_terms) >= 2:
        return True
    return " national football team " in padded and _has_no_sentence_shape(normalized)


def _has_no_sentence_shape(value: str) -> bool:
    if any(character in value for character in [".", ",", ";", ":"]):
        return False
    sentence_verbs = [" is ", " are ", " can ", " could ", " should ", " will ", " would ", " may "]
    return not any(verb in f" {value} " for verb in sentence_verbs)
