"""
NAYA — Version Manager
Tracks system version, build info, and supports rollback metadata.
"""
import os
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

log = logging.getLogger("NAYA.VERSION")
ROOT = Path(__file__).parent.parent

CURRENT_VERSION = "12.0.0"
BUILD_DATE = "2026-03-26"
CODENAME = "SUPREME"


class VersionManager:
    """Manages system versioning, changelog, and rollback points."""

    def __init__(self):
        self._version = CURRENT_VERSION
        self._build_date = BUILD_DATE
        self._codename = CODENAME
        self._history_file = ROOT / "data" / "version_history.json"
        self._history: List[Dict] = []
        self._load_history()

    def _load_history(self):
        try:
            if self._history_file.exists():
                self._history = json.loads(self._history_file.read_text())
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text(json.dumps(self._history, indent=2))
        except Exception as exc:
            log.warning("Failed to save version history: %s", exc)

    def get_version(self) -> Dict[str, Any]:
        return {
            "version": self._version,
            "codename": self._codename,
            "build_date": self._build_date,
            "python": os.sys.version.split()[0],
            "environment": os.getenv("NAYA_ENV", "local"),
        }

    def record_deployment(self, notes: str = "") -> Dict:
        """Record a deployment event."""
        entry = {
            "version": self._version,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "environment": os.getenv("NAYA_ENV", "local"),
            "notes": notes,
            "checksum": self._compute_checksum(),
        }
        self._history.append(entry)
        self._save_history()
        log.info("Deployment recorded: v%s", self._version)
        return entry

    def get_history(self, limit: int = 10) -> List[Dict]:
        return self._history[-limit:]

    def can_rollback(self) -> bool:
        return len(self._history) >= 2

    def get_rollback_target(self) -> Optional[Dict]:
        if len(self._history) >= 2:
            return self._history[-2]
        return None

    def _compute_checksum(self) -> str:
        """Quick checksum of core files."""
        h = hashlib.md5()
        core_files = ["main.py", "requirements.txt", "Dockerfile"]
        for f in core_files:
            p = ROOT / f
            if p.exists():
                h.update(p.read_bytes())
        return h.hexdigest()[:12]

    def get_stats(self) -> Dict:
        return {
            "current": self._version,
            "deployments": len(self._history),
            "last_deployment": self._history[-1] if self._history else None,
            "can_rollback": self.can_rollback(),
        }


_VM: Optional[VersionManager] = None

def get_version_manager() -> VersionManager:
    global _VM
    if _VM is None:
        _VM = VersionManager()
    return _VM
