"""Alert listing and acknowledgment endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user
from app.core.supabase_client import get_supabase
from app.schemas.alerts import AlertResponse, AlertListResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/{user_id}", response_model=AlertListResponse)
def list_alerts(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_supabase),
):
    """Lists all alerts for a user, most recent first.
    TODO: restrict to self or linked family/health_worker once user_contacts is built."""
    result = (
        db.table("alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("sent_at", desc=True)
        .execute()
    )
    return AlertListResponse(alerts=result.data or [])


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_supabase),
):
    """Marks an alert as acknowledged."""
    existing = db.table("alerts").select("*").eq("id", alert_id).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    result = (
        db.table("alerts")
        .update({"acknowledged": True})
        .eq("id", alert_id)
        .execute()
    )
    return result.data[0]