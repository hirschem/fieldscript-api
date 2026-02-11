# Maximum allowed total decoded bytes for OCR images (20MB)
MAX_OCR_TOTAL_IMAGE_BYTES = 20 * 1024 * 1024
import os

ENV = os.getenv("ENV", "dev")
is_dev = ENV.lower() in {"dev", "development", "local"}
APP_NAME = "fieldscript-api"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Parse CORS_ORIGINS env var as comma-separated list
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if is_dev:
	allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"] + _cors_origins
else:
	allowed_origins = _cors_origins
