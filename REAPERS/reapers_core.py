import time
import logging
from typing import Dict

from REAPERS.integrity_guard import IntegrityGuard

log = logging.getLogger("NAYA.REAPERS")
from REAPERS.snapshot_manager import SnapshotManager
from REAPERS.boot_authority import BootAuthority
from REAPERS.reapers_repair import ReapersRepair
from REAPERS.crash_predictor import CrashPredictor
from REAPERS.runtime_watchdog import RuntimeWatchdog
from REAPERS.isolation_engine import IsolationEngine
from REAPERS.adaptive_security_layer import AdaptiveSecurityLayer
from REAPERS.anti_clone_guard import AntiCloneGuard
from REAPERS.anti_exfiltration import AntiExfiltrationGuard
from REAPERS.auto_scanner import AutoScanner


class ReapersKernel:

    def __init__(self):

        self.targets: Dict[str, str] = {
            "decision_core": "NAYA_CORE/decision/decision_core.py",
            "execution_trigger": "NAYA_CORE/decision/execution_trigger.py",
            "capital_manager": "NAYA_CORE/economic/capital_reserve_manager.py",
            "project_bridge": "NAYA_CORE/decision/project_engine_bridge.py",
        }

        self.snapshot_manager = SnapshotManager()
        self.integrity_guard = IntegrityGuard(self.targets)
        self.boot_authority = BootAuthority()
        self.crash_predictor = CrashPredictor()
        self.runtime_watchdog = RuntimeWatchdog()
        self.isolation_engine = IsolationEngine()
        self.adaptive_security = AdaptiveSecurityLayer()
        self.anti_clone_guard = AntiCloneGuard()
        self.anti_exfiltration = AntiExfiltrationGuard()
        self.auto_scanner = AutoScanner()

        # ThreatMemory optionnel
        try:
            from REAPERS.threat_memory import ThreatMemory
            threat_memory = ThreatMemory()
        except Exception:
            threat_memory = None
        self.repair_engine = ReapersRepair(
            snapshot_manager=self.snapshot_manager,
            isolation_engine=self.isolation_engine,
            threat_memory=threat_memory,
        )

    def start(self):

        self.snapshot_manager.create_snapshot(reason="boot")
        self.integrity_guard.create_baseline()

        # Clone guard
        clone_check = self.anti_clone_guard.verify_not_clone()
        if not clone_check["legitimate"]:
            log.error(f"[REAPERS] Non-registered machine detected — clone suspected: {clone_check}")

        if not self.boot_authority.authorize():
            raise SystemExit("Boot blocked by REAPERS")

        # Boot-time autoscan (non-blocking: errors logged, never crash boot)
        try:
            report = self.auto_scanner.run_full_scan()
            if not report.is_clean:
                log.warning(
                    f"[REAPERS] AutoScan found {report.total_issues} issue(s) — "
                    f"secrets={len(report.secrets_found)} "
                    f"bandit={len(report.bandit_issues)} "
                    f"safety={len(report.safety_issues)}"
                )
        except Exception as e:
            log.warning(f"[REAPERS] AutoScan error at boot: {e}")

        self.monitor_loop()

    def monitor_loop(self):

        scan_counter = 0
        SCAN_EVERY_N_CYCLES = 4320  # ~6h at 5s intervals

        while True:

            # 🔐 Runtime Protection
            debugger = self.runtime_watchdog.debugger_detected()
            suspicious = self.runtime_watchdog.suspicious_environment()

            if debugger:
                log.warning("[REAPERS] Debugger detected")
                self.adaptive_security.evaluate_threat(
                    integrity_breach=False, debugger_detected=True, repeated_failures=False
                )

            if suspicious:
                log.warning("[REAPERS] Suspicious environment detected")
                self.adaptive_security.evaluate_threat(
                    integrity_breach=False, debugger_detected=True, repeated_failures=False
                )

            # 🔎 Integrity Check
            integrity_results = self.integrity_guard.check_integrity()
            any_breach = False

            for module_name, is_valid in integrity_results.items():

                if not is_valid:
                    log.warning(f"[REAPERS] Integrity breach: {module_name}")
                    any_breach = True

                    self.isolation_engine.quarantine(module_name)

                    # Restore from latest boot snapshot if available
                    snapshots = self.snapshot_manager.list_snapshots()
                    if snapshots:
                        latest_snap_id = snapshots[-1]["id"]
                        self.snapshot_manager.restore_snapshot(latest_snap_id)
                    else:
                        log.warning(f"[REAPERS] No snapshot available for {module_name}")

                    self.integrity_guard.create_baseline()

                    log.info(f"[REAPERS] Restored: {module_name}")

            if any_breach:
                self.adaptive_security.evaluate_threat(
                    integrity_breach=True, debugger_detected=debugger, repeated_failures=False
                )

            # 🔍 Periodic AutoScan (every ~6h)
            scan_counter += 1
            if scan_counter >= SCAN_EVERY_N_CYCLES:
                scan_counter = 0
                try:
                    report = self.auto_scanner.run_full_scan()
                    if not report.is_clean:
                        log.warning(f"[REAPERS] Periodic scan: {report.total_issues} issue(s) detected")
                except Exception as e:
                    log.warning(f"[REAPERS] Periodic scan error: {e}")

            time.sleep(5)
