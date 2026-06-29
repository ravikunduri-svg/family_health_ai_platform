"""Full-text search across documents, medicines, events, and lab values."""
from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import SearchResponse, SearchResult

router = APIRouter()


@router.get("", response_model=SearchResponse)
async def search(
    q: str,
    request: Request,
    member_id: str | None = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    q = q.strip()
    results: list[dict] = []

    # Search documents (title, facility_name, doctor_name)
    doc_q = (
        db.table("health_documents")
        .select("id,member_id,title,facility_name,report_date")
        .is_("deleted_at", None)
        .ilike("title", f"%{q}%")
    )
    if member_id:
        doc_q = doc_q.eq("member_id", member_id)
    doc_res = doc_q.limit(20).execute()
    for row in (doc_res.data or []):
        results.append({
            "entity_type": "document",
            "id": row["id"],
            "member_id": row["member_id"],
            "title": row["title"],
            "snippet": row.get("facility_name"),
            "date": row.get("report_date"),
        })

    # Search medicines (brand_name, generic_name)
    med_q = (
        db.table("medicines")
        .select("id,member_id,brand_name,generic_name,prescribed_date")
        .ilike("brand_name", f"%{q}%")
    )
    if member_id:
        med_q = med_q.eq("member_id", member_id)
    med_res = med_q.limit(10).execute()
    for row in (med_res.data or []):
        results.append({
            "entity_type": "medicine",
            "id": row["id"],
            "member_id": row["member_id"],
            "title": row.get("brand_name") or row.get("generic_name") or "Medicine",
            "snippet": row.get("generic_name"),
            "date": row.get("prescribed_date"),
        })

    # Search events (title)
    evt_q = (
        db.table("health_events")
        .select("id,member_id,title,event_type,event_date")
        .is_("deleted_at", None)
        .ilike("title", f"%{q}%")
    )
    if member_id:
        evt_q = evt_q.eq("member_id", member_id)
    evt_res = evt_q.limit(10).execute()
    for row in (evt_res.data or []):
        results.append({
            "entity_type": "event",
            "id": row["id"],
            "member_id": row["member_id"],
            "title": row["title"],
            "snippet": row.get("event_type"),
            "date": row.get("event_date"),
        })

    # Search lab values (test_name)
    lab_q = (
        db.table("lab_values")
        .select("id,member_id,test_name,value,unit,report_date")
        .ilike("test_name", f"%{q}%")
    )
    if member_id:
        lab_q = lab_q.eq("member_id", member_id)
    lab_res = lab_q.limit(10).execute()
    for row in (lab_res.data or []):
        val_str = f"{row.get('value')} {row.get('unit') or ''}".strip() if row.get('value') else None
        results.append({
            "entity_type": "lab_value",
            "id": row["id"],
            "member_id": row["member_id"],
            "title": row["test_name"],
            "snippet": val_str,
            "date": row.get("report_date"),
        })

    audit(db, "read", "search", None, member_id, user.id,
          request.client.host if request.client else None, {"q": q})

    return {"query": q, "results": results, "total": len(results)}
