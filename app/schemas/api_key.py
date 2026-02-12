from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ProjectApiKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    key_prefix: str  # first 8 chars of the key
    key_hash: str  # full hash for in-memory/test logic
    key_fingerprint: str  # last 8 chars of key_hash
    name: Optional[str] = None  # label like "prod", "dev"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

# In-memory store for dev/demo (replace with DB/ORM in production)
PROJECT_API_KEYS = {}

# Example interface for future DB migration:
# def save_api_key(api_key: ProjectApiKey): ...
# def get_api_key_by_prefix(prefix: str): ...
# def get_api_key_by_id(key_id: str): ...
# def list_api_keys_for_project(project_id: str): ...
# def revoke_api_key(key_id: str): ...
