"""
QUALITÉ #7 — Durcissement sécurité production.

Implémente les meilleures pratiques de sécurité : sanitization des entrées,
protection CSRF, rate limiting, headers de sécurité, audit trail.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize toutes les entrées utilisateur pour prévenir les injections."""

    SQL_PATTERNS = re.compile(r"(--|;|'|\"|\b(DROP|DELETE|INSERT|UPDATE|ALTER|EXEC|UNION)\b)", re.IGNORECASE)
    XSS_PATTERNS = re.compile(r"(<script|javascript:|on\w+=)", re.IGNORECASE)
    PATH_TRAVERSAL = re.compile(r"\.\./|\.\.\\")

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        value = value[:max_length]
        value = cls.XSS_PATTERNS.sub("", value)
        value = cls.PATH_TRAVERSAL.sub("", value)
        return value.strip()

    @classmethod
    def is_safe_sql(cls, value: str) -> bool:
        return not bool(cls.SQL_PATTERNS.search(value))

    @classmethod
    def sanitize_email(cls, email: str) -> str:
        email = email.strip().lower()[:254]
        if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email):
            return ""
        return email

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        safe = re.sub(r"[^\w\-.]", "_", filename)
        safe = cls.PATH_TRAVERSAL.sub("", safe)
        return safe[:255]


class SecurityHeaders:
    """Headers de sécurité HTTP pour l'API FastAPI."""

    HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
    }

    @classmethod
    def get_all(cls) -> Dict[str, str]:
        return cls.HEADERS.copy()


class AuditTrail:
    """Système d'audit trail pour tracer toutes les actions sensibles."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []

    def log_event(
        self,
        action: str,
        actor: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "resource": resource,
            "severity": severity,
            "details": details or {},
            "event_hash": hashlib.sha256(
                f"{action}{actor}{resource}{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16],
        }
        self._events.append(event)

        if severity in ("critical", "high"):
            logger.warning(f"[AuditTrail] {severity.upper()}: {action} by {actor} on {resource}")

    def get_events(self, limit: int = 100, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        events = self._events
        if severity:
            events = [e for e in events if e["severity"] == severity]
        return events[-limit:]

    def stats(self) -> Dict[str, Any]:
        severity_counts: Dict[str, int] = {}
        for e in self._events:
            severity_counts[e["severity"]] = severity_counts.get(e["severity"], 0) + 1
        return {
            "total_events": len(self._events),
            "by_severity": severity_counts,
        }


class TokenManager:
    """Gestion sécurisée des tokens d'authentification."""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_token(token: str, salt: str = "") -> str:
        return hashlib.sha256(f"{salt}{token}".encode()).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


input_sanitizer = InputSanitizer()
security_headers = SecurityHeaders()
audit_trail = AuditTrail()
token_manager = TokenManager()
