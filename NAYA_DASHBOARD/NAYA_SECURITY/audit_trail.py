"""NAYA V19 - Audit Trail - Trace d audit de toutes les operations."""
import time, logging, json, hashlib
from typing import Dict, List
from pathlib import Path

log = logging.getLogger("NAYA.AUDIT")
AUDIT_FILE = Path("data/cache/audit_trail.json")

class AuditTrail:
    def __init__(self):
        self._entries: List[Dict] = []
        self._load()

    def log_action(self, actor: str, action: str, target: str,
                   details: Dict = None, outcome: str = "success") -> Dict:
        entry = {
            "id": hashlib.md5(f"{actor}{action}{time.time()}".encode()).hexdigest()[:12],
            "actor": actor, "action": action, "target": target,
            "details": details or {}, "outcome": outcome, "ts": time.time()
        }
        self._entries.append(entry)
        if len(self._entries) % 20 == 0:
            self._save()
        return entry

    def get_trail(self, actor: str = None, action: str = None, limit: int = 50) -> List:
        entries = self._entries
        if actor:
            entries = [e for e in entries if e["actor"] == actor]
        if action:
            entries = [e for e in entries if e["action"] == action]
        return entries[-limit:]

    def _save(self):
        try:
            AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
            AUDIT_FILE.write_text(json.dumps(self._entries[-1000:], default=str))
        except Exception:
            pass

    def _load(self):
        try:
            if AUDIT_FILE.exists():
                self._entries = json.loads(AUDIT_FILE.read_text())
        except Exception:
            self._entries = []

    def get_stats(self) -> Dict:
        return {"total_entries": len(self._entries)}
