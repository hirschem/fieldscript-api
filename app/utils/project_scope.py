from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.common import ErrorResponse
from fastapi import HTTPException

def enforce_project_scope(request: Request, project_id: str):
    request.state.project_id = project_id
    header_id = request.headers.get("x-project-id")
    if header_id is not None and header_id != project_id:
        request_id = getattr(request.state, "request_id", "unknown")
        request.state.error_code = "PROJECT_ID_MISMATCH"
        resp = JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="PROJECT_ID_MISMATCH",
                message="x-project-id header does not match path project_id",
                request_id=request_id
            ).model_dump()
        )
        resp.headers["x-request-id"] = request_id
        raise HTTPException(status_code=400, detail=resp.body.decode())
