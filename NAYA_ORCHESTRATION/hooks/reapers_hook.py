"""NAYA Orchestration — REAPERS Hook"""
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.ORCH.REAPERS_HOOK")

class ReapersHook:
    """Hook REAPERS pour signaler événements critiques à l'orchestration."""

    def __init__(self):
        self._callbacks: Dict[str, list] = {}
        self._events_emitted = 0

    def emit(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        payload = payload or {}
        self._events_emitted += 1
        log.debug(f"[REAPERS_HOOK] Event: {event} | payload={payload}")
        for cb in self._callbacks.get(event, []):
            try:
                cb(event, payload)
            except Exception as e:
                log.warning(f"[REAPERS_HOOK] Callback error on {event}: {e}")

    def on(self, event: str, callback) -> None:
        """Register callback for a REAPERS event."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def emit_threat(self, threat_type: str, severity: str = "HIGH", details: str = "") -> None:
        """Shortcut for threat events."""
        self.emit("THREAT_DETECTED", {"type": threat_type, "severity": severity, "details": details})

    def emit_integrity_breach(self, target: str) -> None:
        """Shortcut for integrity breach events."""
        self.emit("INTEGRITY_BREACH", {"target": target, "action": "ISOLATE"})

    @property
    def stats(self) -> Dict:
        return {"events_emitted": self._events_emitted, "event_types": list(self._callbacks.keys())}
