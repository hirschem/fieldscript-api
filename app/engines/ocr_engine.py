import abc
from typing import List, Optional

class OCREngine(abc.ABC):
    @abc.abstractmethod
    async def run(self, images: List[str], document_type: Optional[str]) -> str:
        pass

class DefaultOCREngine(OCREngine):
    async def run(self, images: List[str], document_type: Optional[str]) -> str:
        return "OCR engine not yet implemented"
