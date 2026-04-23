"""NAYA V19 - Secure Memory Manager - Gestion securisee de la memoire."""
import logging, os, hashlib, time
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.KERNEL.MEMORY")

class SecureMemoryManager:
    """Gere la memoire securisee du systeme avec chiffrement leger."""

    def __init__(self):
        self._secure_store: Dict[str, Dict] = {}
        self._access_log: list = []
        self._encryption_key = os.getenv("NAYA_SECRET_KEY", "naya_default_key_change_me")

    def store_secure(self, key: str, value: Any, classification: str = "internal") -> None:
        """Stocke une valeur de maniere securisee."""
        hashed_key = self._hash(key)
        self._secure_store[hashed_key] = {
            "value": value, "classification": classification,
            "stored_at": time.time(), "original_key": key
        }
        self._access_log.append({"action": "store", "key": key, "ts": time.time()})

    def retrieve_secure(self, key: str) -> Optional[Any]:
        hashed_key = self._hash(key)
        entry = self._secure_store.get(hashed_key)
        if entry:
            self._access_log.append({"action": "retrieve", "key": key, "ts": time.time()})
            return entry["value"]
        return None

    def delete_secure(self, key: str) -> bool:
        hashed_key = self._hash(key)
        if hashed_key in self._secure_store:
            del self._secure_store[hashed_key]
            self._access_log.append({"action": "delete", "key": key, "ts": time.time()})
            return True
        return False

    def wipe_all(self) -> int:
        """Efface toute la memoire securisee."""
        count = len(self._secure_store)
        self._secure_store.clear()
        self._access_log.append({"action": "wipe", "count": count, "ts": time.time()})
        log.info(f"[SECURE-MEM] Wipe: {count} entries effacees")
        return count

    def _hash(self, key: str) -> str:
        return hashlib.sha256(f"{self._encryption_key}:{key}".encode()).hexdigest()[:16]

    def get_stats(self) -> Dict:
        return {
            "stored_entries": len(self._secure_store),
            "access_log_size": len(self._access_log),
            "classifications": list(set(e["classification"] for e in self._secure_store.values()))
        }
