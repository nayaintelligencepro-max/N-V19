"""NAYA V19 - Cognition hybride - Combine LLM et logique interne pour decisions"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_HYBRID_COGNITION")

class EngineHybridCognition:
    """Combine LLM et logique interne pour decisions."""

    def __init__(self):
        self._log: List[Dict] = []

    def decide(self, context: Dict, llm_available: bool = False) -> Dict:
        if llm_available:
            return {"method": "llm_augmented", "confidence": 0.85, "fallback": False}
        return {"method": "rule_based", "confidence": 0.6, "fallback": True, "note": "LLM indisponible, logique interne utilisee"}

    def score_with_fallback(self, data: Dict) -> float:
        value = data.get("value", 0)
        urgency = data.get("urgency", 0.5)
        solvability = data.get("solvability", 0.5)
        return round(value * 0.3 + urgency * 0.35 + solvability * 0.35, 3)

    def get_stats(self) -> Dict:
        return {"module": "engine_hybrid_cognition", "log_size": len(self._log)}
