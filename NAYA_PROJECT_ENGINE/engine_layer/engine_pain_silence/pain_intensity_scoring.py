"""NAYA V19 - Scoring intensite douleur - Score l intensite de la douleur pour priorisation"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.PAIN_INTENSITY_SCORING")

class PainIntensityScoring:
    """Score l intensite de la douleur pour priorisation."""

    def __init__(self):
        self._log: List[Dict] = []

    WEIGHTS = {"financial_impact": 0.3, "frequency": 0.2, "visibility": 0.15, "urgency": 0.2, "solvability": 0.15}

    def score(self, financial_impact: float, frequency: float, visibility: float,
              urgency: float, solvability: float) -> Dict:
        total = (financial_impact * self.WEIGHTS["financial_impact"] +
                 frequency * self.WEIGHTS["frequency"] +
                 visibility * self.WEIGHTS["visibility"] +
                 urgency * self.WEIGHTS["urgency"] +
                 solvability * self.WEIGHTS["solvability"])
        level = "critical" if total > 0.8 else "high" if total > 0.6 else "medium" if total > 0.4 else "low"
        return {"intensity_score": round(total, 3), "level": level, "actionable": total > 0.5}

    def get_stats(self) -> Dict:
        return {"module": "pain_intensity_scoring"}
