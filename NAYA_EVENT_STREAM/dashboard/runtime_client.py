"""NAYA V19 - Dashboard Runtime Client - Client WebSocket pour le dashboard."""
import logging, json, time
from typing import Dict, Optional, Callable
log = logging.getLogger("NAYA.EVENTS.CLIENT")

class RuntimeClient:
    def __init__(self, ws_url: str = "ws://localhost:8899"):
        self._ws_url = ws_url
        self._connected = False
        self._callbacks: list = []
        self._message_count = 0

    def on_message(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def connect(self) -> bool:
        log.info(f"[EVENTS-CLIENT] Connecting to {self._ws_url}")
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, data: Dict) -> bool:
        if not self._connected:
            return False
        self._message_count += 1
        return True

    def get_stats(self) -> Dict:
        return {"connected": self._connected, "messages": self._message_count, "url": self._ws_url}
