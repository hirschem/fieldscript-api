from typing import Dict
from app.schemas.job import OCRJob

# Temporary in-memory job store. Replace with persistent DB in production.
JOBS: Dict[str, OCRJob] = {}
