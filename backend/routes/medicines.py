"""CRUD for medicines — active and past prescriptions."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import MedicineCreate, MedicineUpdate, MedicineResponse

router = APIRouter()


@router.get("", response_model=list[MedicineResponse])
async def list_medicines(
    request: Request,
    member_id: str | None = None,
    is_active: bool | None = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.table("medicines").select("*").order("prescribed_date", desc=True)
    if member_id:
        query = query.eq("member_id", member_id)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    result = query.execute()
    audit(db, "read", "medicines", None, member_id, user.id,
          request.client.host if request.client else None)
    return result.data or []


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MedicineResponse)
async def create_medicine(
    payload: MedicineCreate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    now = datetime.utcnow().isoformat()
    row = payload.model_dump()
    row["member_id"] = str(row["member_id"])
    if row.get("document_id"):
        row["document_id"] = str(row["document_id"])
    if row.get("prescribed_date"):
        row["prescribed_date"] = str(row["prescribed_date"])
    row["created_at"] = now
    row["updated_at"] = now

    result = db.table("medicines").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create medicine record")
    created = result.data[0]
    audit(db, "create", "medicines", created["id"], created["member_id"],
          user.id, request.client.host if request.client else None)
    return created


@router.put("/{med_id}", response_model=MedicineResponse)
async def update_medicine(
    med_id: UUID,
    payload: MedicineUpdate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "prescribed_date" in updates and updates["prescribed_date"]:
        updates["prescribed_date"] = str(updates["prescribed_date"])
    updates["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("medicines").update(updates).eq("id", str(med_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    row = result.data[0]
    audit(db, "update", "medicines", str(med_id), row.get("member_id"),
          user.id, request.client.host if request.client else None)
    return row


@router.delete("/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(
    med_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("medicines").select("member_id").eq("id", str(med_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    member_id = result.data[0].get("member_id")
    db.table("medicines").delete().eq("id", str(med_id)).execute()
    audit(db, "delete", "medicines", str(med_id), member_id, user.id,
          request.client.host if request.client else None)
