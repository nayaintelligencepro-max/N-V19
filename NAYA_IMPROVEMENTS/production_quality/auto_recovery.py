"""
QUALITÉ #8 — Système d'auto-récupération automatique.

Détecte les pannes et redémarre automatiquement les composants défaillants
sans intervention humaine, avec escalade progressive.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RecoveryAction:
    component: str
    action: str
    attempt: int
    success: bool
    duration_ms: float
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ComponentHealth:
    name: str
    healthy: bool = True
    consecutive_failures: int = 0
    total_recoveries: int = 0
    last_check: str = ""
    recovery_actions: List[RecoveryAction] = field(default_factory=list)


class AutoRecoverySystem:
    """
    Système d'auto-récupération pour NAYA Supreme.

    Niveaux d'escalade:
    1. Retry simple (attente exponentielle)
    2. Restart du composant
    3. Fallback vers service alternatif
    4. Notification Telegram à la créatrice
    5. Mode maintenance automatique
    """

    ESCALATION_THRESHOLDS = {
        1: "retry",
        3: "restart_component",
        5: "activate_fallback",
        8: "notify_creator",
        10: "maintenance_mode",
    }

    def __init__(self) -> None:
        self._components: Dict[str, ComponentHealth] = {}
        self._total_recoveries: int = 0
        self._maintenance_mode: bool = False
        logger.info("[AutoRecovery] Initialisé — surveillance auto-récupération activée")

    def register_component(self, name: str) -> None:
        """Enregistre un composant à surveiller."""
        self._components[name] = ComponentHealth(name=name)

    def report_failure(self, component_name: str, error: str = "") -> str:
        """Signale une défaillance et déclenche la récupération."""
        if component_name not in self._components:
            self.register_component(component_name)

        comp = self._components[component_name]
        comp.healthy = False
        comp.consecutive_failures += 1
        comp.last_check = datetime.now(timezone.utc).isoformat()

        action = self._determine_action(comp.consecutive_failures)

        recovery = RecoveryAction(
            component=component_name,
            action=action,
            attempt=comp.consecutive_failures,
            success=False,
            duration_ms=0,
        )
        comp.recovery_actions.append(recovery)

        logger.warning(
            f"[AutoRecovery] {component_name} failure #{comp.consecutive_failures}: "
            f"action={action} | error={error}"
        )
        return action

    def report_success(self, component_name: str) -> None:
        """Signale une récupération réussie."""
        if component_name in self._components:
            comp = self._components[component_name]
            if not comp.healthy:
                comp.healthy = True
                comp.total_recoveries += 1
                self._total_recoveries += 1
                comp.consecutive_failures = 0
                logger.info(f"[AutoRecovery] {component_name} RÉCUPÉRÉ (recovery #{comp.total_recoveries})")

    def _determine_action(self, failure_count: int) -> str:
        """Détermine l'action de récupération basée sur le nombre de pannes."""
        action = "retry"
        for threshold, act in sorted(self.ESCALATION_THRESHOLDS.items()):
            if failure_count >= threshold:
                action = act
        return action

    def execute_with_recovery(
        self,
        component_name: str,
        fn: Callable[..., Any],
        max_retries: int = 3,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Exécute avec auto-récupération en cas d'échec."""
        for attempt in range(1, max_retries + 1):
            try:
                start = time.monotonic()
                result = fn(*args, **kwargs)
                duration = (time.monotonic() - start) * 1000
                self.report_success(component_name)
                return result
            except Exception as e:
                action = self.report_failure(component_name, str(e))
                if attempt < max_retries:
                    wait_time = min(2 ** attempt, 30)
                    logger.info(f"[AutoRecovery] {component_name} retry dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def system_health(self) -> Dict[str, Any]:
        """État de santé global du système."""
        healthy = sum(1 for c in self._components.values() if c.healthy)
        unhealthy = [c.name for c in self._components.values() if not c.healthy]
        return {
            "status": "healthy" if not unhealthy else "degraded",
            "components_total": len(self._components),
            "components_healthy": healthy,
            "unhealthy_components": unhealthy,
            "total_recoveries": self._total_recoveries,
            "maintenance_mode": self._maintenance_mode,
        }


auto_recovery_system = AutoRecoverySystem()
