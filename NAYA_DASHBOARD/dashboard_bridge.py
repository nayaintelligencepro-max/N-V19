"""NAYA V19 - Dashboard Bridge - Pont entre le backend et le dashboard TORI."""
import logging, time
from typing import Dict, Optional, Any

log = logging.getLogger("NAYA.DASHBOARD.BRIDGE")

class DashboardBridge:
    """Pont unifie entre le core NAYA et le dashboard TORI."""

    def __init__(self):
        self._last_snapshot: Dict = {}
        self._update_count = 0

    def get_system_snapshot(self) -> Dict:
        snapshot = {"ts": time.time(), "update": self._update_count}
        try:
            from naya_self_diagnostic.diagnostic import get_diagnostic
            snapshot["diagnostic"] = get_diagnostic().get_report()
        except Exception:
            snapshot["diagnostic"] = {"overall": "unavailable"}
        try:
            from naya_intention_loop.intention_loop import get_intention_loop
            snapshot["intention"] = get_intention_loop().get_stats()
        except Exception:
            snapshot["intention"] = {}
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            snapshot["memory"] = get_narrative_memory().get_stats()
        except Exception:
            snapshot["memory"] = {}
        try:
            from naya_guardian.guardian import get_guardian
            snapshot["guardian"] = get_guardian().status
        except Exception:
            snapshot["guardian"] = {}
        self._last_snapshot = snapshot
        self._update_count += 1
        return snapshot

    def push_event(self, event_type: str, data: Dict) -> None:
        log.debug(f"[BRIDGE] Event: {event_type}")

    def get_stats(self) -> Dict:
        return {"updates": self._update_count, "last_ts": self._last_snapshot.get("ts")}
