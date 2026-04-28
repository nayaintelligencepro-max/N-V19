"""NAYA V19 - Actor Registry - Registre des acteurs autorises."""
import logging, time, hashlib
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.GATEWAY.ACTORS")

class ActorRegistry:
    """Enregistre et authentifie les acteurs autorises a interagir avec NAYA."""

    SYSTEM_ACTORS = {
        "founder": {"level": "supreme", "permissions": ["*"], "description": "Fondatrice - acces total"},
        "system": {"level": "system", "permissions": ["execute", "monitor", "evolve"], "description": "Systeme interne"},
        "scheduler": {"level": "system", "permissions": ["execute", "hunt", "notify"], "description": "Planificateur"},
        "tori": {"level": "interface", "permissions": ["read", "command", "monitor"], "description": "Dashboard TORI"},
        "guardian": {"level": "system", "permissions": ["execute", "hunt", "notify", "escalate"], "description": "Mode Guardian"},
        "reapers": {"level": "system", "permissions": ["security", "isolate", "repair", "monitor"], "description": "Systeme immunitaire"},
    }

    def __init__(self):
        self._actors = dict(self.SYSTEM_ACTORS)
        self._sessions: Dict[str, Dict] = {}
        self._auth_log: List[Dict] = []

    def authenticate(self, actor_id: str, token: str = None) -> Dict:
        actor = self._actors.get(actor_id)
        if not actor:
            self._auth_log.append({"actor": actor_id, "result": "rejected", "reason": "unknown", "ts": time.time()})
            return {"authenticated": False, "reason": "Acteur inconnu"}
        session_id = hashlib.sha256(f"{actor_id}:{time.time()}".encode()).hexdigest()[:16]
        self._sessions[session_id] = {"actor": actor_id, "level": actor["level"], "created": time.time()}
        self._auth_log.append({"actor": actor_id, "result": "authenticated", "session": session_id, "ts": time.time()})
        return {"authenticated": True, "session_id": session_id, "level": actor["level"], "permissions": actor["permissions"]}

    def has_permission(self, actor_id: str, permission: str) -> bool:
        actor = self._actors.get(actor_id)
        if not actor:
            return False
        return "*" in actor["permissions"] or permission in actor["permissions"]

    def register_actor(self, actor_id: str, level: str, permissions: List[str], description: str = "") -> None:
        self._actors[actor_id] = {"level": level, "permissions": permissions, "description": description}
        log.info(f"[ACTORS] Registered: {actor_id} (level={level})")

    def get_active_sessions(self) -> List[Dict]:
        now = time.time()
        return [{"session": sid, **s} for sid, s in self._sessions.items() if now - s["created"] < 3600]

    def revoke_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_stats(self) -> Dict:
        return {
            "registered_actors": len(self._actors),
            "active_sessions": len(self.get_active_sessions()),
            "auth_attempts": len(self._auth_log),
            "actors": list(self._actors.keys())
        }


_registry = ActorRegistry()


def validate_actor(actor_id: str) -> bool:
    """Valide qu'un acteur est enregistré et autorisé."""
    return actor_id in _registry._actors
