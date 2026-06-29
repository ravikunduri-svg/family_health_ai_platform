# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**AI-Powered Family Health Operating System.** Turns scattered Indian medical records into a longitudinal health timeline with AI extraction, trend charts, doctor-ready summaries, and rule-based alerts.

Stack: Python FastAPI backend · Supabase (PostgreSQL + Storage + Auth) · Plain HTML/CSS/JS frontend · Chart.js · pdfplumber + pytesseract · Claude API (haiku) for AI extraction.

## Build & Run

### Local dev

```bash
# 1. Copy env template and fill in values
cp backend/.env.example backend/.env

# 2. Copy frontend config and fill in values
cp frontend/js/config.example.js frontend/js/config.js

# 3. Install Python deps (Python 3.11+)
pip install -r backend/requirements.txt

# 4. Install Tesseract OCR
# Windows: choco install tesseract
# Linux:   apt-get install -y tesseract-ocr

# 5. Run SQL migration in Supabase SQL Editor
# Open: https://supabase.com/dashboard → SQL Editor → paste migrations/001_init.sql

# 6. Create storage bucket 'health-docs' in Supabase Storage

# 7. Start backend
cd backend
uvicorn main:app --reload --port 8000

# 8. Open frontend with VS Code Live Server or similar
# Frontend is static HTML — no build step needed
```

### Phase 0 validation (REQUIRED before production)

```bash
cd backend
python validate_extraction.py /path/to/thyrocare_report.pdf
python validate_extraction.py /path/to/reports/ --ai   # also runs Claude extraction
```

Target: >85% accuracy on lab value extraction from Indian lab reports.

## Architecture

```
GitHub Pages (HTML/CSS/JS)  →  FastAPI on Render  →  Supabase PostgreSQL
                                    |                       |
                              Claude API (haiku)    Supabase Storage
```

**Two-stage extraction pipeline** (runs as FastAPI BackgroundTask after upload):
- Stage 1: pdfplumber/pytesseract → raw text → 40+ regex patterns → `lab_values` rows
- Stage 2: Claude `claude-haiku-4-5-20251001` → diagnoses, medicines, events → `medicines` + `health_events` rows
- Stage 3: Rule-based alert generation → `alerts` rows

## File Structure

```
backend/
  main.py              FastAPI app + CORS + router registration
  auth.py              JWT validation dep + audit() helper
  database.py          Supabase client singleton
  models.py            All Pydantic request/response models
  routes/              9 route modules (members, documents, lab_values, medicines, events, alerts, trends, summary, search)
  extraction/
    extractor.py       Pipeline orchestrator (call this from BackgroundTask)
    lab_patterns.py    40+ Indian lab test regex definitions
    pdf_extractor.py   pdfplumber → raw text
    image_extractor.py pytesseract → raw text
    ai_extractor.py    Claude API call → structured JSON
    alert_rules.py     Rule-based alert generation (threshold + renewal)
  validate_extraction.py  Phase 0 validation script

frontend/
  index.html / *.html  11 pages (no build step)
  css/main.css         All styles
  js/config.example.js → copy to config.js (gitignored)
  js/api.js            Supabase auth + apiFetch wrapper + api.{} methods
  js/*.js              One JS file per page

migrations/
  001_init.sql         Full schema — run once in Supabase SQL Editor
```

## Compliance (Non-Negotiable)

Every feature that touches patient data must satisfy:

- **HIPAA**: PHI never in logs, alerts, or email notifications. Encryption in transit and at rest. Audit trail: append-only `audit_log` table for all PHI access. Minimum necessary data access.
- **GDPR**: No PII in file paths, log messages, or error responses — use UUIDs. All writes to storage need a documented retention policy. Soft delete only (no hard deletes on PHI).
- **SOC 2**: Credentials via env vars / secrets manager only — never hardcoded. Structured logs. All critical paths have error handling.

## Data Model Rules

- Patient identifiers: use internal UUIDs. Never expose SSN or national ID.
- Every PHI table has `created_at`, `updated_at`, `deleted_at` (soft delete only).
- All DB queries go through Supabase client methods — no raw string SQL.
- `SUPABASE_SERVICE_KEY` on backend only. `SUPABASE_ANON_KEY` on frontend only.

## API Rules

- `get_current_user` dependency required on every route.
- `audit()` called on every read or write of a patient record.
- Error responses never include PHI. Generic 500 message only.
- AI extraction disclaimer required in UI on every AI-sourced field.

## Key Decisions

- AI model: `llama-3.3-70b-versatile` via Groq API (free tier; env var: `GROQ_API_KEY`)
- Alert generation: rule-based only — no AI inference in alerts
- No medication interaction check (licensed drug DB required — out of scope v1)
- Reprocess endpoint deletes child records before re-extracting (not additive)

## Output Template (for any significant feature output)

```
# Output: [description]
# Source: [file:line or data source]
# Assumptions: [list or NONE]
# Confidence: High | Medium | Low
# Review gate: [Dev / QA / HIPAA Officer / Change Board]
# Compliance flags: [GDPR | HIPAA | SOC2 | NONE]
```
