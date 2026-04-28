"""
NAYA V19 - Geographic Cloner
Quand un service fonctionne quelque part, identifie automatiquement les marches
similaires et adapte l offre. Un succes local devient un template mondial.
"""
import time, logging, copy
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.GEO.CLONE")

@dataclass
class MarketProfile:
    geography: str
    population: int
    gdp_per_capita: float
    digital_maturity: float  # 0-1
    language: str
    currency: str
    regulatory_complexity: float  # 0-1
    market_size_eur: float
    similar_to: List[str] = field(default_factory=list)

@dataclass
class ClonedOffer:
    original_geography: str
    target_geography: str
    adapted_offer: Dict[str, Any]
    estimated_market_size: float
    adaptation_score: float
    cloned_at: float = field(default_factory=time.time)

class GeographicCloner:
    """Clone et adapte les offres qui marchent vers des marches geographiques similaires."""

    MARKET_DB = {
        "polynesie_francaise": MarketProfile("polynesie_francaise", 280000, 18000, 0.5, "fr", "XPF", 0.6, 500000000, ["nouvelle_caledonie", "wallis_futuna", "reunion", "guadeloupe"]),
        "nouvelle_caledonie": MarketProfile("nouvelle_caledonie", 290000, 20000, 0.55, "fr", "XPF", 0.6, 600000000, ["polynesie_francaise", "reunion"]),
        "reunion": MarketProfile("reunion", 900000, 15000, 0.6, "fr", "EUR", 0.5, 1500000000, ["guadeloupe", "martinique", "mayotte"]),
        "guadeloupe": MarketProfile("guadeloupe", 400000, 14000, 0.55, "fr", "EUR", 0.5, 800000000, ["martinique", "reunion", "guyane"]),
        "martinique": MarketProfile("martinique", 375000, 15000, 0.55, "fr", "EUR", 0.5, 750000000, ["guadeloupe", "reunion"]),
        "fiji": MarketProfile("fiji", 900000, 5000, 0.35, "en", "FJD", 0.4, 500000000, ["samoa", "tonga", "vanuatu"]),
        "maurice": MarketProfile("maurice", 1300000, 9000, 0.6, "fr", "MUR", 0.5, 1200000000, ["reunion", "madagascar"]),
        "france": MarketProfile("france", 67000000, 35000, 0.85, "fr", "EUR", 0.7, 2500000000000, ["belgique", "suisse", "luxembourg"]),
    }

    def __init__(self):
        self._cloned: List[ClonedOffer] = []
        self._success_map: Dict[str, List[str]] = {}  # geo -> [offer_types reussis]

    def record_success(self, geography: str, offer_type: str) -> None:
        if geography not in self._success_map:
            self._success_map[geography] = []
        self._success_map[geography].append(offer_type)

    def find_clone_targets(self, source_geography: str) -> List[Dict]:
        """Trouve les marches similaires ou cloner une offre reussie."""
        source = self.MARKET_DB.get(source_geography)
        if not source:
            return []

        targets = []
        for geo, profile in self.MARKET_DB.items():
            if geo == source_geography:
                continue
            similarity = self._compute_similarity(source, profile)
            if similarity >= 0.4:
                targets.append({
                    "geography": geo,
                    "similarity": round(similarity, 2),
                    "population": profile.population,
                    "market_size_eur": profile.market_size_eur,
                    "language": profile.language,
                    "currency": profile.currency,
                    "priority": "high" if geo in source.similar_to else "medium"
                })
        targets.sort(key=lambda t: t["similarity"], reverse=True)
        return targets

    def clone_offer(self, offer: Dict, source_geo: str, target_geo: str) -> ClonedOffer:
        """Clone et adapte une offre pour un nouveau marche."""
        source_profile = self.MARKET_DB.get(source_geo)
        target_profile = self.MARKET_DB.get(target_geo)

        adapted = copy.deepcopy(offer)
        if target_profile:
            # Adapter prix au pouvoir d achat
            if source_profile and source_profile.gdp_per_capita > 0:
                ratio = target_profile.gdp_per_capita / source_profile.gdp_per_capita
                if "price" in adapted:
                    adapted["price"] = max(1000, round(adapted["price"] * ratio, -1))
            adapted["currency"] = target_profile.currency
            adapted["language"] = target_profile.language
            adapted["geography"] = target_geo

        similarity = self._compute_similarity(source_profile, target_profile) if source_profile and target_profile else 0.5

        cloned = ClonedOffer(
            original_geography=source_geo,
            target_geography=target_geo,
            adapted_offer=adapted,
            estimated_market_size=target_profile.market_size_eur if target_profile else 0,
            adaptation_score=similarity
        )
        self._cloned.append(cloned)
        log.info(f"[GEO-CLONE] {source_geo} -> {target_geo} (sim={similarity:.2f})")
        return cloned

    def _compute_similarity(self, a: MarketProfile, b: MarketProfile) -> float:
        score = 0.0
        if a.language == b.language:
            score += 0.3
        if a.currency == b.currency:
            score += 0.1
        gdp_ratio = min(a.gdp_per_capita, b.gdp_per_capita) / max(a.gdp_per_capita, b.gdp_per_capita)
        score += gdp_ratio * 0.2
        digital_diff = 1.0 - abs(a.digital_maturity - b.digital_maturity)
        score += digital_diff * 0.2
        if b.geography in a.similar_to:
            score += 0.2
        return min(1.0, score)

    def get_stats(self) -> Dict:
        return {
            "total_cloned": len(self._cloned),
            "success_map": {g: len(offers) for g, offers in self._success_map.items()},
            "markets_known": len(self.MARKET_DB)
        }

_cloner = None
def get_geographic_cloner() -> GeographicCloner:
    global _cloner
    if _cloner is None:
        _cloner = GeographicCloner()
    return _cloner
