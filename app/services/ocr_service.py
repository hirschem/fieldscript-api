from app.schemas.ocr import OCRRequest, OCRResponse
from app.engines.ocr_engine import DefaultOCREngine
import hashlib
import json

_ocr_cache = {}

class OCRService:
    def __init__(self):
        self.engine = DefaultOCREngine()


    def compute_request_hash(self, request: OCRRequest) -> str:
        # Deterministic hash: images + document_type
        data = {
            "images": request.images,
            "document_type": request.document_type,
        }
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    def is_cache_hit(self, req_hash: str) -> bool:
        return req_hash in _ocr_cache

    async def process(self, request: OCRRequest, request_id: str) -> tuple[OCRResponse, bool]:
        req_hash = self.compute_request_hash(request)
        if self.is_cache_hit(req_hash):
            cached = _ocr_cache[req_hash]
            return OCRResponse(text=cached["text"], request_id=request_id), True
        text = await self.engine.run(request.images, request.document_type)
        _ocr_cache[req_hash] = {"text": text}
        return OCRResponse(text=text, request_id=request_id), False
