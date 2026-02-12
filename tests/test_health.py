
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client(override_api_key_store):
    return TestClient(app)

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok"}
    assert "x-request-id" in resp.headers
