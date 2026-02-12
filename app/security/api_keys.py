import os
import base64
import secrets
import hmac
import hashlib
from typing import Optional
from datetime import datetime
from app.schemas.api_key import ProjectApiKey, PROJECT_API_KEYS

API_KEY_PREFIX = "mph_"
API_KEY_LENGTH = 32  # bytes
API_KEY_PREFIX_LEN = 8


def verify_api_key_allow_revoked(raw_key: str, project_id: str) -> Optional[ProjectApiKey]:
    key_hash = hash_api_key(raw_key)
    for api_key in PROJECT_API_KEYS.values():
        if compare_hashes(api_key.key_hash, key_hash) and api_key.project_id == project_id:
            return api_key
    return None
import os
import base64
import secrets
import hmac
import hashlib
from typing import Optional
from datetime import datetime
from app.schemas.api_key import ProjectApiKey, PROJECT_API_KEYS

API_KEY_PREFIX = "mph_"
API_KEY_LENGTH = 32  # bytes
API_KEY_PREFIX_LEN = 8


def get_pepper() -> str:
    val = os.getenv("API_KEY_PEPPER")
    if val:
        return val
    # Allow fallback for tests only
    if "PYTEST_CURRENT_TEST" in os.environ:
        return "test_pepper"
    raise RuntimeError("API_KEY_PEPPER env var is required for API key operations.")


def generate_api_key() -> str:
    raw = secrets.token_urlsafe(API_KEY_LENGTH)
    # Remove padding, ensure prefix
    raw = raw.rstrip("=")
    return f"{API_KEY_PREFIX}{raw}"


def key_prefix(raw_key: str, n: int = API_KEY_PREFIX_LEN) -> str:
    return raw_key[:n]


def hash_api_key(raw_key: str) -> str:
    pepper = get_pepper().encode()
    h = hmac.new(pepper, raw_key.encode(), hashlib.sha256)
    return h.hexdigest()


def compare_hashes(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def store_api_key(project_id: str, raw_key: str, name: Optional[str] = None) -> ProjectApiKey:
    prefix = key_prefix(raw_key)
    key_hash = hash_api_key(raw_key)
    key_fingerprint = key_hash[-8:] if key_hash else ""
    api_key = ProjectApiKey(
        project_id=project_id,
        key_prefix=prefix,
        key_hash=key_hash,
        key_fingerprint=key_fingerprint,
        name=name,
        created_at=datetime.utcnow(),
        last_used_at=None,
        revoked_at=None
    )
    PROJECT_API_KEYS[api_key.id] = api_key
    return api_key


def verify_api_key(raw_key: str) -> Optional[ProjectApiKey]:
    key_hash = hash_api_key(raw_key)
    for api_key in PROJECT_API_KEYS.values():
        if api_key.revoked_at is not None:
            continue
        if compare_hashes(api_key.key_hash, key_hash):
            # Best-effort update last_used_at
            try:
                api_key.last_used_at = datetime.utcnow()
            except Exception:
                pass
            return api_key
    return None
