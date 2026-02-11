import sys
from loguru import logger
import json

class JsonLogSink:
    def write(self, message):
        record = message.record
        log = {
            "level": record["level"].name,
            "time": record["time"].isoformat(),
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"]
        }
        print(json.dumps(log))

    def flush(self):
        pass

def setup_logging():
    logger.remove()
    logger.add(JsonLogSink(), level="INFO")
    logger.add(sys.stderr, level="ERROR")
