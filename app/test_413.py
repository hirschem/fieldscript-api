# 1️⃣ Test: Single image exceeds per-image 10MB cap
def test_ocr_single_image_exceeds_per_image_cap_returns_413():
    """
    Send 1 image with decoded size 11MB (over per-image cap).
    Expect 413 with correct error contract.
    """
    project_id = "abc"
    url = f"/v1/projects/{project_id}/ocr"
    image = _fake_b64_str(11 * 1024 * 1024)
    resp = client.post(
        url,
        headers={
            "content-type": "application/json",
            "x-project-id": project_id,
        },
        json={
            "images": [image],
            "document_type": "invoice",
        },
    )
    assert resp.status_code == 413, resp.text
    data = resp.json()
    assert set(data.keys()) == {"error_code", "message", "request_id"}
    assert data["error_code"] == "PAYLOAD_TOO_LARGE"
    assert data["message"] == "An individual image exceeds allowed size"
    assert "x-request-id" in resp.headers
    assert resp.headers["x-request-id"] == data["request_id"]
    assert data["request_id"] and data["request_id"] != "unknown"

# 2️⃣ Test: Exactly 20MB total should succeed
def test_ocr_payload_exactly_total_limit_succeeds():
    """
    Send 2 images of exactly 10MB decoded each (total 20MB).
    Should succeed (200).
    """
    project_id = "abc"
    url = f"/v1/projects/{project_id}/ocr"
    img = _fake_b64_str(10 * 1024 * 1024)
    images = [img, img]
    resp = client.post(
        url,
        headers={
            "content-type": "application/json",
            "x-project-id": project_id,
        },
        json={
            "images": images,
            "document_type": "invoice",
        },
    )
    assert resp.status_code == 200, resp.text
    assert "x-request-id" in resp.headers
    data = resp.json()
    assert "request_id" in data
    assert data["request_id"] == resp.headers["x-request-id"]
    assert "text" in data

# 3️⃣ Test: Project scope mismatch returns 400
def test_ocr_project_scope_mismatch_returns_400():
    """
    Path project_id = "abc", header x-project-id = "wrong".
    Should return 400 with error contract.
    """
    project_id = "abc"
    url = f"/v1/projects/{project_id}/ocr"
    resp = client.post(
        url,
        headers={
            "content-type": "application/json",
            "x-project-id": "wrong",
        },
        json={
            "images": [_fake_b64_str(1024)],
            "document_type": "invoice",
        },
    )
    assert resp.status_code == 400, resp.text
    data = resp.json()
    assert "error_code" in data
    assert "message" in data
    assert "request_id" in data
    assert "x-request-id" in resp.headers

# test_413.py
# This is a unit/contract test for the app-level payload guard and error schema.
# NOTE: This test asserts the app's 413 error schema. On Vercel or any platform with proxy/body-size limits,
# a 413 or 4xx may be returned by the platform before reaching FastAPI, and will NOT use our JSON schema.
# This test is for TestClient/CI only, not live server integration.

import pytest
from fastapi.testclient import TestClient
from app.main import app  # adjust if your app import path differs

pytestmark = pytest.mark.contract


client = TestClient(app)


import base64
def _fake_b64_str(decoded_bytes: int) -> str:
    return base64.b64encode(b"\x00" * decoded_bytes).decode("ascii")


def test_ocr_payload_too_large_returns_413_standard_error():
    """
    Total payload size guard test.

    We keep each image under the per-image 10MB cap, but exceed total cap (20MB)
    by sending 3 images of 7MB each => 21MB total.
    """
    project_id = "abc"
    url = f"/v1/projects/{project_id}/ocr"

    # 7MB per image, decoded bytes
    per_image = 7 * 1024 * 1024  # decoded bytes
    images = [_fake_b64_str(per_image) for _ in range(3)]  # 21MB decoded total

    # Include x-project-id header that matches the path, to avoid mismatch 400.
    resp = client.post(
        url,
        headers={
            "content-type": "application/json",
            "x-project-id": project_id,
        },
        json={
            "images": images,
            "document_type": "invoice",
        },
    )

    assert resp.status_code == 413, resp.text

    # Standardized error schema
    data = resp.json()
    assert set(data.keys()) == {"error_code", "message", "request_id"}
    assert data["error_code"] == "PAYLOAD_TOO_LARGE"
    assert data["message"] == "Total image payload exceeds allowed size"

    # x-request-id must be present and match body request_id
    assert "x-request-id" in resp.headers
    assert resp.headers["x-request-id"] == data["request_id"]
    assert data["request_id"] and data["request_id"] != "unknown"


def test_ocr_payload_under_limit_succeeds():
    """
    Control test: a small payload should succeed (placeholder OCR response ok).
    """
    project_id = "abc"
    url = f"/v1/projects/{project_id}/ocr"

    resp = client.post(
        url,
        headers={
            "content-type": "application/json",
            "x-project-id": project_id,
        },
        json={
            "images": [_fake_b64_str(1024)],  # 1KB
            "document_type": "invoice",
        },
    )

    assert resp.status_code == 200, resp.text
    assert "x-request-id" in resp.headers

    data = resp.json()
    # Your OCRResponse should at least include request_id and text
    assert "request_id" in data
    assert data["request_id"] == resp.headers["x-request-id"]
    assert "text" in data
