from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Any
from app.dependencies import get_current_user
from app.core.supabase_client import get_supabase
from app.schemas.risk import RiskScoreResponse, RiskHistoryResponse

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/{user_id}/current", response_model=RiskScoreResponse)
async def get_current_risk(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    # TODO: Add authorization check: a user can only view their own risk data 
    # unless their role is 'family' or 'health_worker' AND they're linked via user_contacts.
    # For now, let any authenticated user query any user_id.

    response = db.table("risk_scores").select("*").eq("user_id", user_id).order("computed_at", desc=True).limit(1).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="No risk score found for user")
        
    return RiskScoreResponse(**response.data[0])

@router.get("/{user_id}/history", response_model=RiskHistoryResponse)
async def get_risk_history(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    # TODO: Add authorization check: a user can only view their own risk data 
    # unless their role is 'family' or 'health_worker' AND they're linked via user_contacts.
    # For now, let any authenticated user query any user_id.

    response = db.table("risk_scores").select("*").eq("user_id", user_id).order("computed_at", desc=True).execute()
    
    scores = [RiskScoreResponse(**row) for row in response.data]
    return RiskHistoryResponse(scores=scores)
