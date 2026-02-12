import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64
import time

client = TestClient(app)

# Helper to create a fake base64 image of N bytes decoded

def _fake_b64_str(decoded_bytes: int) -> str:
    return base64.b64encode(b"\x00" * decoded_bytes).decode("ascii")

PROJECT_ID = "test"
OCR_URL = f"/v1/projects/{PROJECT_ID}/ocr"

# 1️⃣ POST returns 202 + job_id

def test_post_ocr_returns_202_and_job_id():
    image = _fake_b64_str(1024)  # 1KB
    resp = client.post(
        OCR_URL,
        headers={"content-type": "application/json", "x-project-id": PROJECT_ID},
        json={"images": [image], "document_type": "invoice"},
    )
    assert resp.status_code == 202, resp.text
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "request_id" in data
    assert resp.headers["x-request-id"] == data["request_id"]

# 2️⃣ GET returns job status transitions

def test_get_job_status_transitions():
    image = _fake_b64_str(1024)
    post_resp = client.post(
        OCR_URL,
        headers={"content-type": "application/json", "x-project-id": PROJECT_ID},
        json={"images": [image], "document_type": "invoice"},
    )
    assert post_resp.status_code == 202, post_resp.text
    post_data = post_resp.json()
    job_id = post_data["job_id"]
    job_request_id = post_data["request_id"]
    job_url = f"/v1/projects/{PROJECT_ID}/jobs/{job_id}"
    # Initial status should be pending or processing
    get_resp = client.get(job_url, headers={"x-project-id": PROJECT_ID})
    assert get_resp.status_code == 200, get_resp.text
    data = get_resp.json()
    assert data["job_id"] == job_id
    assert data["status"] in ["pending", "processing", "completed", "failed"]
    assert "request_id" in data
    assert data["request_id"] == job_request_id
    assert "x-request-id" in get_resp.headers
    # Wait for job to complete
    for _ in range(30):
        get_resp = client.get(job_url, headers={"x-project-id": PROJECT_ID})
        assert "x-request-id" in get_resp.headers
        data = get_resp.json()
        assert data["request_id"] == job_request_id
        if data["status"] == "completed":
            assert "result" in data
            break
        elif data["status"] == "failed":
            assert "error" in data
            break
        time.sleep(0.1)
    else:
        pytest.fail("Job did not complete in time")

# 3️⃣ 413 payload guard still works

def test_post_ocr_payload_too_large_returns_413():
    # One image of 10MB + 1 byte triggers per-image cap
    image = _fake_b64_str(10 * 1024 * 1024 + 1)
    resp = client.post(
        OCR_URL,
        headers={"content-type": "application/json", "x-project-id": PROJECT_ID},
        json={"images": [image], "document_type": "invoice"},
    )
    assert resp.status_code == 413, resp.text
    data = resp.json()
    assert data["error_code"] == "PAYLOAD_TOO_LARGE"
    assert "request_id" in data
    assert resp.headers["x-request-id"] == data["request_id"]

# 4️⃣ 404 for wrong project_id

def test_get_job_wrong_project_id_returns_404():
    image = _fake_b64_str(1024)
    post_resp = client.post(
        OCR_URL,
        headers={"content-type": "application/json", "x-project-id": PROJECT_ID},
        json={"images": [image], "document_type": "invoice"},
    )
    assert post_resp.status_code == 202, post_resp.text
    post_data = post_resp.json()
    job_id = post_data["job_id"]
    wrong_project_id = "notright"
    job_url = f"/v1/projects/{wrong_project_id}/jobs/{job_id}"
    get_resp = client.get(job_url, headers={"x-project-id": wrong_project_id})
    assert get_resp.status_code == 404, get_resp.text
    data = get_resp.json()
    assert data["error_code"] == "NOT_FOUND"
    assert "request_id" in data
    assert "x-request-id" in get_resp.headers
