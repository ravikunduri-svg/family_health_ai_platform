"""
Extraction orchestrator — dispatches PDF vs image, runs Stage 1 + Stage 2, writes results to DB.
Called as a FastAPI BackgroundTask after upload.

Stage 1: OCR → raw text → regex lab value extraction
Stage 2: Claude AI → medicines + health_events
Stage 3: Alert rule evaluation
"""
import logging
import re
from datetime import date, datetime
from typing import Any, Optional

from database import db
from extraction.pdf_extractor import extract_text_from_pdf
from extraction.image_extractor import extract_text_from_image
from extraction.lab_patterns import LAB_PATTERNS
from extraction.ai_extractor import extract_unstructured
from extraction.alert_rules import generate_alerts_from_lab_values, generate_alerts_from_medicines

log = logging.getLogger(__name__)

# Regex to find the first floating-point / integer value on a line
_VALUE_RE = re.compile(r"\b(\d+\.?\d*)\b")
# Regex to find reference range  e.g.  4.0 - 5.9  or  4.0–5.9  or  (4.0-5.9)
_RANGE_RE = re.compile(r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)")


def process_document(
    document_id: str,
    file_bytes: bytes,
    file_type: str,   # "pdf" or "image"
    member_id: str,
    report_date: Optional[str] = None,
) -> None:
    """
    Full extraction pipeline. Runs in background after upload.
    Updates health_documents.ocr_status as it progresses.
    """
    _set_status(document_id, "processing")
    try:
        # ── Stage 1: OCR ─────────────────────────────────────────────────────
        raw_text = _run_ocr(file_bytes, file_type)
        if not raw_text:
            log.warning("doc %s: OCR returned empty text", document_id)
            _set_status(document_id, "failed")
            return

        # Persist raw text
        db.table("health_documents").update({
            "ocr_raw_text": raw_text,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", document_id).execute()

        # ── Stage 1b: Regex lab value extraction ─────────────────────────────
        lab_rows = _extract_lab_values(raw_text, document_id, member_id, report_date)
        if lab_rows:
            db.table("lab_values").insert(lab_rows).execute()
            log.info("doc %s: extracted %d lab values", document_id, len(lab_rows))

        # ── Stage 2: Claude AI extraction ─────────────────────────────────────
        ai_result = extract_unstructured(raw_text)
        db.table("health_documents").update({
            "ai_extraction": ai_result,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", document_id).execute()

        # Parse AI output → medicines + health_events
        medicine_rows = _parse_medicines(ai_result, document_id, member_id, report_date)
        if medicine_rows:
            db.table("medicines").insert(medicine_rows).execute()
            log.info("doc %s: extracted %d medicines", document_id, len(medicine_rows))

        event_rows = _parse_events(ai_result, document_id, member_id, report_date)
        if event_rows:
            db.table("health_events").insert(event_rows).execute()
            log.info("doc %s: extracted %d health events", document_id, len(event_rows))

        # ── Stage 3: Alert rules ───────────────────────────────────────────────
        lab_alerts = generate_alerts_from_lab_values(lab_rows, member_id)
        med_alerts = generate_alerts_from_medicines(medicine_rows, member_id)
        all_alerts = lab_alerts + med_alerts
        if all_alerts:
            db.table("alerts").insert(all_alerts).execute()
            log.info("doc %s: generated %d alerts", document_id, len(all_alerts))

        _set_status(document_id, "done")

    except Exception as exc:
        import traceback
        log.error("doc %s extraction failed: %s — %s\n%s", document_id, type(exc).__name__, exc, traceback.format_exc())
        _set_status(document_id, "failed")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_status(document_id: str, status: str) -> None:
    db.table("health_documents").update({
        "ocr_status": status,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", document_id).execute()


def _run_ocr(file_bytes: bytes, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_bytes)
    if file_type == "text":
        # Reprocess path: raw text already extracted, passed as bytes
        return file_bytes.decode("utf-8", errors="replace")
    return extract_text_from_image(file_bytes)


def _extract_lab_values(
    raw_text: str,
    document_id: str,
    member_id: str,
    report_date: Optional[str],
) -> list[dict[str, Any]]:
    """
    For each line in raw_text, try each lab pattern.
    If alias matches the line, extract the first numeric value and optional reference range.
    """
    lines = raw_text.lower().splitlines()
    matched_tests: set[str] = set()
    results: list[dict[str, Any]] = []

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        for pattern in LAB_PATTERNS:
            test_name = pattern["test_name"]
            if test_name in matched_tests:
                continue  # already found this test in this document

            matched = any(alias.lower() in line_stripped for alias in pattern["aliases"])
            if not matched:
                continue

            # Find all numeric values on this line
            nums = _VALUE_RE.findall(line_stripped)
            if not nums:
                continue

            # First numeric is the measured value; ignore if it looks like a ratio
            value = float(nums[0])

            # Try to find reference range on same line
            ref_low: Optional[float] = pattern.get("ref_low")
            ref_high: Optional[float] = pattern.get("ref_high")
            range_match = _RANGE_RE.search(line_stripped)
            if range_match:
                try:
                    ref_low = float(range_match.group(1))
                    ref_high = float(range_match.group(2))
                except ValueError:
                    pass

            is_abnormal = None
            if ref_low is not None and ref_high is not None:
                is_abnormal = not (ref_low <= value <= ref_high)

            results.append({
                "document_id": document_id,
                "member_id": member_id,
                "test_name": test_name,
                "display_name": pattern["aliases"][0].title(),
                "value": value,
                "unit": pattern.get("unit"),
                "reference_low": ref_low,
                "reference_high": ref_high,
                "is_abnormal": is_abnormal,
                "report_date": report_date,
            })
            matched_tests.add(test_name)

    return results


def _parse_medicines(
    ai_result: dict[str, Any],
    document_id: str,
    member_id: str,
    report_date: Optional[str],
) -> list[dict[str, Any]]:
    rows = []
    for med in ai_result.get("medicines") or []:
        brand = med.get("brand") or ""
        generic = med.get("generic") or ""
        if not brand and not generic:
            continue
        rows.append({
            "document_id": document_id,
            "member_id": member_id,
            "brand_name": brand or None,
            "generic_name": generic or None,
            "dosage": med.get("dose"),
            "frequency": med.get("frequency"),
            "prescribed_date": report_date,
            "prescribed_by": ai_result.get("doctor"),
            "is_active": True,
        })
    return rows


def _parse_events(
    ai_result: dict[str, Any],
    document_id: str,
    member_id: str,
    report_date: Optional[str],
) -> list[dict[str, Any]]:
    rows = []
    for diagnosis in ai_result.get("diagnoses") or []:
        if not diagnosis:
            continue
        rows.append({
            "document_id": document_id,
            "member_id": member_id,
            "event_type": "diagnosis",
            "title": diagnosis,
            "event_date": ai_result.get("dates", {}).get("report") or report_date,
            "doctor_name": ai_result.get("doctor"),
            "facility_name": ai_result.get("facility"),
        })
    for procedure in ai_result.get("procedures") or []:
        if not procedure:
            continue
        rows.append({
            "document_id": document_id,
            "member_id": member_id,
            "event_type": "procedure",
            "title": procedure,
            "event_date": ai_result.get("dates", {}).get("report") or report_date,
            "doctor_name": ai_result.get("doctor"),
            "facility_name": ai_result.get("facility"),
        })
    return rows
