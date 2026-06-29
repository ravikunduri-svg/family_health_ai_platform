"""Alerts — read and dismiss only. Generation is in alert_rules.py."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client
from uuid import UUID

from auth import get_current_user, audit
from database import get_db
from models import AlertResponse

router = APIRouter()


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    request: Request,
    member_id: str | None = None,
    include_dismissed: bool = False,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.table("alerts").select("*").order("created_at", desc=True)
    if member_id:
        query = query.eq("member_id", member_id)
    if not include_dismissed:
        query = query.eq("is_dismissed", False)
    result = query.execute()
    audit(db, "read", "alerts", None, member_id, user.id,
          request.client.host if request.client else None)
    return result.data or []


@router.post("/{alert_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_alert(
    alert_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("alerts").select("member_id").eq("id", str(alert_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    member_id = result.data[0].get("member_id")

    db.table("alerts").update({"is_dismissed": True}).eq("id", str(alert_id)).execute()
    audit(db, "update", "alerts", str(alert_id), member_id, user.id,
          request.client.host if request.client else None, {"action": "dismiss"})
    return {"id": str(alert_id), "is_dismissed": True}
