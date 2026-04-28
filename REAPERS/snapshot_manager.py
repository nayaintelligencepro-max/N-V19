"""NAYA V19 - REAPERS Snapshot Manager - Snapshots systeme pour recovery."""
import time, logging, json, shutil
from typing import Dict, List, Optional
from pathlib import Path
log = logging.getLogger("NAYA.REAPERS.SNAPSHOT")

SNAPSHOT_DIR = Path("data/cache/snapshots")

class ReapersSnapshotManager:
    """Cree et gere les snapshots du systeme pour recovery rapide."""

    MAX_SNAPSHOTS = 10

    def __init__(self):
        self._snapshots: List[Dict] = []
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, reason: str = "scheduled") -> Dict:
        snapshot_id = f"SNAP_{int(time.time())}"
        snapshot_path = SNAPSHOT_DIR / snapshot_id
        snapshot_path.mkdir(exist_ok=True)

        # Snapshot state files
        files_saved = 0
        for state_file in Path("data").rglob("*.json"):
            try:
                dest = snapshot_path / state_file.name
                shutil.copy2(state_file, dest)
                files_saved += 1
            except Exception:
                pass

        entry = {
            "id": snapshot_id, "reason": reason,
            "files": files_saved, "ts": time.time(),
            "path": str(snapshot_path)
        }
        self._snapshots.append(entry)
        self._cleanup_old()
        log.info(f"[SNAPSHOT] {snapshot_id}: {files_saved} fichiers sauvegardes")
        return entry

    def restore_snapshot(self, snapshot_id: str) -> Dict:
        snapshot_path = SNAPSHOT_DIR / snapshot_id
        if not snapshot_path.exists():
            return {"error": "snapshot_not_found"}
        restored = 0
        for f in snapshot_path.iterdir():
            try:
                dest = Path("data/cache") / f.name
                shutil.copy2(f, dest)
                restored += 1
            except Exception:
                pass
        log.info(f"[SNAPSHOT] Restaure: {snapshot_id} ({restored} fichiers)")
        return {"restored": True, "snapshot_id": snapshot_id, "files": restored}

    def _cleanup_old(self) -> None:
        if len(self._snapshots) > self.MAX_SNAPSHOTS:
            old = self._snapshots[:-self.MAX_SNAPSHOTS]
            for s in old:
                try:
                    shutil.rmtree(s["path"], ignore_errors=True)
                except Exception:
                    pass
            self._snapshots = self._snapshots[-self.MAX_SNAPSHOTS:]

    def list_snapshots(self) -> List[Dict]:
        return self._snapshots.copy()

    def get_stats(self) -> Dict:
        return {"total_snapshots": len(self._snapshots), "max": self.MAX_SNAPSHOTS}


# Backward-compatible alias
SnapshotManager = ReapersSnapshotManager
