"""Moteur de résilience et modes de survie NAYA."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict


log = logging.getLogger(__name__)


class ResilienceMode(str, Enum):
    FULL = "FULL"
    HYBRID = "HYBRID"
    CLOUD = "CLOUD"
    OFFLINE = "OFFLINE"


class ResilienceEngine:
    """Gère le mode de fonctionnement en cas de défaillance."""

    def __init__(self) -> None:
        self.mode = ResilienceMode.FULL

    def switch_mode(self, mode: ResilienceMode, reason: str) -> Dict[str, str]:
        """Bascule vers un nouveau mode avec raison tracée."""
        old = self.mode
        self.mode = mode
        log.warning("Resilience mode switch: %s -> %s (%s)", old, mode, reason)
        return {"old_mode": old.value, "new_mode": mode.value, "reason": reason}

    def handle_agent_failure(self, agent_name: str) -> Dict[str, str]:
        """Politique simple de dégradation progressive."""
        if self.mode == ResilienceMode.FULL:
            return self.switch_mode(ResilienceMode.HYBRID, f"agent_failure:{agent_name}")
        if self.mode == ResilienceMode.HYBRID:
            return self.switch_mode(ResilienceMode.CLOUD, f"agent_failure:{agent_name}")
        return {"old_mode": self.mode.value, "new_mode": self.mode.value, "reason": "already_degraded"}

    def status(self) -> Dict[str, str]:
        """État courant du mode de résilience."""
        return {"mode": self.mode.value}


resilience_engine = ResilienceEngine()
