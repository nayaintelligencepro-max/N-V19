"""NAYA V19 - Engine Master - Orchestrateur principal des moteurs NAYA."""
import logging, time
from typing import Dict, List, Optional, Any

log = logging.getLogger("NAYA.CORE.MASTER")

class EngineMaster:
    """Orchestre tous les moteurs du systeme NAYA."""

    def __init__(self):
        self._engines: Dict[str, Dict] = {}
        self._boot_order: List[str] = []
        self._started = False

    def register_engine(self, name: str, engine: Any, priority: int = 5) -> None:
        self._engines[name] = {"engine": engine, "priority": priority, "status": "registered", "started_at": None}
        self._boot_order = sorted(self._engines.keys(), key=lambda n: self._engines[n]["priority"])
        log.debug(f"[MASTER] Engine registered: {name} (priority={priority})")

    def start_all(self) -> Dict:
        results = {}
        for name in self._boot_order:
            entry = self._engines[name]
            try:
                engine = entry["engine"]
                if hasattr(engine, "start"):
                    engine.start()
                elif hasattr(engine, "initialize"):
                    engine.initialize()
                entry["status"] = "running"
                entry["started_at"] = time.time()
                results[name] = "ok"
            except Exception as e:
                entry["status"] = "failed"
                results[name] = str(e)[:60]
                log.error(f"[MASTER] Engine {name} failed: {e}")
        self._started = True
        log.info(f"[MASTER] {sum(1 for v in results.values() if v == 'ok')}/{len(results)} engines started")
        return results

    def stop_all(self) -> Dict:
        results = {}
        for name in reversed(self._boot_order):
            entry = self._engines[name]
            try:
                engine = entry["engine"]
                if hasattr(engine, "stop"):
                    engine.stop()
                entry["status"] = "stopped"
                results[name] = "ok"
            except Exception as e:
                results[name] = str(e)[:60]
        self._started = False
        return results

    def get_engine(self, name: str) -> Optional[Any]:
        entry = self._engines.get(name)
        return entry["engine"] if entry else None

    def activate(self) -> Dict:
        return self.start_all()

    def get_status(self) -> Dict:
        return {
            "started": self._started,
            "total_engines": len(self._engines),
            "running": sum(1 for e in self._engines.values() if e["status"] == "running"),
            "engines": {n: e["status"] for n, e in self._engines.items()}
        }

    def get_stats(self) -> Dict:
        return self.get_status()
