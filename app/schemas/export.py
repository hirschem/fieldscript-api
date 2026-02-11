from pydantic import BaseModel
from typing import Optional

class ExportRequest(BaseModel):
    data: Optional[str] = None

class ExportResponse(BaseModel):
    result: str
    request_id: str
