from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

_STANDARD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}

_SENSITIVE_SUBSTRINGS = (
    "authorization",
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "credential",
)


def sanitize_log_value(key: str, value: Any) -> Any:
    key_lower = key.lower()
    if any(sub in key_lower for sub in _SENSITIVE_SUBSTRINGS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: sanitize_log_value(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_log_value(key, item) for item in value]
    if isinstance(value, str) and (
        value.startswith("Bearer ") or value.startswith("sk-") or "Bearer " in value
    ):
        return "[REDACTED]"
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_FIELDS and not key.startswith("_"):
                event[key] = sanitize_log_value(key, value)
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event, default=str, separators=(",", ":"))


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
