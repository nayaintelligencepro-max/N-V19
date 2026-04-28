"""
NAYA SUPREME V19.5 — AMÉLIORATION #13 : BACKUP & DISASTER RECOVERY
═══════════════════════════════════════════════════════════════════════
Sauvegarde automatique des données critiques.
  - Prospects et pipeline
  - Paramètres du learner (autonomous_learner.json)
  - Mémoire vectorielle
  - Configuration système
  - Contrat d'existence

Fréquence : quotidienne + avant chaque déploiement.
Rétention : 30 jours de snapshots.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.BACKUP")


@dataclass
class BackupMetadata:
    backup_id: str
    timestamp: str
    files_backed_up: int
    total_size_bytes: int
    backup_type: str
    status: str = "completed"
    checksum: str = ""


@dataclass
class RestoreResult:
    success: bool
    files_restored: int
    errors: List[str]
    restored_from: str


CRITICAL_FILES = [
    "contrat d'existence de NAYA par sa creatrice.txt",
    "SYSTEM_IDENTITY.ini",
    ".env.example",
    "data/cache/autonomous_learner.json",
    "data/cache/prospect_memory.json",
    "data/cache/offer_memory.json",
    "data/cache/pipeline_state.json",
]

CRITICAL_DIRS = [
    "NAYA_CORE",
    "NAYA_IMPROVEMENTS",
    "CONSTITUTION",
]


class BackupEngine:
    """
    Sauvegarde et restauration automatique des données critiques.
    """

    def __init__(self, backup_root: Optional[Path] = None) -> None:
        self.backup_root = backup_root or Path("data/backups")
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.history: List[BackupMetadata] = []
        self.retention_days = 30

    def create_backup(
        self,
        project_root: Path,
        backup_type: str = "daily",
    ) -> BackupMetadata:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{backup_type}_{timestamp}"
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        files_backed = 0
        total_size = 0
        checksums = []

        for rel_path in CRITICAL_FILES:
            src = project_root / rel_path
            if src.exists():
                dst = backup_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                size = src.stat().st_size
                total_size += size
                files_backed += 1
                checksums.append(self._file_checksum(src))

        for rel_dir in CRITICAL_DIRS:
            src_dir = project_root / rel_dir
            if src_dir.is_dir():
                for py_file in src_dir.rglob("*.py"):
                    rel = py_file.relative_to(project_root)
                    dst = backup_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(py_file), str(dst))
                    size = py_file.stat().st_size
                    total_size += size
                    files_backed += 1
                    checksums.append(self._file_checksum(py_file))

        manifest = {
            "backup_id": backup_id,
            "timestamp": timestamp,
            "type": backup_type,
            "files": files_backed,
            "size": total_size,
            "project_root": str(project_root),
        }
        manifest_path = backup_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        overall_checksum = hashlib.sha256(
            "|".join(sorted(checksums)).encode()
        ).hexdigest()[:16]

        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            files_backed_up=files_backed,
            total_size_bytes=total_size,
            backup_type=backup_type,
            checksum=overall_checksum,
        )
        self.history.append(metadata)

        log.info(
            "Backup created: %s files=%d size=%d type=%s",
            backup_id, files_backed, total_size, backup_type,
        )
        return metadata

    def restore_backup(
        self,
        backup_id: str,
        project_root: Path,
    ) -> RestoreResult:
        backup_dir = self.backup_root / backup_id
        if not backup_dir.exists():
            return RestoreResult(
                success=False, files_restored=0,
                errors=[f"Backup not found: {backup_id}"],
                restored_from=backup_id,
            )

        files_restored = 0
        errors = []

        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.exists():
            return RestoreResult(
                success=False, files_restored=0,
                errors=["Manifest not found"],
                restored_from=backup_id,
            )

        for rel_path in CRITICAL_FILES:
            src = backup_dir / rel_path
            if src.exists():
                dst = project_root / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(str(src), str(dst))
                    files_restored += 1
                except OSError as e:
                    errors.append(f"Failed to restore {rel_path}: {e}")

        for rel_dir in CRITICAL_DIRS:
            src_dir = backup_dir / rel_dir
            if src_dir.is_dir():
                for py_file in src_dir.rglob("*.py"):
                    rel = py_file.relative_to(backup_dir)
                    dst = project_root / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(str(py_file), str(dst))
                        files_restored += 1
                    except OSError as e:
                        errors.append(f"Failed to restore {rel}: {e}")

        log.info("Backup restored: %s files=%d errors=%d", backup_id, files_restored, len(errors))

        return RestoreResult(
            success=len(errors) == 0,
            files_restored=files_restored,
            errors=errors,
            restored_from=backup_id,
        )

    def cleanup_old_backups(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        removed = 0

        if not self.backup_root.exists():
            return 0

        for entry in self.backup_root.iterdir():
            if not entry.is_dir():
                continue
            manifest_path = entry / "manifest.json"
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text())
                    ts = manifest.get("timestamp", "")
                    if ts:
                        backup_date = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                        backup_date = backup_date.replace(tzinfo=timezone.utc)
                        if backup_date < cutoff:
                            shutil.rmtree(str(entry))
                            removed += 1
                except (json.JSONDecodeError, ValueError, OSError):
                    continue

        if removed > 0:
            log.info("Cleaned up %d old backups", removed)
        return removed

    def list_backups(self) -> List[BackupMetadata]:
        return list(self.history)

    def _file_checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    def verify_backup(self, backup_id: str) -> bool:
        backup_dir = self.backup_root / backup_id
        if not backup_dir.exists():
            return False
        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.exists():
            return False
        try:
            manifest = json.loads(manifest_path.read_text())
            return manifest.get("files", 0) > 0
        except (json.JSONDecodeError, OSError):
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_backups": len(self.history),
            "total_size_bytes": sum(b.total_size_bytes for b in self.history),
            "last_backup": self.history[-1].timestamp if self.history else "never",
            "retention_days": self.retention_days,
        }


backup_engine = BackupEngine()
