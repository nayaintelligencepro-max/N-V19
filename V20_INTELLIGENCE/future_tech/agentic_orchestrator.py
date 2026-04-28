"""
NAYA V20 — Agentic Orchestrator
══════════════════════════════════════════════════════════════════════════════
Production-grade multi-agent task routing and execution tracking.

DOCTRINE:
  As NAYA V20 scales to hundreds of simultaneous deals, no human can manage
  task assignment manually.  This orchestrator routes incoming tasks to the
  most suitable registered agent based on capabilities and capacity,
  maintaining a full delegation audit trail.

ARCHITECTURE:
  Agents register their capabilities and concurrency limits.
  Tasks are submitted with required_capabilities.
  The orchestrator matches tasks to agents and tracks lifecycle:
    PENDING → ASSIGNED → RUNNING → COMPLETED | FAILED

MAX_PARALLEL = 50 concurrent tasks across all agents.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.AGENTIC_ORCHESTRATOR")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "agentic_orchestrator.json"

MAX_PARALLEL = 50

_VALID_STATUSES = {"PENDING", "ASSIGNED", "RUNNING", "COMPLETED", "FAILED"}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AgentTask:
    """A unit of work routed through the agentic orchestrator."""

    task_id: str
    task_type: str
    payload: Dict
    priority: int               # 1 (lowest) – 10 (highest)
    status: str                 # PENDING | ASSIGNED | RUNNING | COMPLETED | FAILED
    assigned_agent_id: str = ""
    created_at: str = ""
    completed_at: str = ""
    result: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class AgenticOrchestrator:
    """
    Routes tasks to registered agents based on capabilities and capacity.

    Thread-safe singleton.  Persists agents registry and task history to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._agents: Dict[str, Dict] = {}
        self._tasks: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._agents = data.get("agents", {})
                    self._tasks = data.get("tasks", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "agents": self._agents,
                        "tasks": self._tasks,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        max_concurrent: int = 1,
    ) -> bool:
        """
        Register an agent with the orchestrator.

        Args:
            agent_id: Unique identifier for this agent.
            name: Human-readable agent name.
            capabilities: List of capability labels this agent can handle.
            max_concurrent: Maximum parallel tasks this agent can accept.

        Returns:
            True on successful registration.
        """
        with self._lock:
            self._agents[agent_id] = {
                "agent_id": agent_id,
                "name": name,
                "capabilities": capabilities,
                "max_concurrent": max_concurrent,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }
        self._save()
        return True

    def _find_best_agent(
        self, required_capabilities: Optional[List[str]]
    ) -> Optional[str]:
        """
        Find the most suitable available agent for a set of required capabilities.

        An agent is eligible if it has all required capabilities and has not
        reached its max_concurrent task limit.

        Args:
            required_capabilities: Capability labels that must be present.
                                   None means any agent qualifies.

        Returns:
            agent_id of the best match, or None if no agent is available.
        """
        # Count currently assigned/running tasks per agent
        agent_load: Dict[str, int] = {aid: 0 for aid in self._agents}
        for task in self._tasks.values():
            if task["status"] in ("ASSIGNED", "RUNNING") and task["assigned_agent_id"]:
                agent_load[task["assigned_agent_id"]] = (
                    agent_load.get(task["assigned_agent_id"], 0) + 1
                )

        for agent_id, agent in self._agents.items():
            # Capability check
            if required_capabilities:
                agent_caps = set(agent.get("capabilities", []))
                if not all(cap in agent_caps for cap in required_capabilities):
                    continue
            # Capacity check
            load = agent_load.get(agent_id, 0)
            if load < agent.get("max_concurrent", 1):
                return agent_id
        return None

    def submit_task(
        self,
        task_id: str,
        task_type: str,
        payload: Dict,
        priority: int = 5,
        required_capabilities: Optional[List[str]] = None,
    ) -> str:
        """
        Submit a task for execution by the best available agent.

        Args:
            task_id: Unique task identifier.
            task_type: Type label describing the task.
            payload: Arbitrary task data dict.
            priority: Integer priority 1 (low) to 10 (high).
            required_capabilities: Capabilities the assigned agent must have.

        Returns:
            task_id as stored.
        """
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=max(1, min(10, priority)),
            status="PENDING",
        )

        with self._lock:
            agent_id = self._find_best_agent(required_capabilities)
            if agent_id:
                task.status = "ASSIGNED"
                task.assigned_agent_id = agent_id
            self._tasks[task_id] = asdict(task)

        self._save()
        return task_id

    def get_task_status(self, task_id: str) -> Dict:
        """
        Retrieve the current state of a task.

        Args:
            task_id: Target task identifier.

        Returns:
            Task dict or {"error": "not found"}.
        """
        with self._lock:
            return dict(self._tasks.get(task_id, {"error": "not found"}))

    def get_delegation_chain(self, task_id: str) -> List[Dict]:
        """
        Return the event chain for a task's lifecycle.

        Args:
            task_id: Target task identifier.

        Returns:
            Ordered list of event dicts describing the delegation history.
        """
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return []

        chain = [
            {"event": "submitted", "task_id": task_id, "at": task.get("created_at", "")}
        ]
        if task.get("assigned_agent_id"):
            chain.append({
                "event": "assigned_to",
                "agent": task["assigned_agent_id"],
                "at": task.get("created_at", ""),
            })
        if task.get("completed_at"):
            chain.append({
                "event": "completed",
                "status": task["status"],
                "at": task["completed_at"],
            })
        return chain

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_agents, total_tasks, and per-status counts.
        """
        with self._lock:
            tasks = list(self._tasks.values())
        status_counts: Dict[str, int] = {s: 0 for s in _VALID_STATUSES}
        for t in tasks:
            status_counts[t.get("status", "PENDING")] = (
                status_counts.get(t.get("status", "PENDING"), 0) + 1
            )
        return {
            "total_agents": len(self._agents),
            "total_tasks": len(tasks),
            "pending": status_counts.get("PENDING", 0),
            "assigned": status_counts.get("ASSIGNED", 0),
            "completed": status_counts.get("COMPLETED", 0),
            "failed": status_counts.get("FAILED", 0),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_orchestrator: Optional[AgenticOrchestrator] = None


def get_agentic_orchestrator() -> AgenticOrchestrator:
    """Return the process-wide singleton AgenticOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgenticOrchestrator()
    return _orchestrator
