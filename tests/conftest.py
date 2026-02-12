
import pytest
from app.security.api_keys import generate_api_key, store_api_key, PROJECT_API_KEYS
from app.deps.stores import get_api_key_store
from app.main import app as fastapi_app
import sys
print("[DEBUG] fastapi_app type:", type(fastapi_app))
print("[DEBUG] has dependency_overrides:", hasattr(fastapi_app, "dependency_overrides"))
mod = sys.modules.get("app")
print("[DEBUG] sys.modules['app']:", mod, "type:", type(mod))
if mod and hasattr(mod, "__file__"):
    print("[DEBUG] sys.modules['app'].__file__:", mod.__file__)
assert hasattr(fastapi_app, "dependency_overrides"), "app.main.app is not the FastAPI instance"

# In-memory API key store for tests
class InMemoryApiKeyStore:
    def create(self, project_id, name=None):
        raw_key = generate_api_key()
        api_key = store_api_key(project_id, raw_key, name=name)
        return raw_key, api_key
    def list(self, project_id):
        return [k for k in PROJECT_API_KEYS.values() if k.project_id == project_id]
    def revoke(self, project_id, key_id):
        key = PROJECT_API_KEYS.get(key_id)
        if not key or key.project_id != project_id:
            return None
        if key.revoked_at is None:
            from datetime import datetime
            key.revoked_at = datetime.utcnow()
        return key
    def verify(self, raw_key):
        from app.security.api_keys import verify_api_key
        return verify_api_key(raw_key)


# Tripwire: fail if SqlApiKeyStore is constructed during tests
import builtins
import types
import pytest
import sys
from app.security.api_keys import generate_api_key, store_api_key, PROJECT_API_KEYS
from app.deps.stores import get_api_key_store
from app.main import app

def _tripwire_sql_api_key_store(*args, **kwargs):
    pytest.fail("SqlApiKeyStore should not be constructed during tests. Use in-memory store only.")

@pytest.fixture(autouse=True)
def override_api_key_store(monkeypatch):
    import app.stores.sql_api_keys
    import app.deps.stores
    # Patch SqlApiKeyStore.__init__ in both modules to fail if constructed
    monkeypatch.setattr(app.stores.sql_api_keys.SqlApiKeyStore, "__init__", lambda self, *a, **kw: pytest.fail("SqlApiKeyStore should not be constructed during tests. Use in-memory store only."))
    monkeypatch.setattr(app.deps.stores.SqlApiKeyStore, "__init__", lambda self, *a, **kw: pytest.fail("SqlApiKeyStore should not be constructed during tests. Use in-memory store only."))
    PROJECT_API_KEYS.clear()
    store = InMemoryApiKeyStore()
    fastapi_app.dependency_overrides[get_api_key_store] = lambda: store
    yield store
    PROJECT_API_KEYS.clear()
    fastapi_app.dependency_overrides.pop(get_api_key_store, None)

# Provide create_project_and_key fixture globally for all tests
@pytest.fixture
def create_project_and_key():
    def _create(project_id="test-proj", name=None):
        raw_key = generate_api_key()
        api_key = store_api_key(project_id, raw_key, name=name)
        return {
            "project_id": project_id,
            "api_key": raw_key,
            "api_key_id": api_key.id
        }
    return _create

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
