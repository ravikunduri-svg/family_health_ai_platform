"""Trend data endpoint — returns time series for a single lab test per member."""
from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from auth import get_current_user, audit
from database import get_db
from models import TrendPoint

router = APIRouter()


@router.get("", response_model=list[TrendPoint])
async def get_trend(
    member_id: str,
    test_name: str,
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Client = Depends(get_db),
    user=Depends(get_current_user),
):
    if not member_id or not test_name:
        raise HTTPException(status_code=400, detail="member_id and test_name are required")

    query = (
        db.table("lab_values")
        .select("report_date,value,unit,is_abnormal,reference_low,reference_high,document_id")
        .eq("member_id", member_id)
        .eq("test_name", test_name)
        .not_.is_("report_date", None)
        .not_.is_("value", None)
        .order("report_date")
    )
    if date_from:
        query = query.gte("report_date", date_from)
    if date_to:
        query = query.lte("report_date", date_to)

    result = query.execute()
    audit(db, "read", "lab_values", None, member_id, user.id,
          request.client.host if request.client else None,
          {"test_name": test_name})
    return [
        {
            "date": row["report_date"],
            "value": row["value"],
            "unit": row.get("unit"),
            "is_abnormal": row.get("is_abnormal"),
            "reference_low": row.get("reference_low"),
            "reference_high": row.get("reference_high"),
            "document_id": row["document_id"],
        }
        for row in (result.data or [])
    ]
