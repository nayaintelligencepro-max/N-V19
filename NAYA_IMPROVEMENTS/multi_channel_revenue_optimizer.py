"""
AMÉLIORATION REVENU #3 — Optimiseur de revenus multi-canaux.

Distribue intelligemment les efforts commerciaux sur plusieurs canaux
(email, LinkedIn, téléphone, web) pour maximiser le ROI par canal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class ChannelPerformance:
    """Performance d'un canal de prospection."""
    channel: str
    total_touches: int = 0
    responses: int = 0
    meetings_booked: int = 0
    deals_closed: int = 0
    revenue_eur: float = 0.0
    cost_eur: float = 0.0

    @property
    def response_rate(self) -> float:
        return (self.responses / max(self.total_touches, 1)) * 100

    @property
    def roi(self) -> float:
        return (self.revenue_eur / max(self.cost_eur, 1)) - 1

    @property
    def cost_per_meeting(self) -> float:
        return self.cost_eur / max(self.meetings_booked, 1)


@dataclass
class ChannelAllocation:
    """Allocation recommandée par canal."""
    channel: str
    budget_pct: float
    effort_pct: float
    expected_roi: float
    reasoning: str


class MultiChannelRevenueOptimizer:
    """
    Optimise la distribution des efforts de prospection sur plusieurs canaux.

    Utilise les performances historiques pour réalloquer dynamiquement
    le budget et l'effort vers les canaux les plus rentables.
    """

    CHANNELS = ["email", "linkedin", "phone", "web_inbound", "referral", "events"]

    DEFAULT_ALLOCATIONS: Dict[str, float] = {
        "email": 0.35,
        "linkedin": 0.25,
        "phone": 0.15,
        "web_inbound": 0.10,
        "referral": 0.10,
        "events": 0.05,
    }

    def __init__(self) -> None:
        self._performance: Dict[str, ChannelPerformance] = {
            ch: ChannelPerformance(channel=ch) for ch in self.CHANNELS
        }
        self._optimization_runs: int = 0
        logger.info("[MultiChannelRevenueOptimizer] Initialisé — 6 canaux monitorés")

    def record_activity(
        self,
        channel: str,
        touches: int = 0,
        responses: int = 0,
        meetings: int = 0,
        deals: int = 0,
        revenue_eur: float = 0.0,
        cost_eur: float = 0.0,
    ) -> None:
        """Enregistre l'activité d'un canal."""
        if channel not in self._performance:
            self._performance[channel] = ChannelPerformance(channel=channel)
        perf = self._performance[channel]
        perf.total_touches += touches
        perf.responses += responses
        perf.meetings_booked += meetings
        perf.deals_closed += deals
        perf.revenue_eur += revenue_eur
        perf.cost_eur += cost_eur

    def optimize(self) -> List[ChannelAllocation]:
        """Calcule l'allocation optimale des efforts par canal."""
        self._optimization_runs += 1

        total_revenue = sum(p.revenue_eur for p in self._performance.values())
        total_touches = sum(p.total_touches for p in self._performance.values())

        allocations: List[ChannelAllocation] = []

        if total_touches < 50:
            for ch, default_pct in self.DEFAULT_ALLOCATIONS.items():
                allocations.append(ChannelAllocation(
                    channel=ch,
                    budget_pct=default_pct * 100,
                    effort_pct=default_pct * 100,
                    expected_roi=2.0,
                    reasoning="Allocation par défaut — données insuffisantes pour optimisation",
                ))
            return allocations

        roi_scores: Dict[str, float] = {}
        for ch, perf in self._performance.items():
            if perf.total_touches > 0:
                roi_scores[ch] = max(0.1, perf.roi + 1)
            else:
                roi_scores[ch] = 0.5

        total_score = sum(roi_scores.values())

        for ch, score in roi_scores.items():
            perf = self._performance[ch]
            allocation_pct = (score / total_score) * 100

            reasoning = (
                f"ROI: {perf.roi:.1f}x | "
                f"Taux réponse: {perf.response_rate:.1f}% | "
                f"Revenue: {perf.revenue_eur:,.0f} EUR"
            )

            allocations.append(ChannelAllocation(
                channel=ch,
                budget_pct=round(allocation_pct, 1),
                effort_pct=round(allocation_pct, 1),
                expected_roi=round(perf.roi, 2),
                reasoning=reasoning,
            ))

        allocations.sort(key=lambda a: a.budget_pct, reverse=True)

        logger.info(
            f"[MultiChannelRevenueOptimizer] Optimisation #{self._optimization_runs}: "
            f"top canal = {allocations[0].channel} ({allocations[0].budget_pct:.0f}%)"
        )
        return allocations

    def stats(self) -> Dict[str, Any]:
        return {
            "channels_tracked": len(self._performance),
            "optimization_runs": self._optimization_runs,
            "total_revenue_eur": sum(p.revenue_eur for p in self._performance.values()),
            "best_channel": max(
                self._performance.values(),
                key=lambda p: p.revenue_eur
            ).channel if self._performance else None,
        }


multi_channel_revenue_optimizer = MultiChannelRevenueOptimizer()
