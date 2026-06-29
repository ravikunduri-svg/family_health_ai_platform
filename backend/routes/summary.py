"""Doctor handoff summary — aggregates all relevant data for a family member."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import SummaryResponse

router = APIRouter()


@router.get("/{member_id}", response_model=SummaryResponse)
async def get_summary(
    member_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    # Member
    m_res = db.table("family_members").select("*").eq("id", str(member_id)).is_("deleted_at", None).execute()
    if not m_res.data:
        raise HTTPException(status_code=404, detail="Member not found")
    member = m_res.data[0]

    # Active medicines
    med_res = db.table("medicines").select("*").eq("member_id", str(member_id)).eq("is_active", True).order("prescribed_date", desc=True).execute()

    # Recent abnormal lab values (last 90 days)
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=90)).date().isoformat()
    lab_res = (
        db.table("lab_values")
        .select("*")
        .eq("member_id", str(member_id))
        .eq("is_abnormal", True)
        .gte("report_date", cutoff)
        .order("report_date", desc=True)
        .execute()
    )

    # Health events (most recent 20)
    evt_res = (
        db.table("health_events")
        .select("*")
        .eq("member_id", str(member_id))
        .is_("deleted_at", None)
        .order("event_date", desc=True)
        .limit(20)
        .execute()
    )

    # Active alerts
    alert_res = (
        db.table("alerts")
        .select("*")
        .eq("member_id", str(member_id))
        .eq("is_dismissed", False)
        .order("created_at", desc=True)
        .execute()
    )

    # Derive conditions: chronic_conditions from member + diagnosis events
    conditions = list(member.get("chronic_conditions") or [])
    for evt in (evt_res.data or []):
        if evt.get("event_type") == "diagnosis" and evt.get("title") not in conditions:
            conditions.append(evt["title"])

    audit(db, "read", "family_members", str(member_id), str(member_id),
          user.id, request.client.host if request.client else None, {"action": "summary"})

    return {
        "member": member,
        "active_medicines": med_res.data or [],
        "recent_lab_abnormals": lab_res.data or [],
        "conditions": conditions,
        "allergies": list(member.get("allergies") or []),
        "recent_events": evt_res.data or [],
        "active_alerts": alert_res.data or [],
        "generated_at": datetime.utcnow(),
    }
