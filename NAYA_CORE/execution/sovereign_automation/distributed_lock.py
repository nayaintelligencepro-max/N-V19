"""NAYA V19 - Distributed Lock - Verrous distribues pour operations critiques."""
import time, logging, threading, uuid
from typing import Dict, Optional

log = logging.getLogger("NAYA.LOCK")

class DistributedLock:
    """Verrous distribues pour empecher les executions concurrentes."""

    DEFAULT_TTL = 30

    def __init__(self):
        self._locks: Dict[str, Dict] = {}
        self._rlock = threading.RLock()

    def acquire(self, resource: str, owner: str = None, ttl: int = None) -> Optional[str]:
        ttl = ttl or self.DEFAULT_TTL
        owner = owner or f"owner_{uuid.uuid4().hex[:8]}"
        with self._rlock:
            existing = self._locks.get(resource)
            if existing:
                if time.time() - existing["acquired_at"] > existing["ttl"]:
                    del self._locks[resource]
                else:
                    return None
            self._locks[resource] = {
                "owner": owner, "acquired_at": time.time(), "ttl": ttl
            }
            return owner

    def release(self, resource: str, owner: str) -> bool:
        with self._rlock:
            lock = self._locks.get(resource)
            if lock and lock["owner"] == owner:
                del self._locks[resource]
                return True
            return False

    def is_locked(self, resource: str) -> bool:
        with self._rlock:
            lock = self._locks.get(resource)
            if not lock:
                return False
            if time.time() - lock["acquired_at"] > lock["ttl"]:
                del self._locks[resource]
                return False
            return True

    def cleanup_expired(self) -> int:
        with self._rlock:
            now = time.time()
            expired = [r for r, l in self._locks.items() if now - l["acquired_at"] > l["ttl"]]
            for r in expired:
                del self._locks[r]
            return len(expired)

    def get_stats(self) -> Dict:
        with self._rlock:
            return {"active_locks": len(self._locks), "locks": list(self._locks.keys())}
