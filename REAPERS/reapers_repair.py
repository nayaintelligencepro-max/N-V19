# REAPERS/reapers_repair.py

import logging
from datetime import datetime, timezone
from typing import Dict

from REAPERS.snapshot_manager import SnapshotManager
from REAPERS.isolation_engine import IsolationEngine
from REAPERS.threat_memory import ThreatMemory

log = logging.getLogger("NAYA.REAPERS.repair")


class ReapersRepair:
    """
    Final integrated repair engine.
    Handles quarantine, restore, memory logging.
    """

    def __init__(
        self,
        snapshot_manager: SnapshotManager,
        isolation_engine: IsolationEngine,
        threat_memory: ThreatMemory
    ) -> None:

        self.snapshot_manager = snapshot_manager
        self.isolation_engine = isolation_engine
        self.threat_memory = threat_memory

        self._repair_log: Dict[str, datetime] = {}

    # ---------------------------------------------------------
    # RESTORE MODULE
    # ---------------------------------------------------------

    def restore_module(self, module_name: str, target_path: str) -> None:

        log.warning(f"[REAPERS] Repair initiated: {module_name}")

        # Log threat
        self.threat_memory.record_threat(
            threat_type="integrity_breach",
            source=module_name,
            severity=1.0,
            details=f"Integrity violation detected on {module_name}"
        )

        # Quarantine
        self.isolation_engine.quarantine(module_name)

        # Restore from latest snapshot if available
        snapshots = self.snapshot_manager.list_snapshots()
        if snapshots:
            latest_snap_id = snapshots[-1]["id"]
            self.snapshot_manager.restore_snapshot(latest_snap_id)
        else:
            log.warning(f"[REAPERS] No snapshot available to restore {module_name}")

        # Reintegration
        self.isolation_engine.reintegrate(module_name)

        # Log repair timestamp
        self._repair_log[module_name] = datetime.now(timezone.utc)

        log.info(f"[REAPERS] Repair completed: {module_name}")

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------

    def repair_history(self) -> Dict[str, datetime]:
        return dict(self._repair_log)
