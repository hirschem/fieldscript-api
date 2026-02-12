# Testing

## What the Test Suite Validates
- POST returns 202 + job_id
- GET returns job status transitions (pending → processing → completed/failed)
- 413 payload guard (per-image cap)
- 404 for project/job isolation

## Why Each Test Matters
- **202 + job_id**: Confirms async contract
- **Status transitions**: Ensures job lifecycle correctness
- **413**: Validates payload guard and error schema
- **404**: Enforces project isolation and error contract

## Running Tests
- From repo root: `python -m pytest -q`
- From tests/: `python -m pytest -q`

## Pytest Configuration
- `pytest.ini` sets pythonpath for import resolution
- `conftest.py` adds repo root to sys.path for tests/

## Not Tested
- External OCR integration
- Performance/scalability
- Production DB-backed jobs

---
For architecture, see [architecture.md](architecture.md).
For decisions log, see [decisions.md](decisions.md).
