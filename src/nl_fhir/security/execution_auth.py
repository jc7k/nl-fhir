"""Explicit authorization for writes to the configured FHIR server."""

import secrets
from typing import Optional

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..config import settings


def require_fhir_execution(credentials: Optional[HTTPAuthorizationCredentials]) -> None:
    """A dedicated bearer credential grants FHIR execution capability only."""
    configured = settings.fhir_execution_token
    if configured is None or not configured.get_secret_value():
        raise HTTPException(503, "FHIR execution is disabled: no execution token configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Bearer authentication required", headers={"WWW-Authenticate": "Bearer"})
    if not secrets.compare_digest(
        credentials.credentials.encode("utf-8"), configured.get_secret_value().encode("utf-8")
    ):
        raise HTTPException(403, "Not authorized to execute FHIR bundles")
