import os
import pytest
from app.db.session import SessionLocal
from app.stores.sql_api_keys import SqlApiKeyStore
from app.security.api_keys import generate_api_key
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="No DATABASE_URL set; skipping DB smoke test.")

def test_sql_api_key_store_smoke():
    project_id = f"test-proj-{uuid.uuid4()}"
    # Create
    db = SessionLocal()
    store = SqlApiKeyStore(db)
    raw_key, rec = store.create(project_id, name="smoke")
    assert rec.project_id == project_id
    # Verify
    found = store.verify(raw_key)
    assert found is not None
    assert found.id == rec.id
    # List
    keys = store.list(project_id)
    assert any(k.id == rec.id for k in keys)
    db.close()
    # New session, check persistence
    db2 = SessionLocal()
    store2 = SqlApiKeyStore(db2)
    found2 = store2.verify(raw_key)
    assert found2 is not None
    # Revoke
    revoked = store2.revoke(project_id, rec.id)
    assert revoked.revoked_at is not None
    # After revoke, verify returns None
    assert store2.verify(raw_key) is None
    db2.close()
