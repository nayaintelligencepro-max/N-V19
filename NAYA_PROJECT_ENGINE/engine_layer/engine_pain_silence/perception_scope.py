"""NAYA V19 - Perception Scope - Determine le scope de perception de la douleur par le prospect"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.PERCEPTION_SCOPE")

class PerceptionScope:
    """Determine le scope de perception de la douleur par le prospect."""

    def __init__(self):
        self._log: List[Dict] = []

    SCOPES = {
        "aware_and_searching": {"conversion_rate": 0.4, "approach": "solution_direct"},
        "aware_but_passive": {"conversion_rate": 0.2, "approach": "education_then_offer"},
        "unaware": {"conversion_rate": 0.05, "approach": "pain_revelation"},
        "in_denial": {"conversion_rate": 0.02, "approach": "data_confrontation"},
    }

    def classify(self, awareness_signals: Dict) -> Dict:
        if awareness_signals.get("actively_searching"): return {"scope": "aware_and_searching", **self.SCOPES["aware_and_searching"]}
        if awareness_signals.get("mentioned_problem"): return {"scope": "aware_but_passive", **self.SCOPES["aware_but_passive"]}
        if awareness_signals.get("denial_signals"): return {"scope": "in_denial", **self.SCOPES["in_denial"]}
        return {"scope": "unaware", **self.SCOPES["unaware"]}

    def get_stats(self) -> Dict:
        return {"module": "perception_scope"}
