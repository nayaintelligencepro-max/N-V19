"""
NAYA Mobile Bridge v5.0
========================
Pont entre le dashboard Python et les apps mobile (PWA + Capacitor).
"""
import json, logging, hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

log = logging.getLogger("NAYA.MOBILE")

class MobileBridge:
    """Pont de communication mobile — WebSocket + REST."""

    def __init__(self, ws_url: str = "ws://localhost:8765"):
        self.ws_url = ws_url
        self._sessions: Dict[str, Dict] = {}
        self._push_queue: List[Dict] = []

    def create_session(self, device_id: str, platform: str = "pwa") -> Dict[str, Any]:
        session_id = hashlib.md5(f"{device_id}{datetime.now(timezone.utc)}".encode()).hexdigest()[:16]
        session = {"session_id": session_id, "device_id": device_id,
                   "platform": platform, "created_at": datetime.now(timezone.utc).isoformat(),
                   "active": True}
        self._sessions[session_id] = session
        return session

    def push_notification(self, session_id: str, event_type: str, payload: Dict) -> bool:
        if session_id not in self._sessions: return False
        notification = {"session_id": session_id, "type": event_type,
                        "payload": payload, "ts": datetime.now(timezone.utc).isoformat()}
        self._push_queue.append(notification)
        log.debug(f"Push queued: {event_type} -> {session_id}")
        return True

    def flush_queue(self) -> List[Dict]:
        notifications = list(self._push_queue)
        self._push_queue.clear()
        return notifications

    def get_session_status(self) -> Dict[str, Any]:
        active = [s for s in self._sessions.values() if s.get("active")]
        return {"total_sessions": len(self._sessions), "active_sessions": len(active),
                "push_queue_size": len(self._push_queue), "ws_url": self.ws_url}

    def build_pwa_manifest(self, app_name: str = "NAYA Intelligence") -> Dict:
        return {
            "name": app_name, "short_name": "NAYA",
            "description": "Intelligence décisionnelle NAYA",
            "start_url": "/", "display": "standalone",
            "background_color": "#0a0a0a", "theme_color": "#00ff88",
            "icons": [
                {"src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ],
            "capabilities": ["push_notifications", "offline_mode", "biometric_auth"]
        }


_BRIDGE: Optional[MobileBridge] = None

def get_mobile_bridge() -> MobileBridge:
    global _BRIDGE
    if _BRIDGE is None: _BRIDGE = MobileBridge()
    return _BRIDGE
