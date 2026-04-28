"""NAYA V19 - Normalisation d ambition - Calibre les ambitions par rapport aux capacites reelles"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_AMBITION_NORMALIZATION")

class EngineAmbitionNormalization:
    """Calibre les ambitions par rapport aux capacites reelles."""

    def __init__(self):
        self._log: List[Dict] = []

    AMBITION_LEVELS = {"conservative": 0.7, "balanced": 1.0, "aggressive": 1.5, "ultra": 2.0}

    def normalize(self, target_revenue: float, current_capacity: float) -> Dict:
        achievable = current_capacity * 4  # 4 weeks
        ratio = target_revenue / achievable if achievable > 0 else 2.0
        if ratio > 2.0:
            return {"level": "unrealistic", "adjusted_target": achievable * 1.5, "original": target_revenue, "ratio": ratio}
        elif ratio > 1.5:
            return {"level": "aggressive", "adjusted_target": target_revenue, "ratio": ratio, "warning": "Requires max effort"}
        return {"level": "achievable", "target": target_revenue, "ratio": ratio}

    def recommend_level(self, weeks_experience: int) -> str:
        if weeks_experience < 4: return "conservative"
        elif weeks_experience < 12: return "balanced"
        return "aggressive"

    def get_stats(self) -> Dict:
        return {"module": "engine_ambition_normalization", "log_size": len(self._log)}
