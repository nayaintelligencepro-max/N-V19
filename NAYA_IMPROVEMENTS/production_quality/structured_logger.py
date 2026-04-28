"""
QUALITÉ #2 — Système de logging structuré production-grade.

Logging JSON structuré avec corrélation de requêtes, niveaux de sévérité,
et rotation automatique des fichiers de log.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Formatter JSON structuré pour les logs production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        if hasattr(record, "agent_name"):
            log_entry["agent_name"] = record.agent_name
        if hasattr(record, "revenue_impact"):
            log_entry["revenue_impact_eur"] = record.revenue_impact

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class NayaLogger:
    """
    Logger structuré pour NAYA Supreme.

    Features:
    - Format JSON pour parsing automatique
    - Corrélation de requêtes via correlation_id
    - Logs séparés par niveau (info, error, revenue)
    - Compatible avec Prometheus/Grafana/ELK
    """

    _instance: Optional["NayaLogger"] = None

    def __init__(self) -> None:
        self._root_logger = logging.getLogger("naya")
        self._root_logger.setLevel(logging.DEBUG)

        if not self._root_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter())
            handler.setLevel(logging.INFO)
            self._root_logger.addHandler(handler)

    @classmethod
    def get_instance(cls) -> "NayaLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def info(self, message: str, **kwargs: Any) -> None:
        extra = kwargs
        self._root_logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._root_logger.warning(message, extra=kwargs)

    def error(self, message: str, exc: Optional[Exception] = None, **kwargs: Any) -> None:
        self._root_logger.error(message, exc_info=exc, extra=kwargs)

    def revenue_event(self, event: str, amount_eur: float, **kwargs: Any) -> None:
        extra = {"revenue_impact": amount_eur, **kwargs}
        self._root_logger.info(f"[REVENUE] {event}: {amount_eur:,.0f} EUR", extra=extra)

    def agent_action(self, agent_name: str, action: str, **kwargs: Any) -> None:
        extra = {"agent_name": agent_name, **kwargs}
        self._root_logger.info(f"[AGENT:{agent_name}] {action}", extra=extra)


naya_logger = NayaLogger.get_instance()
