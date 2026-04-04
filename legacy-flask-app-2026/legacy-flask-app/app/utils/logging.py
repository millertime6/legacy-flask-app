import json
import logging
import uuid
from datetime import datetime, timezone

from flask import g, request


class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            message.update(record.event)
        return json.dumps(message)


def configure_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    @app.before_request
    def set_correlation_id():
        incoming = request.headers.get("X-Correlation-ID")
        g.correlation_id = incoming or str(uuid.uuid4())


def audit_log(entity_type: str, operation: str, status: str, details: dict | None = None):
    payload = {
        "correlation_id": getattr(g, "correlation_id", "N/A"),
        "entity_type": entity_type,
        "operation": operation,
        "status": status,
    }
    if details:
        payload["details"] = details
    logging.getLogger("legacy_app.audit").info(
        f"{entity_type} {operation} {status}",
        extra={"event": payload},
    )
