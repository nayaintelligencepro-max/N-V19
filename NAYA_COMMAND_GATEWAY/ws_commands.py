"""
NAYA — Command Gateway WebSocket Server
Port 8766 — Reçoit les intentions TORI et les dispatche vers NAYA_CORE
"""
import asyncio, json, os, logging, time
import websockets
from .intent_schema import create_intent
from .gateway import CommandGateway

log = logging.getLogger("NAYA.CMDGW")

# Journal simplifié sans fichier clé obligatoire
class SimpleJournal:
    def __init__(self):
        self.entries = []
    def log(self, intent_dict):
        self.entries.append({**intent_dict, "_ts": time.time()})
        if len(self.entries) > 1000:
            self.entries = self.entries[-500:]

_journal = SimpleJournal()
_gateway = CommandGateway(_journal)

# Référence vers le système NAYA (injectée au boot)
_naya_system = None

def set_naya_system(system):
    global _naya_system
    _naya_system = system

async def _dispatch_to_naya(text: str) -> dict:
    """Dispatch l'intention texte vers NAYA et retourne la réponse."""
    if not _naya_system:
        return {"response": "NAYA non initialisée", "type": "error"}
    
    try:
        # Enregistrer l'activité humaine
        if hasattr(_naya_system, 'sovereign_engine') and _naya_system.sovereign_engine:
            _naya_system.sovereign_engine.register_human_activity()
        
        brain = getattr(_naya_system, '_brain', None)
        if brain and brain.available:
            from NAYA_CORE.execution.naya_brain import TaskType
            prompt = f"""Tu es NAYA, un système exécutif autonome souverain.
Stéphanie t'envoie ce message depuis son cockpit TORI: "{text}"
Réponds directement, clairement, en français. Max 200 mots."""
            r = brain.think(prompt, TaskType.STRATEGIC)
            return {"response": r.text, "type": "naya_response", "voice": True}
        else:
            # Réponse système sans LLM
            return {"response": f"NAYA reçoit: '{text}' — LLM non configuré, système opérationnel.", 
                    "type": "system_ack", "voice": False}
    except Exception as e:
        return {"response": f"Erreur: {str(e)[:100]}", "type": "error"}

async def handler(websocket):
    remote = websocket.remote_address
    log.info(f"[CMDGW] Connexion TORI: {remote}")
    
    try:
        await websocket.send(json.dumps({
            "type": "gateway_ready",
            "message": "NAYA Command Gateway opérationnel",
            "ts": time.time()
        }))
        
        async for msg in websocket:
            try:
                data = json.loads(msg)
                log.debug(f"[CMDGW] Intent reçu: {data.get('intent','?')} | text: {str(data.get('text',''))[:50]}")
                
                # Créer un intent formaté
                intent = create_intent(
                    actor={"id": "tori", "role": "sovereign"},
                    category="supervision",
                    action=data.get("intent", "USER_MESSAGE"),
                    context={"text": data.get("text", ""), "ts": data.get("timestamp", time.time())}
                )
                
                # Passer par la gateway sécurisée
                gw_result = _gateway.handle(intent)
                
                if gw_result.get("status") == "accepted":
                    # Dispatcher vers NAYA
                    naya_resp = await _dispatch_to_naya(data.get("text", ""))
                    await websocket.send(json.dumps({
                        **naya_resp,
                        "intent_id": intent.intent_id,
                        "gateway": gw_result,
                        "ts": time.time()
                    }))
                else:
                    await websocket.send(json.dumps({
                        "type": "rejected",
                        "reason": gw_result.get("reason"),
                        "ts": time.time()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"type": "error", "reason": "invalid_json"}))
            except Exception as e:
                log.error(f"[CMDGW] Handler error: {e}")
                await websocket.send(json.dumps({"type": "error", "reason": str(e)[:100]}))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    log.info(f"[CMDGW] TORI déconnectée: {remote}")


async def run_server(host="127.0.0.1", port=8766):
    """Lance le serveur Command Gateway."""
    server = await websockets.serve(handler, host, port)
    log.info(f"[CMDGW] ✅ Démarré ws://{host}:{port}")
    return server


async def main():
    async with websockets.serve(handler, "127.0.0.1", 8766):
        log.info("[CMDGW] Command Gateway ws://127.0.0.1:8766")
        await asyncio.Future()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
