"""Owner authentication for note management endpoints."""

import os
import secrets

from fastapi import Header, HTTPException


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    configured_key = os.getenv("PEYTZNOTES_ADMIN_KEY")
    if not configured_key:
        raise HTTPException(status_code=503, detail="Owner access is not configured")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, configured_key):
        raise HTTPException(status_code=401, detail="Owner key required")
