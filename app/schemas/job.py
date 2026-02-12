from typing import Optional, Literal
from pydantic import BaseModel
from app.schemas.ocr import OCRResponse

class OCRJob(BaseModel):
    """
    Represents an asynchronous OCR job for background processing.
    """
    job_id: str
    project_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    result: Optional[OCRResponse] = None
    error: Optional[str] = None
    request_id: str
