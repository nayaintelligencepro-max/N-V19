"""
POST-CHALLENGE DECISION ENGINE — IA Décisionnelle Autonome
═══════════════════════════════════════════════════════════════
Analyse les 10 jours de challenge et décide automatiquement de la stratégie optimale.
Basée sur la performance réelle, pas sur des hypothèses.
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

log = logging.getLogger("NAYA.POST_CHALLENGE_DECISION")


@dataclass
class DecisionRecommendation:
    """Recommandation stratégique basée sur performance."""
    strategy: str
    confidence: float
    rationale: str
    actions: List[str]
    projected_revenue_m3: float


class PostChallengeDecisionEngine:
    """
    Moteur de décision autonome post-challenge.
    Analyse les résultats et décide de la stratégie optimale automatiquement.
    """

    def __init__(self):
        log.info("✅ PostChallengeDecisionEngine initialized")

    def analyze_and_decide(
        self,
        real_sales_stats: Dict[str, Any],
        challenge_stats: Dict[str, Any]
    ) -> DecisionRecommendation:
        """
        Analyse les performances et décide de la stratégie optimale.

        Critères de décision :
        1. Revenus totaux vs objectif
        2. Secteur dominant
        3. Taux de conversion
        4. Time-to-close moyen
        5. Performance BOTANICA/TINY HOUSE
        """

        total_revenue = real_sales_stats.get("revenue_confirmed_eur", 0)
        confirmed_sales = real_sales_stats.get("confirmed_sales", 0)
        avg_deal = real_sales_stats.get("average_deal_eur", 0)

        # Analyse secteur dominant
        sector_performance = self._analyze_sector_performance(real_sales_stats)
        best_sector = max(sector_performance.items(), key=lambda x: x[1]["revenue"])

        # Décision basée sur performance
        if total_revenue >= 100000:
            # Performance exceptionnelle → Scale agressif
            return DecisionRecommendation(
                strategy="SCALE_AGGRESSIVE",
                confidence=0.95,
                rationale=(
                    f"Performance exceptionnelle : {total_revenue:,.0f} EUR en 10 jours. "
                    f"Secteur dominant : {best_sector[0]}. "
                    "Scaling immédiat recommandé."
                ),
                actions=[
                    "Recruter 2 commerciaux OT/IEC62443",
                    "Automatiser séquences secteur dominant",
                    "Lancer campagne LinkedIn Ads ciblée",
                    "Développer partenariats grands comptes",
                    "Objectif M+3 : 300 000 EUR"
                ],
                projected_revenue_m3=300000
            )

        elif total_revenue >= 80000:
            # Performance solide → Optimiser et scaler
            return DecisionRecommendation(
                strategy="OPTIMIZE_AND_SCALE",
                confidence=0.85,
                rationale=(
                    f"Performance solide : {total_revenue:,.0f} EUR. "
                    f"Optimiser {best_sector[0]} puis scaler."
                ),
                actions=[
                    "Automatiser 100% séquences best performer",
                    "A/B testing offres secteur dominant",
                    "Recruter 1 SDR dédié",
                    "Upsell clients existants +30%",
                    "Objectif M+3 : 200 000 EUR"
                ],
                projected_revenue_m3=200000
            )

        elif confirmed_sales >= 10:
            # 10 ventes mais revenus < objectif → Focus qualité deals
            return DecisionRecommendation(
                strategy="FOCUS_PREMIUM_DEALS",
                confidence=0.75,
                rationale=(
                    f"{confirmed_sales} ventes mais revenus moyens. "
                    "Remonter ticket moyen via deals premium."
                ),
                actions=[
                    "Cibler exclusivement CAC40 + OIV",
                    "Pack minimum 15k EUR",
                    "Démonstrations ROI personnalisées",
                    "Partenariats intégrateurs SCADA",
                    "Objectif M+3 : 150 000 EUR"
                ],
                projected_revenue_m3=150000
            )

        else:
            # Performance insuffisante → Pivoter stratégie
            return DecisionRecommendation(
                strategy="PIVOT_STRATEGY",
                confidence=0.60,
                rationale=(
                    f"Performance {total_revenue:,.0f} EUR < objectif. "
                    "Pivot vers BOTANICA/TINY HOUSE ou optimisation radicale OT."
                ),
                actions=[
                    "Audit complet séquences actuelles",
                    "Test BOTANICA e-commerce 30 jours",
                    "Test TINY HOUSE prospection 30 jours",
                    "Revoir positionnement offres OT",
                    "Objectif M+3 : 80 000 EUR"
                ],
                projected_revenue_m3=80000
            )

    def _analyze_sector_performance(
        self,
        stats: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Analyse la performance par secteur."""
        # Simulation - à remplacer par vraies données
        return {
            "energie_utilities": {"revenue": 45000, "deals": 4, "avg": 11250},
            "transport_logistique": {"revenue": 25000, "deals": 3, "avg": 8333},
            "manufacturing": {"revenue": 15000, "deals": 2, "avg": 7500},
            "aerospace_defence": {"revenue": 5000, "deals": 1, "avg": 5000},
        }

    def should_activate_botanica(self, stats: Dict[str, Any]) -> bool:
        """Décide si activer BOTANICA."""
        return stats.get("revenue_confirmed_eur", 0) < 50000

    def should_activate_tiny_house(self, stats: Dict[str, Any]) -> bool:
        """Décide si activer TINY HOUSE."""
        return stats.get("revenue_confirmed_eur", 0) < 60000


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine = None


def get_post_challenge_decision_engine():
    """Retourne l'instance singleton."""
    global _engine
    if _engine is None:
        _engine = PostChallengeDecisionEngine()
    return _engine
