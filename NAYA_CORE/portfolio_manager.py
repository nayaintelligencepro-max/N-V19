"""
NAYA V19 — Portfolio Manager
Gère les 6 projets business et génère des rapports de revenus.
Connecte PROJECT_01-P6 avec les vraies données.
"""
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("NAYA.PORTFOLIO")


class PortfolioManager:
    """Gestionnaire des 6 projets business NAYA."""

    PROJECTS = {
        "P01_CASH_RAPIDE": {
            "name": "Cash Rapide B2B",
            "levels": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "target_monthly": 150000,
            "active": True,
        },
        "P03_BOTANICA": {
            "name": "NAYA Botanica (Shopify)",
            "target_monthly": 30000,
            "active": True,
            "shopify": True,
        },
        "P04_TINY_HOUSE": {
            "name": "Tiny House Solutions",
            "target_monthly": 80000,
            "active": True,
        },
        "P05_MARCHES_OUBLIES": {
            "name": "Marchés Oubliés — Diaspora",
            "target_monthly": 50000,
            "active": True,
            "multilang": True,
        },
        "P06_IMMOBILIER": {
            "name": "Acquisition Immobilière",
            "target_monthly": 40000,
            "active": True,
        },
    }

    def __init__(self):
        self._pipeline_cache = {}
        self._last_report: Optional[Dict] = None

    def generate_report(self) -> Dict:
        """Génère un rapport complet de tous les projets."""
        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            pt = PipelineTracker()
            kpis = pt.get_kpis()
            pipeline_total = kpis.get("pipeline_eur", 0)
            won_total = kpis.get("revenue_won_eur", 0)
        except Exception:
            pipeline_total = 0
            won_total = 0

        # Stats Shopify Botanica
        shopify_revenue = 0
        try:
            from NAYA_CORE.integrations.shopify_integration import ShopifyIntegration
            sh = ShopifyIntegration()
            if sh.available:
                orders = sh.get_orders(10)
                shopify_revenue = sum(
                    float(o.get("total_price", 0))
                    for o in orders.get("orders", [])
                )
        except Exception:
            pass

        # Stats marchés oubliés
        forgotten_prospects = 0
        try:
            from NAYA_REVENUE_ENGINE.unified_revenue_engine import ForgottenMarketsEngine
            fm = ForgottenMarketsEngine()
            stats = fm.get_market_stats()
            forgotten_prospects = stats.get("prospects_generated", 0)
        except Exception:
            pass

        summary = {
            "pipeline_total_eur": pipeline_total,
            "won_total_eur": won_total,
            "shopify_revenue_eur": shopify_revenue,
            "forgotten_prospects": forgotten_prospects,
            "projects_active": len([p for p in self.PROJECTS.values() if p.get("active")]),
            "total_target_monthly": sum(p.get("target_monthly", 0) for p in self.PROJECTS.values()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._last_report = {
            "summary": summary,
            "projects": self.PROJECTS,
        }

        log.info(
            f"[PORTFOLIO] Pipeline: {pipeline_total:,.0f}€ | "
            f"Won: {won_total:,.0f}€ | "
            f"Shopify: {shopify_revenue:,.0f}€"
        )

        # Notification Telegram si revenus significatifs
        if won_total > 0 or shopify_revenue > 0:
            try:
                from NAYA_CORE.money_notifier import get_money_notifier
                mn = get_money_notifier()
                if mn.available:
                    mn._send(
                        f"📊 <b>RAPPORT PORTFOLIO</b>\n\n"
                        f"💰 Pipeline: <b>{pipeline_total:,.0f}€</b>\n"
                        f"✅ Gagné: <b>{won_total:,.0f}€</b>\n"
                        f"🛒 Shopify: <b>{shopify_revenue:,.0f}€</b>\n"
                        f"🌍 Prospects marchés oubliés: {forgotten_prospects}"
                    )
            except Exception:
                pass

        return self._last_report or {"summary": summary}

    def get_project(self, project_id: str) -> Optional[Dict]:
        return self.PROJECTS.get(project_id)

    def get_active_projects(self) -> List[Dict]:
        return [
            {"id": k, **v}
            for k, v in self.PROJECTS.items()
            if v.get("active")
        ]


_PM: Optional[PortfolioManager] = None
_PM_LOCK = __import__("threading").Lock()

def get_portfolio_manager() -> PortfolioManager:
    global _PM
    if _PM is None:
        with _PM_LOCK:
            if _PM is None:
                _PM = PortfolioManager()
    return _PM
