"""Upload, list, and manage health documents. Triggers extraction pipeline on upload."""
import io
import os
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import DocumentDetail, DocumentSummary
from extraction.extractor import process_document

router = APIRouter()

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/jpg", "image/webp"}
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    member_id: str = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    report_date: Optional[str] = Form(None),
    facility_name: Optional[str] = Form(None),
    doctor_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, JPG, or PNG.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    file_type = "pdf" if file.content_type == "application/pdf" else "image"
    doc_id = str(uuid.uuid4())
    ext = "pdf" if file_type == "pdf" else file.filename.rsplit(".", 1)[-1].lower()
    storage_path = f"{member_id}/{doc_id}.{ext}"

    # Store in Supabase Storage
    try:
        db.storage.from_("health-docs").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="File storage failed") from exc

    file_url = db.storage.from_("health-docs").get_public_url(storage_path)

    now = datetime.utcnow().isoformat()
    row = {
        "id": doc_id,
        "member_id": member_id,
        "document_type": document_type,
        "title": title,
        "file_url": file_url,
        "file_type": file_type,
        "report_date": report_date,
        "facility_name": facility_name,
        "doctor_name": doctor_name,
        "notes": notes,
        "ocr_status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    result = db.table("health_documents").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save document record")

    audit(db, "upload", "health_documents", doc_id, member_id,
          user.id, request.client.host if request.client else None)

    # Kick off extraction in background
    background_tasks.add_task(
        process_document,
        document_id=doc_id,
        file_bytes=file_bytes,
        file_type=file_type,
        member_id=member_id,
        report_date=report_date,
    )

    return {"id": doc_id, "ocr_status": "pending"}


@router.get("", response_model=list[DocumentSummary])
async def list_documents(
    request: Request,
    member_id: Optional[str] = None,
    document_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    query = (
        db.table("health_documents")
        .select("id,member_id,document_type,title,file_url,file_type,report_date,facility_name,doctor_name,ocr_status,created_at")
        .is_("deleted_at", None)
        .order("report_date", desc=True)
    )
    if member_id:
        query = query.eq("member_id", member_id)
    if document_type:
        query = query.eq("document_type", document_type)
    if date_from:
        query = query.gte("report_date", date_from)
    if date_to:
        query = query.lte("report_date", date_to)
    if q:
        query = query.ilike("title", f"%{q}%")

    result = query.execute()
    audit(db, "read", "health_documents", None, member_id, user.id,
          request.client.host if request.client else None, {"q": q})
    return result.data or []


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(
    doc_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("health_documents").select("*").eq("id", str(doc_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = result.data[0]

    # Fetch child records
    labs = db.table("lab_values").select("id,test_name,display_name,value,unit,reference_low,reference_high,is_abnormal").eq("document_id", str(doc_id)).execute()
    meds = db.table("medicines").select("id,brand_name,generic_name,dosage,frequency,duration_days,is_active").eq("document_id", str(doc_id)).execute()
    evts = db.table("health_events").select("id,event_type,title,event_date,doctor_name").eq("document_id", str(doc_id)).is_("deleted_at", None).execute()

    audit(db, "read", "health_documents", str(doc_id), doc.get("member_id"),
          user.id, request.client.host if request.client else None)

    return {
        **doc,
        "lab_values": labs.data or [],
        "medicines": meds.data or [],
        "events": evts.data or [],
    }


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("health_documents").select("member_id,file_url").eq("id", str(doc_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = result.data[0]

    db.table("health_documents").update({
        "deleted_at": datetime.utcnow().isoformat()
    }).eq("id", str(doc_id)).execute()

    audit(db, "delete", "health_documents", str(doc_id), doc.get("member_id"),
          user.id, request.client.host if request.client else None)


@router.post("/{doc_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(
    doc_id: UUID,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    result = db.table("health_documents").select("member_id,file_url,file_type,report_date,ocr_raw_text").eq("id", str(doc_id)).is_("deleted_at", None).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = result.data[0]

    if not doc.get("ocr_raw_text"):
        raise HTTPException(status_code=400, detail="No OCR text available — re-upload the file")

    # Delete existing child extractions before reprocessing
    db.table("lab_values").delete().eq("document_id", str(doc_id)).execute()
    db.table("medicines").delete().eq("document_id", str(doc_id)).execute()
    db.table("health_events").update({"deleted_at": datetime.utcnow().isoformat()}).eq("document_id", str(doc_id)).execute()

    audit(db, "reprocess", "health_documents", str(doc_id), doc.get("member_id"),
          user.id, request.client.host if request.client else None)

    # Re-run only AI extraction (raw text already in DB)
    from extraction.extractor import process_document
    background_tasks.add_task(
        process_document,
        document_id=str(doc_id),
        file_bytes=doc["ocr_raw_text"].encode(),  # signal: raw text mode
        file_type="text",
        member_id=doc["member_id"],
        report_date=doc.get("report_date"),
    )
    return {"id": str(doc_id), "status": "reprocessing"}
