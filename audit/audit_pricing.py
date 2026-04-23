"""
NAYA SUPREME V19 — Audit Pricing Engine
Dynamic pricing based on company size, OT complexity, sector. 5k-20k EUR range.
Production-ready, async, zero placeholders.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.AuditPricing")


class AuditPricing:
    """
    Dynamic pricing engine for OT/ICS audits.
    Calculates fair pricing based on scope, complexity, and value delivered.
    """

    # Base pricing tiers (EUR)
    BASE_PRICING = {
        "express": {"min": 5000, "max": 10000, "duration_days": 5},
        "standard": {"min": 10000, "max": 20000, "duration_days": 10},
        "comprehensive": {"min": 20000, "max": 40000, "duration_days": 20},
        "enterprise": {"min": 40000, "max": 100000, "duration_days": 40},
    }

    # Sector multipliers (criticality factor)
    SECTOR_MULTIPLIERS = {
        "Energy": 1.4,
        "Water": 1.3,
        "Transport": 1.2,
        "Defense": 1.5,
        "Healthcare": 1.2,
        "Manufacturing": 1.0,
        "Food": 1.0,
        "Chemicals": 1.3,
        "Banking": 1.2,
    }

    # Company size multipliers
    SIZE_MULTIPLIERS = {
        "Small": 0.7,
        "Medium": 1.0,
        "Large": 1.3,
        "Enterprise": 1.6,
    }

    # Complexity factors
    COMPLEXITY_FACTORS = {
        "ot_device_count": {
            "0-50": 0.8,
            "51-200": 1.0,
            "201-500": 1.3,
            "500+": 1.6,
        },
        "site_count": {
            "1": 1.0,
            "2-5": 1.2,
            "6-10": 1.4,
            "10+": 1.7,
        },
        "system_types": {
            "1-2": 0.9,
            "3-4": 1.1,
            "5+": 1.3,
        },
    }

    async def calculate_price(
        self,
        company_name: str,
        sector: str,
        company_size: str,
        audit_scope: Dict[str, Any],
        audit_type: str = "IEC62443",
    ) -> Dict[str, Any]:
        """
        Calculate audit price dynamically.

        Args:
            company_name: Target company
            sector: Industry sector
            company_size: Small/Medium/Large/Enterprise
            audit_scope: Scope details (devices, sites, systems, etc.)
            audit_type: IEC62443, NIS2, or BOTH

        Returns:
            Detailed pricing breakdown
        """
        log.info(f"Calculating audit price for {company_name} ({sector}, {company_size})")

        try:
            # Determine base tier
            tier = await self._determine_tier(audit_scope, company_size)

            # Get base price range
            base_min = self.BASE_PRICING[tier]["min"]
            base_max = self.BASE_PRICING[tier]["max"]

            # Apply sector multiplier
            sector_multiplier = self.SECTOR_MULTIPLIERS.get(sector, 1.0)

            # Apply size multiplier
            size_multiplier = self.SIZE_MULTIPLIERS.get(company_size, 1.0)

            # Apply complexity multipliers
            complexity_multiplier = await self._calculate_complexity(audit_scope)

            # Calculate final price
            total_multiplier = sector_multiplier * size_multiplier * complexity_multiplier

            calculated_min = int(base_min * total_multiplier)
            calculated_max = int(base_max * total_multiplier)

            # Ensure minimum floor (1000 EUR - PLANCHER INVIOLABLE)
            calculated_min = max(1000, calculated_min)
            calculated_max = max(calculated_min, calculated_max)

            # Adjust for audit type
            if audit_type == "BOTH":
                calculated_min = int(calculated_min * 1.5)
                calculated_max = int(calculated_max * 1.5)

            # Recommend optimal price (70% of range)
            recommended_price = int(calculated_min + (calculated_max - calculated_min) * 0.7)

            # Build pricing tiers (3 options)
            pricing_options = self._build_pricing_options(
                calculated_min, calculated_max, tier, audit_type
            )

            pricing_result = {
                "company_name": company_name,
                "sector": sector,
                "company_size": company_size,
                "audit_type": audit_type,
                "tier": tier,
                "duration_days": self.BASE_PRICING[tier]["duration_days"],
                "price_range_eur": {
                    "min": calculated_min,
                    "max": calculated_max,
                },
                "recommended_price_eur": recommended_price,
                "pricing_options": pricing_options,
                "multipliers": {
                    "sector": sector_multiplier,
                    "size": size_multiplier,
                    "complexity": complexity_multiplier,
                    "total": total_multiplier,
                },
                "scope_details": audit_scope,
            }

            log.info(
                f"Price calculated for {company_name}: {recommended_price} EUR "
                f"(range: {calculated_min}-{calculated_max} EUR)"
            )

            return pricing_result

        except Exception as e:
            log.error(f"Pricing calculation failed for {company_name}: {e}", exc_info=True)
            raise

    async def _determine_tier(
        self, audit_scope: Dict[str, Any], company_size: str
    ) -> str:
        """Determine pricing tier based on scope."""
        await asyncio.sleep(0.01)

        device_count = audit_scope.get("ot_device_count", 0)
        site_count = audit_scope.get("site_count", 1)
        system_types = len(audit_scope.get("system_types", []))

        # Scoring system
        score = 0

        # Device count contribution
        if device_count > 500:
            score += 4
        elif device_count > 200:
            score += 3
        elif device_count > 50:
            score += 2
        else:
            score += 1

        # Site count contribution
        if site_count > 10:
            score += 3
        elif site_count > 5:
            score += 2
        elif site_count > 1:
            score += 1

        # System types contribution
        if system_types >= 5:
            score += 2
        elif system_types >= 3:
            score += 1

        # Company size contribution
        if company_size == "Enterprise":
            score += 2
        elif company_size == "Large":
            score += 1

        # Map score to tier
        if score >= 10:
            return "enterprise"
        elif score >= 7:
            return "comprehensive"
        elif score >= 4:
            return "standard"
        else:
            return "express"

    async def _calculate_complexity(self, audit_scope: Dict[str, Any]) -> float:
        """Calculate complexity multiplier."""
        await asyncio.sleep(0.01)

        multiplier = 1.0

        # Device count
        device_count = audit_scope.get("ot_device_count", 0)
        if device_count > 500:
            multiplier *= self.COMPLEXITY_FACTORS["ot_device_count"]["500+"]
        elif device_count > 200:
            multiplier *= self.COMPLEXITY_FACTORS["ot_device_count"]["201-500"]
        elif device_count > 50:
            multiplier *= self.COMPLEXITY_FACTORS["ot_device_count"]["51-200"]
        else:
            multiplier *= self.COMPLEXITY_FACTORS["ot_device_count"]["0-50"]

        # Site count
        site_count = audit_scope.get("site_count", 1)
        if site_count > 10:
            multiplier *= self.COMPLEXITY_FACTORS["site_count"]["10+"]
        elif site_count > 5:
            multiplier *= self.COMPLEXITY_FACTORS["site_count"]["6-10"]
        elif site_count > 1:
            multiplier *= self.COMPLEXITY_FACTORS["site_count"]["2-5"]
        else:
            multiplier *= self.COMPLEXITY_FACTORS["site_count"]["1"]

        # System types
        system_types = len(audit_scope.get("system_types", []))
        if system_types >= 5:
            multiplier *= self.COMPLEXITY_FACTORS["system_types"]["5+"]
        elif system_types >= 3:
            multiplier *= self.COMPLEXITY_FACTORS["system_types"]["3-4"]
        else:
            multiplier *= self.COMPLEXITY_FACTORS["system_types"]["1-2"]

        return round(multiplier, 2)

    def _build_pricing_options(
        self,
        min_price: int,
        max_price: int,
        tier: str,
        audit_type: str,
    ) -> List[Dict[str, Any]]:
        """Build 3 pricing options (essential, recommended, premium)."""
        # Essential - minimum
        essential_price = min_price

        # Recommended - 70% of range
        recommended_price = int(min_price + (max_price - min_price) * 0.7)

        # Premium - maximum with extras
        premium_price = max_price

        options = [
            {
                "tier": "Essential",
                "price_eur": essential_price,
                "description": f"Core {audit_type} audit",
                "deliverables": [
                    "Gap analysis report",
                    "Compliance score",
                    "Priority recommendations",
                ],
                "duration_days": self.BASE_PRICING[tier]["duration_days"],
            },
            {
                "tier": "Recommended",
                "price_eur": recommended_price,
                "description": f"Complete {audit_type} audit with roadmap",
                "deliverables": [
                    "Comprehensive audit report (20-40 pages)",
                    "Gap analysis and findings",
                    "Detailed recommendations",
                    "Implementation roadmap",
                    "Executive presentation",
                ],
                "duration_days": self.BASE_PRICING[tier]["duration_days"] + 2,
                "popular": True,
            },
            {
                "tier": "Premium",
                "price_eur": premium_price,
                "description": f"Full {audit_type} audit + implementation support",
                "deliverables": [
                    "All Recommended tier deliverables",
                    "Vulnerability scanning",
                    "Remediation support (30 days)",
                    "Training session for team",
                    "Quarterly follow-up review",
                ],
                "duration_days": self.BASE_PRICING[tier]["duration_days"] + 5,
            },
        ]

        return options

    async def estimate_from_signals(
        self,
        sector: str,
        company_size: str,
        pain_signals: List[str],
    ) -> Dict[str, Any]:
        """
        Estimate pricing from pain signals (quick estimate for outreach).

        Args:
            sector: Industry sector
            company_size: Small/Medium/Large/Enterprise
            pain_signals: List of detected pain signals

        Returns:
            Quick price estimate
        """
        log.info(f"Estimating price from signals: {sector}, {company_size}")

        try:
            # Infer scope from pain signals
            inferred_scope = {
                "ot_device_count": 100,  # Assume medium
                "site_count": 1,
                "system_types": ["SCADA", "PLC"],  # Default
            }

            # If multiple pain signals, assume higher complexity
            if len(pain_signals) > 3:
                inferred_scope["ot_device_count"] = 300
                inferred_scope["site_count"] = 2

            # Call main pricing function
            pricing = await self.calculate_price(
                company_name="Prospect",
                sector=sector,
                company_size=company_size,
                audit_scope=inferred_scope,
                audit_type="IEC62443",
            )

            return {
                "estimated_price_eur": pricing["recommended_price_eur"],
                "price_range_eur": pricing["price_range_eur"],
                "tier": pricing["tier"],
                "confidence": "MEDIUM",
                "note": "Estimate based on pain signals - subject to scope confirmation",
            }

        except Exception as e:
            log.error(f"Signal-based pricing estimate failed: {e}", exc_info=True)
            # Fallback to conservative estimate
            return {
                "estimated_price_eur": 15000,
                "price_range_eur": {"min": 10000, "max": 20000},
                "tier": "standard",
                "confidence": "LOW",
                "note": "Conservative fallback estimate",
            }
