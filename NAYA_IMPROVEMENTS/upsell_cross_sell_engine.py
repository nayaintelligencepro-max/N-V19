"""
AMÉLIORATION REVENU #5 — Moteur d'upsell et cross-sell automatique.

Détecte les opportunités d'upsell et cross-sell sur les clients existants
pour maximiser la valeur à vie (LTV) de chaque client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class UpsellOpportunity:
    """Une opportunité d'upsell ou cross-sell identifiée."""
    opportunity_id: str
    client_id: str
    current_service: str
    recommended_service: str
    opportunity_type: str  # upsell / cross_sell
    estimated_value_eur: float
    confidence: float
    trigger_reason: str
    recommended_timing: str


SERVICE_GRAPH: Dict[str, Dict[str, Any]] = {
    "security_assessment": {
        "upsell": ["audit_iec62443", "audit_nis2"],
        "cross_sell": ["formation_ot", "monitoring_continu"],
        "value_multiplier": 2.5,
    },
    "audit_iec62443": {
        "upsell": ["remediation_plan", "certification_accompagnement"],
        "cross_sell": ["audit_nis2", "formation_ot"],
        "value_multiplier": 2.0,
    },
    "audit_nis2": {
        "upsell": ["remediation_plan", "conformite_continue"],
        "cross_sell": ["audit_iec62443", "security_assessment"],
        "value_multiplier": 1.8,
    },
    "formation_ot": {
        "upsell": ["formation_avancee", "certification"],
        "cross_sell": ["security_assessment", "audit_iec62443"],
        "value_multiplier": 3.0,
    },
    "remediation_plan": {
        "upsell": ["managed_security_service"],
        "cross_sell": ["formation_ot", "monitoring_continu"],
        "value_multiplier": 1.5,
    },
}

SERVICE_PRICES: Dict[str, float] = {
    "audit_iec62443": 8000,
    "audit_nis2": 12000,
    "security_assessment": 5000,
    "formation_ot": 3000,
    "remediation_plan": 15000,
    "formation_avancee": 6000,
    "certification_accompagnement": 20000,
    "conformite_continue": 18000,
    "managed_security_service": 30000,
    "monitoring_continu": 24000,
    "certification": 10000,
}


class UpsellCrossSellEngine:
    """
    Détecte et recommande les opportunités d'upsell/cross-sell.

    Analyse le portefeuille client et le graphe de services pour identifier
    les services complémentaires à forte valeur ajoutée.
    """

    TIMING_RULES: Dict[str, str] = {
        "upsell": "30 jours après livraison du service initial",
        "cross_sell": "14 jours après le premier rapport positif",
    }

    def __init__(self) -> None:
        self._opportunities: List[UpsellOpportunity] = []
        self._total_identified_eur: float = 0.0
        logger.info("[UpsellCrossSellEngine] Initialisé — graphe de services chargé")

    def analyze_client(
        self,
        client_id: str,
        current_services: List[str],
        satisfaction_score: float = 0.8,
        months_as_client: int = 1,
    ) -> List[UpsellOpportunity]:
        """Analyse un client et identifie les opportunités."""
        opportunities: List[UpsellOpportunity] = []

        for current_service in current_services:
            graph = SERVICE_GRAPH.get(current_service, {})

            for upsell_service in graph.get("upsell", []):
                if upsell_service in current_services:
                    continue
                price = SERVICE_PRICES.get(upsell_service, 5000)
                confidence = min(0.95, satisfaction_score * (1 + months_as_client * 0.05))

                opp = UpsellOpportunity(
                    opportunity_id=f"UP_{client_id}_{upsell_service}",
                    client_id=client_id,
                    current_service=current_service,
                    recommended_service=upsell_service,
                    opportunity_type="upsell",
                    estimated_value_eur=price,
                    confidence=round(confidence, 3),
                    trigger_reason=f"Client satisfait ({satisfaction_score:.0%}) de {current_service}",
                    recommended_timing=self.TIMING_RULES["upsell"],
                )
                opportunities.append(opp)
                self._total_identified_eur += price

            for cross_service in graph.get("cross_sell", []):
                if cross_service in current_services:
                    continue
                price = SERVICE_PRICES.get(cross_service, 5000)
                confidence = min(0.85, satisfaction_score * 0.8)

                opp = UpsellOpportunity(
                    opportunity_id=f"CS_{client_id}_{cross_service}",
                    client_id=client_id,
                    current_service=current_service,
                    recommended_service=cross_service,
                    opportunity_type="cross_sell",
                    estimated_value_eur=price,
                    confidence=round(confidence, 3),
                    trigger_reason=f"Complémentaire naturel de {current_service}",
                    recommended_timing=self.TIMING_RULES["cross_sell"],
                )
                opportunities.append(opp)
                self._total_identified_eur += price

        opportunities.sort(key=lambda o: o.estimated_value_eur * o.confidence, reverse=True)
        self._opportunities.extend(opportunities)

        logger.info(
            f"[UpsellCrossSellEngine] {client_id}: "
            f"{len(opportunities)} opportunités identifiées "
            f"({sum(o.estimated_value_eur for o in opportunities):,.0f} EUR)"
        )
        return opportunities

    def stats(self) -> Dict[str, Any]:
        return {
            "total_opportunities": len(self._opportunities),
            "total_identified_eur": self._total_identified_eur,
            "by_type": {
                "upsell": len([o for o in self._opportunities if o.opportunity_type == "upsell"]),
                "cross_sell": len([o for o in self._opportunities if o.opportunity_type == "cross_sell"]),
            },
        }


upsell_cross_sell_engine = UpsellCrossSellEngine()
