"""
NAYA — Strategic Pricing Engine
Prix basé sur la VALEUR et la DOULEUR — jamais sur le coût.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum

class PriceAnchor(Enum):
    PAIN_VALUE = "pain_value"        # % de la douleur évitée
    MARKET_RATE = "market_rate"      # Référence marché x premium
    ROI_BASED = "roi_based"          # Valeur ROI générée

class ServiceType(Enum):
    DIAGNOSTIC = "diagnostic"
    AUDIT = "audit"
    CONSULTING = "consulting"
    IMPLEMENTATION = "implementation"
    TRAINING = "training"
    RETAINER = "retainer"
    CHATBOT = "chatbot"

@dataclass
class PricePoint:
    floor: float; recommended: float; ceiling: float
    anchor: PriceAnchor; rationale: str

    def premium_round(self, price: float) -> float:
        if price < 2000: return round(price/500)*500
        if price < 10000: return round(price/1000)*1000
        if price < 50000: return round(price/5000)*5000
        return round(price/10000)*10000

class StrategicPricingEngine:
    """Calcule le prix optimal basé sur valeur créée."""

    FLOOR = 1000
    BASE_RATES = {
        ServiceType.DIAGNOSTIC: (1500, 5000),
        ServiceType.AUDIT: (3000, 15000),
        ServiceType.CONSULTING: (2000, 25000),
        ServiceType.IMPLEMENTATION: (5000, 50000),
        ServiceType.TRAINING: (1500, 8000),
        ServiceType.RETAINER: (1500, 8000),
        ServiceType.CHATBOT: (8000, 80000),
    }

    def calculate_price(self, impact_value: float, client_capacity: float,
                        service_type: str = "consulting",
                        urgency: float = 0.5) -> float:
        stype = ServiceType(service_type) if isinstance(service_type, str) else service_type
        floor, ceiling = self.BASE_RATES.get(stype, (2000, 20000))
        pain_price = impact_value * 0.15  # 15% de la douleur évitée
        capacity_price = client_capacity * 0.20
        base = (pain_price + capacity_price) / 2
        urgency_premium = base * urgency * 0.3
        price = base + urgency_premium
        return max(self.FLOOR, min(ceiling, self._round_premium(price)))

    def build_offer(self, pain_monthly: float, timeline: str = "72H") -> Dict:
        urgency = {"24H": 0.9, "48H": 0.7, "72H": 0.5}.get(timeline, 0.5)
        price = self.calculate_price(pain_monthly*12, pain_monthly*3, urgency=urgency)
        anchor = price * 1.4
        retainer = self._round_premium(price * 0.15)
        return {
            "price": price, "anchor": anchor, "retainer": retainer,
            "timeline": timeline, "roi_multiple": round(pain_monthly*3/price, 1)
        }

    def _round_premium(self, p: float) -> float:
        if p < 2000: return round(p/500)*500
        if p < 10000: return round(p/1000)*1000
        if p < 50000: return round(p/5000)*5000
        return round(p/10000)*10000
