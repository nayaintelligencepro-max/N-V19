"""NAYA Orchestration — Execution Request"""
import uuid
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ExecutionRequest:
    """Formal execution request — everything needed to execute a task."""
    id: str = field(default_factory=lambda: f"REQ_{uuid.uuid4().hex[:10].upper()}")
    directive: str = ""
    tasks: List[Dict] = field(default_factory=list)
    priority: int = 5
    payload: Dict = field(default_factory=dict)
    requester: str = "autonomous"
    env: str = "local"
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "directive": self.directive,
            "tasks_count": len(self.tasks), "priority": self.priority,
            "requester": self.requester, "env": self.env,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionRequest":
        return cls(
            id=data.get("id", f"REQ_{uuid.uuid4().hex[:10].upper()}"),
            directive=data.get("directive", ""),
            tasks=data.get("tasks", []),
            priority=data.get("priority", 5),
            payload=data.get("payload", {}),
            requester=data.get("requester", "api"),
            env=data.get("env", "local"),
        )

    @property
    def is_overdue(self) -> bool:
        if self.deadline is None: return False
        return time.time() > self.deadline
