"""
AMÉLIORATION REVENU #4 — Moteur de tarification intelligente.

Ajuste dynamiquement les prix en fonction de la taille du prospect,
du secteur, de l'urgence réglementaire et de la concurrence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PricingResult:
    """Résultat de la tarification intelligente."""
    service_key: str
    base_price_eur: float
    adjusted_price_eur: float
    discount_pct: float
    premium_pct: float
    factors_applied: Dict[str, float]
    confidence: float
    reasoning: str


class SmartPricingEngine:
    """
    Tarification dynamique basée sur des facteurs contextuels.

    Facteurs pris en compte :
    - Taille de l'entreprise (CA, effectif)
    - Urgence réglementaire (deadline NIS2/IEC62443)
    - Complexité technique (nombre de sites, assets OT)
    - Historique client (fidélité, volume)
    - Pression concurrentielle
    """

    SIZE_MULTIPLIERS: Dict[str, float] = {
        "startup": 0.70,
        "pme": 0.85,
        "eti": 1.00,
        "grande_entreprise": 1.30,
        "multinationale": 1.60,
    }

    URGENCY_PREMIUMS: Dict[str, float] = {
        "immediate": 0.25,
        "30_days": 0.15,
        "90_days": 0.05,
        "6_months": 0.00,
        "no_deadline": -0.05,
    }

    SECTOR_ADJUSTMENTS: Dict[str, float] = {
        "energie": 1.20,
        "transport": 1.15,
        "finance": 1.25,
        "industrie": 1.10,
        "sante": 1.15,
        "default": 1.00,
    }

    MINIMUM_PRICE_EUR: float = 1000.0

    def __init__(self) -> None:
        self._pricing_history: List[PricingResult] = []
        logger.info("[SmartPricingEngine] Initialisé — tarification dynamique activée")

    def _classify_company_size(self, revenue_eur: float, employees: int) -> str:
        if revenue_eur > 1_000_000_000 or employees > 5000:
            return "multinationale"
        if revenue_eur > 250_000_000 or employees > 1000:
            return "grande_entreprise"
        if revenue_eur > 50_000_000 or employees > 250:
            return "eti"
        if revenue_eur > 2_000_000 or employees > 10:
            return "pme"
        return "startup"

    def _get_sector_adjustment(self, sector: str) -> float:
        sector_lower = sector.lower()
        for key, adjustment in self.SECTOR_ADJUSTMENTS.items():
            if key in sector_lower:
                return adjustment
        return self.SECTOR_ADJUSTMENTS["default"]

    def calculate_price(
        self,
        service_key: str,
        base_price_eur: float,
        company_revenue_eur: float = 10_000_000,
        employee_count: int = 100,
        sector: str = "industrie",
        urgency: str = "90_days",
        is_returning_client: bool = False,
        complexity_score: float = 0.5,
    ) -> PricingResult:
        """Calcule le prix optimal pour un service donné."""
        factors: Dict[str, float] = {}

        company_size = self._classify_company_size(company_revenue_eur, employee_count)
        size_mult = self.SIZE_MULTIPLIERS.get(company_size, 1.0)
        factors["company_size"] = size_mult

        sector_adj = self._get_sector_adjustment(sector)
        factors["sector"] = sector_adj

        urgency_prem = self.URGENCY_PREMIUMS.get(urgency, 0)
        factors["urgency"] = 1.0 + urgency_prem

        complexity_adj = 1.0 + (complexity_score - 0.5) * 0.4
        factors["complexity"] = complexity_adj

        loyalty_discount = 0.0
        if is_returning_client:
            loyalty_discount = 0.10
            factors["loyalty_discount"] = -loyalty_discount

        total_multiplier = size_mult * sector_adj * (1 + urgency_prem) * complexity_adj
        adjusted_price = base_price_eur * total_multiplier

        if is_returning_client:
            adjusted_price *= (1 - loyalty_discount)

        adjusted_price = max(adjusted_price, self.MINIMUM_PRICE_EUR)
        adjusted_price = round(adjusted_price / 100) * 100

        premium_pct = ((adjusted_price / base_price_eur) - 1) * 100 if base_price_eur else 0
        discount_pct = max(0, -premium_pct)
        premium_pct = max(0, premium_pct)

        result = PricingResult(
            service_key=service_key,
            base_price_eur=base_price_eur,
            adjusted_price_eur=adjusted_price,
            discount_pct=round(discount_pct, 1),
            premium_pct=round(premium_pct, 1),
            factors_applied=factors,
            confidence=0.85,
            reasoning=(
                f"Entreprise {company_size} ({sector}) — "
                f"urgence {urgency} — "
                f"{'client fidèle' if is_returning_client else 'nouveau client'}"
            ),
        )

        self._pricing_history.append(result)
        logger.info(
            f"[SmartPricingEngine] {service_key}: "
            f"{base_price_eur:,.0f} EUR → {adjusted_price:,.0f} EUR "
            f"(x{total_multiplier:.2f})"
        )
        return result

    def stats(self) -> Dict[str, Any]:
        if not self._pricing_history:
            return {"total_priced": 0}
        avg_premium = sum(r.premium_pct for r in self._pricing_history) / len(self._pricing_history)
        return {
            "total_priced": len(self._pricing_history),
            "average_premium_pct": round(avg_premium, 1),
            "total_pipeline_value": sum(r.adjusted_price_eur for r in self._pricing_history),
        }


smart_pricing_engine = SmartPricingEngine()
