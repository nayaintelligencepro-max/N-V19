"""
NAYA — Service Registry
Tracks all registered services, their health, and dependencies.
Used by bootstrap and monitoring to verify system integrity.
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

log = logging.getLogger("NAYA.REGISTRY")


@dataclass
class ServiceEntry:
    name: str
    module_path: str
    status: str = "registered"  # registered, healthy, degraded, failed
    instance: Any = None
    registered_at: float = field(default_factory=time.time)
    last_health_check: float = 0.0
    error: str = ""
    dependencies: List[str] = field(default_factory=list)


class ServiceRegistry:
    """Central registry for all NAYA services."""

    def __init__(self):
        self._services: Dict[str, ServiceEntry] = {}
        self._lock = threading.RLock()

    def register(self, name: str, module_path: str, instance: Any = None,
                 dependencies: List[str] = None) -> bool:
        with self._lock:
            self._services[name] = ServiceEntry(
                name=name, module_path=module_path,
                instance=instance, status="healthy" if instance else "registered",
                dependencies=dependencies or [],
            )
            log.info("Service registered: %s", name)
            return True

    def get(self, name: str) -> Optional[ServiceEntry]:
        return self._services.get(name)

    def get_instance(self, name: str) -> Any:
        entry = self._services.get(name)
        return entry.instance if entry else None

    def set_status(self, name: str, status: str, error: str = ""):
        entry = self._services.get(name)
        if entry:
            entry.status = status
            entry.error = error
            entry.last_health_check = time.time()

    def health_check(self) -> Dict[str, Any]:
        results = {}
        for name, entry in self._services.items():
            healthy = entry.status in ("healthy", "registered")
            if entry.instance and hasattr(entry.instance, "health_check"):
                try:
                    entry.instance.health_check()
                    entry.status = "healthy"
                except Exception as exc:
                    entry.status = "degraded"
                    entry.error = str(exc)
                    healthy = False
            entry.last_health_check = time.time()
            results[name] = {"status": entry.status, "healthy": healthy, "error": entry.error}
        return results

    def list_services(self) -> List[Dict]:
        return [{"name": e.name, "status": e.status, "module": e.module_path,
                 "has_instance": e.instance is not None}
                for e in self._services.values()]

    def get_stats(self) -> Dict:
        total = len(self._services)
        healthy = sum(1 for e in self._services.values() if e.status == "healthy")
        return {"total": total, "healthy": healthy, "degraded": total - healthy}


_REGISTRY: Optional[ServiceRegistry] = None
_LOCK = threading.Lock()

def get_service_registry() -> ServiceRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        with _LOCK:
            if _REGISTRY is None:
                _REGISTRY = ServiceRegistry()
    return _REGISTRY
