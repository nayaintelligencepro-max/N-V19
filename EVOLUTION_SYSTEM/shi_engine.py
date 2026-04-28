"""NAYA V19 - SHI Engine - Strategic Health Index."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.SHI")

class SHIEngine:
    """Calcule l indice de sante strategique global du systeme."""

    DIMENSIONS = {
        "revenue_health": 0.25,
        "hunt_efficiency": 0.20,
        "system_stability": 0.20,
        "evolution_rate": 0.15,
        "security_posture": 0.10,
        "pipeline_depth": 0.10,
    }

    def __init__(self):
        self._scores: Dict[str, float] = {d: 0.5 for d in self.DIMENSIONS}
        self._history: list = []

    def update(self, dimension: str, score: float) -> None:
        if dimension in self._scores:
            self._scores[dimension] = max(0, min(1, score))

    def calculate_shi(self) -> Dict:
        shi = sum(self._scores[d] * w for d, w in self.DIMENSIONS.items())
        level = "excellent" if shi > 0.8 else "good" if shi > 0.6 else "moderate" if shi > 0.4 else "critical"
        result = {"shi": round(shi, 3), "level": level, "dimensions": self._scores.copy()}
        self._history.append({"shi": shi, "ts": time.time()})
        return result

    def get_trend(self, n: int = 10) -> List:
        return self._history[-n:]

    def get_stats(self) -> Dict:
        return self.calculate_shi()

from typing import List
