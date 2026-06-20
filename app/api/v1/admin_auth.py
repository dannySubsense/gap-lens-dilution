import secrets
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def require_admin_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    key = settings.admin_api_key
    if not key:
        return
    if credentials is None or not secrets.compare_digest(credentials.credentials, key):
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
