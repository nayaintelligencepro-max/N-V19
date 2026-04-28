"""NAYA V19 - Idempotency Guard - Empeche les executions en double."""
import time, logging, hashlib
from typing import Dict, Optional

log = logging.getLogger("NAYA.IDEMPOTENCY")

class IdempotencyGuard:
    """Garantit qu une operation n est executee qu une seule fois."""

    TTL = 3600 * 24  # 24h

    def __init__(self):
        self._executed: Dict[str, Dict] = {}

    def generate_key(self, operation: str, params: Dict) -> str:
        payload = f"{operation}:{sorted(params.items())}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def check_and_mark(self, key: str) -> bool:
        """Retourne True si l operation peut etre executee (premiere fois)."""
        self._cleanup()
        if key in self._executed:
            log.debug(f"[IDEMPOTENCY] Operation {key} deja executee")
            return False
        self._executed[key] = {"ts": time.time(), "count": 1}
        return True

    def is_duplicate(self, key: str) -> bool:
        return key in self._executed

    def _cleanup(self) -> None:
        cutoff = time.time() - self.TTL
        expired = [k for k, v in self._executed.items() if v["ts"] < cutoff]
        for k in expired:
            del self._executed[k]

    def get_stats(self) -> Dict:
        return {"tracked_operations": len(self._executed)}
