from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FixtureStatus(StrEnum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"
    postponed = "postponed"
    unknown = "unknown"


class LiveFixture(BaseModel):
    source: str
    source_match_id: str
    date: datetime
    tournament: str = "World Cup 2026"
    stage: str
    group_name: str | None = None
    home_team: str
    away_team: str
    neutral: bool = True
    venue: str | None = None
    city: str | None = None
    country: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    status: FixtureStatus = FixtureStatus.scheduled
    raw: dict = Field(default_factory=dict)


class LiveIngestResult(BaseModel):
    provider: str
    fetched_at: datetime
    fixtures: list[LiveFixture]
    warnings: list[str] = Field(default_factory=list)
