from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Any, List
from app.dependencies import get_current_user
from app.core.supabase_client import get_supabase
from app.schemas.eeg import (
    EEGSessionCreate, EEGSessionResponse, EEGPredictionCreate, EEGPredictionResponse,
    EEGRiskPredictRequest, EEGRiskPredictResponse
)
from app.services.eeg_inference import predict_eeg_window, calculate_multimodal_risk

router = APIRouter(prefix="/eeg", tags=["eeg"])

@router.post("/sessions", response_model=EEGSessionResponse)
def create_session(
    request: EEGSessionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Starts a new cranial EEG earbud streaming session."""
    data = {
        "user_id": request.user_id,
        "device_id": request.device_id,
        "sample_rate_hz": request.sample_rate_hz,
    }
    result = db.table("eeg_sessions").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to initialize EEG session")
    return EEGSessionResponse(**result.data[0])

@router.post("/sessions/{session_id}/predictions", response_model=EEGPredictionResponse)
def record_prediction(
    session_id: str,
    request: EEGPredictionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Records an anomaly classification prediction for an EEG window."""
    data = {
        "session_id": session_id,
        "predicted_class": request.predicted_class,
        "confidence": request.confidence,
        "window_start_ms": request.window_start_ms,
    }
    result = db.table("eeg_predictions").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log EEG prediction")
    return EEGPredictionResponse(**result.data[0])

@router.get("/users/{user_id}/latest", response_model=List[EEGPredictionResponse])
def get_latest_user_predictions(
    user_id: str,
    limit: int = 10,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Retrieves latest predictions for a given user across sessions."""
    sessions = db.table("eeg_sessions").select("id").eq("user_id", user_id).execute()
    if not sessions.data:
        return []
    session_ids = [s["id"] for s in sessions.data]
    preds = (
        db.table("eeg_predictions")
        .select("*")
        .in_("session_id", session_ids)
        .order("predicted_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [EEGPredictionResponse(**row) for row in (preds.data or [])]

@router.post("/predict-risk", response_model=EEGRiskPredictResponse)
def predict_and_calculate_risk(
    request: EEGRiskPredictRequest,
    db: Client = Depends(get_supabase)
):
    """
    Direct ML inference on raw EEG window (16 values) combined with biometric
    and environmental parameters to predict seizure status and calculate overall health risk score.
    """
    try:
        eeg_res = predict_eeg_window(request.eeg_readings)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"EEG Prediction error: {str(e)}")

    biometric_dict = {
        "heart_rate": request.heart_rate,
        "spo2": request.spo2,
        "skin_temp": request.skin_temp
    }
    environmental_dict = {
        "heat_index": request.heat_index,
        "aqi": request.aqi
    }

    risk_res = calculate_multimodal_risk(eeg_res, biometric=biometric_dict, environmental=environmental_dict)

    # Optional timeline save to Supabase if requested
    if request.save_to_timeline and request.user_id:
        try:
            # 1. Save biometric reading
            db.table("biometric_readings").insert({
                "user_id": request.user_id,
                "heart_rate": request.heart_rate,
                "spo2": request.spo2,
                "skin_temp": request.skin_temp
            }).execute()

            # 2. Save risk score
            db.table("risk_scores").insert({
                "user_id": request.user_id,
                "score": risk_res["score"],
                "risk_level": risk_res["risk_level"].lower(),
                "contributing_factors": risk_res["contributing_factors"]
            }).execute()

            # 3. If seizure or critical risk, raise alert
            if eeg_res["class_id"] in [1, 2, 3] or risk_res["risk_level"] in ["High", "Critical"]:
                db.table("alerts").insert({
                    "user_id": request.user_id,
                    "alert_type": "EEG" if eeg_res["class_id"] in [1, 2, 3] else "Heat",
                    "severity": "critical" if risk_res["risk_level"] == "Critical" else "warning",
                    "message": f"ML Alert: {eeg_res['class_name']} detected ({round(eeg_res['confidence']*100, 1)}% conf). Risk Score: {risk_res['score']}/100.",
                    "channel": "both",
                    "delivery_status": "sent"
                }).execute()
        except Exception as db_err:
            import logging
            logging.error(f"Failed to record risk inference to Supabase: {db_err}")

    return EEGRiskPredictResponse(
        class_id=eeg_res["class_id"],
        class_name=eeg_res["class_name"],
        confidence=eeg_res["confidence"],
        probabilities=eeg_res["probabilities"],
        risk_score=risk_res["score"],
        risk_level=risk_res["risk_level"],
        contributing_factors=risk_res["contributing_factors"],
        features=eeg_res["features"],
        model_name=eeg_res["model_name"]
    )

