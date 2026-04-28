"""NAYA V19 — Strategic Domain Router"""
import logging
from typing import Dict, List, Optional, Tuple
log = logging.getLogger("NAYA.DECISION.ROUTER")

class StrategicDomainRouter:
    """Route les opportunités vers le bon moteur de revenus selon le domaine."""
    
    DOMAIN_MAP = {
        "cash_rapide": {
            "keywords": ["audit", "diagnostic", "chatbot", "ia", "saas", "consulting", "quick"],
            "engine": "CASH_RAPIDE", "priority": 1,
        },
        "mega_project": {
            "keywords": ["infrastructure", "google", "microsoft", "million", "enterprise", "platform"],
            "engine": "MEGA_PROJECT", "priority": 2,
        },
        "ecommerce": {
            "keywords": ["shop", "product", "cosmetic", "botanica", "ecommerce", "retail"],
            "engine": "ECOMMERCE", "priority": 3,
        },
        "marches_oublies": {
            "keywords": ["forgotten", "underserved", "island", "remote", "niche", "untapped"],
            "engine": "MARCHES_OUBLIES", "priority": 4,
        },
        "immobilier": {
            "keywords": ["property", "terrain", "house", "rent", "renovate", "real_estate"],
            "engine": "ACQUISITION_IMMOBILIERE", "priority": 5,
        },
        "fintech": {
            "keywords": ["bank", "payment", "transfer", "fintech", "naya_paye"],
            "engine": "NAYA_PAYE", "priority": 6,
        },
    }
    
    def __init__(self):
        self._routing_history: List[Dict] = []
    
    def route(self, opportunity: Dict) -> Dict:
        """Route une opportunité vers le bon domaine/engine."""
        text = " ".join([
            str(opportunity.get("sector", "")),
            str(opportunity.get("description", "")),
            str(opportunity.get("pain_category", "")),
            str(opportunity.get("title", "")),
        ]).lower()
        
        scores: List[Tuple[str, float]] = []
        for domain, config in self.DOMAIN_MAP.items():
            score = sum(1 for kw in config["keywords"] if kw in text)
            if score > 0:
                scores.append((domain, score))
        
        if not scores:
            # Défaut: cash rapide (le plus rapide à exécuter)
            best_domain = "cash_rapide"
        else:
            scores.sort(key=lambda x: x[1], reverse=True)
            best_domain = scores[0][0]
        
        engine = self.DOMAIN_MAP[best_domain]["engine"]
        priority = self.DOMAIN_MAP[best_domain]["priority"]
        
        result = {
            "domain": best_domain, "engine": engine, "priority": priority,
            "confidence": scores[0][1] / max(len(self.DOMAIN_MAP[best_domain]["keywords"]), 1) if scores else 0.5,
            "all_matches": [(d, s) for d, s in scores[:3]] if scores else [],
        }
        
        self._routing_history.append({"opportunity": opportunity.get("id"), **result})
        if len(self._routing_history) > 500:
            self._routing_history = self._routing_history[-500:]
        
        return result
    
    def get_distribution(self) -> Dict:
        dist = {}
        for r in self._routing_history:
            d = r.get("domain", "unknown")
            dist[d] = dist.get(d, 0) + 1
        return dist
    
    def get_stats(self) -> Dict:
        return {
            "total_routed": len(self._routing_history),
            "distribution": self.get_distribution(),
            "domains_available": list(self.DOMAIN_MAP.keys()),
        }
