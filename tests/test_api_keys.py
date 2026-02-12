import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security.api_keys import PROJECT_API_KEYS, generate_api_key, store_api_key
from datetime import datetime

@pytest.fixture(autouse=True)
def reset_store_and_env(monkeypatch):
    PROJECT_API_KEYS.clear()
    monkeypatch.setenv("API_KEY_PEPPER", "test_pepper")
    yield
    PROJECT_API_KEYS.clear()

@pytest.fixture
def client(override_api_key_store):
    return TestClient(app)

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


def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}


def test_create_requires_auth(client):
    resp = client.post("/api/projects/test-proj/api-keys", json={})
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"

def test_create_invalid_key(client):
    resp = client.post("/api/projects/test-proj/api-keys", json={}, headers=auth_headers("invalid"))
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"

def test_list_requires_auth(client):
    resp = client.get("/api/projects/test-proj/api-keys")
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"

def test_create_and_list_key(client, create_project_and_key):
    info = create_project_and_key()
    # Create a second key using the first key
    resp = client.post(
        f"/api/projects/{info['project_id']}/api-keys",
        json={"name": "second"},
        headers=auth_headers(info["api_key"])
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "api_key" in data and data["api_key"].startswith("mph_")
    assert data["key_prefix"] == data["api_key"][:8]
    assert "key_hash" not in data
    # List keys
    resp2 = client.get(f"/api/projects/{info['project_id']}/api-keys", headers=auth_headers(info["api_key"]))
    assert resp2.status_code == 200
    items = resp2.json()["items"]
    assert any(k["api_key_id"] == data["api_key_id"] for k in items)
    # No raw api_key in list
    for k in items:
        assert "api_key" not in k
        assert info["api_key"] not in str(k)

def test_revoke_and_idempotency(client, create_project_and_key):
    info = create_project_and_key()
    # Revoke
    resp = client.post(f"/api/projects/{info['project_id']}/api-keys/{info['api_key_id']}/revoke", headers=auth_headers(info["api_key"]))
    assert resp.status_code == 200
    revoked_at = resp.json()["revoked_at"]
    assert revoked_at is not None
    # Revoke again (idempotent)
    resp2 = client.post(f"/api/projects/{info['project_id']}/api-keys/{info['api_key_id']}/revoke", headers=auth_headers(info["api_key"]))
    assert resp2.status_code == 200
    assert resp2.json()["revoked_at"] == revoked_at
    # After revoke, cannot use key
    resp3 = client.post(f"/api/projects/{info['project_id']}/api-keys", json={}, headers=auth_headers(info["api_key"]))
    assert resp3.status_code == 401
    assert resp3.headers["WWW-Authenticate"] == "Bearer"

def test_project_mismatch_forbidden(client, create_project_and_key):
    infoA = create_project_and_key("projA")
    infoB = create_project_and_key("projB")
    # Try to use keyA on project B
    resp = client.get(f"/api/projects/{infoB['project_id']}/api-keys", headers=auth_headers(infoA["api_key"]))
    assert resp.status_code == 403
    # Try to use keyB on project A
    resp2 = client.get(f"/api/projects/{infoA['project_id']}/api-keys", headers=auth_headers(infoB["api_key"]))
    assert resp2.status_code == 403

def test_last_used_at_updates(client, create_project_and_key):
    info = create_project_and_key()
    # Use key
    client.get(f"/api/projects/{info['project_id']}/api-keys", headers=auth_headers(info["api_key"]))
    # List keys
    resp = client.get(f"/api/projects/{info['project_id']}/api-keys", headers=auth_headers(info["api_key"]))
    items = resp.json()["items"]
    for k in items:
        if k["api_key_id"] == info["api_key_id"]:
            assert k["last_used_at"] is not None
