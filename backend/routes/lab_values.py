"""CRUD for lab_values — manual correction of extracted values."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import LabValueResponse, LabValueUpdate

router = APIRouter()


@router.get("", response_model=list[LabValueResponse])
async def list_lab_values(
    request: Request,
    member_id: str | None = None,
    test_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.table("lab_values").select("*").order("report_date", desc=True)
    if member_id:
        query = query.eq("member_id", member_id)
    if test_name:
        query = query.eq("test_name", test_name)
    if date_from:
        query = query.gte("report_date", date_from)
    if date_to:
        query = query.lte("report_date", date_to)

    result = query.execute()
    audit(db, "read", "lab_values", None, member_id, user.id,
          request.client.host if request.client else None)
    return result.data or []


@router.put("/{lab_id}", response_model=LabValueResponse)
async def update_lab_value(
    lab_id: UUID,
    payload: LabValueUpdate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.table("lab_values").update(updates).eq("id", str(lab_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lab value not found")
    row = result.data[0]
    audit(db, "update", "lab_values", str(lab_id), row.get("member_id"),
          user.id, request.client.host if request.client else None)
    return row


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_value(
    lab_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("lab_values").select("member_id").eq("id", str(lab_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lab value not found")
    member_id = result.data[0].get("member_id")

    db.table("lab_values").delete().eq("id", str(lab_id)).execute()
    audit(db, "delete", "lab_values", str(lab_id), member_id, user.id,
          request.client.host if request.client else None)
