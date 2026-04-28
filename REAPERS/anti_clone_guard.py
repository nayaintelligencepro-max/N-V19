"""NAYA V19 - Anti-Clone Guard - Empeche le clonage non autorise du systeme."""
import hashlib, time, logging, os, platform
from typing import Dict
log = logging.getLogger("NAYA.REAPERS.ANTICLONE")

class AntiCloneGuard:
    """Detecte les tentatives de clonage du systeme."""

    def __init__(self):
        self._machine_id = self._get_machine_id()
        self._registered_machines: set = {self._machine_id}
        self._clone_attempts: list = []

    def _get_machine_id(self) -> str:
        parts = [platform.node(), platform.machine(), platform.system()]
        unique = ":".join(parts)
        return hashlib.sha256(unique.encode()).hexdigest()[:16]

    def verify_not_clone(self) -> Dict:
        current = self._get_machine_id()
        is_registered = current in self._registered_machines
        if not is_registered:
            self._clone_attempts.append({
                "machine_id": current, "ts": time.time(),
                "hostname": platform.node()
            })
            log.error(f"[ANTICLONE] Machine non enregistree detectee: {current}")
        return {
            "legitimate": is_registered,
            "machine_id": current,
            "registered_machines": len(self._registered_machines),
            "clone_attempts": len(self._clone_attempts)
        }

    def register_machine(self, machine_id: str = None) -> str:
        mid = machine_id or self._get_machine_id()
        self._registered_machines.add(mid)
        log.info(f"[ANTICLONE] Machine enregistree: {mid}")
        return mid

    def get_stats(self) -> Dict:
        return {
            "current_machine": self._machine_id,
            "registered": len(self._registered_machines),
            "clone_attempts": len(self._clone_attempts),
            "last_attempt": self._clone_attempts[-1] if self._clone_attempts else None
        }
