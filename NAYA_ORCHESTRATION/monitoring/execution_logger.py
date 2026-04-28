"""NAYA Orchestration — Execution Logger"""
import logging
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone

log = logging.getLogger("NAYA.ORCH.EXEC_LOGGER")

class ExecutionLogger:
    """Logs all execution events with structured JSON output."""

    def __init__(self, log_dir: Optional[str] = None):
        self._entries: List[Dict] = []
        self._log_dir = Path(log_dir) if log_dir else Path("logs/execution_reports")
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO", context: Optional[Dict] = None) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat() + "Z",
            "level": level,
            "message": message,
            "context": context or {},
        }
        self._entries.append(entry)
        getattr(log, level.lower(), log.info)(f"{message} | {context}")

    def log_task_start(self, task_id: str, task_type: str, executor: str) -> None:
        self.log(f"TASK_START: {task_id}", "INFO", {"task_id": task_id, "type": task_type, "executor": executor})

    def log_task_end(self, task_id: str, status: str, duration_ms: float = 0.0) -> None:
        self.log(f"TASK_END: {task_id} [{status}]", "INFO" if status == "OK" else "ERROR",
                 {"task_id": task_id, "status": status, "duration_ms": duration_ms})

    def log_plan(self, plan_id: str, tasks: int, env: str) -> None:
        self.log(f"PLAN_START: {plan_id} ({tasks} tasks, env={env})", "INFO",
                 {"plan_id": plan_id, "tasks": tasks, "env": env})

    def flush(self) -> None:
        """Write buffered entries to disk."""
        if not self._entries:
            return
        path = self._log_dir / f"exec_{int(time.time())}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for e in self._entries:
                f.write(json.dumps(e) + "\n")
        self._entries.clear()

    def get_recent(self, n: int = 50) -> List[Dict]:
        return self._entries[-n:]
