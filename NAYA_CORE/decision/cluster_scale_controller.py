"""NAYA V19 - Cluster Scale Controller - Controleur de scaling du cluster"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.CLUSTER_SCALE_CONTROLLER")

class ClusterScaleController:
    """Controleur de scaling du cluster."""

    def __init__(self):
        self._history: List[Dict] = []

    def evaluate_scaling(self, load: float, queue_size: int) -> Dict:
        if load > 0.8 or queue_size > 20:
            return {"action": "scale_up", "reason": f"load={load} queue={queue_size}"}
        elif load < 0.2 and queue_size == 0:
            return {"action": "scale_down", "reason": "Low load"}
        return {"action": "maintain", "load": load}

    def recommend_nodes(self, workload_type: str) -> int:
        RECS = {"hunt": 2, "outreach": 3, "analysis": 1, "payment": 1}
        return RECS.get(workload_type, 1)

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
