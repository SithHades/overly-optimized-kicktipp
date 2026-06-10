from datetime import datetime

from pydantic import BaseModel, Field


class ScoringRulesSchema(BaseModel):
    correct_result: int = Field(default=2, ge=0)
    correct_goal_difference: int = Field(default=3, ge=0)
    exact_score: int = Field(default=4, ge=0)


class TeamSide(BaseModel):
    id: int | None = None
    name: str


class MatchSummary(BaseModel):
    id: int
    source: str | None = None
    source_match_id: str | None = None
    date: datetime
    stage: str
    group_name: str | None = None
    home_team: TeamSide
    away_team: TeamSide
    venue: str | None = None
    status: str = "scheduled"


class ScoreProbability(BaseModel):
    score: str
    p: float


class RecommendedTip(BaseModel):
    score: str
    expected_points: float
    explanation: str


class PredictionResponse(BaseModel):
    match: MatchSummary
    p_home_win: float
    p_draw: float
    p_away_win: float
    lambda_home: float
    lambda_away: float
    most_likely_scores: list[ScoreProbability]
    recommended_tip: RecommendedTip
    model_notes: list[str]


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]
