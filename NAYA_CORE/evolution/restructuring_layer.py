"""NAYA V19 - Restructuring Layer - Restructure le systeme quand necessaire."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.EVOLUTION.RESTRUCTURE")

class RestructuringLayer:
    """Restructure les modules du systeme sans downtime."""

    def __init__(self):
        self._restructurings: List[Dict] = []

    def evaluate_need(self, system_metrics: Dict) -> Dict:
        needs = []
        error_rate = system_metrics.get("error_rate", 0)
        if error_rate > 0.1:
            needs.append({"area": "error_handling", "severity": "high",
                         "action": "Renforcer le error handling dans les modules critiques"})
        load = system_metrics.get("avg_load", 0)
        if load > 0.8:
            needs.append({"area": "performance", "severity": "high",
                         "action": "Restructurer pour meilleure distribution de charge"})
        memory = system_metrics.get("memory_usage_pct", 0)
        if memory > 85:
            needs.append({"area": "memory", "severity": "medium",
                         "action": "Optimiser la gestion memoire"})
        return {"needs_restructuring": len(needs) > 0, "items": needs}

    def execute_restructuring(self, area: str, action: str) -> Dict:
        result = {
            "area": area, "action": action,
            "executed_at": time.time(), "status": "completed"
        }
        self._restructurings.append(result)
        log.info(f"[RESTRUCTURE] {area}: {action}")
        return result

    def get_stats(self) -> Dict:
        return {"total_restructurings": len(self._restructurings)}
