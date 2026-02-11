# Fieldscript API

FastAPI OCR API with strict payload contract enforcement and request-id propagation.

## Key Endpoint

### POST /v1/projects/{project_id}/ocr

**Headers:**
- `x-project-id` (must match `{project_id}` in the path)

**Returns:**
- `200 OK`: JSON includes `request_id` and `text`, header `x-request-id`
- `413 Payload Too Large`: JSON schema:
	```json
	{ "error_code": "PAYLOAD_TOO_LARGE", "message": "...", "request_id": "..." }
	```
	Header `x-request-id` matches body `request_id`

## Payload Limits
- **Per image:** 10MB decoded bytes
- **Total:** 20MB decoded bytes

> Note: Platform proxies (Vercel, etc.) may return 413 before FastAPI and won’t use our schema; contract tests are for CI/TestClient.

## Local Setup

```powershell
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Run tests
python -m pytest -vv
```

## Tests
- Contract tests: see `app/test_413.py`

---

### Dev Notes
If you have previously committed venv/caches, run this to untrack them:

```powershell
git rm -r --cached .venv __pycache__ .pytest_cache .vscode
```
# FastAPI backend run instructions

## Install dependencies
pip install -r requirements.txt

## Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

## Endpoints:
- GET /health
- GET /version
- POST /v1/projects/{project_id}/ocr
- POST /v1/projects/{project_id}/export

CORS is enabled for http://localhost:3000
JSON logging is configured.
Request ID middleware is active.
Standard error schema is used.
