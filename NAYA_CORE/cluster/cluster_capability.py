"""
NAYA V19 - Cluster Capability Registry
Enregistre les capacites de chaque noeud du cluster.
"""
import time, logging, threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CLUSTER.CAP")

@dataclass
class NodeCapability:
    node_id: str
    capabilities: Set[str] = field(default_factory=set)
    max_concurrent: int = 10
    current_load: int = 0
    specializations: Dict[str, float] = field(default_factory=dict)
    last_update: float = field(default_factory=time.time)
    healthy: bool = True

    @property
    def available_capacity(self) -> int:
        return max(0, self.max_concurrent - self.current_load)

    @property
    def load_ratio(self) -> float:
        return self.current_load / self.max_concurrent if self.max_concurrent > 0 else 1.0


class ClusterCapabilityRegistry:
    STANDARD_CAPS = {
        "llm_inference", "web_scraping", "email_outreach",
        "payment_processing", "pdf_generation", "data_analysis",
        "hunt_detection", "offer_creation", "negotiation",
        "channel_management", "sourcing", "monitoring"
    }

    def __init__(self):
        self._nodes: Dict[str, NodeCapability] = {}
        self._lock = threading.RLock()
        self.register_node("local", self.STANDARD_CAPS, max_concurrent=20)

    def register_node(self, node_id: str, capabilities: Set[str] = None,
                      max_concurrent: int = 10, specializations: Dict[str, float] = None) -> None:
        with self._lock:
            self._nodes[node_id] = NodeCapability(
                node_id=node_id,
                capabilities=capabilities or self.STANDARD_CAPS.copy(),
                max_concurrent=max_concurrent,
                specializations=specializations or {}
            )

    def find_best_node(self, required_capability: str) -> Optional[str]:
        with self._lock:
            candidates = []
            for nid, node in self._nodes.items():
                if not node.healthy or required_capability not in node.capabilities:
                    continue
                spec_score = node.specializations.get(required_capability, 0.5)
                load_score = 1.0 - node.load_ratio
                score = spec_score * 0.6 + load_score * 0.4
                candidates.append((nid, score))
            if not candidates:
                return None
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

    def find_nodes_with(self, capability: str) -> List[str]:
        with self._lock:
            return [nid for nid, n in self._nodes.items()
                    if capability in n.capabilities and n.healthy]

    def update_load(self, node_id: str, load: int) -> None:
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].current_load = load
                self._nodes[node_id].last_update = time.time()

    def increment_load(self, node_id: str) -> bool:
        with self._lock:
            node = self._nodes.get(node_id)
            if node and node.available_capacity > 0:
                node.current_load += 1
                return True
            return False

    def decrement_load(self, node_id: str) -> None:
        with self._lock:
            node = self._nodes.get(node_id)
            if node and node.current_load > 0:
                node.current_load -= 1

    def set_health(self, node_id: str, healthy: bool) -> None:
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].healthy = healthy

    def get_cluster_capacity(self) -> Dict:
        with self._lock:
            total_cap = sum(n.max_concurrent for n in self._nodes.values() if n.healthy)
            total_load = sum(n.current_load for n in self._nodes.values() if n.healthy)
            healthy = sum(1 for n in self._nodes.values() if n.healthy)
            return {
                "total_nodes": len(self._nodes), "healthy_nodes": healthy,
                "total_capacity": total_cap, "total_load": total_load,
                "available": total_cap - total_load,
                "utilization": total_load / total_cap if total_cap > 0 else 0
            }

    def get_stats(self) -> Dict:
        cap = self.get_cluster_capacity()
        with self._lock:
            all_caps = set()
            for n in self._nodes.values():
                all_caps.update(n.capabilities)
        cap["unique_capabilities"] = len(all_caps)
        return cap

_reg = None
_reg_lock = threading.Lock()
def get_capability_registry() -> ClusterCapabilityRegistry:
    global _reg
    if _reg is None:
        with _reg_lock:
            if _reg is None:
                _reg = ClusterCapabilityRegistry()
    return _reg
