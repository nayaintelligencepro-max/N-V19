"""
NAYA — Observation Bus WebSocket Server
Port 8899 — Broadcast l'état interne NAYA vers TORI
"""
import asyncio, json, logging, time
import websockets
from .bus import ObservationBus

log = logging.getLogger("NAYA.OBSBUS")

_bus = ObservationBus()
_server = None
_naya_system_ref = None

def set_naya_system(system):
    global _naya_system_ref
    _naya_system_ref = system

async def handler(ws):
    await _bus.register(ws)
    log.info(f"[OBSBUS] TORI connectée: {ws.remote_address}")
    
    # Envoyer snapshot immédiat au nouveau client
    if _naya_system_ref:
        try:
            snapshot = _naya_system_ref.get_status()
            await ws.send(json.dumps(ObservationBus.envelope(
                origin="SYSTEM", channel="state",
                scope="global", target="tori",
                payload={"type": "snapshot", "data": snapshot}
            )))
        except Exception:
            pass
    
    try:
        async for _ in ws:
            pass  # Read-only bus
    finally:
        await _bus.unregister(ws)
        log.debug(f"[OBSBUS] Client déconnecté")


async def broadcast_state(state: dict):
    """Broadcast l'état NAYA à tous les observateurs TORI."""
    msg = ObservationBus.envelope(
        origin="NAYA_CORE", channel="state",
        scope="global", target="tori",
        payload={"type": "state_update", "data": state, "ts": time.time()}
    )
    await _bus.emit(msg)


async def broadcast_event(event_type: str, data: dict, origin: str = "SYSTEM"):
    """Broadcast un événement spécifique."""
    msg = ObservationBus.envelope(
        origin=origin, channel="events",
        scope="system", target="tori",
        payload={"type": event_type, "data": data, "ts": time.time()}
    )
    await _bus.emit(msg)


def publish_sync(event_type: str, data: dict, origin: str = "SYSTEM"):
    """API synchrone — publie depuis n'importe quel thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast_event(event_type, data, origin))
    except Exception:
        pass


async def run_server(host="0.0.0.0", port=8899):
    global _server
    _server = await websockets.serve(handler, host, port)
    log.info(f"[OBSBUS] ✅ Démarré ws://{host}:{port}")
    return _server


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8899):
        log.info("[OBSBUS] Observation Bus ws://0.0.0.0:8899")
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
