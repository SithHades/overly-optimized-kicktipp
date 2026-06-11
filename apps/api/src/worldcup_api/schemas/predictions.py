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


class TeamRating(BaseModel):
    team: str
    model_elo: int
    strength_score: float
    tier: str
    known_rating: bool


class PredictionConfidence(BaseModel):
    label: str
    score: float
    reason: str


class ModelContext(BaseModel):
    model_version: str
    data_source: str
    training_status: str
    rating_source: str
    explanation: list[str]


class MatchPreviewResponse(BaseModel):
    fixture: str
    tactical_preview: str
    key_factors: list[str]
    upset_scenario: str
    injury_watch: list[str]
    source_urls: list[str]
    confidence: float


class PredictionResponse(BaseModel):
    match: MatchSummary
    p_home_win: float
    p_draw: float
    p_away_win: float
    lambda_home: float
    lambda_away: float
    most_likely_scores: list[ScoreProbability]
    recommended_tip: RecommendedTip
    home_rating: TeamRating
    away_rating: TeamRating
    rating_delta: int
    confidence: PredictionConfidence
    model_context: ModelContext
    model_notes: list[str]


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]


class PredictionListResponse(BaseModel):
    predictions: list[PredictionResponse]
