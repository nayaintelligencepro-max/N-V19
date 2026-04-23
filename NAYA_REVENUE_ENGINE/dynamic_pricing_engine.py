"""
NAYA V19 — Dynamic Pricing Engine (B1)
Calcule le prix optimal en temps réel basé sur:
- Capacité de paiement du prospect
- Urgence de la douleur
- Rareté de la solution
- ROI réel pour le client
"""
import time, logging, math
from typing import Dict, Optional
log = logging.getLogger("NAYA.PRICING")

class DynamicPricingEngine:
    """Prix dynamique — s adapte au ROI réel du client."""
    
    PREMIUM_FLOOR = 1000  # Jamais en dessous
    TIERS = {
        "premium": {"min": 1000, "max": 10000, "default": 5000},
        "premium_plus": {"min": 10000, "max": 30000, "default": 20000},
        "executive": {"min": 30000, "max": 60000, "default": 40000},
        "enterprise": {"min": 60000, "max": 100000, "default": 80000},
        "strategic": {"min": 100000, "max": 500000, "default": 200000},
        "high_stakes": {"min": 500000, "max": 15000000, "default": 1000000},
    }
    
    def __init__(self):
        self._pricing_history: list = []
        self._total_priced = 0
    
    def calculate_price(self, context: Dict) -> Dict:
        """Calcule le prix optimal pour une opportunité."""
        self._total_priced += 1
        
        pain_cost = context.get("annual_pain_cost", 0)
        budget = context.get("client_budget", 0)
        urgency = context.get("urgency", 0.5)  # 0-1
        rarity = context.get("solution_rarity", 0.5)  # 0-1
        competition = context.get("competitors", 3)
        company_size = context.get("employees", 10)
        
        # Base price = 10-30% of the annual pain cost (ROI justifiable)
        if pain_cost > 0:
            roi_factor = 0.15 + (urgency * 0.15)  # 15-30% du coût annuel
            base = pain_cost * roi_factor
        elif budget > 0:
            base = budget * 0.7  # 70% du budget déclaré
        else:
            base = 5000  # Défaut premium
        
        # Ajustements
        urgency_multiplier = 1 + (urgency * 0.5)  # +0 à +50%
        rarity_multiplier = 1 + (rarity * 0.3)  # +0 à +30%
        competition_factor = max(0.8, 1 - (competition * 0.05))  # -5% par concurrent
        size_factor = 1 + (math.log10(max(company_size, 1)) * 0.1)  # +log scaling
        
        optimal = base * urgency_multiplier * rarity_multiplier * competition_factor * size_factor
        
        # Appliquer le plancher premium
        optimal = max(optimal, self.PREMIUM_FLOOR)
        
        # Déterminer le tier
        tier = "premium"
        for tier_name, bounds in self.TIERS.items():
            if bounds["min"] <= optimal <= bounds["max"]:
                tier = tier_name
                break
        if optimal > 500000:
            tier = "high_stakes"
        
        result = {
            "optimal_price_eur": round(optimal, 2),
            "tier": tier,
            "base_price": round(base, 2),
            "multipliers": {
                "urgency": round(urgency_multiplier, 2),
                "rarity": round(rarity_multiplier, 2),
                "competition": round(competition_factor, 2),
                "company_size": round(size_factor, 2),
            },
            "roi_for_client": round(pain_cost / max(optimal, 1), 1) if pain_cost > 0 else None,
            "recommended_range": {
                "min": round(optimal * 0.85, 2),
                "max": round(optimal * 1.25, 2),
            },
        }
        
        self._pricing_history.append({**result, "ts": time.time()})
        if len(self._pricing_history) > 500:
            self._pricing_history = self._pricing_history[-500:]
        
        return result
    
    def get_stats(self) -> Dict:
        return {
            "total_priced": self._total_priced,
            "avg_price": round(sum(p["optimal_price_eur"] for p in self._pricing_history) / max(len(self._pricing_history), 1), 2),
            "tier_distribution": self._tier_dist(),
        }
    
    def _tier_dist(self) -> Dict:
        dist = {}
        for p in self._pricing_history:
            t = p.get("tier", "unknown")
            dist[t] = dist.get(t, 0) + 1
        return dist
