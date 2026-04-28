"""NAYA V19 - Observation Bus - Bus d observation pour TORI."""
import asyncio, json, logging, time
from typing import Set, Dict, Any
log = logging.getLogger("NAYA.OBSBUS")

class ObservationBus:
    def __init__(self):
        self._clients: Set = set()
        self._event_count = 0

    async def register(self, ws) -> None:
        self._clients.add(ws)

    async def unregister(self, ws) -> None:
        self._clients.discard(ws)

    async def emit(self, message: Dict) -> int:
        sent = 0
        dead = set()
        for ws in self._clients:
            try:
                await ws.send(json.dumps(message))
                sent += 1
            except Exception:
                dead.add(ws)
        self._clients -= dead
        self._event_count += sent
        return sent

    @staticmethod
    def envelope(origin: str, channel: str, scope: str,
                 target: str, payload: Any) -> Dict:
        return {
            "origin": origin, "channel": channel,
            "scope": scope, "target": target,
            "payload": payload, "ts": time.time()
        }

    def get_stats(self) -> Dict:
        return {"clients": len(self._clients), "events_sent": self._event_count}
