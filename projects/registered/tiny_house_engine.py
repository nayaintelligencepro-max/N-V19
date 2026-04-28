"""
TINY HOUSE ENGINE — Maisons Modulaires Tropicales
═══════════════════════════════════════════════════════════════
Business model : Maisons modulaires adaptées climat tropical Polynésie.
Revenue model : Commission 8-12% sur ventes + services architecture.
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

log = logging.getLogger("NAYA.TINY_HOUSE")


@dataclass
class TinyHouseModel:
    """Modèle de Tiny House."""
    model_id: str
    name: str
    description: str
    surface_m2: float
    price_eur: float
    commission_pct: float
    features: List[str]
    climate_rating: str  # tropical_premium | tropical_standard | universal
    delivery_days: int


class TinyHouseEngine:
    """
    Moteur NAYA TINY HOUSE.

    Pipeline :
    1. Design maisons modulaires tropicales
    2. Partenariats constructeurs locaux
    3. Marketing digital + showroom virtuel
    4. Ventes + services architecture personnalisée
    5. Commission + services additionnels
    """

    def __init__(self):
        self.models: List[TinyHouseModel] = []
        self._init_models()
        log.info("✅ TinyHouseEngine initialized - %d models", len(self.models))

    def _init_models(self) -> None:
        """Initialise les modèles de Tiny Houses."""
        self.models = [
            TinyHouseModel(
                model_id="TH001",
                name="Moana Compact",
                description="Studio tropical 20m² avec terrasse. Parfait pour bureau ou guest house.",
                surface_m2=20.0,
                price_eur=35000,
                commission_pct=10.0,
                features=[
                    "Isolation tropicale renforcée",
                    "Ventilation naturelle optimisée",
                    "Terrasse bois exotique 8m²",
                    "Toiture anti-cyclonique",
                    "Installation électrique autonome ready"
                ],
                climate_rating="tropical_premium",
                delivery_days=45
            ),
            TinyHouseModel(
                model_id="TH002",
                name="Fenua Confort",
                description="T2 tropical 35m² avec cuisine et SDB complètes.",
                surface_m2=35.0,
                price_eur=55000,
                commission_pct=10.0,
                features=[
                    "2 pièces + cuisine + SDB",
                    "Climatisation naturelle passive",
                    "Terrasse couverte 12m²",
                    "Toiture végétalisée option",
                    "Récupération eau de pluie"
                ],
                climate_rating="tropical_premium",
                delivery_days=60
            ),
            TinyHouseModel(
                model_id="TH003",
                name="Tiki Premium",
                description="T3 tropical 50m² haut standing avec véranda.",
                surface_m2=50.0,
                price_eur=85000,
                commission_pct=12.0,
                features=[
                    "3 pièces + cuisine équipée + 2 SDB",
                    "Véranda 15m² vue panoramique",
                    "Climatisation hybride",
                    "Panneaux solaires intégrés",
                    "Design architecte personnalisé"
                ],
                climate_rating="tropical_premium",
                delivery_days=90
            ),
            TinyHouseModel(
                model_id="TH004",
                name="Bungalow Plage",
                description="Bungalow 60m² front de mer avec deck.",
                surface_m2=60.0,
                price_eur=120000,
                commission_pct=12.0,
                features=[
                    "4 pièces + 2 SDB + cuisine pro",
                    "Deck bois exotique 25m²",
                    "Protection anti-corrosion marine",
                    "100% autonome (eau + électricité)",
                    "Jacuzzi extérieur option"
                ],
                climate_rating="tropical_premium",
                delivery_days=120
            ),
        ]

    def get_models(self) -> List[Dict[str, Any]]:
        """Retourne les modèles disponibles."""
        return [
            {
                "model_id": m.model_id,
                "name": m.name,
                "description": m.description,
                "surface_m2": m.surface_m2,
                "price_eur": m.price_eur,
                "commission_eur": m.price_eur * (m.commission_pct / 100),
                "features": m.features,
                "climate_rating": m.climate_rating,
                "delivery_days": m.delivery_days,
            }
            for m in self.models
        ]

    def calculate_revenue_projection(self, sales_per_year: int) -> Dict[str, float]:
        """Calcule la projection de revenus."""
        avg_price = sum(m.price_eur for m in self.models) / len(self.models)
        avg_commission_pct = sum(m.commission_pct for m in self.models) / len(self.models)

        yearly_revenue = sales_per_year * avg_price
        yearly_commission = yearly_revenue * (avg_commission_pct / 100)

        return {
            "sales_per_year": sales_per_year,
            "avg_price_eur": avg_price,
            "avg_commission_pct": avg_commission_pct,
            "yearly_revenue_eur": yearly_revenue,
            "yearly_commission_eur": yearly_commission,
            "monthly_commission_eur": yearly_commission / 12,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques TINY HOUSE."""
        return {
            "total_models": len(self.models),
            "avg_price_eur": sum(m.price_eur for m in self.models) / len(self.models),
            "avg_commission_pct": sum(m.commission_pct for m in self.models) / len(self.models),
            "total_surface_m2": sum(m.surface_m2 for m in self.models),
            "price_range_eur": {
                "min": min(m.price_eur for m in self.models),
                "max": max(m.price_eur for m in self.models),
            },
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine = None


def get_tiny_house_engine():
    """Retourne l'instance singleton de TinyHouseEngine."""
    global _engine
    if _engine is None:
        _engine = TinyHouseEngine()
    return _engine
