from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class EEGSessionCreate(BaseModel):
    user_id: str
    device_id: Optional[str] = None
    sample_rate_hz: int = 250

class EEGSessionResponse(BaseModel):
    id: str
    user_id: str
    device_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    sample_rate_hz: Optional[int] = 250

    model_config = ConfigDict(from_attributes=True)

class EEGPredictionCreate(BaseModel):
    predicted_class: str = "healthy"
    confidence: float = 0.99
    window_start_ms: Optional[int] = 0

class EEGPredictionResponse(BaseModel):
    id: int
    session_id: str
    predicted_class: str
    confidence: float
    window_start_ms: Optional[int] = None
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EEGRiskPredictRequest(BaseModel):
    eeg_readings: list[float]
    heart_rate: Optional[float] = 75.0
    spo2: Optional[float] = 98.0
    skin_temp: Optional[float] = 36.6
    heat_index: Optional[float] = 32.0
    aqi: Optional[float] = 95.0
    user_id: Optional[str] = None
    save_to_timeline: Optional[bool] = False

class EEGRiskPredictResponse(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    probabilities: dict[str, float]
    risk_score: float
    risk_level: str
    contributing_factors: dict[str, Any]
    features: dict[str, float]
    model_name: str

