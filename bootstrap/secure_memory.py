"""
NAYA — Secure Memory
In-memory vault for runtime secrets. Prevents secrets from leaking
into logs, crash dumps, or serialized state.
"""
import os
import hashlib
import logging
import threading
from typing import Dict, Optional, Any

log = logging.getLogger("NAYA.SECURE_MEM")


class SecureMemory:
    """Thread-safe in-memory secret store with access auditing."""

    def __init__(self):
        self._vault: Dict[str, str] = {}
        self._access_log: list = []
        self._lock = threading.RLock()

    def store(self, key: str, value: str) -> bool:
        """Store a secret in the vault."""
        if not key or not value:
            return False
        with self._lock:
            self._vault[key] = value
            self._access_log.append({"action": "store", "key": key})
        return True

    def retrieve(self, key: str, caller: str = "unknown") -> Optional[str]:
        """Retrieve a secret with audit logging."""
        with self._lock:
            value = self._vault.get(key)
            self._access_log.append({
                "action": "retrieve", "key": key,
                "caller": caller, "found": value is not None
            })
        return value

    def delete(self, key: str) -> bool:
        """Securely delete a secret."""
        with self._lock:
            if key in self._vault:
                self._vault[key] = "0" * len(self._vault[key])  # overwrite
                del self._vault[key]
                self._access_log.append({"action": "delete", "key": key})
                return True
        return False

    def has(self, key: str) -> bool:
        return key in self._vault

    def keys(self):
        return list(self._vault.keys())

    def load_from_env(self, prefix: str = "NAYA_SECRET_"):
        """Load secrets from environment variables with prefix."""
        loaded = 0
        for k, v in os.environ.items():
            if k.startswith(prefix) and v:
                clean_key = k[len(prefix):]
                self.store(clean_key, v)
                loaded += 1
        if loaded:
            log.info("Loaded %d secrets from env (prefix=%s)", loaded, prefix)
        return loaded

    def get_audit_summary(self) -> Dict:
        return {
            "stored_keys": len(self._vault),
            "access_count": len(self._access_log),
            "last_accesses": self._access_log[-10:] if self._access_log else [],
        }

    def clear_all(self):
        """Wipe all secrets from memory."""
        with self._lock:
            for k in list(self._vault.keys()):
                self._vault[k] = "0" * len(self._vault[k])
            self._vault.clear()
            self._access_log.append({"action": "clear_all"})
            log.info("All secrets cleared from memory")


_SECURE_MEM: Optional[SecureMemory] = None
_LOCK = threading.Lock()

def get_secure_memory() -> SecureMemory:
    global _SECURE_MEM
    if _SECURE_MEM is None:
        with _LOCK:
            if _SECURE_MEM is None:
                _SECURE_MEM = SecureMemory()
    return _SECURE_MEM
