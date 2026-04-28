"""
NAYA — Module Registry
Central catalog of all system modules with status, version, health.
Used by the dashboard and diagnostic tools.
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.MODULE_REG")


@dataclass
class ModuleInfo:
    name: str
    path: str
    category: str  # core, revenue, security, intelligence, infrastructure
    status: str = "unknown"  # active, degraded, disabled, error
    version: str = "1.0.0"
    loaded_at: float = 0.0
    last_error: str = ""


class ModuleRegistry:
    """Tracks all registered NAYA modules."""

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._lock = threading.RLock()
        self._auto_discover()

    def _auto_discover(self):
        """Register known core modules."""
        _KNOWN = [
            ("naya_brain", "NAYA_CORE.execution.naya_brain", "core"),
            ("scheduler", "NAYA_CORE.scheduler", "core"),
            ("revenue_engine", "NAYA_REVENUE_ENGINE.unified_revenue_engine", "revenue"),
            ("payment_engine", "NAYA_REVENUE_ENGINE.payment_engine", "revenue"),
            ("outreach_engine", "NAYA_REVENUE_ENGINE.outreach_engine", "revenue"),
            ("prospect_finder", "NAYA_REVENUE_ENGINE.prospect_finder_v10", "revenue"),
            ("reapers", "REAPERS.reapers_core", "security"),
            ("conversion_engine", "NAYA_CORE.conversion_engine", "revenue"),
            ("synthesis_engine", "NAYA_CORE.outcome_synthesis_engine", "core"),
            ("cognitive_pipeline", "NAYA_CORE.cognitive_pipeline", "intelligence"),
            ("interface_bridge", "NAYA_CORE.interface_bridge", "infrastructure"),
            ("secrets_loader", "SECRETS.secrets_loader", "infrastructure"),
            # V19.3: stripe_integration retiré (non dispo Polynésie). Utiliser NAYA_REVENUE_ENGINE.payment_engine (PayPal + Deblock).
            ("telegram_integration", "NAYA_CORE.integrations.telegram_integration", "infrastructure"),
            ("linkedin_integration", "NAYA_CORE.integrations.linkedin_integration", "revenue"),
            ("orchestrator", "NAYA_ORCHESTRATION.orchestrator", "core"),
            ("watchdog", "NAYA_CORE.monitoring.system_watchdog", "infrastructure"),
        ]
        for name, path, category in _KNOWN:
            self._modules[name] = ModuleInfo(name=name, path=path, category=category)

    def register(self, name: str, path: str, category: str = "custom",
                 version: str = "1.0.0") -> bool:
        with self._lock:
            self._modules[name] = ModuleInfo(
                name=name, path=path, category=category,
                version=version, status="active", loaded_at=time.time()
            )
        return True

    def set_status(self, name: str, status: str, error: str = ""):
        entry = self._modules.get(name)
        if entry:
            entry.status = status
            entry.last_error = error

    def get(self, name: str) -> Optional[ModuleInfo]:
        return self._modules.get(name)

    def verify_imports(self) -> Dict[str, str]:
        """Try importing all registered modules and report status."""
        results = {}
        for name, info in self._modules.items():
            try:
                __import__(info.path, fromlist=["_"])
                info.status = "active"
                info.loaded_at = time.time()
                results[name] = "active"
            except Exception as exc:
                info.status = "error"
                info.last_error = str(exc)[:100]
                results[name] = f"error: {exc}"
        return results

    def list_by_category(self, category: str = None) -> List[Dict]:
        modules = self._modules.values()
        if category:
            modules = [m for m in modules if m.category == category]
        return [{"name": m.name, "path": m.path, "category": m.category,
                 "status": m.status} for m in modules]

    def get_stats(self) -> Dict:
        total = len(self._modules)
        by_status = {}
        for m in self._modules.values():
            by_status[m.status] = by_status.get(m.status, 0) + 1
        return {"total": total, "by_status": by_status,
                "categories": list(set(m.category for m in self._modules.values()))}


_REGISTRY: Optional[ModuleRegistry] = None
_LOCK = threading.Lock()

def get_module_registry() -> ModuleRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        with _LOCK:
            if _REGISTRY is None:
                _REGISTRY = ModuleRegistry()
    return _REGISTRY
