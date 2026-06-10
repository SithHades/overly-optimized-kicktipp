from pydantic import BaseModel, Field


class DataQualityIssue(BaseModel):
    type: str
    message: str
    suggested_fix: str | None = None


class DataQualityAudit(BaseModel):
    severity: str
    issues: list[DataQualityIssue] = Field(default_factory=list)


class InjuryItem(BaseModel):
    player: str
    status: str
    confidence: float = Field(ge=0, le=1)
    expected_impact: str


class TeamIntel(BaseModel):
    team: str
    tactical_summary: str
    likely_formation: str | None = None
    injuries: list[InjuryItem] = Field(default_factory=list)
    morale_notes: str | None = None
    model_adjustment_hint: str
    confidence: float = Field(ge=0, le=1)
