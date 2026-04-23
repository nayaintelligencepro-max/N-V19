"""NAYA V19 - Adaptive Growth Core - Croissance adaptative du systeme."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.GROWTH")

class AdaptiveGrowthCore:
    """Le systeme grandit en s adaptant: renforce ce qui marche, abandonne ce qui echoue."""

    def __init__(self):
        self._growth_metrics: Dict[str, float] = {}
        self._adaptations: List[Dict] = []

    def record_metric(self, area: str, performance: float) -> None:
        current = self._growth_metrics.get(area, 0.5)
        self._growth_metrics[area] = current * 0.7 + performance * 0.3

    def get_growth_areas(self) -> List[Dict]:
        return [
            {"area": a, "score": round(s, 3), "action": "reinforce" if s > 0.6 else "adapt"}
            for a, s in sorted(self._growth_metrics.items(), key=lambda x: x[1], reverse=True)
        ]

    def suggest_adaptation(self) -> Dict:
        weak = [a for a, s in self._growth_metrics.items() if s < 0.4]
        strong = [a for a, s in self._growth_metrics.items() if s > 0.7]
        return {
            "reinforce": strong[:3], "adapt": weak[:3],
            "overall_growth": sum(self._growth_metrics.values()) / max(1, len(self._growth_metrics))
        }

    def get_stats(self) -> Dict:
        return {"areas_tracked": len(self._growth_metrics), "adaptations": len(self._adaptations)}
