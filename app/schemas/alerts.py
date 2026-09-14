"""Pydantic request/response models for the alerts endpoints."""

from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    user_id: str
    risk_score_id: int | None = None
    alert_type: str | None = None
    channel: str
    message: str
    acknowledged: bool
    sent_at: datetime


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]