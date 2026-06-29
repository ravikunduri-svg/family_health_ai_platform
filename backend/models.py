"""Pydantic v2 request/response models. No PHI in field names or log messages."""
from __future__ import annotations
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# family_members
# ─────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    relationship: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    relationship: Optional[str] = None
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None
    notes: Optional[str] = None


class MemberResponse(BaseModel):
    id: UUID
    name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    relationship: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────
# health_documents
# ─────────────────────────────────────────────────────────────

class DocumentSummary(BaseModel):
    id: UUID
    member_id: UUID
    document_type: str
    title: str
    file_url: str
    file_type: Optional[str] = None
    report_date: Optional[date] = None
    facility_name: Optional[str] = None
    doctor_name: Optional[str] = None
    ocr_status: str
    created_at: datetime


class LabValueInDocument(BaseModel):
    id: UUID
    test_name: str
    display_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    is_abnormal: Optional[bool] = None


class MedicineInDocument(BaseModel):
    id: UUID
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    is_active: bool = True


class EventInDocument(BaseModel):
    id: UUID
    event_type: str
    title: str
    event_date: Optional[date] = None
    doctor_name: Optional[str] = None


class DocumentDetail(BaseModel):
    id: UUID
    member_id: UUID
    document_type: str
    title: str
    file_url: str
    file_type: Optional[str] = None
    report_date: Optional[date] = None
    facility_name: Optional[str] = None
    doctor_name: Optional[str] = None
    notes: Optional[str] = None
    ocr_status: str
    ai_extraction: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    lab_values: list[LabValueInDocument] = Field(default_factory=list)
    medicines: list[MedicineInDocument] = Field(default_factory=list)
    events: list[EventInDocument] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# lab_values
# ─────────────────────────────────────────────────────────────

class LabValueUpdate(BaseModel):
    test_name: Optional[str] = None
    display_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    is_abnormal: Optional[bool] = None


class LabValueResponse(BaseModel):
    id: UUID
    document_id: UUID
    member_id: UUID
    test_name: str
    display_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    is_abnormal: Optional[bool] = None
    report_date: Optional[date] = None
    created_at: datetime


class TrendPoint(BaseModel):
    date: date
    value: float
    unit: Optional[str] = None
    is_abnormal: Optional[bool] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    document_id: UUID


# ─────────────────────────────────────────────────────────────
# medicines
# ─────────────────────────────────────────────────────────────

class MedicineCreate(BaseModel):
    member_id: UUID
    document_id: Optional[UUID] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    prescribed_date: Optional[date] = None
    prescribed_by: Optional[str] = None
    duration_days: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None


class MedicineUpdate(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    prescribed_date: Optional[date] = None
    prescribed_by: Optional[str] = None
    duration_days: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class MedicineResponse(BaseModel):
    id: UUID
    member_id: UUID
    document_id: Optional[UUID] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    prescribed_date: Optional[date] = None
    prescribed_by: Optional[str] = None
    duration_days: Optional[int] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────
# health_events
# ─────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    member_id: UUID
    document_id: Optional[UUID] = None
    event_type: str
    title: str
    event_date: Optional[date] = None
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    event_type: Optional[str] = None
    title: Optional[str] = None
    event_date: Optional[date] = None
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    notes: Optional[str] = None


class EventResponse(BaseModel):
    id: UUID
    member_id: UUID
    document_id: Optional[UUID] = None
    event_type: str
    title: str
    event_date: Optional[date] = None
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────
# alerts
# ─────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: UUID
    member_id: UUID
    alert_type: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_dismissed: bool
    source_doc_id: Optional[UUID] = None
    created_at: datetime


# ─────────────────────────────────────────────────────────────
# summary (doctor handoff)
# ─────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    member: MemberResponse
    active_medicines: list[MedicineResponse]
    recent_lab_abnormals: list[LabValueResponse]
    recent_labs_all: list[LabValueResponse]
    conditions: list[str]         # from chronic_conditions + diagnosed events
    allergies: list[str]
    recent_events: list[EventResponse]
    active_alerts: list[AlertResponse]
    generated_at: datetime


# ─────────────────────────────────────────────────────────────
# search
# ─────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    entity_type: str              # document/medicine/event/lab_value
    id: UUID
    member_id: UUID
    title: str
    snippet: Optional[str] = None
    date: Optional[date] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
