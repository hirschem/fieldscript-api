
# Fieldscript API

Production-grade FastAPI OCR service with strict payload enforcement, request ID tracing, and contract-tested error handling.

---

## Overview

Fieldscript API is a backend service designed to process base64-encoded document images for OCR extraction while enforcing strict API contracts.

This project emphasizes:

- Deterministic error semantics  
- Route-level payload enforcement  
- Request ID propagation for traceability  
- Boundary-tested contract behavior  
- Middleware-aware design  

The goal of this project is to demonstrate production-oriented backend engineering practices rather than prototype-level experimentation.

---

## Endpoint

### `POST /v1/projects/{project_id}/ocr`

Processes one or more base64-encoded images for OCR.

### Required Headers

```
x-project-id: {project_id}
Content-Type: application/json
```

The `x-project-id` header must match the `{project_id}` path parameter.

---

## Payload Limits (Decoded Bytes)

Limits are enforced using decoded image size — not base64 string length.

- **10MB per image**
- **20MB total per request**

If limits are exceeded, the API returns a standardized `413` response:

```json
{
	"error_code": "PAYLOAD_TOO_LARGE",
	"message": "Total image payload exceeds allowed size",
	"request_id": "..."
}
```

The response will always include:

`x-request-id: <same value as request_id>`

---

## Design Decisions

### Route-Level Payload Enforcement

Payload limits are enforced directly inside the OCR route rather than relying solely on FastAPI exception handlers.

This guarantees deterministic 413 behavior even when custom middleware stacks may interfere with exception propagation.

### Decoded Byte Size Estimation

Base64 payloads are evaluated using a decoded-size estimation formula:

```
decoded_size = (len(base64_string) * 3) // 4 - padding
```

This prevents unnecessary memory allocation by avoiding full image decoding during validation.

### Request ID Propagation

Each request receives a request_id via middleware.

All responses include:

- request_id in the JSON body
- x-request-id response header

This ensures traceable API behavior across middleware, logging, and error boundaries.

---

## Running Locally

**Create Virtual Environment**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Install Dependencies**
```powershell
pip install -r requirements.txt
```

**Run the Server**
```powershell
uvicorn app.main:app --reload
```

**Running Tests**
```powershell
python -m pytest -vv
```

Contract tests validate:

- Per-image payload limits
- Total payload limits
- Exact boundary conditions
- Project scope enforcement
- Request ID propagation

---

## Deployment Notes

On certain hosting platforms (e.g., reverse proxies or serverless platforms), large payloads may be rejected before reaching the FastAPI application layer. In those cases, platform-level 413 responses will not use this API’s standardized schema.

Contract tests apply to application-layer behavior using FastAPI's TestClient.

---

## Project Structure

```
app/
	main.py
	services/
	engines/
	schemas/
	utils/
	middleware/
	test_413.py
```

The project separates:

- API surface layer
- Business/service layer
- Engine layer
- Utilities
- Middleware
- Contract tests
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
