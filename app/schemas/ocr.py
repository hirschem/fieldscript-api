
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Optional, Dict
import logging
from app.utils.base64_size import estimate_base64_decoded_bytes

class OCRRequest(BaseModel):
    images: List[str]
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

    @field_validator("images")
    @classmethod
    def validate_images(cls, v):
        reason = None
        request_id = None
        try:
            # Try to get request_id from context if available (middleware sets it)
            try:
                from starlette_context import context
                request_id = context.data.get("request_id")
            except Exception:
                pass
            if not isinstance(v, list):
                reason = "images must be a non-empty list"
                raise ValueError(reason)
            if len(v) < 1:
                reason = "images must contain at least one image"
                raise ValueError(reason)
            if len(v) > 10:
                reason = "images cannot contain more than 10 images"
                raise ValueError(reason)
            for img in v:
                if not isinstance(img, str):
                    reason = "each image must be a base64 string"
                    raise ValueError(reason)
                # Optionally: basic base64 sanity check (characters/padding)
                # But do NOT check length or decoded size here
            return v
        except Exception as e:
            log_reason = reason or str(e)
            logging.warning(f"OCRRequest validation failed: {log_reason}; request_id={request_id}")
            raise ValueError(log_reason)

class OCRResponse(BaseModel):
    text: str
    request_id: str
