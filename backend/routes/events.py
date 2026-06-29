"""CRUD for health_events — timeline entries per family member."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import EventCreate, EventUpdate, EventResponse

router = APIRouter()


@router.get("", response_model=list[EventResponse])
async def list_events(
    request: Request,
    member_id: str | None = None,
    event_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    query = (
        db.table("health_events")
        .select("*")
        .is_("deleted_at", None)
        .order("event_date", desc=True)
    )
    if member_id:
        query = query.eq("member_id", member_id)
    if event_type:
        query = query.eq("event_type", event_type)
    if date_from:
        query = query.gte("event_date", date_from)
    if date_to:
        query = query.lte("event_date", date_to)

    result = query.execute()
    audit(db, "read", "health_events", None, member_id, user.id,
          request.client.host if request.client else None)
    return result.data or []


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
async def create_event(
    payload: EventCreate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    now = datetime.utcnow().isoformat()
    row = payload.model_dump()
    row["member_id"] = str(row["member_id"])
    if row.get("document_id"):
        row["document_id"] = str(row["document_id"])
    if row.get("event_date"):
        row["event_date"] = str(row["event_date"])
    row["created_at"] = now
    row["updated_at"] = now

    result = db.table("health_events").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create event")
    created = result.data[0]
    audit(db, "create", "health_events", created["id"], created["member_id"],
          user.id, request.client.host if request.client else None)
    return created


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    payload: EventUpdate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "event_date" in updates and updates["event_date"]:
        updates["event_date"] = str(updates["event_date"])
    updates["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("health_events").update(updates).eq("id", str(event_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Event not found")
    row = result.data[0]
    audit(db, "update", "health_events", str(event_id), row.get("member_id"),
          user.id, request.client.host if request.client else None)
    return row


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("health_events").select("member_id").eq("id", str(event_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Event not found")
    member_id = result.data[0].get("member_id")
    db.table("health_events").update({"deleted_at": datetime.utcnow().isoformat()}).eq("id", str(event_id)).execute()
    audit(db, "delete", "health_events", str(event_id), member_id, user.id,
          request.client.host if request.client else None)
