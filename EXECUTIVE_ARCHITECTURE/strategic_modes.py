"""NAYA V19 - Strategic Modes - Modes strategiques adaptatifs."""
import time, logging
from typing import Dict
from enum import Enum
log = logging.getLogger("NAYA.EXEC.MODES")

class Mode(Enum):
    AGGRESSIVE = "aggressive"   # Max chasse, max outreach
    BALANCED = "balanced"       # Equilibre chasse/execution
    CONSERVATIVE = "conservative"  # Focus execution, peu de chasse
    SURVIVAL = "survival"       # Minimum vital, conservation ressources
    GROWTH = "growth"           # Investissement croissance

class StrategicModes:
    """Gere les modes strategiques du systeme selon le contexte."""

    MODE_CONFIGS = {
        Mode.AGGRESSIVE:   {"hunt_interval_s": 1800, "max_parallel": 4, "outreach_rate": 10, "risk_tolerance": 0.7},
        Mode.BALANCED:     {"hunt_interval_s": 3600, "max_parallel": 4, "outreach_rate": 5,  "risk_tolerance": 0.5},
        Mode.CONSERVATIVE: {"hunt_interval_s": 7200, "max_parallel": 4, "outreach_rate": 2,  "risk_tolerance": 0.3},
        Mode.SURVIVAL:     {"hunt_interval_s": 14400,"max_parallel": 4, "outreach_rate": 1,  "risk_tolerance": 0.1},
        Mode.GROWTH:       {"hunt_interval_s": 2400, "max_parallel": 4, "outreach_rate": 8,  "risk_tolerance": 0.6},
    }

    def __init__(self):
        self._current = Mode.BALANCED
        self._history: list = []

    def switch(self, mode: Mode, reason: str = "") -> Dict:
        old = self._current
        self._current = mode
        config = self.MODE_CONFIGS[mode]
        self._history.append({"from": old.value, "to": mode.value, "reason": reason, "ts": time.time()})
        log.info(f"[MODES] {old.value} -> {mode.value}: {reason}")
        return {"mode": mode.value, "config": config}

    def auto_select(self, weekly_revenue: float, target: float = 60000,
                    error_count: int = 0) -> Dict:
        ratio = weekly_revenue / target if target > 0 else 0
        if error_count > 10:
            return self.switch(Mode.SURVIVAL, "Trop d erreurs")
        if ratio < 0.3:
            return self.switch(Mode.AGGRESSIVE, f"Revenue {ratio:.0%} sous objectif")
        if ratio < 0.7:
            return self.switch(Mode.GROWTH, f"Revenue {ratio:.0%} en croissance")
        if ratio >= 1.0:
            return self.switch(Mode.BALANCED, f"Objectif atteint ({ratio:.0%})")
        return self.switch(Mode.BALANCED, "Mode par defaut")

    def get_current_config(self) -> Dict:
        return {"mode": self._current.value, "config": self.MODE_CONFIGS[self._current]}

    def get_stats(self) -> Dict:
        return {"current_mode": self._current.value, "mode_changes": len(self._history)}
