"""NAYA V19 - Event Envelope - Format standard des evenements."""
import time, uuid
from typing import Dict, Any, Optional

class EventEnvelope:
    """Enveloppe standard pour tous les evenements du systeme."""

    @staticmethod
    def create(origin: str, channel: str, payload: Any,
               scope: str = "internal", target: str = "all",
               event_type: str = "event") -> Dict:
        return {
            "id": f"evt_{uuid.uuid4().hex[:10]}",
            "origin": origin, "channel": channel,
            "scope": scope, "target": target,
            "type": event_type, "payload": payload,
            "ts": time.time()
        }

    @staticmethod
    def system_event(module: str, action: str, data: Dict = None) -> Dict:
        return EventEnvelope.create(
            origin=module, channel="system",
            payload={"action": action, "data": data or {}},
            event_type="system"
        )

    @staticmethod
    def business_event(project: str, event_type: str, data: Dict = None) -> Dict:
        return EventEnvelope.create(
            origin=project, channel="business",
            payload={"event": event_type, "data": data or {}},
            event_type="business"
        )

    @staticmethod
    def revenue_event(amount: float, source: str, details: Dict = None) -> Dict:
        return EventEnvelope.create(
            origin="revenue_engine", channel="revenue",
            payload={"amount": amount, "source": source, "details": details or {}},
            event_type="revenue"
        )
