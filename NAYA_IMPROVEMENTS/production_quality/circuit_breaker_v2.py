"""
QUALITÉ #3 — Circuit Breaker V2 avancé.

Protection automatique contre les pannes en cascade avec états
CLOSED/OPEN/HALF_OPEN, métriques détaillées et fallback automatique.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStats:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    consecutive_failures: int = 0
    last_failure_at: Optional[str] = None
    last_success_at: Optional[str] = None
    state_changes: int = 0


class CircuitBreakerV2:
    """
    Circuit Breaker pattern avancé pour la résilience du système.

    - CLOSED: Le circuit fonctionne normalement
    - OPEN: Les appels sont bloqués (fallback utilisé)
    - HALF_OPEN: Un seul appel test est autorisé pour vérifier la récupération

    Améliorations V2:
    - Fallback automatique configurable
    - Métriques détaillées par circuit
    - Reset automatique après timeout
    - Notification Telegram sur changement d'état
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        half_open_max_calls: int = 1,
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._half_open_max = half_open_max_calls
        self._state = CBState.CLOSED
        self._stats = CircuitBreakerStats()
        self._last_open_at: float = 0
        self._half_open_calls: int = 0
        logger.info(f"[CircuitBreaker:{name}] Initialisé (threshold={failure_threshold}, timeout={recovery_timeout_seconds}s)")

    @property
    def state(self) -> CBState:
        if self._state == CBState.OPEN:
            if time.monotonic() - self._last_open_at >= self._recovery_timeout:
                self._transition_to(CBState.HALF_OPEN)
        return self._state

    def _transition_to(self, new_state: CBState) -> None:
        old = self._state
        self._state = new_state
        self._stats.state_changes += 1
        if new_state == CBState.OPEN:
            self._last_open_at = time.monotonic()
        if new_state == CBState.HALF_OPEN:
            self._half_open_calls = 0
        logger.warning(f"[CircuitBreaker:{self.name}] {old.value} -> {new_state.value}")

    def call(self, fn: Callable[..., T], *args: Any, fallback: Optional[Callable[..., T]] = None, **kwargs: Any) -> T:
        """Exécute une fonction à travers le circuit breaker."""
        current_state = self.state
        self._stats.total_calls += 1

        if current_state == CBState.OPEN:
            self._stats.rejected_calls += 1
            if fallback:
                logger.info(f"[CircuitBreaker:{self.name}] OPEN — utilisation du fallback")
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

        if current_state == CBState.HALF_OPEN:
            if self._half_open_calls >= self._half_open_max:
                self._stats.rejected_calls += 1
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(f"Circuit {self.name} HALF_OPEN limit reached")
            self._half_open_calls += 1

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if fallback:
                logger.info(f"[CircuitBreaker:{self.name}] Failure — utilisation du fallback: {e}")
                return fallback(*args, **kwargs)
            raise

    def _on_success(self) -> None:
        self._stats.successful_calls += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_at = datetime.now(timezone.utc).isoformat()
        if self._state == CBState.HALF_OPEN:
            self._transition_to(CBState.CLOSED)

    def _on_failure(self) -> None:
        self._stats.failed_calls += 1
        self._stats.consecutive_failures += 1
        self._stats.last_failure_at = datetime.now(timezone.utc).isoformat()
        if self._stats.consecutive_failures >= self._failure_threshold:
            self._transition_to(CBState.OPEN)

    def reset(self) -> None:
        """Reset manuel du circuit breaker."""
        self._transition_to(CBState.CLOSED)
        self._stats.consecutive_failures = 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self._stats.total_calls,
            "successful": self._stats.successful_calls,
            "failed": self._stats.failed_calls,
            "rejected": self._stats.rejected_calls,
            "consecutive_failures": self._stats.consecutive_failures,
            "state_changes": self._stats.state_changes,
            "success_rate_pct": round(
                (self._stats.successful_calls / max(self._stats.total_calls, 1)) * 100, 1
            ),
        }


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreakerRegistry:
    """Registre global de tous les circuit breakers."""

    def __init__(self) -> None:
        self._breakers: Dict[str, CircuitBreakerV2] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ) -> CircuitBreakerV2:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreakerV2(name, failure_threshold, recovery_timeout_seconds)
        return self._breakers[name]

    def all_stats(self) -> Dict[str, Any]:
        return {name: cb.get_stats() for name, cb in self._breakers.items()}


circuit_breaker_registry = CircuitBreakerRegistry()
