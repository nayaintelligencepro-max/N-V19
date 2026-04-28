"""NAYA CORE — Adaptive Feedback Engine"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

log = logging.getLogger("NAYA.EVOLUTION.FEEDBACK")

class AdaptiveFeedback:
    """Apprend des résultats passés pour affiner les décisions futures."""

    REFINEMENT_THRESHOLD = 20000  # EUR impact minimum pour déclencher raffinement
    MAX_HISTORY = 500

    def __init__(self):
        self._history: List[Dict] = []
        self._refinements_applied = 0
        self._patterns: Dict[str, float] = {}

    def learn(self, opportunity: Dict, result: Dict) -> Optional[str]:
        """
        Enregistre le résultat d'une opportunité et affine les patterns.
        Returns: refinement_type si raffinement appliqué, None sinon
        """
        impact = result.get("impact", 0)
        sector = opportunity.get("sector", "unknown")
        opp_type = opportunity.get("type", "unknown")

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "sector": sector,
            "type": opp_type,
            "impact": impact,
            "won": result.get("won", impact > 0),
            "price": opportunity.get("price", 0),
        }
        self._history.append(entry)
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY:]

        # Update sector score
        key = f"{sector}:{opp_type}"
        prev = self._patterns.get(key, 0.5)
        self._patterns[key] = prev * 0.8 + (1.0 if entry["won"] else 0.0) * 0.2

        refinement = None
        if impact > self.REFINEMENT_THRESHOLD:
            refinement = "strategic"
            self._refinements_applied += 1
            log.info(f"[FEEDBACK] Strategic refinement triggered — impact={impact}€ sector={sector}")
        elif impact < -5000:
            refinement = "avoidance"
            log.warning(f"[FEEDBACK] Avoidance pattern stored — loss={impact}€ sector={sector}")

        return refinement

    def get_sector_score(self, sector: str, opp_type: str = "") -> float:
        """Returns win probability for a sector/type combo (0-1)."""
        key = f"{sector}:{opp_type}" if opp_type else sector
        return self._patterns.get(key, 0.5)

    def get_top_sectors(self, n: int = 5) -> List[Dict]:
        """Returns top n sectors by win score."""
        sorted_patterns = sorted(self._patterns.items(), key=lambda x: x[1], reverse=True)
        return [{"sector_type": k, "score": round(v, 3)} for k, v in sorted_patterns[:n]]

    def stats(self) -> Dict:
        return {
            "history_size": len(self._history),
            "refinements_applied": self._refinements_applied,
            "patterns_learned": len(self._patterns),
            "avg_impact": round(sum(e["impact"] for e in self._history) / max(len(self._history), 1), 2),
        }
