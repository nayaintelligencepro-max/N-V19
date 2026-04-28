"""NAYA V19 - Extracteur de couts caches - Detecte les couts caches dans les organisations"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.HIDDEN_COST_EXTRACTORS")

class HiddenCostExtractors:
    """Detecte les couts caches dans les organisations."""

    def __init__(self):
        self._log: List[Dict] = []

    HIDDEN_COST_PATTERNS = [
        {"pattern": "manual_processes", "multiplier": 2.0, "description": "Processus manuels repetitifs"},
        {"pattern": "employee_turnover", "multiplier": 1.5, "description": "Turnover employes lie au probleme"},
        {"pattern": "opportunity_cost", "multiplier": 3.0, "description": "Cout d opportunite manquee"},
        {"pattern": "compliance_risk", "multiplier": 2.5, "description": "Risque de non-conformite"},
    ]

    def extract(self, visible_cost: float, patterns_detected: list) -> Dict:
        total_hidden = 0
        details = []
        for p in self.HIDDEN_COST_PATTERNS:
            if p["pattern"] in patterns_detected:
                hidden = visible_cost * (p["multiplier"] - 1)
                total_hidden += hidden
                details.append({"pattern": p["pattern"], "hidden_cost": hidden, "desc": p["description"]})
        return {"visible_cost": visible_cost, "hidden_cost": total_hidden, "total_real_cost": visible_cost + total_hidden, "details": details}

    def get_stats(self) -> Dict:
        return {"module": "hidden_cost_extractors"}
