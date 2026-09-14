from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Any
from app.dependencies import get_current_user
from app.core.supabase_client import get_supabase
from app.schemas.readings import BiometricBatchRequest, BiometricBatchResponse

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

@router.post("/biometrics", response_model=BiometricBatchResponse)
async def ingest_biometrics(
    request: BiometricBatchRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    if not request.readings:
        raise HTTPException(status_code=400, detail="Empty batch")
    
    user_id = current_user["id"]
    
    insert_data = []
    for reading in request.readings:
        data = reading.model_dump()
        data["user_id"] = user_id
        # Supabase API expects strings for datetime fields
        if data.get("recorded_at"):
            data["recorded_at"] = data["recorded_at"].isoformat()
        insert_data.append(data)
        
    try:
        response = db.table("biometric_readings").insert(insert_data).execute()
        
        inserted_rows = response.data
        inserted_count = len(inserted_rows)
        reading_ids = [row["id"] for row in inserted_rows]
        
        # Compute risk score with the most recent reading (the last one in the batch)
        latest_reading = insert_data[-1]
        try:
            from app.services.risk_engine import compute_risk_score
            import logging

            environmental_data = None
            try:
                user_row = db.table("users").select("region").eq("id", user_id).execute()
                if user_row.data and user_row.data[0].get("region"):
                    region = user_row.data[0]["region"]
                    env_row = (
                        db.table("environmental_readings")
                        .select("*")
                        .eq("region", region)
                        .order("recorded_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if env_row.data:
                        environmental_data = env_row.data[0]
            except Exception as env_lookup_error:
                logging.error(f"Failed to fetch environmental data: {env_lookup_error}")

            risk_result = compute_risk_score(latest_reading, environmental=environmental_data)
            
            # Insert risk score
            risk_insert_data = {
                "user_id": user_id,
                "score": risk_result["score"],
                "risk_level": risk_result["risk_level"],
                "contributing_factors": risk_result["contributing_factors"]
            }
            db.table("risk_scores").insert(risk_insert_data).execute()
        except Exception as e:
            logging.error(f"Failed to compute or store risk score: {str(e)}")
        
        return BiometricBatchResponse(
            inserted_count=inserted_count,
            reading_ids=reading_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
