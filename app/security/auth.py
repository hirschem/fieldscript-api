from typing import Optional
from pydantic import BaseModel
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from app.deps.stores import get_api_key_store
from app.schemas.api_key import ProjectApiKey
from app.security.api_keys import verify_api_key_allow_revoked

# Dependency for revoke endpoint: allows revoked keys to authenticate for idempotency
def require_api_key_for_revoke(
    project_id: str,
    request: Request,
    store = Depends(get_api_key_store)
) -> 'AuthContext':
    raw_key = extract_api_key(request)
    request_id = getattr(request.state, "request_id", None)
    if not raw_key:
        body = {"error": "unauthorized", "message": "Missing or invalid API key"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(
            status_code=401,
            detail=body,
            headers={"WWW-Authenticate": "Bearer"}
        )
    record: ProjectApiKey = verify_api_key_allow_revoked(raw_key, project_id)
    if not record:
        body = {"error": "unauthorized", "message": "Missing or invalid API key"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(
            status_code=401,
            detail=body,
            headers={"WWW-Authenticate": "Bearer"}
        )
    if record.project_id != project_id:
        body = {"error": "forbidden", "message": "API key does not have access to this project"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(status_code=403, detail=body)
    ctx = AuthContext(project_id=record.project_id, api_key_id=record.id, key_fingerprint=record.key_fingerprint)
    request.state.auth = ctx
    return ctx
from app.deps.stores import get_api_key_store
from app.schemas.api_key import ProjectApiKey
from fastapi import Depends

class AuthContext(BaseModel):
    project_id: str
    api_key_id: str
    key_fingerprint: str


def extract_api_key(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        key = auth[7:].strip()
        if key:
            return key
    key2 = request.headers.get("x-api-key")
    if key2 and key2.strip():
        return key2.strip()
    return None


def require_api_key(
    request: Request,
    expected_project_id: Optional[str] = None,
    store = Depends(get_api_key_store)
) -> AuthContext:
    raw_key = extract_api_key(request)
    request_id = getattr(request.state, "request_id", None)
    if not raw_key:
        body = {"error": "unauthorized", "message": "Missing or invalid API key"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(
            status_code=401,
            detail=body,
            headers={"WWW-Authenticate": "Bearer"}
        )
    record: ProjectApiKey = store.verify(raw_key)
    if not record:
        body = {"error": "unauthorized", "message": "Missing or invalid API key"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(
            status_code=401,
            detail=body,
            headers={"WWW-Authenticate": "Bearer"}
        )
    if expected_project_id and record.project_id != expected_project_id:
        body = {"error": "forbidden", "message": "API key does not have access to this project"}
        if request_id:
            body["request_id"] = request_id
        raise HTTPException(status_code=403, detail=body)
    ctx = AuthContext(project_id=record.project_id, api_key_id=record.id, key_fingerprint=record.key_fingerprint)
    request.state.auth = ctx
    return ctx

# FastAPI dependency for project-scoped routes
# Only enforce project_id from path params in dependency/middleware. For body-based project_id, enforce inside handler or use a dependency that caches body bytes on request.state.
def require_api_key_dep(
    project_id: str,
    request: Request,
    store = Depends(get_api_key_store)
) -> AuthContext:
    return require_api_key(request, expected_project_id=project_id, store=store)
