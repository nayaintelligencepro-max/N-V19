"""
NAYA V19.6 — Offer Pricing Model
Revenue Module
Tarification dynamique contextuelle basée sur prospect, secteur, moment marché
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

class PricingStrategy(str):
    """Stratégies tarifaires"""
    VALUE_BASED = "value_based"      # Basé valeur pour client
    COST_PLUS = "cost_plus"          # Coût + marge
    DYNAMIC = "dynamic"              # Dynamique marché
    TIERED = "tiered"                # Tiers (Quick/Standard/Premium)
    COMPETITIVE = "competitive"      # Basé concurrence

@dataclass
class PricingContext:
    """Contexte de tarification"""
    prospect_company_size: int
    prospect_revenue_eur: float
    sector: str
    ot_signals_strength: float  # 0.0-1.0 signal urgence
    urgency_level: str  # "low", "medium", "high", "critical"
    decision_maker_level: str  # "analyst", "manager", "director", "cfo"
    seasonality: str  # "q1", "q2", "q3", "q4"
    budget_cycle_status: str  # "open", "closing", "frozen"
    competitor_pressure: float  # 0.0-1.0

@dataclass
class OfferPrice:
    """Offre tarifée"""
    base_price_eur: float
    adjustments_eur: float
    final_price_eur: float
    strategy_used: PricingStrategy
    confidence_score: float  # 0.0-1.0
    justification: str
    discount_percent: float = 0.0
    payment_terms: str = "Net 30"
    proposal_valid_until: str = ""

class OfferPricingModel:
    """
    Modèle tarifaire dynamique V19.
    Adapte prix selon : secteur, urgence, budget prospect, cycles budgétaires.
    Minimum: 1000 EUR (inviolable).
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sector_multipliers = {
            "Transport": 1.0,
            "Energie": 1.3,           # Budgets plus larges
            "Manufacturing": 1.1,
            "IEC62443": 1.2,
            "CAC40": 1.5,             # Grands comptes
            "SME": 0.85                # PME
        }
        self.urgency_multipliers = {
            "low": 0.9,
            "medium": 1.0,
            "high": 1.15,
            "critical": 1.35
        }

    async def calculate_price(
        self,
        base_service_price: float,
        context: PricingContext,
        strategy: PricingStrategy = PricingStrategy.DYNAMIC
    ) -> OfferPrice:
        """Calcule prix offre dynamiquement"""
        try:
            # Validations
            if base_service_price < 1000:
                self.logger.warning(f"Base price {base_service_price} < 1000 EUR minimum")

            # Calcul prix selon stratégie
            if strategy == PricingStrategy.VALUE_BASED:
                final_price = await self._calculate_value_based(base_service_price, context)

            elif strategy == PricingStrategy.DYNAMIC:
                final_price = await self._calculate_dynamic_price(base_service_price, context)

            elif strategy == PricingStrategy.TIERED:
                final_price = await self._calculate_tiered_price(base_service_price, context)

            elif strategy == PricingStrategy.COMPETITIVE:
                final_price = await self._calculate_competitive_price(base_service_price, context)

            else:
                final_price = base_service_price

            # Ajustements finaux
            adjustments = final_price - base_service_price
            confidence = self._calculate_confidence(context, strategy)
            justification = self._generate_justification(context, strategy, adjustments)

            return OfferPrice(
                base_price_eur=base_service_price,
                adjustments_eur=adjustments,
                final_price_eur=final_price,
                strategy_used=strategy,
                confidence_score=confidence,
                justification=justification,
                discount_percent=max(0, -adjustments / base_service_price * 100) if adjustments < 0 else 0,
                proposal_valid_until=self._get_valid_until_date()
            )

        except Exception as e:
            self.logger.error(f"Pricing calculation failed: {e}")
            # Fallback: base price
            return OfferPrice(
                base_price_eur=base_service_price,
                adjustments_eur=0.0,
                final_price_eur=base_service_price,
                strategy_used=PricingStrategy.COST_PLUS,
                confidence_score=0.5,
                justification="Fallback pricing: calculation error"
            )

    async def _calculate_value_based(
        self,
        base_price: float,
        context: PricingContext
    ) -> float:
        """Tarification basée valeur pour client"""

        # Plus la douleur est forte, plus on peut charger
        pain_multiplier = 1.0 + (context.ot_signals_strength * 0.5)

        # Taille du prospect
        if context.prospect_revenue_eur > 100_000_000:
            size_multiplier = 1.4  # Grands comptes peuvent payer plus
        elif context.prospect_revenue_eur > 10_000_000:
            size_multiplier = 1.2
        else:
            size_multiplier = 1.0

        final = base_price * pain_multiplier * size_multiplier
        return max(final, 1000)  # Minimum inviolable

    async def _calculate_dynamic_price(
        self,
        base_price: float,
        context: PricingContext
    ) -> float:
        """Tarification dynamique (marché + urgence)"""

        # Multiplicateurs
        sector_mult = self.sector_multipliers.get(context.sector, 1.0)
        urgency_mult = self.urgency_multipliers.get(context.urgency_level, 1.0)

        # Budget cycle: prix plus élevé si fin de trimestre (rush budgets)
        cycle_mult = 1.15 if context.budget_cycle_status == "closing" else 1.0

        # Ajustement concurrence
        competition_discount = 1.0 - (context.competitor_pressure * 0.2)

        final = base_price * sector_mult * urgency_mult * cycle_mult * competition_discount
        return max(final, 1000)

    async def _calculate_tiered_price(
        self,
        base_price: float,
        context: PricingContext
    ) -> float:
        """Tarification par tiers (Quick/Standard/Premium)"""

        # Decision maker level → tier
        if context.decision_maker_level in ["cfo", "director"]:
            # Premium tier: charge 30% plus
            return base_price * 1.3
        elif context.decision_maker_level == "manager":
            # Standard tier
            return base_price
        else:
            # Analyst: discount 15%
            return base_price * 0.85

    async def _calculate_competitive_price(
        self,
        base_price: float,
        context: PricingContext
    ) -> float:
        """Tarification vs concurrence"""

        # Si forte pression concurrence, réduire légèrement
        if context.competitor_pressure > 0.7:
            return base_price * 0.9  # 10% discount face concurrence
        else:
            return base_price

    def _calculate_confidence(self, context: PricingContext, strategy: PricingStrategy) -> float:
        """Score confiance de l'estimation tarifaire"""
        score = 0.8  # Base

        # Données complètes → confiance +
        if context.prospect_revenue_eur > 0:
            score += 0.1
        if context.ot_signals_strength > 0.5:
            score += 0.05

        # Données incomplètes → confiance -
        if context.urgency_level == "low":
            score -= 0.1

        return min(score, 1.0)

    def _generate_justification(
        self,
        context: PricingContext,
        strategy: PricingStrategy,
        adjustments: float
    ) -> str:
        """Justifie la tarification"""

        reasons = []

        if strategy == PricingStrategy.VALUE_BASED:
            if context.ot_signals_strength > 0.7:
                reasons.append("High pain signal = value-based premium")

        if context.urgency_level == "critical":
            reasons.append("Critical urgency multiplier applied")

        if context.prospect_revenue_eur > 100_000_000:
            reasons.append("Enterprise-scale prospect = premium pricing")

        if context.competitor_pressure > 0.7:
            reasons.append("Competitive pressure = competitive pricing")

        if adjustments < 0:
            reasons.append(f"Early-bird discount: {abs(adjustments):.0f} EUR")

        return " | ".join(reasons) if reasons else "Standard pricing applied"

    def _get_valid_until_date(self) -> str:
        """Retourne date validité proposition"""
        from datetime import datetime, timedelta
        valid_until = datetime.utcnow() + timedelta(days=14)
        return valid_until.strftime("%Y-%m-%d")

    async def apply_discount(
        self,
        offer_price: OfferPrice,
        reason: str,
        discount_percent: float
    ) -> OfferPrice:
        """Applique réduction"""

        if discount_percent > 30:
            self.logger.warning(f"Large discount {discount_percent}% requested - escalate to leadership")

        discount_amount = offer_price.final_price_eur * discount_percent / 100
        new_final = max(offer_price.final_price_eur - discount_amount, 1000)

        offer_price.final_price_eur = new_final
        offer_price.discount_percent = discount_percent
        offer_price.justification += f" | Discount {discount_percent}% ({reason})"

        return offer_price

    def get_pricing_recommendations(self, context: PricingContext) -> Dict:
        """Retourne recommandations tarifaires"""
        return {
            "recommended_strategy": PricingStrategy.DYNAMIC,
            "sector_dynamics": self.sector_multipliers.get(context.sector, 1.0),
            "urgency_factor": self.urgency_multipliers.get(context.urgency_level, 1.0),
            "market_conditions": {
                "competitor_pressure": context.competitor_pressure,
                "budget_cycle": context.budget_cycle_status,
                "seasonality": context.seasonality
            },
            "recommendation": "Use dynamic pricing with urgency multiplier"
        }

# Export
__all__ = ['OfferPricingModel', 'PricingStrategy', 'PricingContext', 'OfferPrice']
