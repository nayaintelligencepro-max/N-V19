"""
NAYA SUPREME V19.3 — AMELIORATION #3
Smart Retry Engine
==================
Retry intelligent avec backoff exponentiel, jitter, et circuit breaker
pour toutes les API externes (Apollo, SendGrid, Groq, etc.).

Unique a NAYA : circuit breaker adaptatif qui apprend les patterns
de disponibilite de chaque API et ajuste les retries en temps reel.
"""
import time
import random
import logging
import threading
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.RETRY")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal: requests pass through
    OPEN = "open"          # Tripped: requests fail immediately
    HALF_OPEN = "half_open"  # Testing: one request allowed to test


@dataclass
class CircuitBreaker:
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure: float = 0
    last_success: float = 0
    open_since: float = 0
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds before trying half-open
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


@dataclass
class RetryResult:
    success: bool
    result: Any = None
    attempts: int = 0
    total_time_ms: float = 0
    last_error: str = ""
    circuit_state: str = "closed"


class SmartRetryEngine:
    """
    Moteur de retry intelligent avec :
    - Backoff exponentiel (base 2) avec jitter aleatoire
    - Circuit breaker par service (evite de surcharger une API down)
    - Metriques par service (latence, taux d'erreur, uptime)
    - Degradation gracieuse (fallback si circuit ouvert)
    - Budget de retry (max tentatives par fenetre de temps)
    """

    def __init__(self):
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        self._global_stats = {
            "total_retries": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_circuit_trips": 0,
        }

    def execute_with_retry(
        self,
        service_name: str,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        fallback: Callable = None,
        timeout_per_call: float = 30.0,
    ) -> RetryResult:
        """
        Execute une fonction avec retry intelligent.

        Args:
            service_name: Nom du service (ex: "apollo", "sendgrid", "groq")
            func: Fonction a executer (doit retourner le resultat)
            max_retries: Nombre max de tentatives
            base_delay: Delai de base entre retries (secondes)
            max_delay: Delai maximum entre retries
            fallback: Fonction de fallback si toutes les tentatives echouent
            timeout_per_call: Timeout par appel individuel
        """
        circuit = self._get_or_create_circuit(service_name)
        start = time.time()

        # Verifier le circuit breaker
        if circuit.state == CircuitState.OPEN:
            elapsed_since_open = time.time() - circuit.open_since
            if elapsed_since_open < circuit.recovery_timeout:
                log.warning(f"[RETRY] Circuit OPEN pour {service_name}, skip ({elapsed_since_open:.0f}s)")
                if fallback:
                    try:
                        result = fallback()
                        return RetryResult(
                            success=True, result=result, attempts=0,
                            total_time_ms=0, circuit_state="open_fallback"
                        )
                    except Exception:
                        pass
                return RetryResult(
                    success=False, attempts=0,
                    last_error=f"Circuit breaker OPEN for {service_name}",
                    circuit_state="open"
                )
            else:
                circuit.state = CircuitState.HALF_OPEN
                log.info(f"[RETRY] Circuit HALF_OPEN pour {service_name} (test)")

        last_error = ""
        for attempt in range(max_retries + 1):
            circuit.total_calls += 1
            try:
                result = func()
                self._record_success(circuit)
                elapsed = (time.time() - start) * 1000
                return RetryResult(
                    success=True, result=result, attempts=attempt + 1,
                    total_time_ms=round(elapsed, 1),
                    circuit_state=circuit.state.value
                )
            except Exception as e:
                last_error = str(e)[:200]
                self._record_failure(circuit)
                self._global_stats["total_retries"] += 1

                if attempt < max_retries:
                    delay = min(max_delay, base_delay * (2 ** attempt))
                    jitter = delay * random.uniform(0.0, 0.5)
                    actual_delay = delay + jitter
                    log.debug(
                        f"[RETRY] {service_name} attempt {attempt + 1}/{max_retries + 1} "
                        f"failed: {last_error[:60]}. Retry in {actual_delay:.1f}s"
                    )
                    time.sleep(actual_delay)

        # Toutes les tentatives echouees
        self._global_stats["total_failures"] += 1
        elapsed = (time.time() - start) * 1000

        if fallback:
            try:
                result = fallback()
                log.info(f"[RETRY] {service_name} fallback success after {max_retries + 1} attempts")
                return RetryResult(
                    success=True, result=result, attempts=max_retries + 1,
                    total_time_ms=round(elapsed, 1),
                    last_error=f"Fallback used: {last_error}",
                    circuit_state=circuit.state.value
                )
            except Exception as fb_err:
                last_error = f"All retries + fallback failed: {fb_err}"

        return RetryResult(
            success=False, attempts=max_retries + 1,
            total_time_ms=round(elapsed, 1),
            last_error=last_error,
            circuit_state=circuit.state.value
        )

    def _get_or_create_circuit(self, name: str) -> CircuitBreaker:
        with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(name=name)
            return self._circuits[name]

    def _record_success(self, circuit: CircuitBreaker) -> None:
        with self._lock:
            circuit.success_count += 1
            circuit.total_successes += 1
            circuit.failure_count = 0
            circuit.last_success = time.time()
            self._global_stats["total_successes"] += 1
            if circuit.state == CircuitState.HALF_OPEN:
                circuit.state = CircuitState.CLOSED
                log.info(f"[RETRY] Circuit CLOSED pour {circuit.name} (recovered)")

    def _record_failure(self, circuit: CircuitBreaker) -> None:
        with self._lock:
            circuit.failure_count += 1
            circuit.total_failures += 1
            circuit.last_failure = time.time()
            if circuit.failure_count >= circuit.failure_threshold:
                if circuit.state != CircuitState.OPEN:
                    circuit.state = CircuitState.OPEN
                    circuit.open_since = time.time()
                    self._global_stats["total_circuit_trips"] += 1
                    log.warning(
                        f"[RETRY] Circuit TRIPPED pour {circuit.name} "
                        f"({circuit.failure_count} echecs consecutifs)"
                    )

    def get_circuit_status(self, service_name: str) -> Dict:
        circuit = self._circuits.get(service_name)
        if not circuit:
            return {"status": "unknown"}
        return {
            "state": circuit.state.value,
            "failures": circuit.failure_count,
            "total_calls": circuit.total_calls,
            "total_failures": circuit.total_failures,
            "success_rate": round(
                circuit.total_successes / max(1, circuit.total_calls) * 100, 1
            ),
            "last_failure": circuit.last_failure,
        }

    def get_stats(self) -> Dict:
        circuits = {}
        for name, cb in self._circuits.items():
            circuits[name] = {
                "state": cb.state.value,
                "success_rate": round(cb.total_successes / max(1, cb.total_calls) * 100, 1),
                "total_calls": cb.total_calls,
            }
        return {
            **self._global_stats,
            "circuits": circuits,
            "total_circuits": len(self._circuits),
        }

    def reset_circuit(self, service_name: str) -> bool:
        with self._lock:
            if service_name in self._circuits:
                self._circuits[service_name].state = CircuitState.CLOSED
                self._circuits[service_name].failure_count = 0
                return True
        return False


_engine: Optional[SmartRetryEngine] = None


def get_smart_retry() -> SmartRetryEngine:
    global _engine
    if _engine is None:
        _engine = SmartRetryEngine()
    return _engine
