from pydantic import BaseModel
from datetime import datetime

class RiskScoreResponse(BaseModel):
    id: int
    user_id: str
    score: float
    risk_level: str
    contributing_factors: dict
    computed_at: datetime

class RiskHistoryResponse(BaseModel):
    scores: list[RiskScoreResponse]
