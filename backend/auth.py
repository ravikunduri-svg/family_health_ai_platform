"""JWT auth dependency — validates Supabase access tokens on every route."""
import logging
from fastapi import Depends, HTTPException, Header, Request
from supabase import Client
from database import get_db

log = logging.getLogger(__name__)


async def get_current_user(
    authorization: str = Header(...),
    db: Client = Depends(get_db),
):
    """
    Validates the Bearer token from Supabase Auth.
    Returns the Supabase user object.
    Raises 401 if token is missing, malformed, or expired.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    try:
        response = db.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.user
    except HTTPException:
        raise
    except Exception:
        # Do not leak any auth error details — treat all failures as 401
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def audit(
    db: Client,
    action: str,
    entity_type: str,
    entity_id: str | None,
    member_id: str | None,
    user_id: str | None,
    client_ip: str | None,
    extra: dict | None = None,
) -> None:
    """
    Append-only audit log write. Never raises — failures are logged but do not block the request.
    """
    try:
        db.table("audit_log").insert({
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "member_id": member_id,
            "user_id": user_id,
            "client_ip": client_ip,
            "extra": extra,
        }).execute()
    except Exception as exc:
        log.error("audit_log write failed: %s", exc)
