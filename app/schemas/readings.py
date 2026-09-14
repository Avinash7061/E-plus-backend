from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BiometricReading(BaseModel):
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    skin_temp: Optional[float] = None
    steps: Optional[int] = None
    recorded_at: datetime
    device_id: Optional[str] = None

class BiometricBatchRequest(BaseModel):
    readings: list[BiometricReading]

class BiometricBatchResponse(BaseModel):
    inserted_count: int
    reading_ids: list[str]
