from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.security.auth import require_api_key_dep, require_api_key_for_revoke, AuthContext
from app.security.api_keys import generate_api_key
from app.deps.stores import get_api_key_store
from fastapi import Depends
from app.schemas.api_key_endpoints import (
    ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyPublic, ApiKeyListResponse, ApiKeyRevokeResponse
)
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/projects/{project_id}/api-keys", tags=["api-keys"])



@router.post("", response_model=ApiKeyCreateResponse)
def create_api_key(
    project_id: str,
    req: ApiKeyCreateRequest,
    request: Request,
    auth: AuthContext = Depends(require_api_key_dep),
    store = Depends(get_api_key_store)
):
    raw_key, api_key = store.create(project_id, req.name)
    return ApiKeyCreateResponse(
        api_key=raw_key,
        api_key_id=api_key.id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        created_at=api_key.created_at
    )

@router.get("", response_model=ApiKeyListResponse)
def list_api_keys(
    project_id: str,
    auth: AuthContext = Depends(require_api_key_dep),
    store = Depends(get_api_key_store)
):
    keys = store.list(project_id)
    items = [
        ApiKeyPublic(
            api_key_id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            revoked_at=k.revoked_at
        ) for k in keys
    ]
    return ApiKeyListResponse(items=items)

@router.post("/{key_id}/revoke", response_model=ApiKeyRevokeResponse)
def revoke_api_key(
    project_id: str,
    key_id: str,
    auth: AuthContext = Depends(require_api_key_for_revoke),
    store = Depends(get_api_key_store)
):
    key = store.revoke(project_id, key_id)
    if not key:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "API key not found"})
    return ApiKeyRevokeResponse(api_key_id=key.id, revoked_at=key.revoked_at)
