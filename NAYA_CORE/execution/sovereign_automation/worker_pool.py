"""NAYA V19 - Worker Pool - Pool de workers pour execution parallele."""
import time, logging, threading, uuid
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
log = logging.getLogger("NAYA.WORKERS")

@dataclass
class Worker:
    worker_id: str
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    tasks_completed: int = 0
    started_at: float = field(default_factory=time.time)

class WorkerPool:
    """Pool de workers thread-safe pour execution parallele."""

    def __init__(self, size: int = 4):
        self._workers: Dict[str, Worker] = {}
        self._lock = threading.RLock()
        for i in range(size):
            wid = f"worker_{i}"
            self._workers[wid] = Worker(worker_id=wid)

    def acquire_worker(self) -> Optional[str]:
        with self._lock:
            for wid, w in self._workers.items():
                if w.status == "idle":
                    w.status = "busy"
                    w.current_task = f"task_{uuid.uuid4().hex[:8]}"
                    return wid
        return None

    def release_worker(self, worker_id: str, success: bool = True) -> None:
        with self._lock:
            w = self._workers.get(worker_id)
            if w:
                w.status = "idle"
                w.current_task = None
                if success:
                    w.tasks_completed += 1

    def get_available_count(self) -> int:
        with self._lock:
            return sum(1 for w in self._workers.values() if w.status == "idle")

    def get_busy_count(self) -> int:
        with self._lock:
            return sum(1 for w in self._workers.values() if w.status == "busy")

    def resize(self, new_size: int) -> None:
        with self._lock:
            current = len(self._workers)
            if new_size > current:
                for i in range(current, new_size):
                    wid = f"worker_{i}"
                    self._workers[wid] = Worker(worker_id=wid)
            elif new_size < current:
                idle = [wid for wid, w in self._workers.items() if w.status == "idle"]
                for wid in idle[:current - new_size]:
                    del self._workers[wid]

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_workers": len(self._workers),
                "idle": sum(1 for w in self._workers.values() if w.status == "idle"),
                "busy": sum(1 for w in self._workers.values() if w.status == "busy"),
                "total_completed": sum(w.tasks_completed for w in self._workers.values())
            }
