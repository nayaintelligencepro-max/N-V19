"""NAYA V19 — Cluster Runtime Manager"""
import time, logging, threading
from typing import Dict, Optional, List
log = logging.getLogger("NAYA.CLUSTER.RUNTIME")

class ClusterRuntime:
    """Gère le cycle de vie runtime de chaque nœud du cluster."""
    def __init__(self, node_id: str = "primary"):
        self.node_id = node_id
        self._started_at = time.time()
        self._nodes: Dict[str, Dict] = {node_id: {"status": "running", "started": time.time()}}
        self._lock = threading.RLock()
        self._mode = "single"  # single | distributed
    
    def register_node(self, node_id: str, endpoint: str = ""):
        with self._lock:
            self._nodes[node_id] = {"status": "running", "started": time.time(), "endpoint": endpoint}
            if len(self._nodes) > 1: self._mode = "distributed"
            log.info(f"[CLUSTER_RT] Node {node_id} registered (mode={self._mode})")
    
    def remove_node(self, node_id: str):
        with self._lock:
            self._nodes.pop(node_id, None)
            if len(self._nodes) <= 1: self._mode = "single"
    
    def set_node_status(self, node_id: str, status: str):
        with self._lock:
            if node_id in self._nodes: self._nodes[node_id]["status"] = status
    
    def get_active_nodes(self) -> List[str]:
        with self._lock:
            return [nid for nid, info in self._nodes.items() if info["status"] == "running"]
    
    def is_distributed(self) -> bool:
        return self._mode == "distributed"
    
    def get_runtime_info(self) -> Dict:
        with self._lock:
            uptime = time.time() - self._started_at
            return {
                "node_id": self.node_id, "mode": self._mode,
                "uptime_seconds": int(uptime), "total_nodes": len(self._nodes),
                "active_nodes": len([n for n in self._nodes.values() if n["status"] == "running"]),
                "nodes": dict(self._nodes),
            }
