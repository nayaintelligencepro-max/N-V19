"""
NAYA V19 - Dynamic Pricing Engine
Prix dynamique en temps reel: analyse capacite du prospect, urgence douleur,
rarete solution pour calculer le prix optimal. ROI-based pricing.
"""
import time, logging, threading, math
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.PRICING.DYNAMIC")

@dataclass
class PricingContext:
    pain_annual_cost: float       # Cout annuel de la douleur pour le prospect
    prospect_revenue: float       # CA estime du prospect
    urgency: float               # 0-1, urgence de resolution
    complexity: float            # 0-1, complexite de la solution
    market_rarity: float         # 0-1, rarete de la solution sur le marche
    competitor_count: int        # Nombre de concurrents sur cette douleur
    prospect_sophistication: float  # 0-1, maturite tech du prospect
    sector: str = ""
    geography: str = ""

@dataclass
class PricingResult:
    recommended_price: float
    floor_price: float
    ceiling_price: float
    roi_for_prospect: float
    confidence: float
    pricing_model: str
    breakdown: Dict[str, float] = field(default_factory=dict)
    payment_options: List[Dict] = field(default_factory=list)

class DynamicPricingEngine:
    """Moteur de prix dynamique adaptatif base sur le ROI reel du client."""

    ABSOLUTE_FLOOR = 1000  # Plancher premium absolu
    ROI_MULTIPLIER_MIN = 3.0  # Le prospect doit gagner au moins 3x
    ROI_MULTIPLIER_TARGET = 5.0  # Cible: 5x ROI

    SECTOR_PREMIUMS = {
        "finance": 1.5, "pharma": 1.4, "tech": 1.2, "gouvernement": 1.3,
        "energie": 1.4, "luxe": 1.6, "immobilier": 1.3, "sante": 1.3,
        "industrie": 1.2, "retail": 1.0, "pme": 1.0, "restaurant": 0.9
    }

    URGENCY_MULTIPLIERS = {
        (0.9, 1.0): 1.8,  # Critique: +80%
        (0.7, 0.9): 1.4,  # Urgent: +40%
        (0.5, 0.7): 1.15, # Modere: +15%
        (0.0, 0.5): 1.0   # Normal
    }

    def __init__(self):
        self._pricing_history: List[Dict] = []
        self._lock = threading.RLock()
        self._total_priced = 0
        self._total_value = 0.0
        self._conversion_rates: Dict[str, List[bool]] = {}

    def calculate_price(self, ctx: PricingContext) -> PricingResult:
        """Calcule le prix optimal en fonction du contexte."""
        # 1. Base: pourcentage du cout de la douleur
        if ctx.pain_annual_cost > 0:
            base_price = ctx.pain_annual_cost * 0.15  # 15% du cout annuel
        else:
            base_price = ctx.prospect_revenue * 0.005  # 0.5% du CA

        # 2. Multiplicateur urgence
        urgency_mult = 1.0
        for (lo, hi), mult in self.URGENCY_MULTIPLIERS.items():
            if lo <= ctx.urgency < hi:
                urgency_mult = mult
                break

        # 3. Multiplicateur rarete
        rarity_mult = 1.0 + (ctx.market_rarity * 0.5)  # +0-50%

        # 4. Multiplicateur secteur
        sector_mult = self.SECTOR_PREMIUMS.get(ctx.sector, 1.0)

        # 5. Ajustement concurrence
        competition_adj = 1.0
        if ctx.competitor_count == 0:
            competition_adj = 1.5  # Monopole de fait
        elif ctx.competitor_count <= 2:
            competition_adj = 1.2
        elif ctx.competitor_count >= 10:
            competition_adj = 0.85

        # 6. Calcul prix recommande
        raw_price = base_price * urgency_mult * rarity_mult * sector_mult * competition_adj

        # 7. Enforce floor — plancher absolu inviolable
        recommended = max(raw_price, self.ABSOLUTE_FLOOR)

        # 8. Pas de plafond — le prix est illimite vers le haut.
        # Seul le plancher (ABSOLUTE_FLOOR) est inviolable.
        # ceiling_price est conserve uniquement pour la transparence ROI client.
        ceiling = recommended * 10  # indicatif seulement, jamais appliqué comme limite

        # 9. ROI pour le prospect
        roi = ctx.pain_annual_cost / recommended if recommended > 0 else 0

        # 10. Ajuster si ROI trop faible
        if roi < self.ROI_MULTIPLIER_MIN and ctx.pain_annual_cost > 0:
            recommended = ctx.pain_annual_cost / self.ROI_MULTIPLIER_TARGET

        recommended = max(recommended, self.ABSOLUTE_FLOOR)
        recommended = round(recommended, -1)  # Arrondir a la dizaine

        # Snap to standard tiers
        recommended = self._snap_to_tier(recommended)
        floor = max(self.ABSOLUTE_FLOOR, recommended * 0.7)
        roi_final = ctx.pain_annual_cost / recommended if recommended > 0 else 0

        # Payment options
        payment_opts = self._generate_payment_options(recommended)

        # Confidence
        confidence = min(1.0, 0.5 + (0.1 if ctx.pain_annual_cost > 0 else 0) +
                        (0.1 if ctx.prospect_revenue > 0 else 0) +
                        (0.15 if ctx.urgency > 0.5 else 0) +
                        (0.15 if ctx.market_rarity > 0.3 else 0))

        result = PricingResult(
            recommended_price=recommended,
            floor_price=floor,
            ceiling_price=ceiling,
            roi_for_prospect=round(roi_final, 1),
            confidence=round(confidence, 2),
            pricing_model="roi_based_dynamic",
            breakdown={
                "base": round(base_price, 2),
                "urgency_mult": urgency_mult,
                "rarity_mult": round(rarity_mult, 2),
                "sector_mult": sector_mult,
                "competition_adj": competition_adj
            },
            payment_options=payment_opts
        )

        with self._lock:
            self._total_priced += 1
            self._total_value += recommended
            self._pricing_history.append({
                "price": recommended, "sector": ctx.sector,
                "roi": roi_final, "ts": time.time()
            })
            if len(self._pricing_history) > 1000:
                self._pricing_history = self._pricing_history[-500:]

        return result

    def _snap_to_tier(self, price: float) -> float:
        """Snap le prix au palier standard le plus proche."""
        TIERS = [1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000,
                 25000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000,
                 150000, 200000, 300000, 500000]
        for t in TIERS:
            if price <= t * 1.15:
                return float(t)
        return round(price, -3)

    def _generate_payment_options(self, price: float) -> List[Dict]:
        """Genere les options de paiement."""
        options = [{"type": "full", "amount": price, "description": "Paiement integral"}]
        if price >= 5000:
            options.append({
                "type": "split_2", "amount": price / 2,
                "description": f"2x {price/2:.0f}EUR (50% maintenant, 50% a livraison)"
            })
        if price >= 10000:
            options.append({
                "type": "split_3", "amount": price / 3,
                "description": f"3x {price/3:.0f}EUR (mensuel)"
            })
        if price >= 20000:
            options.append({
                "type": "milestone", "amount": price * 0.3,
                "description": f"Par jalons: 30% / 40% / 30%"
            })
        return options

    def record_conversion(self, sector: str, converted: bool) -> None:
        """Enregistre si un prix propose a ete accepte ou refuse."""
        with self._lock:
            if sector not in self._conversion_rates:
                self._conversion_rates[sector] = []
            self._conversion_rates[sector].append(converted)
            if len(self._conversion_rates[sector]) > 100:
                self._conversion_rates[sector] = self._conversion_rates[sector][-50:]

    def get_sector_conversion_rate(self, sector: str) -> float:
        with self._lock:
            history = self._conversion_rates.get(sector, [])
            if not history:
                return 0.5
            return sum(history) / len(history)

    def get_stats(self) -> Dict:
        with self._lock:
            avg = self._total_value / self._total_priced if self._total_priced > 0 else 0
            return {
                "total_priced": self._total_priced,
                "total_value": self._total_value,
                "average_price": round(avg, 2),
                "floor": self.ABSOLUTE_FLOOR,
                "conversion_rates": {
                    s: round(sum(h)/len(h), 2) if h else 0
                    for s, h in self._conversion_rates.items()
                }
            }

_engine = None
_engine_lock = threading.Lock()
def get_dynamic_pricing() -> DynamicPricingEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = DynamicPricingEngine()
    return _engine
