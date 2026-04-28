"""
NAYA — Shopify Integration (Projet Botanica)
Gestion des produits, commandes, stratégie e-commerce.
Requiert: SHOPIFY_SHOP_URL + SHOPIFY_ACCESS_TOKEN dans .env
"""
import os
import logging
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SHOPIFY")

def _gs(key, default=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__("os").environ.get(key, default)



class ShopifyIntegration:
    """Connecteur Shopify pour le projet Botanica et e-commerce NAYA."""

    def __init__(self):
        self.shop_url = _gs("SHOPIFY_SHOP_URL").rstrip("/")
        self.token = _gs("SHOPIFY_ACCESS_TOKEN")
        self.available = bool(self.shop_url and self.token)
        if not self.available:
            log.debug("Shopify non configuré — ajoute SHOPIFY_SHOP_URL + SHOPIFY_ACCESS_TOKEN dans .env")

    def _headers(self) -> Dict:
        return {
            "X-Shopify-Access-Token": self.token,
            "Content-Type": "application/json",
        }

    def _url(self, endpoint: str) -> str:
        return f"{self.shop_url}/admin/api/2024-01/{endpoint}.json"

    def process(self, payload: Dict) -> Dict:
        action = payload.get("action", "status")
        if not self.available:
            return {"status": "not_configured", "hint": "Ajoute SHOPIFY_SHOP_URL + SHOPIFY_ACCESS_TOKEN dans .env"}
        if action == "products":
            return self.get_products(payload.get("limit", 10))
        elif action == "orders":
            return self.get_orders(payload.get("limit", 10))
        elif action == "strategy":
            return self.generate_strategy(payload)
        elif action == "create_product":
            return self.create_product(payload.get("product", {}))
        return {"status": "ok", "shop": self.shop_url}

    def get_products(self, limit: int = 10) -> Dict:
        try:
            import httpx
            resp = httpx.get(self._url("products"), params={"limit": limit}, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                products = resp.json().get("products", [])
                return {"status": "ok", "count": len(products), "products": [
                    {"id": p["id"], "title": p["title"], "price": p.get("variants", [{}])[0].get("price", "0")}
                    for p in products
                ]}
            return {"status": "error", "code": resp.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_orders(self, limit: int = 10) -> Dict:
        try:
            import httpx
            resp = httpx.get(self._url("orders"), params={"limit": limit, "status": "any"}, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                orders = resp.json().get("orders", [])
                total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
                return {"status": "ok", "count": len(orders), "total_revenue_eur": round(total_revenue, 2)}
            return {"status": "error", "code": resp.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_product(self, product_data: Dict) -> Dict:
        try:
            import httpx
            payload = {"product": product_data}
            resp = httpx.post(self._url("products"), json=payload, headers=self._headers(), timeout=10)
            if resp.status_code == 201:
                p = resp.json().get("product", {})
                return {"status": "created", "product_id": p.get("id"), "title": p.get("title")}
            return {"status": "error", "code": resp.status_code, "body": resp.text[:300]}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_strategy(self, payload: Dict) -> Dict:
        """Génère une stratégie e-commerce avec le brain NAYA."""
        try:
            from NAYA_CORE.execution.naya_brain import get_brain, TaskType
            brain = get_brain()
            if not brain.available:
                return {"status": "llm_required", "hint": "Configure ANTHROPIC_API_KEY"}
            products = self.get_products(20)
            orders = self.get_orders(50)
            prompt = f"""Analyse cette boutique Shopify NAYA:
Produits: {products}
Commandes récentes: {orders}
Budget marketing: {payload.get('budget_eur', 500)}€

Génère: 1) Top 3 produits à promouvoir 2) Stratégie pricing 3) Actions 72h pour +20% CA.
Floor minimum par vente: 30€."""
            r = brain.think(prompt, TaskType.STRATEGIC)
            return {"status": "ok", "strategy": r.text, "data": {"products": products, "orders": orders}}
        except Exception as e:
            return {"status": "error", "error": str(e)}
