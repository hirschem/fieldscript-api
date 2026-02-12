import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security.api_keys import generate_api_key, store_api_key

@pytest.fixture
def client(override_api_key_store):
    return TestClient(app)

def test_request_id_added_when_missing(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert resp.headers["x-request-id"]

def test_request_id_preserved_when_provided(client):
    resp = client.get("/version", headers={"x-request-id": "test-req-123"})
    assert resp.status_code == 200
    assert resp.headers["x-request-id"] == "test-req-123"

def test_logs_include_auth_metadata_when_present(client, caplog, create_project_and_key):
    info = create_project_and_key()
    caplog.set_level(logging.INFO, logger="request_log")
    # Use a protected endpoint (list API keys)
    resp = client.get(f"/api/projects/{info['project_id']}/api-keys", headers={"Authorization": f"Bearer {info['api_key']}"})
    assert resp.status_code == 200
    found = False
    for record in caplog.records:
        log = record.msg if isinstance(record.msg, dict) else record.getMessage()
        if isinstance(log, dict):
            d = log
        else:
            try:
                import json
                d = json.loads(log)
            except Exception:
                continue
        if d.get("project_id") == info["project_id"] and d.get("api_key_id") == info["api_key_id"] and d.get("key_fingerprint"):
            found = True
            assert d["path"].startswith("/api/projects/")
            assert d["status_code"] == 200
    assert found, "Auth metadata not found in logs"

def test_logs_do_not_include_sensitive_headers(client, caplog, create_project_and_key):
    info = create_project_and_key()
    caplog.set_level(logging.INFO, logger="request_log")
    resp = client.get(f"/api/projects/{info['project_id']}/api-keys", headers={"Authorization": f"Bearer {info['api_key']}"})
    assert resp.status_code == 200
    for record in caplog.records:
        msg = record.getMessage()
        assert "Authorization" not in msg
        assert "X-API-Key" not in msg
        assert info["api_key"] not in msg
