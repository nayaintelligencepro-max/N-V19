"""
NAYA V19 - Regression Guard
Verifie qu apres chaque evolution, toutes les capacites precedentes fonctionnent encore.
Aucune evolution ne peut reduire les capacites existantes.
"""
import time, logging, threading, json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.REGRESSION")

@dataclass
class CapabilityTest:
    name: str
    test_fn: Callable
    category: str  # core, revenue, hunt, security, communication
    critical: bool = True
    last_result: Optional[bool] = None
    last_run: float = 0.0
    failure_count: int = 0

@dataclass
class RegressionReport:
    timestamp: float
    total_tests: int
    passed: int
    failed: int
    critical_failures: List[str]
    all_results: Dict[str, bool]
    regression_detected: bool

class RegressionGuard:
    """Garde contre la regression - aucune evolution ne peut affaiblir le systeme."""

    def __init__(self):
        self._tests: Dict[str, CapabilityTest] = {}
        self._reports: List[RegressionReport] = []
        self._lock = threading.RLock()
        self._baseline_capabilities: Dict[str, bool] = {}
        self._register_core_tests()

    def _register_core_tests(self):
        """Enregistre les tests de capacites fondamentales."""
        self.register_test("secrets_loading", self._test_secrets, "core", critical=True)
        self.register_test("database_access", self._test_database, "core", critical=True)
        self.register_test("llm_availability", self._test_llm, "core", critical=True)
        self.register_test("scheduler_running", self._test_scheduler, "core", critical=True)
        self.register_test("memory_persistence", self._test_memory, "core", critical=True)
        self.register_test("revenue_engine", self._test_revenue, "revenue", critical=True)
        self.register_test("hunt_detection", self._test_hunt, "hunt", critical=True)
        self.register_test("notification_channel", self._test_notification, "communication", critical=False)
        self.register_test("payment_processing", self._test_payment, "revenue", critical=False)
        self.register_test("reapers_security", self._test_reapers, "security", critical=True)

    def register_test(self, name: str, test_fn: Callable, category: str = "custom",
                      critical: bool = False) -> None:
        self._tests[name] = CapabilityTest(
            name=name, test_fn=test_fn, category=category, critical=critical
        )

    def run_all(self) -> RegressionReport:
        """Execute tous les tests de regression."""
        results = {}
        critical_failures = []

        for name, test in self._tests.items():
            try:
                result = test.test_fn()
                test.last_result = result
                test.last_run = time.time()
                results[name] = result
                if not result:
                    test.failure_count += 1
                    if test.critical:
                        critical_failures.append(name)
            except Exception as e:
                results[name] = False
                test.last_result = False
                test.failure_count += 1
                if test.critical:
                    critical_failures.append(name)
                log.error(f"[REGRESSION] Test {name} exception: {e}")

        passed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)

        # Detect regression vs baseline
        regression = False
        for name, current in results.items():
            baseline = self._baseline_capabilities.get(name)
            if baseline is True and current is False:
                regression = True
                log.error(f"[REGRESSION] REGRESSION DETECTEE: {name} etait OK, maintenant KO")

        report = RegressionReport(
            timestamp=time.time(),
            total_tests=len(results),
            passed=passed,
            failed=failed,
            critical_failures=critical_failures,
            all_results=results,
            regression_detected=regression
        )

        with self._lock:
            self._reports.append(report)
            if len(self._reports) > 100:
                self._reports = self._reports[-50:]

        if regression:
            log.error(f"[REGRESSION] !! REGRESSION DETECTEE: {critical_failures}")
        else:
            log.info(f"[REGRESSION] Tests: {passed}/{len(results)} OK | Regression: NON")

        return report

    def save_baseline(self) -> None:
        """Sauvegarde l etat actuel comme baseline de reference."""
        report = self.run_all()
        self._baseline_capabilities = report.all_results.copy()
        log.info(f"[REGRESSION] Baseline sauvegardee: {report.passed}/{report.total_tests} capacites")

    def check_evolution_safe(self, evolution_name: str) -> Dict:
        """Verifie si le systeme est safe apres une evolution."""
        report = self.run_all()
        return {
            "evolution": evolution_name,
            "safe": not report.regression_detected,
            "passed": report.passed,
            "failed": report.failed,
            "critical_failures": report.critical_failures,
            "action": "PROCEED" if not report.regression_detected else "ROLLBACK"
        }

    # ── Tests unitaires de capacites ──
    def _test_secrets(self) -> bool:
        try:
            from SECRETS.secrets_loader import get_status
            s = get_status()
            return s.get("configured", 0) >= 1
        except Exception:
            return False

    def _test_database(self) -> bool:
        try:
            from PERSISTENCE.database.db_manager import get_db
            get_db().fetch_one("SELECT 1")
            return True
        except Exception:
            return False

    def _test_llm(self) -> bool:
        try:
            from NAYA_CORE.execution.naya_brain import get_brain
            return get_brain().available
        except Exception:
            return False

    def _test_scheduler(self) -> bool:
        try:
            from NAYA_CORE.scheduler import get_scheduler
            return get_scheduler().running
        except Exception:
            return False

    def _test_memory(self) -> bool:
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            m = get_narrative_memory()
            return m is not None
        except Exception:
            return False

    def _test_revenue(self) -> bool:
        try:
            from NAYA_REVENUE_ENGINE.unified_revenue_engine import UnifiedRevenueEngine
            return True
        except Exception:
            return False

    def _test_hunt(self) -> bool:
        try:
            from NAYA_CORE.hunt.advanced_hunt_engine import AdvancedHuntEngine
            return True
        except Exception:
            return False

    def _test_notification(self) -> bool:
        try:
            from NAYA_CORE.notifier import get_notifier
            return get_notifier() is not None
        except Exception:
            return False

    def _test_payment(self) -> bool:
        try:
            from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
            return True
        except Exception:
            return False

    def _test_reapers(self) -> bool:
        try:
            from REAPERS.reapers_core import ReapersCore
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict:
        with self._lock:
            last = self._reports[-1] if self._reports else None
            return {
                "total_tests": len(self._tests),
                "baseline_set": len(self._baseline_capabilities) > 0,
                "last_run": {
                    "passed": last.passed, "failed": last.failed,
                    "regression": last.regression_detected,
                    "critical_failures": last.critical_failures
                } if last else None,
                "total_reports": len(self._reports)
            }

_guard = None
def get_regression_guard():
    global _guard
    if _guard is None:
        _guard = RegressionGuard()
    return _guard
