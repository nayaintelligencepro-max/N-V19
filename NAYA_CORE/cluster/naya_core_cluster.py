"""NAYA V19 - Naya Core Cluster - Facade principale du sous-systeme cluster."""
import logging, threading
from typing import Dict, Optional

log = logging.getLogger("NAYA.CLUSTER")

class NayaCoreCluster:
    """Facade unifiee pour toutes les operations cluster."""

    def __init__(self):
        self._mode = "single_node"
        self._nodes = {"local": {"role": "leader", "healthy": True}}
        self._lock = threading.RLock()

    def get_status(self) -> Dict:
        with self._lock:
            return {
                "mode": self._mode,
                "total_nodes": len(self._nodes),
                "leader": next((nid for nid, n in self._nodes.items() if n["role"] == "leader"), "local"),
                "healthy_nodes": sum(1 for n in self._nodes.values() if n["healthy"]),
                "nodes": {nid: n.copy() for nid, n in self._nodes.items()}
            }

    def add_node(self, node_id: str, role: str = "follower") -> Dict:
        with self._lock:
            self._nodes[node_id] = {"role": role, "healthy": True}
            if len(self._nodes) > 1:
                self._mode = "multi_node"
            log.info(f"[CLUSTER] Node added: {node_id} ({role})")
            return self.get_status()

    def remove_node(self, node_id: str) -> Dict:
        with self._lock:
            self._nodes.pop(node_id, None)
            if len(self._nodes) <= 1:
                self._mode = "single_node"
            return self.get_status()

    def set_node_health(self, node_id: str, healthy: bool) -> None:
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id]["healthy"] = healthy

    def is_leader(self) -> bool:
        return True  # En single_node, toujours leader

    def get_cluster_capacity(self) -> Dict:
        with self._lock:
            healthy = sum(1 for n in self._nodes.values() if n["healthy"])
            return {"capacity": healthy * 10, "nodes": healthy, "mode": self._mode}

    def get_stats(self) -> Dict:
        return self.get_status()
