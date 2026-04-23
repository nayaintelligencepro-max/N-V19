"""NAYA V19 - Allocation Intelligence - Intelligence d allocation des ressources"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.ALLOCATION_INTELLIGENCE")

class AllocationIntelligence:
    """Intelligence d allocation des ressources."""

    def __init__(self):
        self._history: List[Dict] = []

    def allocate(self, resources: int, opportunities: list) -> Dict:
        total_value = sum(o.get("value", 0) for o in opportunities) or 1
        allocation = {}
        for o in opportunities:
            share = max(1, int(resources * o.get("value", 0) / total_value))
            allocation[o.get("id", "?")] = share
        return allocation

    def rebalance(self, current: Dict, performance: Dict) -> Dict:
        rebalanced = current.copy()
        for key, perf in performance.items():
            if perf > 0.8 and key in rebalanced:
                rebalanced[key] = int(rebalanced[key] * 1.2)
            elif perf < 0.3 and key in rebalanced:
                rebalanced[key] = max(1, int(rebalanced[key] * 0.7))
        return rebalanced

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
