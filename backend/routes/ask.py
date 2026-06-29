"""Natural language health query — answers questions about a member's records using Groq."""
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from auth import get_current_user, audit
from database import get_db

log = logging.getLogger(__name__)
router = APIRouter()

_MODEL = "llama-3.3-70b-versatile"
_MAX_CONTEXT_CHARS = 6000
_MAX_ANSWER_TOKENS = 600


def _build_context(db: Client, member_id: str) -> tuple[str, list[dict]]:
    """Fetch and format member health data into a compact context string."""
    sources: list[dict] = []

    # Member info
    mem = db.table("family_members").select("*").eq("id", member_id).is_("deleted_at", None).execute()
    if not mem.data:
        return "", []
    m = mem.data[0]
    lines = [
        f"Member: {m['name']}" +
        (f" | DOB: {m['dob']}" if m.get("dob") else "") +
        (f" | Blood: {m['blood_type']}" if m.get("blood_type") else ""),
    ]
    if m.get("chronic_conditions"):
        lines.append(f"Chronic conditions: {', '.join(m['chronic_conditions'])}")
    if m.get("allergies"):
        lines.append(f"Allergies: {', '.join(m['allergies'])}")

    # Health events
    evts = (
        db.table("health_events")
        .select("id,event_type,title,event_date,doctor_name,facility_name")
        .eq("member_id", member_id)
        .is_("deleted_at", None)
        .order("event_date", desc=True)
        .limit(50)
        .execute()
    )
    if evts.data:
        lines.append("\n=== HEALTH EVENTS ===")
        for e in evts.data:
            parts = [e.get("event_date") or "?", e.get("event_type") or "", e["title"]]
            if e.get("doctor_name"):
                parts.append(e["doctor_name"])
            if e.get("facility_name"):
                parts.append(e["facility_name"])
            lines.append(" | ".join(p for p in parts if p))
            sources.append({"type": "event", "title": e["title"], "date": e.get("event_date"), "id": e["id"]})

    # Medicines
    meds = (
        db.table("medicines")
        .select("id,brand_name,generic_name,dosage,frequency,prescribed_date,is_active,prescribed_by")
        .eq("member_id", member_id)
        .order("prescribed_date", desc=True)
        .limit(60)
        .execute()
    )
    if meds.data:
        lines.append("\n=== MEDICINES ===")
        for med in meds.data:
            name = med.get("brand_name") or med.get("generic_name") or "Unknown"
            parts = [name]
            if med.get("dosage"):
                parts.append(med["dosage"])
            if med.get("frequency"):
                parts.append(med["frequency"])
            if med.get("prescribed_date"):
                parts.append(f"from {med['prescribed_date']}")
            parts.append("active" if med.get("is_active") else "inactive")
            lines.append(" | ".join(parts))
            sources.append({"type": "medicine", "title": name, "date": med.get("prescribed_date"), "id": med["id"]})

    # Lab values (most recent per test)
    labs = (
        db.table("lab_values")
        .select("id,test_name,value,unit,is_abnormal,report_date")
        .eq("member_id", member_id)
        .order("report_date", desc=True)
        .limit(100)
        .execute()
    )
    if labs.data:
        lines.append("\n=== LAB VALUES ===")
        for lab in labs.data:
            val = f"{lab.get('value')} {lab.get('unit') or ''}".strip()
            flag = " [HIGH/LOW]" if lab.get("is_abnormal") else ""
            lines.append(f"{lab.get('report_date') or '?'} | {lab['test_name']} | {val}{flag}")
            sources.append({"type": "lab_value", "title": lab["test_name"], "date": lab.get("report_date"), "id": lab["id"]})

    # Documents list
    docs = (
        db.table("health_documents")
        .select("id,title,document_type,report_date,facility_name")
        .eq("member_id", member_id)
        .is_("deleted_at", None)
        .order("report_date", desc=True)
        .limit(30)
        .execute()
    )
    if docs.data:
        lines.append("\n=== DOCUMENTS ===")
        for doc in docs.data:
            parts = [doc.get("report_date") or "?", doc.get("document_type") or "", doc["title"]]
            if doc.get("facility_name"):
                parts.append(doc["facility_name"])
            lines.append(" | ".join(p for p in parts if p))
            sources.append({"type": "document", "title": doc["title"], "date": doc.get("report_date"), "id": doc["id"]})

    context = "\n".join(lines)
    return context[:_MAX_CONTEXT_CHARS], sources


def _ask_groq(context: str, question: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured")

    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("groq package not installed")

    prompt = f"""\
You are a personal health assistant. Answer the user's question based strictly on the health records below.

Rules:
- Only use information explicitly present in the records. If the answer is not there, say "I don't have that information in your health records."
- Be specific with dates when available.
- Keep the answer clear and concise — 2 to 4 sentences maximum.
- Do not give clinical advice or diagnoses. End with: "Please consult your doctor for medical decisions."

Health Records:
{context}

Question: {question}

Answer:"""

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=_MODEL,
        max_tokens=_MAX_ANSWER_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content.strip()


@router.get("")
async def ask_health_question(
    q: str,
    member_id: str,
    request: Request,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    if not q or len(q.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question must be at least 3 characters")
    if not member_id:
        raise HTTPException(status_code=400, detail="member_id is required")

    context, sources = _build_context(db, member_id)
    if not context:
        raise HTTPException(status_code=404, detail="Member not found")

    try:
        answer = _ask_groq(context, q.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        log.error("ask_health_question failed: %s — %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail="Failed to generate answer")

    audit(db, "read", "ask", None, member_id, user.id,
          request.client.host if request.client else None, {"q": q})

    # Deduplicate sources by id, keep most relevant (events + medicines first)
    seen = set()
    deduped = []
    for s in sources:
        if s["id"] not in seen:
            seen.add(s["id"])
            deduped.append(s)

    return {"question": q, "answer": answer, "sources": deduped[:10]}
