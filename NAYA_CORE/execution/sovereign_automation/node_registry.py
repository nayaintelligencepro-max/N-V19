"""NAYA V19 - Node Registry - Registre des noeuds d execution."""
import time, logging, threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.NODES")

@dataclass
class ExecutionNode:
    node_id: str
    node_type: str  # local, vm, cloud_run
    endpoint: str = "localhost"
    healthy: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    tasks_completed: int = 0
    current_tasks: int = 0
    max_tasks: int = 10

class NodeRegistry:
    """Registre des noeuds d execution disponibles."""

    def __init__(self):
        self._nodes: Dict[str, ExecutionNode] = {}
        self._lock = threading.RLock()
        # Auto-register local node
        self.register("local_0", "local", "localhost", max_tasks=20)

    def register(self, node_id: str, node_type: str, endpoint: str = "localhost",
                 max_tasks: int = 10) -> None:
        with self._lock:
            self._nodes[node_id] = ExecutionNode(
                node_id=node_id, node_type=node_type,
                endpoint=endpoint, max_tasks=max_tasks
            )

    def unregister(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)

    def heartbeat(self, node_id: str) -> None:
        with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node.last_heartbeat = time.time()

    def get_available(self) -> List[ExecutionNode]:
        with self._lock:
            return [n for n in self._nodes.values()
                    if n.healthy and n.current_tasks < n.max_tasks]

    def get_best_node(self, task_type: str = "general") -> Optional[str]:
        available = self.get_available()
        if not available:
            return None
        best = min(available, key=lambda n: n.current_tasks)
        return best.node_id

    def mark_unhealthy(self, node_id: str) -> None:
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].healthy = False

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_nodes": len(self._nodes),
                "healthy": sum(1 for n in self._nodes.values() if n.healthy),
                "total_capacity": sum(n.max_tasks for n in self._nodes.values()),
                "current_load": sum(n.current_tasks for n in self._nodes.values()),
                "nodes": {nid: {"type": n.node_type, "healthy": n.healthy, "load": n.current_tasks}
                         for nid, n in self._nodes.items()}
            }
