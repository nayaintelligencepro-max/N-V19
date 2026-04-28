"""
NAYA SUPREME V19.5 — AMÉLIORATION #4 : FEEDBACK LOOP CONNECTOR
═══════════════════════════════════════════════════════════════════
Connecte le pipeline de vente à l'AutonomousLearner.
Chaque deal WON/LOST/IGNORED est automatiquement enregistré
et les paramètres de chasse sont ajustés en temps réel.

FLUX : Pipeline → FeedbackLoopConnector → AutonomousLearner
       → Paramètres optimisés → HuntEngine (boucle fermée)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

log = logging.getLogger("NAYA.FEEDBACK_LOOP")


class DealResult(str):
    WON = "won"
    LOST = "lost"
    IGNORED = "ignored"
    RECYCLED = "recycled"


@dataclass
class DealFeedback:
    deal_id: str
    result: str
    sector: str
    signal_type: str
    offer_tier: str
    proposed_amount_eur: float
    final_amount_eur: float
    days_to_close: int
    objections_encountered: List[str] = field(default_factory=list)
    winning_angle: str = ""
    loss_reason: str = ""
    channel: str = "email"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class LearningInsight:
    sector: str
    metric: str
    old_value: float
    new_value: float
    change_pct: float
    confidence: float
    observation_count: int


class FeedbackLoopConnector:
    """
    Pont entre le pipeline de vente et le système d'apprentissage.
    Transforme chaque résultat de deal en signal d'apprentissage.
    """

    def __init__(self) -> None:
        self.feedback_log: List[DealFeedback] = []
        self.insights: List[LearningInsight] = []
        self.sector_stats: Dict[str, Dict[str, Any]] = {}
        self.channel_stats: Dict[str, Dict[str, Any]] = {}
        self.objection_stats: Dict[str, int] = {}
        self._optimal_params: Dict[str, Any] = {}

    def record_deal(self, feedback: DealFeedback) -> List[LearningInsight]:
        """
        Enregistre un deal et retourne les insights générés.
        """
        self.feedback_log.append(feedback)
        self._update_sector_stats(feedback)
        self._update_channel_stats(feedback)
        self._update_objection_stats(feedback)

        insights = self._compute_insights(feedback.sector)
        self.insights.extend(insights)

        log.info(
            "Deal recorded: %s result=%s sector=%s amount=%.0f€",
            feedback.deal_id, feedback.result, feedback.sector, feedback.final_amount_eur,
        )
        return insights

    def _update_sector_stats(self, fb: DealFeedback) -> None:
        if fb.sector not in self.sector_stats:
            self.sector_stats[fb.sector] = {
                "total": 0, "won": 0, "lost": 0, "ignored": 0,
                "total_revenue": 0.0, "avg_deal_value": 0.0,
                "avg_days_to_close": 0.0, "best_tier": "",
                "conversion_rate": 0.0,
            }
        s = self.sector_stats[fb.sector]
        s["total"] += 1
        if fb.result == "won":
            s["won"] += 1
            s["total_revenue"] += fb.final_amount_eur
        elif fb.result == "lost":
            s["lost"] += 1
        else:
            s["ignored"] += 1

        if s["won"] > 0:
            s["avg_deal_value"] = s["total_revenue"] / s["won"]
        s["conversion_rate"] = s["won"] / s["total"] if s["total"] > 0 else 0

        won_deals = [f for f in self.feedback_log
                     if f.sector == fb.sector and f.result == "won"]
        if won_deals:
            s["avg_days_to_close"] = sum(d.days_to_close for d in won_deals) / len(won_deals)
            tier_counts: Dict[str, int] = {}
            for d in won_deals:
                tier_counts[d.offer_tier] = tier_counts.get(d.offer_tier, 0) + 1
            s["best_tier"] = max(tier_counts, key=tier_counts.get) if tier_counts else ""

    def _update_channel_stats(self, fb: DealFeedback) -> None:
        if fb.channel not in self.channel_stats:
            self.channel_stats[fb.channel] = {
                "total": 0, "won": 0, "revenue": 0.0, "conversion_rate": 0.0,
            }
        c = self.channel_stats[fb.channel]
        c["total"] += 1
        if fb.result == "won":
            c["won"] += 1
            c["revenue"] += fb.final_amount_eur
        c["conversion_rate"] = c["won"] / c["total"] if c["total"] > 0 else 0

    def _update_objection_stats(self, fb: DealFeedback) -> None:
        for obj in fb.objections_encountered:
            self.objection_stats[obj] = self.objection_stats.get(obj, 0) + 1

    def _compute_insights(self, sector: str) -> List[LearningInsight]:
        insights = []
        s = self.sector_stats.get(sector)
        if not s or s["total"] < 3:
            return insights

        old_params = self._optimal_params.get(sector, {})
        old_conv = old_params.get("conversion_rate", 0.0)
        new_conv = s["conversion_rate"]

        if old_conv > 0 and abs(new_conv - old_conv) > 0.05:
            change = (new_conv - old_conv) / old_conv * 100 if old_conv else 0
            insights.append(LearningInsight(
                sector=sector,
                metric="conversion_rate",
                old_value=old_conv,
                new_value=new_conv,
                change_pct=change,
                confidence=min(s["total"] / 20, 1.0),
                observation_count=s["total"],
            ))

        self._optimal_params[sector] = {
            "conversion_rate": new_conv,
            "avg_deal_value": s["avg_deal_value"],
            "best_tier": s["best_tier"],
            "avg_days_to_close": s["avg_days_to_close"],
        }

        return insights

    def get_optimized_params(self, sector: str) -> Dict[str, Any]:
        """
        Retourne les paramètres optimisés pour un secteur donné.
        Utilisé par HuntEngine pour ajuster la stratégie.
        """
        return self._optimal_params.get(sector, {
            "conversion_rate": 0.0,
            "avg_deal_value": 5000,
            "best_tier": "TIER2",
            "avg_days_to_close": 14,
        })

    def get_top_objections(self, limit: int = 5) -> List[tuple]:
        sorted_obj = sorted(self.objection_stats.items(), key=lambda x: x[1], reverse=True)
        return sorted_obj[:limit]

    def get_best_channels(self) -> List[Dict[str, Any]]:
        channels = []
        for name, stats in self.channel_stats.items():
            channels.append({"channel": name, **stats})
        return sorted(channels, key=lambda x: x["conversion_rate"], reverse=True)

    def get_sector_rankings(self) -> List[Dict[str, Any]]:
        rankings = []
        for name, stats in self.sector_stats.items():
            rankings.append({"sector": name, **stats})
        return sorted(rankings, key=lambda x: x["conversion_rate"], reverse=True)

    def generate_telegram_report(self) -> str:
        total_deals = len(self.feedback_log)
        won_deals = sum(1 for f in self.feedback_log if f.result == "won")
        total_rev = sum(f.final_amount_eur for f in self.feedback_log if f.result == "won")
        conv_rate = won_deals / total_deals if total_deals > 0 else 0

        top_sector = ""
        if self.sector_stats:
            best = max(self.sector_stats.items(), key=lambda x: x[1]["conversion_rate"])
            top_sector = f"{best[0]} ({best[1]['conversion_rate']:.0%})"

        return (
            "NAYA LEARNING — Rapport\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Deals analysés    : {total_deals}\n"
            f"Taux conversion   : {conv_rate:.0%}\n"
            f"Revenu total WON  : {total_rev:,.0f}€\n"
            f"Meilleur secteur  : {top_sector}\n"
            f"Insights générés  : {len(self.insights)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )


feedback_loop_connector = FeedbackLoopConnector()
