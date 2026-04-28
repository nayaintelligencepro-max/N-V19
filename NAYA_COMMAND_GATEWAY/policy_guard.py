"""NAYA V19 - Policy Guard - Garde les commandes selon les politiques."""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.GATEWAY.POLICY")

class PolicyGuard:
    """Filtre les commandes selon les politiques de securite et de gouvernance."""

    ALLOWED_ACTORS = {"founder", "system", "scheduler", "tori", "guardian"}
    RESTRICTED_COMMANDS = {
        "shutdown": {"required_actor": "founder", "requires_confirmation": True},
        "delete_data": {"required_actor": "founder", "requires_confirmation": True},
        "change_doctrine": {"required_actor": "founder", "requires_confirmation": True},
        "disable_reapers": {"required_actor": "founder", "requires_confirmation": True},
    }

    def __init__(self):
        self._blocked: List[Dict] = []
        self._allowed: List[Dict] = []

    def check(self, command: str, actor: str, params: Dict = None) -> Dict:
        """Verifie si une commande est autorisee."""
        if actor not in self.ALLOWED_ACTORS:
            self._blocked.append({"command": command, "actor": actor, "reason": "actor_unknown", "ts": time.time()})
            return {"allowed": False, "reason": f"Acteur {actor} non reconnu"}

        restriction = self.RESTRICTED_COMMANDS.get(command)
        if restriction:
            if actor != restriction["required_actor"]:
                self._blocked.append({"command": command, "actor": actor, "reason": "insufficient_rights", "ts": time.time()})
                return {"allowed": False, "reason": f"Commande {command} reservee a {restriction['required_actor']}"}
            if restriction.get("requires_confirmation"):
                return {"allowed": True, "requires_confirmation": True, "warning": f"Commande sensible: {command}"}

        self._allowed.append({"command": command, "actor": actor, "ts": time.time()})
        return {"allowed": True}

    def get_stats(self) -> Dict:
        return {"allowed": len(self._allowed), "blocked": len(self._blocked)}
