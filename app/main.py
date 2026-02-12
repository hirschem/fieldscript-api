from fastapi import BackgroundTasks
from uuid import uuid4
from app.schemas.job import OCRJob
from app.services.job_store import JOBS
#
# Payload limits are enforced INSIDE this route (route-local guard) to guarantee the 413 contract regardless of middleware stack or exception handler behavior.
# Limits are based on DECODED bytes (not base64 string length): 10MB per image, 20MB total.
# Returns standardized 413 error schema and sets x-request-id header to match body request_id.
# This ensures contract tests pass even if global handlers/middleware are bypassed.

def b64_decoded_size(b64_s: str) -> int:
    """
    Estimate decoded byte size of a base64 string WITHOUT decoding.
    Formula: (len * 3) // 4 - padding
    Used for payload enforcement to avoid memory blowups.
    """
    s = "".join(b64_s.split())
    if not s:
        return 0
    padding = 2 if s.endswith("==") else 1 if s.endswith("=") else 0
    return (len(s) * 3) // 4 - padding

import sys
import time
import json
import logging
from fastapi import FastAPI, Request, status, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.errors import PayloadTooLargeError
from app.middleware.request_id import RequestIDMiddleware
from app.logging_setup import setup_logging
from app.schemas.common import ErrorResponse
from app.schemas.ocr import OCRRequest, OCRResponse
from app.services.ocr_service import OCRService
from app.schemas.export import ExportRequest, ExportResponse
from app.request_logging import RequestLoggingMiddleware
from app.context_middleware import ContextMiddleware
from app.rate_limit_middleware import RateLimitMiddleware
from app.security_headers_middleware import SecurityHeadersMiddleware
from app.usage import get_usage_events
from app import config
from app.utils.project_scope import enforce_project_scope
from app.utils.base64_size import estimate_base64_decoded_bytes as _estimate_base64_decoded_bytes
from contextlib import asynccontextmanager

def safe_estimate_base64_decoded_bytes(val):
    try:
        if not isinstance(val, str):
            raise ValueError("Image is not a string")
        return _estimate_base64_decoded_bytes(val)
    except Exception:
        raise ValueError("Failed to estimate base64 decoded bytes")

logger = logging.getLogger("payload_guard")

# Version constants
SERVICE_NAME = "fieldscript-api"
SERVICE_VERSION = "1.0.0"
PROMPT_VERSION = "ocr_v1_2026-02-11"
EXPORT_VERSION = "export_v1"
TEMPLATE_VERSION = "template_v1"

setup_logging()

@asynccontextmanager
async def lifespan(app):
    # Startup
    startup_log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "event": "startup",
        "service_name": SERVICE_NAME,
        "service_version": SERVICE_VERSION,
        "env": config.ENV
    }
    # DEV-only extra info
    if config.is_dev:
        startup_log.update({
            "python_executable": sys.executable,
            "dev_flag": True,
            "version": SERVICE_VERSION
        })
    print(json.dumps(startup_log))
    yield
    # Shutdown
    print(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "event": "shutdown",
        "service_name": SERVICE_NAME,
        "service_version": SERVICE_VERSION,
        "env": config.ENV
    }))




# Instantiate FastAPI app
app = FastAPI(lifespan=lifespan)

# Register API key management router (required for tests)
from app.api.routes import api_keys as api_keys_router
app.include_router(api_keys_router.router)


# New middleware order for correct short-circuit header application
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)


# Register the dry-run endpoint after app = FastAPI(...)
@app.post("/v1/projects/{project_id}/ocr/dry-run")
async def ocr_dry_run(project_id: str, request: Request, body: OCRRequest):
    # Project scoping enforcement
    request.state.project_id = project_id
    header_id = request.headers.get("x-project-id")
    if header_id is not None and header_id != project_id:
        request_id = getattr(request.state, "request_id", "unknown")
        request.state.error_code = "PROJECT_ID_MISMATCH"
        resp = JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="PROJECT_ID_MISMATCH",
                message="x-project-id header does not match project_id in path.",
                request_id=request_id
            ).model_dump()
        )
        resp.headers["x-request-id"] = request_id
        return resp
    if not config.is_dev:
        resp = JSONResponse(status_code=404, content={"detail": "Not found"})
        request_id = getattr(request.state, "request_id", "unknown")
        resp.headers["x-request-id"] = request_id
        return resp
    service = OCRService()
    request_id = getattr(request.state, "request_id", "unknown")
    req_hash = service.compute_request_hash(body)
    cache_hit = service.is_cache_hit(req_hash)
    request.state.cache_hit = cache_hit
    resp = JSONResponse(content={
        "request_id": request_id,
        "request_hash": req_hash,
        "cache_hit": cache_hit
    })
    resp.headers["x-request-id"] = request_id
    return resp


# Mount health router
from app.health import router as health_router
app.include_router(health_router)

@app.get("/version")
def version():
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "prompt_version": PROMPT_VERSION,
        "export_version": EXPORT_VERSION,
        "template_version": TEMPLATE_VERSION
    }




@app.post("/v1/projects/{project_id}/ocr")
async def ocr(
    project_id: str,
    request: Request,
    body: OCRRequest,
    background_tasks: BackgroundTasks
):
    """
    Accepts OCR requests, enqueues background processing, and returns a job_id for async polling.
    Uses FastAPI BackgroundTasks to avoid blocking the request thread.
    """
    enforce_project_scope(request, project_id)
    PER_IMAGE_CAP = 10 * 1024 * 1024
    TOTAL_CAP = 20 * 1024 * 1024
    request_id = getattr(request.state, "request_id", "unknown")
    images = body.images
    total_bytes = 0
    for img in images:
        size_i = b64_decoded_size(img)
        if size_i > PER_IMAGE_CAP:
            body_ = {
                "error_code": "PAYLOAD_TOO_LARGE",
                "message": "An individual image exceeds allowed size",
                "request_id": request_id,
            }
            resp = JSONResponse(status_code=413, content=body_)
            resp.headers["x-request-id"] = request_id
            return resp
        total_bytes += size_i
    if total_bytes > TOTAL_CAP:
        body_ = {
            "error_code": "PAYLOAD_TOO_LARGE",
            "message": "Total image payload exceeds allowed size",
            "request_id": request_id,
        }
        resp = JSONResponse(status_code=413, content=body_)
        resp.headers["x-request-id"] = request_id
        return resp

    job_id = str(uuid4())
    job = OCRJob(
        job_id=job_id,
        project_id=project_id,
        status="pending",
        result=None,
        error=None,
        request_id=request_id
    )
    JOBS[job_id] = job

    async def process_ocr_job(job_id: str, body: OCRRequest, request_id: str):
        job = JOBS.get(job_id)
        if not job:
            return
        job.status = "processing"
        try:
            service = OCRService()
            response, _cache_hit = await service.process(body, request_id)
            job.status = "completed"
            job.result = response
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.exception(f"OCR job {job_id} failed")
            # Do not re-raise; log and mark as failed

    background_tasks.add_task(process_ocr_job, job_id, body, request_id)

    resp = JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "pending",
            "request_id": request_id
        }
    )
    resp.headers["x-request-id"] = request_id
    return resp
# ...existing code...

# GET /v1/projects/{project_id}/jobs/{job_id}
@app.get("/v1/projects/{project_id}/jobs/{job_id}")
async def get_ocr_job(project_id: str, job_id: str, request: Request):
    """
    Returns the status/result of an OCR job. Enforces project scope and error contract.
    """
    enforce_project_scope(request, project_id)
    request_id = getattr(request.state, "request_id", "unknown")
    job = JOBS.get(job_id)
    if not job or job.project_id != project_id:
        body = {
            "error_code": "NOT_FOUND",
            "message": "Job not found",
            "request_id": request_id
        }
        resp = JSONResponse(status_code=404, content=body)
        resp.headers["x-request-id"] = request_id
        return resp
    result = {
        "job_id": job.job_id,
        "status": job.status,
        "request_id": job.request_id
    }
    if job.status == "completed" and job.result:
        result["result"] = job.result.model_dump()
    if job.status == "failed" and job.error:
        result["error"] = job.error
    resp = JSONResponse(content=result)
    resp.headers["x-request-id"] = request_id
    return resp


@app.post("/v1/projects/{project_id}/export", response_model=ExportResponse)
def export(project_id: str, request: Request, body: ExportRequest):
    request_id = getattr(request.state, "request_id", "unknown")
    # Placeholder logic
    response = ExportResponse(result="Export placeholder", request_id=request_id)
    resp = JSONResponse(content=response.model_dump())
    resp.headers["x-request-id"] = request_id
    return resp

# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    request.state.error_code = "VALIDATION_ERROR"
    resp = JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid request",
            request_id=request_id
        ).model_dump()
    )
    resp.headers["x-request-id"] = request_id
    return resp


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    error_code = f"HTTP_{exc.status_code}"
    message = exc.detail if exc.detail else "HTTP error occurred."
    # If detail is a dict, extract error_code/message if present
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error_code", error_code)
        message = exc.detail.get("message", message)
    request.state.error_code = error_code
    resp = JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            request_id=request_id
        ).model_dump()
    )
    resp.headers["x-request-id"] = request_id
    # Preserve headers from HTTPException (e.g., WWW-Authenticate)
    if exc.headers:
        for k, v in exc.headers.items():
            resp.headers[k] = v
    return resp




# Ensure exactly one global Exception handler that prints tracebacks to sys.stderr
import traceback

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    request.state.error_code = "INTERNAL_ERROR"
    print(f"\n================ TRACEBACK_START request_id={request_id} ================", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print(f"================ TRACEBACK_END request_id={request_id} ================\n", file=sys.stderr)
    resp = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            request_id=request_id
        ).model_dump()
    )
    resp.headers["x-request-id"] = request_id
    return resp


# Debug endpoints (dev only)
debug_router = APIRouter()

@debug_router.get("/debug/usage")
def debug_usage(request: Request):
    if not config.is_dev:
        # Always return 404 and x-request-id header
        resp = JSONResponse(status_code=404, content={"detail": "Not found"})
        request_id = getattr(request.state, "request_id", "unknown")
        resp.headers["x-request-id"] = request_id
        return resp
    resp = JSONResponse(content=get_usage_events())
    request_id = getattr(request.state, "request_id", "unknown")
    resp.headers["x-request-id"] = request_id
    return resp

@debug_router.get("/debug/health")
def debug_health(request: Request):
    if not config.is_dev:
        resp = JSONResponse(status_code=404, content={"detail": "Not found"})
        request_id = getattr(request.state, "request_id", "unknown")
        resp.headers["x-request-id"] = request_id
        return resp
    resp = JSONResponse(content={"status": "ok", "env": config.ENV})
    request_id = getattr(request.state, "request_id", "unknown")
    resp.headers["x-request-id"] = request_id
    return resp

if config.is_dev:
    app.include_router(debug_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
