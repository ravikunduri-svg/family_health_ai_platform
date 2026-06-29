"""CRUD for family_members. Soft delete only — PHI never hard-deleted."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import MemberCreate, MemberUpdate, MemberResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MemberResponse)
async def create_member(
    payload: MemberCreate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    now = datetime.utcnow().isoformat()
    row = {
        **payload.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    # Convert date to string for Supabase
    if row.get("dob"):
        row["dob"] = str(row["dob"])

    result = db.table("family_members").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create member")

    created = result.data[0]
    audit(db, "create", "family_members", created["id"], created["id"],
          user.id, request.client.host if request.client else None)
    return created


@router.get("", response_model=list[MemberResponse])
async def list_members(
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("family_members").select("*").is_("deleted_at", None).order("created_at").execute()
    audit(db, "read", "family_members", None, None, user.id, request.client.host if request.client else None)
    return result.data or []


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("family_members").select("*").eq("id", str(member_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Member not found")
    audit(db, "read", "family_members", str(member_id), str(member_id),
          user.id, request.client.host if request.client else None)
    return result.data[0]


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "dob" in updates and updates["dob"]:
        updates["dob"] = str(updates["dob"])
    updates["updated_at"] = datetime.utcnow().isoformat()

    result = (
        db.table("family_members")
        .update(updates)
        .eq("id", str(member_id))
        .is_("deleted_at", None)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Member not found")
    audit(db, "update", "family_members", str(member_id), str(member_id),
          user.id, request.client.host if request.client else None)
    return result.data[0]


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    # Soft delete only
    result = (
        db.table("family_members")
        .update({"deleted_at": datetime.utcnow().isoformat()})
        .eq("id", str(member_id))
        .is_("deleted_at", None)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Member not found")
    audit(db, "delete", "family_members", str(member_id), str(member_id),
          user.id, request.client.host if request.client else None)
