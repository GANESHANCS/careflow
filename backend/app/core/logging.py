import logging
import json
import sys
from datetime import datetime, timezone
from backend.app.core.config import settings

# Sensitive keys to scrub from logs
SENSITIVE_KEYS = {"password", "authorization", "token", "secret", "access_token", "secret_key"}


class JSONFormatter(logging.Formatter):
    """
    Production-grade JSON log formatter for structured logging.
    Excludes sensitive header keys and parameters.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach extra structured metadata if present
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "client_ip"):
            if hasattr(record, key):
                val = getattr(record, key)
                if isinstance(val, str) and any(sk in key.lower() for sk in SENSITIVE_KEYS):
                    val = "[REDACTED]"
                log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging():
    """Configure system logger based on ENVIRONMENT setting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT.lower() == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
        )

    root_logger.addHandler(handler)


logger = logging.getLogger("careflow.api")
