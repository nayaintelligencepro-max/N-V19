"""
NAYA V19 - Predictive Scoring Engine
Score de probabilite de closing pour chaque opportunite.
Base sur: taille douleur, reactivite prospect, secteur, historique succes.
"""
import time, logging, threading, math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.SCORING.PREDICT")

@dataclass
class ScoringInput:
    pain_value_eur: float
    pain_urgency: float         # 0-1
    prospect_responsiveness: float  # 0-1 (a-t-il repondu vite?)
    sector: str
    offer_match_quality: float  # 0-1 (offre vs besoin)
    competitor_presence: float  # 0-1
    decision_maker_contact: bool
    budget_confirmed: bool
    previous_interactions: int

@dataclass
class ScoringResult:
    close_probability: float
    priority_rank: str      # S, A, B, C, D
    recommended_action: str
    estimated_close_days: int
    factors: Dict[str, float] = field(default_factory=dict)

class PredictiveScoringEngine:
    """Score predictif de closing - priorise les meilleures opportunites."""

    SECTOR_WEIGHTS = {
        "pme": 0.7, "restaurant": 0.65, "commerce": 0.6,
        "tech": 0.5, "finance": 0.45, "sante": 0.5,
        "gouvernement": 0.35, "industrie": 0.4, "immobilier": 0.55,
        "energie": 0.4, "education": 0.5
    }

    def __init__(self):
        self._history: List[Dict] = []
        self._sector_success: Dict[str, List[bool]] = {}
        self._lock = threading.RLock()
        self._total_scored = 0

    def score(self, inp: ScoringInput) -> ScoringResult:
        """Calcule le score predictif de closing."""
        factors = {}

        # F1: Valeur de la douleur (log scale)
        if inp.pain_value_eur >= 50000:
            factors["value"] = 0.9
        elif inp.pain_value_eur >= 20000:
            factors["value"] = 0.75
        elif inp.pain_value_eur >= 5000:
            factors["value"] = 0.6
        else:
            factors["value"] = 0.4

        # F2: Urgence
        factors["urgency"] = inp.pain_urgency

        # F3: Reactivite prospect
        factors["responsiveness"] = inp.prospect_responsiveness

        # F4: Secteur (taux historique)
        sector_rate = self._get_sector_rate(inp.sector)
        factors["sector"] = sector_rate

        # F5: Qualite du match offre/besoin
        factors["match"] = inp.offer_match_quality

        # F6: Contact decision maker
        factors["decision_maker"] = 0.85 if inp.decision_maker_contact else 0.3

        # F7: Budget confirme
        factors["budget"] = 0.9 if inp.budget_confirmed else 0.4

        # F8: Historique interactions
        interaction_score = min(1.0, inp.previous_interactions * 0.15)
        factors["interactions"] = interaction_score

        # F9: Concurrence inverse
        factors["low_competition"] = 1.0 - inp.competitor_presence

        # Weighted average
        weights = {
            "value": 0.10, "urgency": 0.15, "responsiveness": 0.15,
            "sector": 0.10, "match": 0.15, "decision_maker": 0.12,
            "budget": 0.10, "interactions": 0.05, "low_competition": 0.08
        }
        probability = sum(factors[k] * weights[k] for k in weights)
        probability = max(0.05, min(0.98, probability))

        # Rank
        if probability >= 0.80:
            rank = "S"
            action = "CLOSER MAINTENANT - opportunite critique"
        elif probability >= 0.65:
            rank = "A"
            action = "Accelerer - relance dans 24h"
        elif probability >= 0.45:
            rank = "B"
            action = "Nurture - envoyer contenu de valeur"
        elif probability >= 0.25:
            rank = "C"
            action = "Veille - recontacter dans 7 jours"
        else:
            rank = "D"
            action = "Incubation - surveiller signaux"

        # Estimated close days
        if rank in ("S", "A"):
            est_days = max(1, int((1 - probability) * 10))
        elif rank == "B":
            est_days = max(7, int((1 - probability) * 21))
        else:
            est_days = max(14, int((1 - probability) * 60))

        result = ScoringResult(
            close_probability=round(probability, 3),
            priority_rank=rank,
            recommended_action=action,
            estimated_close_days=est_days,
            factors={k: round(v, 3) for k, v in factors.items()}
        )

        with self._lock:
            self._total_scored += 1
            self._history.append({
                "probability": probability, "rank": rank,
                "sector": inp.sector, "value": inp.pain_value_eur, "ts": time.time()
            })
            if len(self._history) > 2000:
                self._history = self._history[-1000:]

        return result

    def record_outcome(self, sector: str, closed: bool) -> None:
        """Enregistre le resultat reel pour ameliorer les predictions."""
        with self._lock:
            if sector not in self._sector_success:
                self._sector_success[sector] = []
            self._sector_success[sector].append(closed)
            if len(self._sector_success[sector]) > 200:
                self._sector_success[sector] = self._sector_success[sector][-100:]

    def _get_sector_rate(self, sector: str) -> float:
        with self._lock:
            history = self._sector_success.get(sector, [])
            if len(history) < 5:
                return self.SECTOR_WEIGHTS.get(sector, 0.5)
            return sum(history) / len(history)

    def rank_opportunities(self, opportunities: List[ScoringInput]) -> List[Dict]:
        """Classe une liste d opportunites par probabilite de closing."""
        scored = []
        for opp in opportunities:
            result = self.score(opp)
            scored.append({
                "input": opp, "result": result,
                "score": result.close_probability
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def get_stats(self) -> Dict:
        with self._lock:
            by_rank = {}
            for h in self._history[-100:]:
                by_rank[h["rank"]] = by_rank.get(h["rank"], 0) + 1
            return {
                "total_scored": self._total_scored,
                "recent_distribution": by_rank,
                "sector_rates": {
                    s: round(sum(h)/len(h), 2)
                    for s, h in self._sector_success.items() if h
                }
            }

_scoring = None
_scoring_lock = threading.Lock()
def get_predictive_scoring() -> PredictiveScoringEngine:
    global _scoring
    if _scoring is None:
        with _scoring_lock:
            if _scoring is None:
                _scoring = PredictiveScoringEngine()
    return _scoring
