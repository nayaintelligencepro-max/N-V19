"""NAYA V19 - Mode chasse - Configure le mode de chasse actif"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_HUNT_MODE")

class EngineHuntMode:
    """Configure le mode de chasse actif."""

    def __init__(self):
        self._log: List[Dict] = []

    MODES = {
        "stealth": {"scan_interval": 1800, "outreach": False, "passive_only": True},
        "active": {"scan_interval": 3600, "outreach": True, "passive_only": False},
        "aggressive": {"scan_interval": 900, "outreach": True, "passive_only": False, "multi_channel": True},
        "guardian": {"scan_interval": 1800, "outreach": True, "passive_only": False, "autonomous": True},
    }

    def get_mode_config(self, mode: str = "active") -> Dict:
        return self.MODES.get(mode, self.MODES["active"])

    def recommend_mode(self, revenue_vs_target: float) -> str:
        if revenue_vs_target < 0.3: return "aggressive"
        if revenue_vs_target < 0.7: return "active"
        return "stealth"

    def get_stats(self) -> Dict:
        return {"module": "engine_hunt_mode", "log_size": len(self._log)}
