"""NAYA V19 - Degradation Control - Gere le mode degrade du systeme."""
import time, logging
from typing import Dict, List
from enum import Enum

log = logging.getLogger("NAYA.DEGRADATION")

class SystemMode(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"
    EMERGENCY = "emergency"

class DegradationControl:
    """Controle les modes degrades: le systeme tourne toujours, meme affaibli."""

    CAPABILITY_PRIORITIES = [
        ("hunt_detection", 1), ("offer_creation", 2), ("payment_processing", 3),
        ("outreach", 4), ("monitoring", 5), ("analytics", 6), ("evolution", 7),
    ]

    def __init__(self):
        self._mode = SystemMode.FULL
        self._disabled: List[str] = []
        self._degradation_history: List[Dict] = []

    def enter_degraded(self, reason: str, disable: List[str] = None) -> Dict:
        old = self._mode
        self._mode = SystemMode.DEGRADED
        self._disabled = disable or []
        self._degradation_history.append({
            "from": old.value, "to": "degraded", "reason": reason,
            "disabled": self._disabled, "ts": time.time()
        })
        log.warning(f"[DEGRADATION] Mode degrade: {reason} | Desactive: {self._disabled}")
        return {"mode": self._mode.value, "disabled": self._disabled}

    def restore_full(self) -> Dict:
        if self._mode == SystemMode.FULL:
            return {"mode": "full", "message": "Deja en mode complet"}
        old = self._mode
        self._mode = SystemMode.FULL
        self._disabled.clear()
        self._degradation_history.append({
            "from": old.value, "to": "full", "reason": "restoration", "ts": time.time()
        })
        log.info("[DEGRADATION] Mode complet restaure")
        return {"mode": "full", "restored": True}

    def is_capability_available(self, capability: str) -> bool:
        return capability not in self._disabled

    def get_available_capabilities(self) -> List[str]:
        return [c for c, _ in self.CAPABILITY_PRIORITIES if c not in self._disabled]

    def auto_degrade_on_resource_shortage(self, available_resources: Dict) -> Dict:
        llm_ok = available_resources.get("llm", False)
        db_ok = available_resources.get("database", True)
        net_ok = available_resources.get("network", True)

        if not db_ok:
            return self.enter_degraded("Database indisponible", ["analytics", "evolution"])
        if not llm_ok:
            return self.enter_degraded("LLM indisponible", ["offer_creation", "analytics"])
        if not net_ok:
            return self.enter_degraded("Reseau indisponible", ["outreach", "hunt_detection"])
        return {"mode": self._mode.value, "all_ok": True}

    def get_stats(self) -> Dict:
        return {
            "current_mode": self._mode.value,
            "disabled_capabilities": self._disabled,
            "available_capabilities": self.get_available_capabilities(),
            "degradation_events": len(self._degradation_history),
            "last_event": self._degradation_history[-1] if self._degradation_history else None
        }
