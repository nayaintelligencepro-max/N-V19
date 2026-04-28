"""NAYA V19 - Cluster Controller - Controleur principal du cluster."""
import logging, time, threading
from typing import Dict, Optional

log = logging.getLogger("NAYA.CLUSTER.CTRL")

class ClusterController:
    """Controleur central du cluster - coordonne les noeuds."""

    def __init__(self):
        self._mode = "single_node"
        self._leader = "local"
        self._nodes: Dict[str, Dict] = {"local": {"status": "active", "role": "leader"}}
        self._lock = threading.RLock()

    def get_mode(self) -> str:
        return self._mode

    def get_leader(self) -> str:
        return self._leader

    def add_node(self, node_id: str, endpoint: str = "") -> Dict:
        with self._lock:
            self._nodes[node_id] = {"status": "active", "role": "follower", "endpoint": endpoint}
            if len(self._nodes) > 1:
                self._mode = "multi_node"
        log.info(f"[CLUSTER] Node added: {node_id}")
        return {"node_id": node_id, "mode": self._mode, "total_nodes": len(self._nodes)}

    def remove_node(self, node_id: str) -> Dict:
        with self._lock:
            self._nodes.pop(node_id, None)
            if len(self._nodes) <= 1:
                self._mode = "single_node"
        return {"removed": node_id, "remaining": len(self._nodes)}

    def health_check(self) -> Dict:
        with self._lock:
            healthy = sum(1 for n in self._nodes.values() if n["status"] == "active")
            return {
                "mode": self._mode, "leader": self._leader,
                "total_nodes": len(self._nodes), "healthy": healthy,
                "all_healthy": healthy == len(self._nodes)
            }

    def get_stats(self) -> Dict:
        return self.health_check()
