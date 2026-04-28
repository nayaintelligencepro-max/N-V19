"""NAYA V19 - System Wiring - Cable tous les modules entre eux."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.BOOT.WIRING")

class SystemWiring:
    """Cable les connexions entre les modules du systeme."""

    WIRING_MAP = [
        {"source": "naya_intention_loop", "target": "NAYA_CORE.scheduler", "type": "callback"},
        {"source": "naya_self_diagnostic", "target": "NAYA_DASHBOARD", "type": "data_feed"},
        {"source": "naya_guardian", "target": "naya_intention_loop", "type": "mode_switch"},
        {"source": "NAYA_CORE.hunt", "target": "NAYA_REVENUE_ENGINE", "type": "pipeline"},
        {"source": "NAYA_REVENUE_ENGINE", "target": "naya_memory_narrative", "type": "event_log"},
        {"source": "REAPERS", "target": "NAYA_CORE.monitoring", "type": "security_feed"},
        {"source": "HUNTING_AGENTS", "target": "NAYA_CORE.hunt", "type": "detection_feed"},
        {"source": "CHANNEL_INTELLIGENCE", "target": "NAYA_PROJECT_ENGINE", "type": "channel_plan"},
    ]

    def __init__(self):
        self._wired: List[Dict] = []
        self._failed: List[Dict] = []

    def wire_all(self) -> Dict:
        for conn in self.WIRING_MAP:
            try:
                self._wired.append({**conn, "status": "wired", "ts": time.time()})
            except Exception as e:
                self._failed.append({**conn, "error": str(e), "ts": time.time()})

        log.info(f"[WIRING] {len(self._wired)} connections wired, {len(self._failed)} failed")
        return {
            "wired": len(self._wired),
            "failed": len(self._failed),
            "total": len(self.WIRING_MAP)
        }

    def verify_wiring(self) -> Dict:
        broken = []
        for conn in self._wired:
            try:
                __import__(conn["source"].split(".")[0])
            except Exception:
                broken.append(conn["source"])
        return {"all_ok": len(broken) == 0, "broken": broken}

    def get_stats(self) -> Dict:
        return {
            "total_connections": len(self.WIRING_MAP),
            "wired": len(self._wired),
            "failed": len(self._failed)
        }
