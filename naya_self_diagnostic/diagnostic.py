"""NAYA — Self Diagnostic complet."""
import time, threading, logging
from typing import Dict, Optional, Tuple
from enum import Enum
log = logging.getLogger("NAYA.DIAGNOSTIC")

class Health(Enum):
    OK = "ok"; DEGRADED = "degraded"; CRITICAL = "critical"; UNKNOWN = "unknown"

class SelfDiagnostic:
    CHECK_INTERVAL = 300
    def __init__(self):
        self._running = False; self._thread = None
        self._last_checks: Dict = {}; self._last_run = 0.0; self._overall = Health.UNKNOWN

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="NAYA-DIAG", daemon=True)
        self._thread.start()

    def stop(self): self._running = False

    def run(self):
        checks = self._run_all()
        self._last_checks = checks; self._last_run = time.time()
        self._overall = self._compute_overall(checks)
        healthy = sum(1 for v in checks.values() if v.get("status") == "ok")
        return {"overall": self._overall.value, "healthy": healthy, "total": len(checks), "last_run": self._last_run, "components": checks, "core": "OK" if self._overall != Health.CRITICAL else "CRITICAL"}

    def get_report(self):
        if not self._last_checks: return self.run()
        healthy = sum(1 for v in self._last_checks.values() if v.get("status") == "ok")
        return {"overall": self._overall.value, "healthy": healthy, "total": len(self._last_checks), "last_run": self._last_run, "components": self._last_checks}

    def _loop(self):
        time.sleep(60)
        while self._running:
            try:
                checks = self._run_all()
                self._last_checks = checks; self._last_run = time.time()
                self._overall = self._compute_overall(checks)
            except Exception as e: log.debug(f"[DIAGNOSTIC] {e}")
            time.sleep(self.CHECK_INTERVAL)

    def _run_all(self):
        checks = {}
        for name, fn in [
            ("superbrain_v6", self._chk_superbrain),
            ("scheduler", self._chk_scheduler),
            ("database", self._chk_db),
            ("llm_brain", self._chk_brain),
            ("notifier", self._chk_notifier),
            ("memory", self._chk_memory),
            ("brain_activator", self._chk_brain_activator),
            ("sovereign_engine", self._chk_sovereign),
        ]:
            t0 = time.time()
            try:
                status, msg = fn()
                checks[name] = {"status": status.value, "message": msg, "latency_ms": round((time.time()-t0)*1000, 1)}
            except Exception as e:
                checks[name] = {"status": "critical", "message": str(e)[:60], "latency_ms": 0}
        return checks

    def _chk_superbrain(self):
        from NAYA_CORE.super_brain_hybrid_v6_0 import get_super_brain
        s = get_super_brain().get_stats()
        return Health.OK, f"v{s.get('version','?')} | {s.get('total_processed',0)} processed"
    def _chk_scheduler(self):
        from NAYA_CORE.scheduler import get_scheduler
        s = get_scheduler().get_status()
        return (Health.OK if s.get("running") else Health.DEGRADED), f"cycle={s.get('cycle',0)}"
    def _chk_db(self):
        try:
            from PERSISTENCE.database.db_manager import get_db; get_db().fetch_one("SELECT 1"); return Health.OK, "SQLite WAL active"
        except Exception as e: return Health.DEGRADED, str(e)[:40]
    def _chk_brain(self):
        try:
            from NAYA_CORE.execution.naya_brain import get_brain
            b = get_brain(); return (Health.OK if b.available else Health.DEGRADED), f"available={b.available}"
        except Exception as e: return Health.DEGRADED, str(e)[:40]
    def _chk_notifier(self):
        try:
            from NAYA_CORE.notifier import get_notifier
            n = get_notifier(); ch = n.channels_online; ch = ch() if callable(ch) else ch
            return (Health.OK if ch else Health.DEGRADED), f"channels={ch or 'none'}"
        except Exception as e: return Health.DEGRADED, str(e)[:40]
    def _chk_memory(self):
        from naya_memory_narrative.narrative_memory import get_narrative_memory
        s = get_narrative_memory().get_stats()
        return Health.OK, f"{s['total_entries']} entries | €{s['total_pipeline_eur']:,.0f}"
    def _chk_brain_activator(self):
        from NAYA_CORE.brain_activator import get_brain_activator
        s = get_brain_activator().get_status()
        return Health.OK, f"{s['layers_loaded']} layers | llm={s['llm_connected']} | fusion={s['fusion_active']}"
    def _chk_sovereign(self):
        from NAYA_CORE.naya_sovereign_engine import get_sovereign
        s = get_sovereign().get_stats()
        return (Health.OK if s.get("running") else Health.DEGRADED), f"cycles={s.get('total_cycles',0)}"
    def _compute_overall(self, checks):
        statuses = [v.get("status") for v in checks.values()]
        if "critical" in statuses: return Health.CRITICAL
        if "degraded" in statuses: return Health.DEGRADED
        return Health.OK

_D = None
_D_lock = __import__('threading').Lock()
def get_diagnostic():
    global _D
    if _D is None:
        with _D_lock:
            if _D is None: _D = SelfDiagnostic()
    return _D
