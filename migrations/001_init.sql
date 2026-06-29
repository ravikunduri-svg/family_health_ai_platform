-- Family Health Record — Initial Schema
-- Run this in the Supabase SQL Editor ONCE to set up all tables.
-- All PHI tables use soft deletes (deleted_at). No hard deletes on PHI.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────
-- family_members
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    dob DATE,
    gender TEXT,
    blood_type TEXT,
    relationship TEXT,          -- self/spouse/parent/child/sibling/other
    allergies TEXT[] DEFAULT '{}',
    chronic_conditions TEXT[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ      -- NULL = active; soft delete only
);

-- ─────────────────────────────────────────────────────────────────
-- health_documents
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES family_members(id),
    document_type TEXT NOT NULL,  -- blood_report/prescription/imaging/vaccination/other
    title TEXT NOT NULL,
    file_url TEXT NOT NULL,       -- Supabase Storage URL
    file_type TEXT,               -- pdf/image
    report_date DATE,
    facility_name TEXT,
    doctor_name TEXT,
    notes TEXT,
    ocr_status TEXT NOT NULL DEFAULT 'pending',  -- pending/processing/done/failed/done_no_ai
    ocr_raw_text TEXT,            -- full extracted text (retained for re-processing)
    ai_extraction JSONB,          -- raw Claude output
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ        -- soft delete
);

-- ─────────────────────────────────────────────────────────────────
-- lab_values
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_values (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES health_documents(id),
    member_id UUID NOT NULL REFERENCES family_members(id),  -- denormalized for trend queries
    test_name TEXT NOT NULL,      -- normalized name, e.g. "HbA1c"
    display_name TEXT,            -- as it appeared in the report
    value NUMERIC,
    unit TEXT,
    reference_low NUMERIC,
    reference_high NUMERIC,
    is_abnormal BOOLEAN,
    report_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- No soft delete: incorrect extractions are simply deleted; no PHI in lab_values metadata
);

-- ─────────────────────────────────────────────────────────────────
-- medicines
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medicines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES health_documents(id),  -- null if added manually
    member_id UUID NOT NULL REFERENCES family_members(id),
    brand_name TEXT,
    generic_name TEXT,
    dosage TEXT,
    frequency TEXT,
    prescribed_date DATE,
    prescribed_by TEXT,
    duration_days INT,            -- null = ongoing / unknown
    is_active BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- health_events
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES family_members(id),
    document_id UUID REFERENCES health_documents(id),  -- null if added manually
    event_type TEXT NOT NULL,     -- diagnosis/procedure/hospitalization/vaccination/symptom/followup
    title TEXT NOT NULL,
    event_date DATE,
    doctor_name TEXT,
    facility_name TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ        -- soft delete
);

-- ─────────────────────────────────────────────────────────────────
-- alerts
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES family_members(id),
    alert_type TEXT NOT NULL,     -- overdue_test/trend_warning/medicine_renewal/followup/abnormal_value
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE,
    is_dismissed BOOLEAN NOT NULL DEFAULT false,
    source_doc_id UUID REFERENCES health_documents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- audit_log  (HIPAA: append-only, tamper-evident)
-- No UPDATE or DELETE routes exist for this table.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action TEXT NOT NULL,         -- read/create/update/delete/upload/extract
    entity_type TEXT NOT NULL,    -- family_members/health_documents/lab_values/medicines/health_events/alerts
    entity_id UUID,
    member_id UUID,               -- which family member's data was accessed
    user_id TEXT,                 -- Supabase auth user ID
    client_ip TEXT,
    extra JSONB,                  -- any additional context (e.g. search query, field changed)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- Indexes for common query patterns
-- ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_health_documents_member_id ON health_documents(member_id);
CREATE INDEX IF NOT EXISTS idx_health_documents_report_date ON health_documents(report_date);
CREATE INDEX IF NOT EXISTS idx_lab_values_member_test ON lab_values(member_id, test_name);
CREATE INDEX IF NOT EXISTS idx_lab_values_report_date ON lab_values(report_date);
CREATE INDEX IF NOT EXISTS idx_medicines_member_active ON medicines(member_id, is_active);
CREATE INDEX IF NOT EXISTS idx_health_events_member_date ON health_events(member_id, event_date);
CREATE INDEX IF NOT EXISTS idx_alerts_member_dismissed ON alerts(member_id, is_dismissed);
CREATE INDEX IF NOT EXISTS idx_audit_log_member ON audit_log(member_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

-- Full-text search index on documents
CREATE INDEX IF NOT EXISTS idx_documents_fts ON health_documents
    USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(facility_name, '') || ' ' || coalesce(doctor_name, '') || ' ' || coalesce(ocr_raw_text, '')));
