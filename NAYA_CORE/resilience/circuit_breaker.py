"""
NAYA V19.3 — CIRCUIT BREAKER + RETRY
Wrapper universel pour tous les appels API externes.

Usage:
    from NAYA_CORE.resilience.circuit_breaker import circuit_breaker, retry

    @circuit_breaker("serper_api", failure_threshold=5, reset_timeout=60)
    @retry(max_attempts=3, backoff_base=1.5)
    async def call_serper(query):
        ...

Fonctionnalités:
- Circuit breaker: ouvre après N échecs, semi-ouvre après T secondes
- Retry exponentiel: base^attempt avec jitter
- Décorateurs async + sync
- Métriques globales accessibles via breaker_registry
"""
import asyncio
import random
import time
import logging
import functools
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, TypeVar, Awaitable, Union
import threading

log = logging.getLogger("NAYA.CIRCUIT")

T = TypeVar("T")


class BreakerState(str, Enum):
    CLOSED = "closed"         # Tout passe
    OPEN = "open"             # Tout bloque
    HALF_OPEN = "half_open"   # Teste un appel


@dataclass
class BreakerMetrics:
    total_calls: int = 0
    total_success: int = 0
    total_failures: int = 0
    total_blocked: int = 0
    state: BreakerState = BreakerState.CLOSED
    last_failure: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    consecutive_failures: int = 0

    def to_dict(self) -> Dict:
        return {
            "total_calls": self.total_calls,
            "total_success": self.total_success,
            "total_failures": self.total_failures,
            "total_blocked": self.total_blocked,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "success_rate": (self.total_success / self.total_calls) if self.total_calls else 0,
        }


class CircuitBreakerError(Exception):
    """Raised when breaker is open and blocks a call."""


class CircuitBreaker:
    """
    Circuit breaker thread-safe avec 3 états (CLOSED / OPEN / HALF_OPEN).
    """

    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout  # secondes avant tentative half-open
        self.metrics = BreakerMetrics()
        self._lock = threading.RLock()

    def _can_attempt(self) -> bool:
        with self._lock:
            now = datetime.now(timezone.utc)
            if self.metrics.state == BreakerState.CLOSED:
                return True
            if self.metrics.state == BreakerState.OPEN:
                # Vérifier si on peut passer en HALF_OPEN
                elapsed = (now - self.metrics.last_state_change).total_seconds()
                if elapsed >= self.reset_timeout:
                    self.metrics.state = BreakerState.HALF_OPEN
                    self.metrics.last_state_change = now
                    log.info(f"[CB:{self.name}] OPEN → HALF_OPEN (tentative)")
                    return True
                return False
            # HALF_OPEN: autoriser un seul appel test
            return True

    def _on_success(self):
        with self._lock:
            self.metrics.total_calls += 1
            self.metrics.total_success += 1
            self.metrics.consecutive_failures = 0
            if self.metrics.state != BreakerState.CLOSED:
                log.info(f"[CB:{self.name}] {self.metrics.state.value} → CLOSED (success)")
                self.metrics.state = BreakerState.CLOSED
                self.metrics.last_state_change = datetime.now(timezone.utc)

    def _on_failure(self):
        with self._lock:
            self.metrics.total_calls += 1
            self.metrics.total_failures += 1
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure = datetime.now(timezone.utc)
            if self.metrics.state == BreakerState.HALF_OPEN:
                # Re-ouvrir immédiatement
                self.metrics.state = BreakerState.OPEN
                self.metrics.last_state_change = datetime.now(timezone.utc)
                log.warning(f"[CB:{self.name}] HALF_OPEN → OPEN (test failed)")
            elif (self.metrics.state == BreakerState.CLOSED
                  and self.metrics.consecutive_failures >= self.failure_threshold):
                self.metrics.state = BreakerState.OPEN
                self.metrics.last_state_change = datetime.now(timezone.utc)
                log.error(f"[CB:{self.name}] CLOSED → OPEN (threshold {self.failure_threshold})")

    def _on_blocked(self):
        with self._lock:
            self.metrics.total_blocked += 1

    async def call_async(self, fn: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        if not self._can_attempt():
            self._on_blocked()
            raise CircuitBreakerError(f"Circuit {self.name} is OPEN")
        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def call_sync(self, fn: Callable[..., T], *args, **kwargs) -> T:
        if not self._can_attempt():
            self._on_blocked()
            raise CircuitBreakerError(f"Circuit {self.name} is OPEN")
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise


# ══════════════════════════════════════════════════════════════════
# REGISTRY GLOBAL (inspecté par le dashboard OODA)
# ══════════════════════════════════════════════════════════════════

class BreakerRegistry:
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_or_create(self, name: str, failure_threshold: int = 5,
                      reset_timeout: int = 60) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, failure_threshold, reset_timeout)
            return self._breakers[name]

    def all(self) -> Dict[str, CircuitBreaker]:
        return dict(self._breakers)

    def global_stats(self) -> Dict:
        return {
            "breakers": len(self._breakers),
            "open": sum(1 for b in self._breakers.values()
                        if b.metrics.state == BreakerState.OPEN),
            "half_open": sum(1 for b in self._breakers.values()
                             if b.metrics.state == BreakerState.HALF_OPEN),
            "closed": sum(1 for b in self._breakers.values()
                          if b.metrics.state == BreakerState.CLOSED),
            "details": {k: b.metrics.to_dict() for k, b in self._breakers.items()},
        }


breaker_registry = BreakerRegistry()


# ══════════════════════════════════════════════════════════════════
# DÉCORATEUR circuit_breaker
# ══════════════════════════════════════════════════════════════════

def circuit_breaker(name: str, failure_threshold: int = 5, reset_timeout: int = 60):
    """Décorateur pour envelopper une fonction dans un circuit breaker."""
    def decorator(fn):
        breaker = breaker_registry.get_or_create(name, failure_threshold, reset_timeout)
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper_async(*args, **kwargs):
                return await breaker.call_async(fn, *args, **kwargs)
            return wrapper_async
        @functools.wraps(fn)
        def wrapper_sync(*args, **kwargs):
            return breaker.call_sync(fn, *args, **kwargs)
        return wrapper_sync
    return decorator


# ══════════════════════════════════════════════════════════════════
# DÉCORATEUR retry
# ══════════════════════════════════════════════════════════════════

def retry(max_attempts: int = 3, backoff_base: float = 1.5,
          max_delay: float = 30.0, exceptions: tuple = (Exception,),
          jitter: bool = True):
    """
    Décorateur retry avec backoff exponentiel + jitter.

    max_attempts: nombre total d'essais (incluant le premier)
    backoff_base: multiplicateur (delay = backoff_base ** attempt)
    max_delay: cap sur le délai (secondes)
    exceptions: tuple d'exceptions à retry (CircuitBreakerError exclue par défaut)
    jitter: ajoute un aléa pour éviter le thundering herd
    """
    # CircuitBreakerError ne doit jamais être retry
    def _should_retry(exc):
        if isinstance(exc, CircuitBreakerError):
            return False
        return isinstance(exc, exceptions)

    def decorator(fn):
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper_async(*args, **kwargs):
                last_exc = None
                for attempt in range(max_attempts):
                    try:
                        return await fn(*args, **kwargs)
                    except Exception as e:
                        last_exc = e
                        if not _should_retry(e) or attempt == max_attempts - 1:
                            raise
                        delay = min(backoff_base ** attempt, max_delay)
                        if jitter:
                            delay *= (0.5 + random.random())
                        log.debug(f"Retry {attempt+1}/{max_attempts} in {delay:.2f}s ({e})")
                        await asyncio.sleep(delay)
                raise last_exc
            return wrapper_async

        @functools.wraps(fn)
        def wrapper_sync(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if not _should_retry(e) or attempt == max_attempts - 1:
                        raise
                    delay = min(backoff_base ** attempt, max_delay)
                    if jitter:
                        delay *= (0.5 + random.random())
                    log.debug(f"Retry {attempt+1}/{max_attempts} in {delay:.2f}s ({e})")
                    time.sleep(delay)
            raise last_exc
        return wrapper_sync
    return decorator


__all__ = [
    "CircuitBreaker", "CircuitBreakerError", "BreakerState", "BreakerMetrics",
    "BreakerRegistry", "breaker_registry",
    "circuit_breaker", "retry",
]
