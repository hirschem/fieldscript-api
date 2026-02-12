from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ApiKeyCreateRequest(BaseModel):
    name: Optional[str] = None

class ApiKeyCreateResponse(BaseModel):
    api_key: str
    api_key_id: str
    key_prefix: str
    name: Optional[str] = None
    created_at: datetime

class ApiKeyPublic(BaseModel):
    api_key_id: str
    key_prefix: str
    name: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyPublic]

class ApiKeyRevokeResponse(BaseModel):
    api_key_id: str
    revoked_at: datetime
