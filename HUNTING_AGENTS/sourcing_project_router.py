"""
NAYA V19 - Sourcing Project Router
Connecte le sourcing agent aux projets specifiques.
Botanica -> fournisseurs cosmetiques. Tiny House -> fabricants modulaires.
"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SOURCING.ROUTER")

class SourcingProjectRouter:
    """Route les besoins de sourcing vers les bons fournisseurs par projet."""

    PROJECT_SOURCING_PROFILES = {
        "PROJECT_03_NAYA_BOTANICA": {
            "categories": ["cosmetics", "packaging", "raw_ingredients"],
            "keywords": {
                "cosmetics": ["organic skincare", "curcuma extract", "skin lightening cream",
                              "weight loss body cream", "natural cosmetics wholesale"],
                "packaging": ["cosmetic bottles", "eco packaging beauty", "luxury cosmetic packaging"],
                "raw_ingredients": ["curcuma powder bulk", "shea butter wholesale",
                                    "coconut oil organic bulk", "aloe vera extract"]
            },
            "requirements": {
                "min_order_samples": True,
                "certifications": ["ISO 22716", "GMP", "organic"],
                "shipping_to": "your_region",
                "request_samples_first": True
            },
            "gammes": [
                {"name": "Perte de poids", "ingredients": ["guarana", "cafe vert", "the vert", "gingembre"]},
                {"name": "Eclaircissant reparateur", "ingredients": ["curcuma", "vitamine C", "niacinamide", "arbutine"]},
                {"name": "Parfums miniatures", "type": "mainstream_niche", "format": "miniature 10-30ml"}
            ]
        },
        "PROJECT_04_TINY_HOUSE": {
            "categories": ["prefab_houses", "solar_panels", "furniture"],
            "keywords": {
                "prefab_houses": ["foldable house 20sqm", "modular tiny house", "prefab container house",
                                  "portable house foldable", "expandable container house"],
                "solar_panels": ["solar panel kit off grid", "renewable energy kit house"],
                "furniture": ["compact furniture tiny house", "foldable furniture space saving"]
            },
            "requirements": {
                "min_order_samples": True,
                "certifications": ["CE", "wind_resistant"],
                "shipping_to": "your_region",
                "special": "Typhoon/cyclone resistant, tropical climate",
                "first_2_units_personal": True,
                "config_unit_1": "1 cuisine salon americain, 1 wc douche, 1 chambre parentale avec douche wc, 1 chambre",
                "config_unit_2": "Meme caracteristiques, configuration differente"
            }
        },
        "PROJECT_05_MARCHES_OUBLIES": {
            "categories": ["general_merchandise", "services"],
            "keywords": {
                "general_merchandise": ["underserved market products", "island market supplies"],
                "services": ["remote service delivery", "digital service platform"]
            },
            "requirements": {"shipping_to": "your_region", "adaptable": True}
        },
        "PROJECT_07_NAYA_PAYE": {
            "categories": ["fintech_infrastructure", "payment_hardware"],
            "keywords": {
                "fintech_infrastructure": ["payment gateway API", "KYC solution", "banking as a service"],
                "payment_hardware": ["POS terminal", "card reader mobile", "NFC payment terminal"]
            },
            "requirements": {"regulatory": "IEOM/ACPR compliance needed"}
        }
    }

    def __init__(self):
        self._sourcing_requests: List[Dict] = []
        self._total_routed = 0

    def get_sourcing_profile(self, project_id: str) -> Optional[Dict]:
        return self.PROJECT_SOURCING_PROFILES.get(project_id)

    def create_sourcing_request(self, project_id: str, category: str = None) -> List[Dict]:
        """Cree des requetes de sourcing pour un projet."""
        profile = self.PROJECT_SOURCING_PROFILES.get(project_id)
        if not profile:
            return []

        requests = []
        categories = [category] if category else profile.get("categories", [])

        for cat in categories:
            keywords = profile.get("keywords", {}).get(cat, [])
            req = {
                "project_id": project_id,
                "category": cat,
                "keywords": keywords,
                "requirements": profile.get("requirements", {}),
                "created_at": time.time(),
                "status": "pending"
            }
            requests.append(req)
            self._sourcing_requests.append(req)
            self._total_routed += 1

        log.info(f"[SOURCING-ROUTER] {len(requests)} requetes pour {project_id}/{category or 'all'}")
        return requests

    def get_botanica_gammes(self) -> List[Dict]:
        """Retourne les gammes produits Botanica pour sourcing cible."""
        profile = self.PROJECT_SOURCING_PROFILES.get("PROJECT_03_NAYA_BOTANICA", {})
        return profile.get("gammes", [])

    def get_tiny_house_config(self) -> Dict:
        """Retourne la config des 2 tiny houses personnelles."""
        profile = self.PROJECT_SOURCING_PROFILES.get("PROJECT_04_TINY_HOUSE", {})
        reqs = profile.get("requirements", {})
        return {
            "personal_units": 2,
            "unit_1": reqs.get("config_unit_1", ""),
            "unit_2": reqs.get("config_unit_2", ""),
            "special_requirements": reqs.get("special", ""),
            "first_2_at_cost": True
        }

    def get_pending_requests(self, project_id: str = None) -> List[Dict]:
        if project_id:
            return [r for r in self._sourcing_requests
                    if r["project_id"] == project_id and r["status"] == "pending"]
        return [r for r in self._sourcing_requests if r["status"] == "pending"]

    def mark_completed(self, idx: int) -> None:
        if 0 <= idx < len(self._sourcing_requests):
            self._sourcing_requests[idx]["status"] = "completed"

    def get_stats(self) -> Dict:
        return {
            "total_routed": self._total_routed,
            "pending": sum(1 for r in self._sourcing_requests if r["status"] == "pending"),
            "projects_with_profiles": list(self.PROJECT_SOURCING_PROFILES.keys())
        }

_router = None
def get_sourcing_router():
    global _router
    if _router is None:
        _router = SourcingProjectRouter()
    return _router
