#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Pricing Intelligence
Dynamic contextual pricing based on sector, company size, pain urgency.
TIERS: TIER1=1k-5k, TIER2=5k-20k, TIER3=20k-100k, TIER4=100k+
Minimum floor 1000 EUR enforced (INVIOLABLE).
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.PricingIntelligence")


# ── Pricing Tiers ─────────────────────────────────────────────────────────────
class PricingTier(str, Enum):
    TIER1 = "TIER1_QUICK_WINS"        # 1k-5k EUR
    TIER2 = "TIER2_PROJETS_COURTS"    # 5k-20k EUR
    TIER3 = "TIER3_CONTRATS_LONGS"    # 20k-100k EUR
    TIER4 = "TIER4_RETAINERS"         # 100k+ EUR


TIER_RANGES = {
    PricingTier.TIER1: {"min": 1_000, "max": 5_000},
    PricingTier.TIER2: {"min": 5_000, "max": 20_000},
    PricingTier.TIER3: {"min": 20_000, "max": 100_000},
    PricingTier.TIER4: {"min": 100_000, "max": None},  # No upper limit
}


# ── Data Models ───────────────────────────────────────────────────────────────
@dataclass
class PricingRecommendation:
    """Dynamic pricing recommendation."""
    base_price: float
    recommended_price: float
    tier: PricingTier
    min_acceptable: float
    max_ceiling: float
    discount_available: float  # Percentage
    urgency_premium: float     # Percentage
    factors: Dict
    confidence: float          # 0-100
    created_at: str

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data


# ── Pricing Intelligence Engine ───────────────────────────────────────────────
class PricingIntelligence:
    """
    Dynamic contextual pricing engine.

    Factors:
    - Sector (critical sectors = premium)
    - Company size (larger = higher budget capacity)
    - Pain urgency (critical = can charge premium)
    - Competition level (high competition = must be competitive)
    - Deal size (volume discounts possible)
    - Timing (end of quarter = more flexible)
    - Historical performance (learn from wins/losses)

    Constraints:
    - Minimum floor: 1000 EUR (INVIOLABLE)
    - Sector-specific pricing bands
    - Competitor benchmarking
    """

    MIN_CONTRACT_VALUE = 1_000  # EUR - INVIOLABLE FLOOR

    # Sector base prices (EUR)
    SECTOR_BASE_PRICES = {
        "transport_logistique": 15_000,
        "energie_utilities": 40_000,
        "manufacturing": 15_000,
        "iec62443": 20_000,
        "other": 10_000,
    }

    # Sector multipliers
    SECTOR_MULTIPLIERS = {
        "energie_utilities": 1.3,      # Critical infrastructure premium
        "iec62443": 1.2,               # Niche specialization premium
        "transport_logistique": 1.1,
        "manufacturing": 1.0,
        "other": 0.9,
    }

    def __init__(self, storage_path: str = "data/intelligence/pricing_history.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.pricing_history: List[Dict] = []
        self._load_history()
        log.info("✅ PricingIntelligence initialized")

    # ── Storage ───────────────────────────────────────────────────────────────
    def _load_history(self) -> None:
        """Load pricing history from storage."""
        if self.storage_path.exists():
            try:
                self.pricing_history = json.loads(self.storage_path.read_text())
                log.info("Loaded %d pricing records", len(self.pricing_history))
            except Exception as exc:
                log.warning("Failed to load pricing history: %s", exc)
                self.pricing_history = []

    def _save_history(self) -> None:
        """Save pricing history to storage."""
        try:
            self.storage_path.write_text(json.dumps(self.pricing_history, indent=2, default=str))
        except Exception as exc:
            log.warning("Failed to save pricing history: %s", exc)

    # ── Main Pricing Logic ────────────────────────────────────────────────────
    async def calculate_price(
        self,
        sector: str,
        company_size: str,        # small, medium, large, enterprise
        pain_urgency: str,        # low, medium, high, critical
        service_type: str,        # audit, consulting, training, saas, etc
        company_revenue: Optional[float] = None,
        competition_level: str = "medium",  # low, medium, high
        context: Optional[Dict] = None,
    ) -> PricingRecommendation:
        """
        Calculate dynamic price for a service.

        Args:
            sector: Business sector
            company_size: Company size category
            pain_urgency: Pain urgency level
            service_type: Type of service
            company_revenue: Company revenue in EUR (optional)
            competition_level: Level of competition
            context: Additional context

        Returns:
            PricingRecommendation with price, tier, and factors
        """
        context = context or {}

        # Start with sector base price
        base_price = self.SECTOR_BASE_PRICES.get(sector, self.SECTOR_BASE_PRICES["other"])

        # Apply factors
        factors = {}
        multiplier = 1.0

        # 1. Sector multiplier
        sector_mult = self.SECTOR_MULTIPLIERS.get(sector, 1.0)
        multiplier *= sector_mult
        factors["sector_multiplier"] = sector_mult

        # 2. Company size
        size_mult = self._company_size_multiplier(company_size, company_revenue)
        multiplier *= size_mult
        factors["company_size_multiplier"] = size_mult

        # 3. Pain urgency
        urgency_mult = self._urgency_multiplier(pain_urgency)
        multiplier *= urgency_mult
        factors["urgency_multiplier"] = urgency_mult

        # 4. Service type
        service_mult = self._service_type_multiplier(service_type)
        multiplier *= service_mult
        factors["service_type_multiplier"] = service_mult

        # 5. Competition adjustment
        competition_mult = self._competition_multiplier(competition_level)
        multiplier *= competition_mult
        factors["competition_multiplier"] = competition_mult

        # Calculate recommended price
        recommended_price = base_price * multiplier

        # Apply floor constraint
        if recommended_price < self.MIN_CONTRACT_VALUE:
            log.warning("Price %.0f EUR below floor, enforcing minimum %.0f EUR",
                       recommended_price, self.MIN_CONTRACT_VALUE)
            recommended_price = self.MIN_CONTRACT_VALUE

        # Determine tier
        tier = self._determine_tier(recommended_price)

        # Calculate discount range
        discount_available = self._calculate_discount_available(
            recommended_price, pain_urgency, competition_level
        )

        # Calculate urgency premium (if applicable)
        urgency_premium = self._calculate_urgency_premium(pain_urgency)

        # Min/max bounds
        min_acceptable = recommended_price * (1 - discount_available / 100)
        min_acceptable = max(min_acceptable, self.MIN_CONTRACT_VALUE)

        max_ceiling = recommended_price * (1 + urgency_premium / 100)

        # Confidence score based on data quality
        confidence = self._calculate_confidence(context)

        recommendation = PricingRecommendation(
            base_price=base_price,
            recommended_price=round(recommended_price, 0),
            tier=tier,
            min_acceptable=round(min_acceptable, 0),
            max_ceiling=round(max_ceiling, 0),
            discount_available=discount_available,
            urgency_premium=urgency_premium,
            factors=factors,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
        )

        # Record in history
        self._record_pricing(recommendation, sector, context)

        log.info("💰 Pricing: %s → %.0f EUR (tier=%s, discount=%.0f%%)",
                 sector, recommended_price, tier.value, discount_available)

        return recommendation

    # ── Multiplier Calculations ───────────────────────────────────────────────
    def _company_size_multiplier(self, company_size: str, revenue: Optional[float]) -> float:
        """Calculate company size multiplier."""
        size_lower = company_size.lower()

        # Revenue-based (preferred)
        if revenue:
            if revenue >= 500_000_000:      # 500M+ EUR
                return 2.5
            elif revenue >= 100_000_000:    # 100M+ EUR
                return 2.0
            elif revenue >= 50_000_000:     # 50M+ EUR
                return 1.7
            elif revenue >= 10_000_000:     # 10M+ EUR
                return 1.4
            elif revenue >= 1_000_000:      # 1M+ EUR
                return 1.1
            else:
                return 0.9

        # Size-based (fallback)
        if "enterprise" in size_lower or "large" in size_lower:
            return 2.0
        elif "medium" in size_lower or "mid" in size_lower:
            return 1.3
        elif "small" in size_lower:
            return 1.0
        else:
            return 0.9

    def _urgency_multiplier(self, urgency: str) -> float:
        """Calculate urgency multiplier."""
        urgency_lower = urgency.lower()

        if urgency_lower == "critical":
            return 1.5
        elif urgency_lower == "high":
            return 1.3
        elif urgency_lower == "medium":
            return 1.1
        else:  # low
            return 1.0

    def _service_type_multiplier(self, service_type: str) -> float:
        """Calculate service type multiplier."""
        service_lower = service_type.lower()

        multipliers = {
            "audit": 1.0,
            "consulting": 1.2,
            "training": 0.8,
            "saas": 0.5,  # Monthly recurring
            "retainer": 1.5,
            "certification": 1.3,
            "remediation": 1.4,
        }

        for key, mult in multipliers.items():
            if key in service_lower:
                return mult

        return 1.0

    def _competition_multiplier(self, competition_level: str) -> float:
        """Calculate competition adjustment."""
        comp_lower = competition_level.lower()

        if comp_lower == "high":
            return 0.9  # Must be competitive
        elif comp_lower == "low":
            return 1.2  # Can charge premium
        else:  # medium
            return 1.0

    # ── Tier & Bounds ─────────────────────────────────────────────────────────
    def _determine_tier(self, price: float) -> PricingTier:
        """Determine pricing tier based on price."""
        if price >= TIER_RANGES[PricingTier.TIER4]["min"]:
            return PricingTier.TIER4
        elif price >= TIER_RANGES[PricingTier.TIER3]["min"]:
            return PricingTier.TIER3
        elif price >= TIER_RANGES[PricingTier.TIER2]["min"]:
            return PricingTier.TIER2
        else:
            return PricingTier.TIER1

    def _calculate_discount_available(
        self,
        price: float,
        urgency: str,
        competition: str,
    ) -> float:
        """Calculate available discount percentage."""
        base_discount = 10.0  # 10% base

        # More discount for high-urgency deals (close faster)
        if urgency.lower() == "critical":
            base_discount += 5.0
        elif urgency.lower() == "high":
            base_discount += 3.0

        # More discount for competitive situations
        if competition.lower() == "high":
            base_discount += 5.0

        # Less discount for premium tiers
        tier = self._determine_tier(price)
        if tier == PricingTier.TIER4:
            base_discount *= 0.7
        elif tier == PricingTier.TIER3:
            base_discount *= 0.85

        return min(base_discount, 20.0)  # Max 20% discount

    def _calculate_urgency_premium(self, urgency: str) -> float:
        """Calculate urgency premium percentage."""
        urgency_lower = urgency.lower()

        if urgency_lower == "critical":
            return 30.0  # Can charge up to 30% premium
        elif urgency_lower == "high":
            return 15.0
        else:
            return 0.0

    def _calculate_confidence(self, context: Dict) -> float:
        """Calculate confidence score based on data quality."""
        score = 50.0

        if context.get("company_revenue"):
            score += 15
        if context.get("competitor_prices"):
            score += 15
        if context.get("historical_deals"):
            score += 10
        if context.get("pain_score"):
            score += 10

        return min(score, 100.0)

    # ── History & Learning ────────────────────────────────────────────────────
    def _record_pricing(
        self,
        recommendation: PricingRecommendation,
        sector: str,
        context: Dict,
    ) -> None:
        """Record pricing decision in history."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "sector": sector,
            "recommended_price": recommendation.recommended_price,
            "tier": recommendation.tier.value,
            "factors": recommendation.factors,
            "context": context,
        }
        self.pricing_history.append(record)

        # Keep last 1000 records
        if len(self.pricing_history) > 1000:
            self.pricing_history = self.pricing_history[-1000:]

        self._save_history()

    async def record_outcome(
        self,
        recommended_price: float,
        actual_price: float,
        won: bool,
        sector: str,
    ) -> None:
        """
        Record pricing outcome for learning.

        Args:
            recommended_price: Our recommended price
            actual_price: Actual price closed at
            won: Whether we won the deal
            sector: Business sector
        """
        outcome = {
            "timestamp": datetime.now().isoformat(),
            "recommended_price": recommended_price,
            "actual_price": actual_price,
            "won": won,
            "sector": sector,
            "discount_pct": ((recommended_price - actual_price) / recommended_price * 100)
                           if recommended_price > 0 else 0,
        }

        # Add to history
        if "outcomes" not in self.__dict__:
            self.outcomes = []
        self.outcomes.append(outcome)

        log.info("📊 Pricing outcome recorded: won=%s, price=%.0f EUR (rec=%.0f EUR)",
                 won, actual_price, recommended_price)

    # ── Competitor Benchmarking ───────────────────────────────────────────────
    async def benchmark_competitors(
        self,
        sector: str,
        service_type: str,
    ) -> Dict:
        """
        Benchmark competitor pricing (mock for now).

        In production, would scrape competitor websites, analyze RFP responses, etc.
        """
        # Mock competitor data
        competitor_prices = {
            "audit": {
                "low": 10_000,
                "avg": 25_000,
                "high": 50_000,
            },
            "consulting": {
                "low": 15_000,
                "avg": 40_000,
                "high": 100_000,
            },
        }

        service_lower = service_type.lower()
        for key in competitor_prices:
            if key in service_lower:
                return competitor_prices[key]

        return {"low": 5_000, "avg": 15_000, "high": 40_000}

    # ── Query ─────────────────────────────────────────────────────────────────
    def get_stats(self) -> Dict:
        """Get pricing statistics."""
        if not self.pricing_history:
            return {
                "total_quotes": 0,
                "avg_price": 0,
                "by_tier": {},
                "by_sector": {},
            }

        by_tier = {}
        by_sector = {}

        for record in self.pricing_history:
            tier = record.get("tier", "unknown")
            sector = record.get("sector", "unknown")

            by_tier[tier] = by_tier.get(tier, 0) + 1
            by_sector[sector] = by_sector.get(sector, 0) + 1

        return {
            "total_quotes": len(self.pricing_history),
            "avg_price": sum(r["recommended_price"] for r in self.pricing_history) / len(self.pricing_history),
            "by_tier": by_tier,
            "by_sector": by_sector,
        }


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test Pricing Intelligence."""
    print("💰 NAYA Pricing Intelligence — Test Module\n")

    pricing = PricingIntelligence()

    # Test scenarios
    test_cases = [
        {
            "name": "Small manufacturing audit",
            "sector": "manufacturing",
            "company_size": "small",
            "pain_urgency": "medium",
            "service_type": "audit",
            "company_revenue": 2_000_000,
            "competition_level": "medium",
        },
        {
            "name": "Large energy utility consulting",
            "sector": "energie_utilities",
            "company_size": "large",
            "pain_urgency": "critical",
            "service_type": "consulting",
            "company_revenue": 500_000_000,
            "competition_level": "low",
        },
        {
            "name": "Medium transport IEC62443 certification",
            "sector": "transport_logistique",
            "company_size": "medium",
            "pain_urgency": "high",
            "service_type": "certification",
            "company_revenue": 50_000_000,
            "competition_level": "high",
        },
    ]

    for test in test_cases:
        name = test.pop("name")
        print(f"\n{'='*70}")
        print(f"Scenario: {name}")
        print(f"{'='*70}")

        recommendation = await pricing.calculate_price(**test)

        print(f"\n💰 Pricing Recommendation:")
        print(f"   Base Price: {recommendation.base_price:,.0f} EUR")
        print(f"   Recommended Price: {recommendation.recommended_price:,.0f} EUR")
        print(f"   Tier: {recommendation.tier.value}")
        print(f"   Min Acceptable: {recommendation.min_acceptable:,.0f} EUR")
        print(f"   Max Ceiling: {recommendation.max_ceiling:,.0f} EUR")
        print(f"   Discount Available: {recommendation.discount_available:.0f}%")
        print(f"   Urgency Premium: {recommendation.urgency_premium:.0f}%")
        print(f"   Confidence: {recommendation.confidence:.0f}%")

        print(f"\n   Factors:")
        for factor, value in recommendation.factors.items():
            print(f"     {factor}: {value:.2f}x")

    # Stats
    print(f"\n{'='*70}")
    print("Statistics")
    print(f"{'='*70}")
    stats = pricing.get_stats()
    print(f"Total quotes: {stats['total_quotes']}")
    print(f"Avg price: {stats['avg_price']:,.0f} EUR")
    print(f"By tier: {stats['by_tier']}")
    print(f"By sector: {stats['by_sector']}")


if __name__ == "__main__":
    asyncio.run(main())
