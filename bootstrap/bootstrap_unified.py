"""
NAYA — Unified Bootstrap
Initializes all subsystems in the correct dependency order.
Called by main.py at startup.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

log = logging.getLogger("NAYA.BOOTSTRAP")
ROOT = Path(__file__).parent.parent


class SystemBootstrap:
    """Boots all NAYA subsystems in dependency order."""

    def __init__(self):
        self.modules_loaded: List[str] = []
        self.modules_failed: List[Dict] = []
        self.boot_start = time.time()

    def initialize(self) -> Dict[str, Any]:
        """Full system boot sequence."""
        log.info("Bootstrap V12 starting...")

        # Phase 1: Secrets
        self._load_module("SECRETS.secrets_loader", "load_all_secrets", call=True)

        # Phase 2: Database
        self._load_module("PERSISTENCE.database.db_manager", "DatabaseManager",
                          init=True, call_method="initialize")

        # Phase 3: Core systems
        self._load_module("NAYA_CORE.interface_bridge", "get_bridge", call=True)
        self._load_module("NAYA_CORE.scheduler", "NayaScheduler")
        self._load_module("NAYA_CORE.execution.naya_brain", "get_brain", call=True)

        # Phase 4: Revenue pipeline
        self._load_module("NAYA_REVENUE_ENGINE.unified_revenue_engine", "UnifiedRevenueEngine")
        self._load_module("NAYA_CORE.conversion_engine", "get_conversion_engine", call=True)
        self._load_module("NAYA_CORE.outcome_synthesis_engine", "get_synthesis_engine", call=True)

        # Phase 5: Security
        self._load_module("REAPERS.reapers_core", "ReapersKernel")

        # Phase 6: Monitoring
        self._load_module("NAYA_CORE.monitoring.system_watchdog", "SystemWatchdog")

        elapsed = time.time() - self.boot_start
        result = {
            "status": "ready" if not self.modules_failed else "degraded",
            "modules_loaded": len(self.modules_loaded),
            "modules_failed": len(self.modules_failed),
            "boot_time_seconds": round(elapsed, 2),
            "loaded": self.modules_loaded,
            "failures": self.modules_failed,
        }
        log.info("Bootstrap complete in %.2fs — %d/%d modules",
                 elapsed, len(self.modules_loaded),
                 len(self.modules_loaded) + len(self.modules_failed))
        return result

    def _load_module(self, module_path: str, attr_name: str,
                     call: bool = False, init: bool = False,
                     call_method: str = None):
        """Safely load a module and optionally call/instantiate it."""
        try:
            mod = __import__(module_path, fromlist=[attr_name])
            obj = getattr(mod, attr_name)
            if call:
                obj()
            elif init:
                instance = obj()
                if call_method:
                    getattr(instance, call_method)()
            self.modules_loaded.append(module_path)
        except Exception as exc:
            self.modules_failed.append({"module": module_path, "error": str(exc)})
            log.warning("Bootstrap failed for %s: %s", module_path, exc)


def bootstrap_system() -> Dict[str, Any]:
    """Convenience function to boot the entire system."""
    return SystemBootstrap().initialize()
