"""Logging utilities with structured JSON output.

Uses python-json-logger when available; falls back to standard logging.
"""
from __future__ import annotations

import logging
import sys
from typing import Any


def _build_json_formatter() -> logging.Formatter:
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore

        class _CloudRadarFormatter(jsonlogger.JsonFormatter):
            def add_fields(
                self,
                log_record: dict[str, Any],
                record: logging.LogRecord,
                message_dict: dict[str, Any],
            ) -> None:
                super().add_fields(log_record, record, message_dict)
                log_record.setdefault("timestamp", log_record.pop("asctime", None))
                log_record.setdefault("level", record.levelname)
                log_record.setdefault("logger", record.name)

        return _CloudRadarFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s",
            rename_fields={"message": "message"},
        )
    except ImportError:
        return logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_build_json_formatter())
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
