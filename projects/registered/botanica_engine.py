"""
NAYA BOTANICA — E-Commerce Cosmétiques Naturels Polynésie
═══════════════════════════════════════════════════════════════
Business model : E-commerce cosmétiques naturels bio Polynésie française.
Revenue model : Marge 40-60% sur produits + abonnement découverte mensuel.
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

log = logging.getLogger("NAYA.BOTANICA")


@dataclass
class BotanicaProduct:
    """Produit cosmétique naturel."""
    product_id: str
    name: str
    description: str
    category: str  # soin_visage | soin_corps | huiles_essentielles | savons
    price_eur: float
    cost_eur: float
    margin_pct: float
    stock: int
    ingredients: List[str]
    origin: str  # polynesian | tropical | organic


class BotanicaEngine:
    """
    Moteur e-commerce NAYA BOTANICA.

    Pipeline :
    1. Sourcing produits naturels Polynésie
    2. Site e-commerce Shopify/WooCommerce
    3. Marketing Instagram/TikTok/Pinterest
    4. Ventes + abonnements découverte
    5. Livraison Polynésie + international
    """

    def __init__(self):
        self.catalogue: List[BotanicaProduct] = []
        self._init_catalogue()
        log.info("✅ BotanicaEngine initialized - %d products", len(self.catalogue))

    def _init_catalogue(self) -> None:
        """Initialise le catalogue produits."""
        self.catalogue = [
            BotanicaProduct(
                product_id="BOT001",
                name="Huile de Monoï Authentique",
                description="Huile de coco macérée aux fleurs de Tiaré. 100% naturelle.",
                category="huiles_essentielles",
                price_eur=24.90,
                cost_eur=12.00,
                margin_pct=51.8,
                stock=50,
                ingredients=["Huile de coco", "Fleurs de Tiaré"],
                origin="polynesian"
            ),
            BotanicaProduct(
                product_id="BOT002",
                name="Savon Tamanu Bio",
                description="Savon artisanal à l'huile de Tamanu. Cicatrisant naturel.",
                category="savons",
                price_eur=14.90,
                cost_eur=6.50,
                margin_pct=56.4,
                stock=100,
                ingredients=["Huile de Tamanu", "Beurre de coco", "Argile volcanique"],
                origin="polynesian"
            ),
            BotanicaProduct(
                product_id="BOT003",
                name="Crème Visage Aloe Tropical",
                description="Crème hydratante à l'aloe vera tropical. Anti-âge naturel.",
                category="soin_visage",
                price_eur=34.90,
                cost_eur=15.00,
                margin_pct=57.0,
                stock=30,
                ingredients=["Aloe vera", "Huile de coco", "Vitamine E naturelle"],
                origin="tropical"
            ),
            BotanicaProduct(
                product_id="BOT004",
                name="Pack Découverte Polynésie",
                description="Coffret 3 produits : Monoï + Savon Tamanu + Mini Crème",
                category="pack",
                price_eur=59.90,
                cost_eur=25.00,
                margin_pct=58.3,
                stock=20,
                ingredients=["Pack découverte"],
                origin="polynesian"
            ),
        ]

    def get_catalogue(self) -> List[Dict[str, Any]]:
        """Retourne le catalogue."""
        return [
            {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "price_eur": p.price_eur,
                "margin_pct": p.margin_pct,
                "stock": p.stock,
                "origin": p.origin,
            }
            for p in self.catalogue
        ]

    def calculate_revenue_projection(self, sales_per_month: int) -> Dict[str, float]:
        """Calcule la projection de revenus."""
        avg_price = sum(p.price_eur for p in self.catalogue) / len(self.catalogue)
        avg_margin = sum(p.margin_pct for p in self.catalogue) / len(self.catalogue)

        monthly_revenue = sales_per_month * avg_price
        monthly_profit = monthly_revenue * (avg_margin / 100)

        return {
            "sales_per_month": sales_per_month,
            "avg_price_eur": avg_price,
            "monthly_revenue_eur": monthly_revenue,
            "monthly_profit_eur": monthly_profit,
            "yearly_revenue_eur": monthly_revenue * 12,
            "yearly_profit_eur": monthly_profit * 12,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques BOTANICA."""
        return {
            "total_products": len(self.catalogue),
            "total_stock_value_eur": sum(p.price_eur * p.stock for p in self.catalogue),
            "average_margin_pct": sum(p.margin_pct for p in self.catalogue) / len(self.catalogue),
            "categories": list(set(p.category for p in self.catalogue)),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine = None


def get_botanica_engine():
    """Retourne l'instance singleton de BotanicaEngine."""
    global _engine
    if _engine is None:
        _engine = BotanicaEngine()
    return _engine
