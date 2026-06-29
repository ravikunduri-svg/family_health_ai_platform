"""
Family Health Record — FastAPI backend entry point.

Compliance notes:
- All routes require authentication (JWT from Supabase Auth).
- PHI never appears in log messages or error responses.
- Audit log written on every PHI read/write.
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes import members, documents, lab_values, medicines, events, alerts, trends, summary, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Family Health Record API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

# CORS — locked to the configured origin in production
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGIN", "http://localhost:5500").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # HIPAA: Never return PHI in error messages
    log.error("Unhandled exception: %s — %s", type(exc).__name__, exc)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})


# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(members.router, prefix="/api/members", tags=["members"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(lab_values.router, prefix="/api/lab-values", tags=["lab-values"])
app.include_router(medicines.router, prefix="/api/medicines", tags=["medicines"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
