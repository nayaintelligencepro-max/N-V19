"""NAYA V19 - Structural Intervention - Interventions structurelles du systeme."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.EXEC.INTERVENTION")

class StructuralIntervention:
    """Decide et execute des interventions structurelles quand necessaire."""

    INTERVENTION_TYPES = {
        "rebalance": "Reequilibrer les ressources entre projets",
        "pivot": "Pivoter un projet non performant",
        "accelerate": "Accelerer un projet tres performant",
        "pause": "Mettre en pause un projet a risque",
        "merge": "Fusionner deux projets complementaires",
    }

    def __init__(self):
        self._interventions: List[Dict] = []
        self._total = 0

    def evaluate_need(self, system_state: Dict) -> Dict:
        needs = []
        revenue = system_state.get("weekly_revenue", 0)
        target = system_state.get("weekly_target", 60000)
        if revenue < target * 0.5:
            needs.append({"type": "accelerate", "reason": f"Revenue {revenue} sous 50% objectif"})
        errors = system_state.get("error_count", 0)
        if errors > 10:
            needs.append({"type": "rebalance", "reason": f"{errors} erreurs detectees"})
        return {"needs_intervention": len(needs) > 0, "interventions": needs}

    def execute(self, intervention_type: str, target: str, params: Dict = None) -> Dict:
        result = {
            "type": intervention_type, "target": target,
            "params": params or {}, "ts": time.time(),
            "description": self.INTERVENTION_TYPES.get(intervention_type, "")
        }
        self._interventions.append(result)
        self._total += 1
        return result

    def get_stats(self) -> Dict:
        return {"total_interventions": self._total, "recent": self._interventions[-5:]}
