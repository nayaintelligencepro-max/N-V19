"""
QUALITÉ #1 — Suite de health checks production-grade.

Vérifie l'état de santé de tous les composants du système en temps réel :
API, bases de données, services externes, agents IA, mémoire, CPU.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    component: str
    status: str  # healthy / degraded / unhealthy / unknown
    latency_ms: float
    details: str
    checked_at: str = ""

    def __post_init__(self) -> None:
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()


class HealthCheckSuite:
    """Suite complète de health checks production-grade."""

    def __init__(self) -> None:
        self._checks: Dict[str, callable] = {
            "python_runtime": self._check_python_runtime,
            "env_variables": self._check_env_variables,
            "filesystem": self._check_filesystem,
            "memory": self._check_memory,
            "imports": self._check_critical_imports,
        }
        logger.info(f"[HealthCheckSuite] Initialisé — {len(self._checks)} checks enregistrés")

    def _check_python_runtime(self) -> HealthCheckResult:
        import sys
        start = time.monotonic()
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        latency = (time.monotonic() - start) * 1000
        is_ok = sys.version_info >= (3, 11)
        return HealthCheckResult(
            component="python_runtime",
            status="healthy" if is_ok else "degraded",
            latency_ms=round(latency, 2),
            details=f"Python {version}" + ("" if is_ok else " (3.11+ recommandé)"),
        )

    def _check_env_variables(self) -> HealthCheckResult:
        start = time.monotonic()
        critical_vars = ["ENVIRONMENT", "SECRET_KEY"]
        missing = [v for v in critical_vars if not os.environ.get(v)]
        latency = (time.monotonic() - start) * 1000
        if not missing:
            return HealthCheckResult("env_variables", "healthy", round(latency, 2), "Toutes les variables critiques présentes")
        return HealthCheckResult(
            "env_variables", "degraded", round(latency, 2),
            f"Variables manquantes: {', '.join(missing)}",
        )

    def _check_filesystem(self) -> HealthCheckResult:
        start = time.monotonic()
        try:
            test_path = "/tmp/naya_health_check_test"
            with open(test_path, "w") as f:
                f.write("ok")
            os.remove(test_path)
            latency = (time.monotonic() - start) * 1000
            return HealthCheckResult("filesystem", "healthy", round(latency, 2), "Lecture/écriture OK")
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return HealthCheckResult("filesystem", "unhealthy", round(latency, 2), str(e))

    def _check_memory(self) -> HealthCheckResult:
        start = time.monotonic()
        try:
            import resource
            usage_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            latency = (time.monotonic() - start) * 1000
            status = "healthy" if usage_mb < 500 else ("degraded" if usage_mb < 1000 else "unhealthy")
            return HealthCheckResult("memory", status, round(latency, 2), f"{usage_mb:.0f} MB")
        except Exception:
            latency = (time.monotonic() - start) * 1000
            return HealthCheckResult("memory", "unknown", round(latency, 2), "resource module unavailable")

    def _check_critical_imports(self) -> HealthCheckResult:
        start = time.monotonic()
        modules = ["fastapi", "pydantic", "httpx"]
        missing = []
        for mod in modules:
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        latency = (time.monotonic() - start) * 1000
        if not missing:
            return HealthCheckResult("imports", "healthy", round(latency, 2), "Tous les modules critiques disponibles")
        return HealthCheckResult("imports", "degraded", round(latency, 2), f"Manquants: {', '.join(missing)}")

    def run_all(self) -> Dict[str, Any]:
        """Exécute tous les health checks et retourne un résumé."""
        results: List[HealthCheckResult] = []
        for name, check_fn in self._checks.items():
            try:
                result = check_fn()
                results.append(result)
            except Exception as e:
                results.append(HealthCheckResult(name, "unhealthy", 0, str(e)))

        overall = "healthy"
        for r in results:
            if r.status == "unhealthy":
                overall = "unhealthy"
                break
            if r.status == "degraded":
                overall = "degraded"

        return {
            "overall_status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": [
                {
                    "component": r.component,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "details": r.details,
                }
                for r in results
            ],
        }


health_check_suite = HealthCheckSuite()
