"""
NAYA — Event Stream WebSocket Server
Port 8765 — Pousse le flux d'événements NAYA vers TORI en temps réel
"""
import asyncio, json, logging, time
import websockets
from .event_envelope import EventEnvelope

log = logging.getLogger("NAYA.EVENTSTREAM")

class EventStreamServer:

    def __init__(self):
        self.clients = set()
        self._buffer = []          # Historique 500 derniers events
        self._seq = 0
        self._server = None

    async def handler(self, websocket):
        self.clients.add(websocket)
        remote = websocket.remote_address
        log.info(f"[EVENTSTREAM] TORI connectée: {remote} — {len(self.clients)} clients")
        
        try:
            # Envoyer l'historique récent au nouveau client
            if self._buffer:
                replay = self._buffer[-20:]  # 20 derniers events
                await websocket.send(json.dumps({
                    "type": "replay",
                    "events": replay,
                    "count": len(replay)
                }))
            
            # Ping keepalive
            while True:
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=30.0)
                except asyncio.TimeoutError:
                    await websocket.send(json.dumps({"type": "ping", "ts": time.time()}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            log.debug(f"[EVENTSTREAM] Client déconnecté — {len(self.clients)} restants")

    async def broadcast(self, event: dict):
        """Broadcast un événement à tous les clients TORI connectés."""
        if not self.clients:
            return
        
        self._seq += 1
        event["seq"] = self._seq
        event["_ts"] = time.time()
        
        # Stocker dans le buffer
        self._buffer.append(event)
        if len(self._buffer) > 500:
            self._buffer = self._buffer[-500:]
        
        message = json.dumps(event)
        disconnected = set()
        for client in list(self.clients):
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        self.clients -= disconnected

    def publish(self, source: str, module: str, kind: str, level: str = "INFO", payload: dict = None, tags: list = None):
        """API synchrone pour publier un événement depuis n'importe où."""
        envelope = EventEnvelope.create(
            source=source, module=module, kind=kind,
            level=level, payload=payload or {}, tags=tags or []
        )
        event = envelope.to_dict()
        
        # Essayer de broadcaster si loop asyncio disponible
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.broadcast(event))
            else:
                self._buffer.append(event)
        except Exception:
            self._buffer.append(event)
        
        return event

    def publish_sovereign_cycle(self, cycle_dict: dict):
        """Publie un cycle souverain vers TORI."""
        return self.publish(
            source="SOVEREIGN", module="naya_sovereign_engine",
            kind="SOVEREIGN_CYCLE", level="INFO",
            payload=cycle_dict,
            tags=["hunt", "cycle", "autonomous"]
        )

    def publish_pain_detected(self, pain: dict, sector: str):
        """Publie une douleur détectée vers TORI."""
        return self.publish(
            source="HUNT", module="super_brain_v6",
            kind="PAIN_DETECTED", level="SUCCESS",
            payload={**pain, "sector": sector},
            tags=["pain", "opportunity", sector]
        )

    def publish_offer_created(self, offer: dict, sector: str):
        """Publie une offre créée vers TORI."""
        return self.publish(
            source="HUNT", module="business_factory",
            kind="OFFER_CREATED", level="SUCCESS",
            payload={**offer, "sector": sector},
            tags=["offer", "revenue", sector]
        )

    def publish_mission(self, mission_type: str, status: str, result: dict = None):
        """Publie l'état d'une mission vers TORI."""
        return self.publish(
            source="AUTONOMOUS", module="autonomous_engine",
            kind=f"MISSION_{status.upper()}",
            level="INFO" if status != "failed" else "ERROR",
            payload={"mission_type": mission_type, "status": status, **(result or {})},
            tags=["mission", mission_type.lower()]
        )

    def publish_reapers_event(self, event_type: str, detail: dict = None):
        """Publie un événement REAPERS vers TORI."""
        return self.publish(
            source="REAPERS", module="reapers_core",
            kind=f"REAPERS_{event_type.upper()}",
            level="CRITICAL" if "THREAT" in event_type.upper() else "WARNING",
            payload=detail or {},
            tags=["security", "reapers", event_type.lower()]
        )

    def publish_system(self, message: str, level: str = "INFO", module: str = "system"):
        """Publie un événement système vers TORI."""
        return self.publish(
            source="SYSTEM", module=module,
            kind="SYSTEM_EVENT", level=level,
            payload={"message": message},
            tags=["system"]
        )

    async def start(self, host="0.0.0.0", port=8765):
        self._server = await websockets.serve(self.handler, host, port)
        log.info(f"[EVENTSTREAM] ✅ Démarré ws://{host}:{port}")
        return self._server

    def get_stats(self):
        return {
            "clients_connected": len(self.clients),
            "events_buffered": len(self._buffer),
            "total_published": self._seq,
        }


# Singleton global
_event_stream_server: EventStreamServer = None

def get_event_stream_server() -> EventStreamServer:
    global _event_stream_server
    if _event_stream_server is None:
        _event_stream_server = EventStreamServer()
    return _event_stream_server
