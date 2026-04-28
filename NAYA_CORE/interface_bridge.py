"""
NAYA — Interface Bridge
Connects NAYA_CORE internal events to external consumers:
Dashboard, API endpoints, WebSocket clients, Telegram.
Thread-safe event bus with subscriber pattern.
"""
import logging
import threading
import time
from typing import Dict, List, Any, Callable, Optional
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

log = logging.getLogger("NAYA.BRIDGE")


@dataclass
class BridgeEvent:
    event_type: str  # hunt.signal, revenue.payment, system.alert, decision.made
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: str = "info"  # debug, info, warning, critical


class InterfaceBridge:
    """Central event bridge — all modules publish here, all consumers subscribe."""

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: deque = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._event_count = 0
        self._started_at = datetime.now(timezone.utc).isoformat()

    def subscribe(self, event_pattern: str, callback: Callable[[BridgeEvent], None]):
        """Subscribe to events matching a pattern (e.g. 'hunt.*', 'revenue.payment')."""
        with self._lock:
            self._subscribers.setdefault(event_pattern, []).append(callback)
            log.debug("Subscriber added for pattern: %s", event_pattern)

    def publish(self, event: BridgeEvent):
        """Publish an event to all matching subscribers."""
        self._event_count += 1
        self._history.append(asdict(event))

        with self._lock:
            subscribers = list(self._subscribers.items())

        for pattern, callbacks in subscribers:
            if self._matches(event.event_type, pattern):
                for cb in callbacks:
                    try:
                        cb(event)
                    except Exception as exc:
                        log.warning("Subscriber error for %s: %s", pattern, exc)

    def emit(self, event_type: str, source: str, payload: Dict = None,
             severity: str = "info"):
        """Convenience method to publish."""
        self.publish(BridgeEvent(
            event_type=event_type, source=source,
            payload=payload or {}, severity=severity
        ))

    def get_history(self, limit: int = 50, event_type: str = None) -> List[Dict]:
        """Get recent events, optionally filtered."""
        events = list(self._history)
        if event_type:
            events = [e for e in events if self._matches(e["event_type"], event_type)]
        return events[-limit:]

    def get_stats(self) -> Dict:
        return {
            "total_events": self._event_count,
            "subscribers": {k: len(v) for k, v in self._subscribers.items()},
            "history_size": len(self._history),
            "started_at": self._started_at,
        }

    @staticmethod
    def _matches(event_type: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            return event_type.startswith(pattern[:-2])
        return event_type == pattern


# Singleton
_BRIDGE: Optional[InterfaceBridge] = None
_LOCK = threading.Lock()

def get_bridge() -> InterfaceBridge:
    global _BRIDGE
    if _BRIDGE is None:
        with _LOCK:
            if _BRIDGE is None:
                _BRIDGE = InterfaceBridge()
    return _BRIDGE


# Backward-compatible alias used by NAYA_INTERFACE
CoreInterfaceBridge = InterfaceBridge
