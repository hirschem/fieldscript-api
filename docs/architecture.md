# Architecture

## OCR Job Lifecycle
- **pending**: Job created, awaiting processing
- **processing**: Background task started
- **completed**: OCR result available
- **failed**: Error occurred during processing

## Async 202 Model
- POST /ocr returns 202 Accepted and job_id
- Client polls GET /jobs/{job_id} for status/result
- Avoids blocking request thread, supports scale

## Background Task Processing
- FastAPI BackgroundTasks used for async job execution
- Jobs processed in-memory (replace with DB for production)

## Project Isolation
- Each job is scoped to project_id
- GET only returns jobs for correct project_id

## Payload Size Limits
- 10MB per image (decoded)
- 20MB total per request
- Enforced route-local for contract compliance

## Error Response Structure
- Standardized JSON: error_code, message, request_id
- x-request-id header always set

## Request ID Tracing
- request_id generated per request
- Propagated in body and header
- Job polling returns original job request_id in body

## Sequence Diagram

Client
  |
  | POST /ocr
  |---------------------->
  |      202 Accepted, job_id
  |<----------------------
  | Poll GET /jobs/{job_id}
  |---------------------->
  |      status/result
  |<----------------------

---
For testing details, see [testing.md](testing.md).
For decisions log, see [decisions.md](decisions.md).
