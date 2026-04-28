"""NAYA V19 - Scoring Matrix - Score les taches pour routage optimal."""
import logging
from typing import Dict, List

log = logging.getLogger("NAYA.ROUTING.SCORE")

class ScoringMatrix:
    """Matrice de scoring pour determiner le meilleur executeur par tache."""

    WEIGHTS = {
        "latency": 0.3, "cost": 0.25, "reliability": 0.25, "capability": 0.2
    }

    EXECUTOR_PROFILES = {
        "local": {"latency": 0.1, "cost": 0.0, "reliability": 0.9, "capability": 0.7},
        "vm": {"latency": 0.3, "cost": 0.3, "reliability": 0.95, "capability": 0.9},
        "cloud_run": {"latency": 0.5, "cost": 0.6, "reliability": 0.99, "capability": 1.0},
    }

    def score_task(self, task_type: str, requirements: Dict = None) -> List[Dict]:
        """Score tous les executeurs pour une tache donnee."""
        req = requirements or {}
        needs_gpu = req.get("needs_gpu", False)
        needs_network = req.get("needs_network", True)
        max_latency = req.get("max_latency_s", 5.0)

        scored = []
        for name, profile in self.EXECUTOR_PROFILES.items():
            score = sum(
                (1.0 - profile[k]) * self.WEIGHTS[k]
                for k in self.WEIGHTS if k in profile
            )
            if needs_gpu and name == "local":
                score *= 0.5
            if not needs_network and name == "cloud_run":
                score *= 1.2  # Bonus offline
            scored.append({"executor": name, "score": round(score, 3), "profile": profile})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def best_executor(self, task_type: str, requirements: Dict = None) -> str:
        results = self.score_task(task_type, requirements)
        return results[0]["executor"] if results else "local"

    def get_stats(self) -> Dict:
        return {
            "executors": list(self.EXECUTOR_PROFILES.keys()),
            "weights": self.WEIGHTS
        }
