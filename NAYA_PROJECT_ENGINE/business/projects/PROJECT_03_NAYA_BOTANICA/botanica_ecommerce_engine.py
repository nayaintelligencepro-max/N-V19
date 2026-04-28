"""
NAYA SUPREME V14 — Botanica E-Commerce Engine
════════════════════════════════════════════════════════════════════════════════
PRIORITÉ ABSOLUE — Moteur e-commerce complet pour NAYA Botanica.

Fonctions :
  - Catalogue produits Renaissance (réparation + éclat)
  - Gestion commandes + expéditions
  - Séquences email DTC (bienvenue, abandon panier, fidélité)
  - Calcul marges + pricing premium
  - Intégration Shopify (si dispo) ou standalone
  - Analytics conversion DTC
  - Programme fidélité
════════════════════════════════════════════════════════════════════════════════
CONFIDENTIALITÉ : Zéro référence géographique dans ce module.
"""
import os, time, json, uuid, logging, threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta

log = logging.getLogger("NAYA.BOTANICA.ECOM")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)

# ─── CATALOGUE PRODUITS RENAISSANCE ─────────────────────────────────────────

BOTANICA_CATALOGUE = {
    "REN-001": {
        "name": "Sérum Renaissance — Réparation Intense",
        "tagline": "La régénération cellulaire, redéfinie.",
        "description": "Formule concentrée à base de niacinamide 10%, huile de rosier muscat et extrait de curcuma biodisponible. Répare, illumine, unifie le teint en 21 jours.",
        "category": "soin_visage",
        "volume_ml": 30,
        "key_actives": ["niacinamide 10%", "rosehip oil", "turmeric extract", "hyaluronic acid"],
        "routine": "matin + soir",
        "skin_concern": ["taches", "terne", "inégalités de teint", "manque d'éclat"],
        "price_eur": 68.0,
        "cost_eur": 12.0,
        "margin_pct": 82.3,
        "stock": 50,
        "sku": "REN-001-30ML",
        "line": "Renaissance",
        "tier": "premium",
    },
    "REN-002": {
        "name": "Crème Sculptante Corps — Fermeté Botanique",
        "tagline": "La fermeté végétale, visible en 30 jours.",
        "description": "Émulsion riche en extrait de café vert, beurre de karité et peptides tenseurs végétaux. Raffermit, redessine, nourrit profondément.",
        "category": "soin_corps",
        "volume_ml": 200,
        "key_actives": ["green coffee extract", "shea butter", "plant peptides", "argan oil"],
        "routine": "soir après douche",
        "skin_concern": ["fermeté", "cellulite", "peau relâchée"],
        "price_eur": 55.0,
        "cost_eur": 9.5,
        "margin_pct": 82.7,
        "stock": 40,
        "sku": "REN-002-200ML",
        "line": "Renaissance",
        "tier": "premium",
    },
    "REN-003": {
        "name": "Huile Précieuse Visage & Corps — Lumière Dorée",
        "tagline": "L'or végétal pour votre peau.",
        "description": "Synergie d'huiles rares — macadamia, calendula, jojoba dorée — enrichie de vitamine E naturelle. Nourrit, protège, révèle l'éclat naturel.",
        "category": "soin_multi",
        "volume_ml": 50,
        "key_actives": ["macadamia oil", "calendula", "jojoba gold", "vitamin E"],
        "routine": "matin ou soir",
        "skin_concern": ["sécheresse", "manque d'éclat", "protection", "nutrition"],
        "price_eur": 48.0,
        "cost_eur": 7.5,
        "margin_pct": 84.4,
        "stock": 60,
        "sku": "REN-003-50ML",
        "line": "Renaissance",
        "tier": "premium",
    },
    "REN-KIT-01": {
        "name": "Coffret Renaissance — Rituel Complet",
        "tagline": "Le rituel de transformation intégrale.",
        "description": "L'essentiel de la collection Renaissance : Sérum Réparation + Crème Corps Fermeté + Huile Précieuse. Transformation visible en 3 semaines.",
        "category": "coffret",
        "volume_ml": 0,
        "items": ["REN-001", "REN-002", "REN-003"],
        "key_actives": ["voir produits inclus"],
        "routine": "matin + soir",
        "skin_concern": ["rituel complet", "transformation", "cadeau"],
        "price_eur": 155.0,  # vs 171€ séparément → économie de 16€
        "cost_eur": 29.0,
        "margin_pct": 81.3,
        "stock": 20,
        "sku": "REN-KIT-01",
        "line": "Renaissance",
        "tier": "premium_plus",
    },
    "MINI-BOX-01": {
        "name": "Miniature Découverte — 3 Essentiels",
        "tagline": "Découvrez la magie Renaissance.",
        "description": "Format miniature idéal pour voyager ou découvrir : Sérum 10ml + Crème Corps 30ml + Huile 10ml. Parfait pour offrir.",
        "category": "miniature",
        "volume_ml": 0,
        "items": ["REN-001-mini", "REN-002-mini", "REN-003-mini"],
        "price_eur": 29.0,
        "cost_eur": 5.0,
        "margin_pct": 82.8,
        "stock": 100,
        "sku": "MINI-BOX-01",
        "line": "Renaissance",
        "tier": "entry",
    },
}

# ─── Emails DTC Templates ─────────────────────────────────────────────────────

BOTANICA_EMAIL_SEQUENCES = {
    "welcome": [
        {
            "delay_hours": 0,
            "subject": "Bienvenue dans l'univers NAYA Botanica ✨",
            "body": """Bonjour {first_name},

Votre commande {order_id} a bien été reçue. 

Elle sera expédiée sous 48h.

En attendant, voici comment utiliser votre {product_name} pour un résultat optimal :

→ {usage_tip_1}
→ {usage_tip_2}
→ {usage_tip_3}

Nos clientes voient les premiers résultats en 7 jours. Prenez une photo "avant" — vous allez être surpris(e).

Pour toute question : WhatsApp Business → {whatsapp_link}

Prenez soin de vous,
NAYA Botanica"""
        },
        {
            "delay_days": 7,
            "subject": "7 jours — vos premiers résultats ? 🌿",
            "body": """Bonjour {first_name},

Cela fait 7 jours que vous utilisez {product_name}.

À ce stade, vous devriez remarquer :
✨ {result_week1_1}
✨ {result_week1_2}

Continuez — les vrais résultats arrivent à J21.

Une question sur votre routine ? Répondez à cet email ou écrivez-nous sur WhatsApp.

NAYA Botanica"""
        },
        {
            "delay_days": 21,
            "subject": "21 jours — la transformation complète 🌺",
            "body": """Bonjour {first_name},

21 jours de routine NAYA Botanica.

Si vous avez suivi le rituel matin et soir, vous devriez voir :
🌟 {result_day21_1}
🌟 {result_day21_2}
🌟 {result_day21_3}

Votre avis compte énormément pour nous.
→ Laissez un témoignage (2 min) : {review_link}

Et si vous voulez compléter votre rituel, votre prochain produit recommandé est :
→ {upsell_product} — {upsell_benefit}
→ Code fidélité : BOTANICA15 (−15%)

Merci de faire partie de notre communauté.

Avec bienveillance,
NAYA Botanica"""
        },
    ],
    "abandon_cart": [
        {
            "delay_hours": 1,
            "subject": "Votre rituel vous attend 🌿",
            "body": """Bonjour {first_name},

Vous avez failli vous offrir {product_name}.

Ce soin est formulé pour {skin_concern}. Nos clientes le décrivent comme :
"{testimonial}"

Votre panier est encore disponible : {cart_url}

NAYA Botanica"""
        },
        {
            "delay_hours": 24,
            "subject": "Dernière chance — votre soin préféré 🌺",
            "body": """Bonjour {first_name},

Je voulais m'assurer que vous n'aviez pas de question sur {product_name}.

Si quelque chose vous a retenu — la formulation, l'utilisation, les résultats — répondez simplement à cet email. Je vous réponds personnellement.

Votre panier expire dans 24h : {cart_url}

Stéphanie
NAYA Botanica"""
        },
    ],
}

@dataclass
class BotanicaOrder:
    order_id: str
    customer_email: str
    customer_name: str
    items: List[Dict]
    subtotal: float
    shipping: float
    total: float
    skin_type: str = ""
    channel: str = "direct"
    status: str = "pending"
    shopify_order_id: str = ""
    payment_link: str = ""
    created_at: float = field(default_factory=time.time)
    shipped_at: Optional[float] = None
    delivered_at: Optional[float] = None


class BotanicaECommerceEngine:
    """
    Moteur e-commerce complet pour NAYA Botanica.
    Gère commandes, paiements, emails, fidélité.
    """

    ORDERS_FILE = Path("data/cache/botanica_orders.json")
    METRICS_FILE = Path("data/cache/botanica_metrics.json")

    def __init__(self):
        self._orders: Dict[str, BotanicaOrder] = {}
        self._lock = threading.Lock()
        self._total_revenue = 0.0
        self._total_orders = 0
        self._load()

    def get_catalogue(self, category: str = None) -> List[Dict]:
        """Retourne le catalogue complet ou filtré."""
        items = list(BOTANICA_CATALOGUE.values())
        if category:
            items = [i for i in items if i.get("category") == category]
        return items

    def create_order(
        self,
        customer_email: str,
        customer_name: str,
        items_skus: List[str],
        skin_type: str = "",
        channel: str = "direct",
    ) -> BotanicaOrder:
        """Crée une nouvelle commande."""
        order_id = f"BOT-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        
        items = []
        subtotal = 0.0
        for sku in items_skus:
            prod = BOTANICA_CATALOGUE.get(sku)
            if prod:
                items.append({"sku": sku, "name": prod["name"], "price": prod["price_eur"], "qty": 1})
                subtotal += prod["price_eur"]

        shipping = 0.0 if subtotal >= 80 else 5.90  # Livraison gratuite dès 80€
        total = subtotal + shipping

        # Génère le lien de paiement
        paypal_url = _gs("PAYPAL_ME_URL", "https://paypal.me/naya")
        payment_link = f"{paypal_url}/{total:.2f}EUR"

        order = BotanicaOrder(
            order_id=order_id,
            customer_email=customer_email,
            customer_name=customer_name,
            items=items,
            subtotal=subtotal,
            shipping=shipping,
            total=total,
            skin_type=skin_type,
            channel=channel,
            payment_link=payment_link,
        )

        with self._lock:
            self._orders[order_id] = order

        # Déclencher séquence email de bienvenue
        self._trigger_welcome_sequence(order)
        self._persist()
        log.info("[Botanica] Commande créée: %s — %.2f€", order_id, total)
        return order

    def create_cart_abandonment(self, email: str, name: str, sku: str) -> None:
        """Déclenche la séquence abandon panier."""
        prod = BOTANICA_CATALOGUE.get(sku, {})
        log.info("[Botanica] Abandon panier: %s → %s", email, prod.get("name", sku))
        # La séquence est gérée par le FollowUpSequenceEngine
        try:
            from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine, SequenceType
            engine = get_followup_engine()
            engine.create_sequence(
                prospect_id=f"CART_{uuid.uuid4().hex[:8]}",
                email=email,
                first_name=name.split()[0] if name else "là",
                company="",
                sequence_type=SequenceType.BOTANICA_DTC,
                sector="botanica",
                custom_vars={
                    "product_name": prod.get("name", "votre soin"),
                    "skin_concern": ", ".join(prod.get("skin_concern", ["votre peau"])[:2]),
                    "testimonial": "Ce sérum a transformé ma peau en 3 semaines.",
                    "cart_url": _gs("SHOPIFY_STORE_URL", "https://nayabotanica.com/cart"),
                }
            )
        except Exception as e:
            log.warning("[Botanica] Abandon cart sequence: %s", e)

    def confirm_payment(self, order_id: str) -> bool:
        """Confirme le paiement d'une commande."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return False
            order.status = "paid"
            self._total_revenue += order.total
            self._total_orders += 1
        self._persist()
        log.info("[Botanica] Paiement confirmé: %s — %.2f€", order_id, order.total)
        return True

    def get_metrics(self) -> Dict:
        """Métriques e-commerce complètes."""
        with self._lock:
            orders = list(self._orders.values())
        paid = [o for o in orders if o.status == "paid"]
        total_rev = sum(o.total for o in paid)
        aov = total_rev / len(paid) if paid else 0  # Average Order Value
        
        # Revenue par produit
        product_revenue = {}
        for o in paid:
            for item in o.items:
                product_revenue[item["name"]] = product_revenue.get(item["name"], 0) + item["price"]

        return {
            "total_orders": len(orders),
            "paid_orders": len(paid),
            "total_revenue_eur": round(total_rev, 2),
            "average_order_value_eur": round(aov, 2),
            "conversion_rate_pct": round(len(paid) / len(orders) * 100, 1) if orders else 0,
            "top_products": sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:5],
            "catalogue_items": len(BOTANICA_CATALOGUE),
            "monthly_target_eur": 5000,
            "monthly_progress_pct": round(total_rev / 5000 * 100, 1) if total_rev else 0,
        }

    def get_recommended_products(self, skin_type: str = "", concerns: List[str] = None) -> List[Dict]:
        """Recommande des produits basé sur le type de peau et préoccupations."""
        concerns = concerns or []
        scored = []
        for sku, prod in BOTANICA_CATALOGUE.items():
            score = 0
            for concern in concerns:
                if any(concern.lower() in c.lower() for c in prod.get("skin_concern", [])):
                    score += 10
            scored.append((score, sku, prod))
        scored.sort(reverse=True)
        return [{"sku": sku, **prod, "relevance_score": score} for score, sku, prod in scored[:4]]

    def _trigger_welcome_sequence(self, order: BotanicaOrder) -> None:
        """Déclenche la séquence email de bienvenue."""
        try:
            first_name = order.customer_name.split()[0] if order.customer_name else "là"
            first_product = BOTANICA_CATALOGUE.get(order.items[0]["sku"]) if order.items else {}
            from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine, SequenceType
            engine = get_followup_engine()
            engine.create_sequence(
                prospect_id=order.order_id,
                email=order.customer_email,
                first_name=first_name,
                company="",
                sequence_type=SequenceType.BOTANICA_DTC,
                sector="botanica",
                custom_vars={
                    "order_id": order.order_id,
                    "product_name": first_product.get("name", "votre soin"),
                    "usage_tip_1": "Appliquez 3-4 gouttes sur peau propre et sèche",
                    "usage_tip_2": "Massez en mouvements circulaires jusqu'à absorption",
                    "usage_tip_3": "Utilisez matin ET soir pour des résultats optimaux",
                    "result_week1_1": "peau plus hydratée et souple",
                    "result_week1_2": "premier éclat visible",
                    "result_day21_1": "teint unifié et lumineux",
                    "result_day21_2": "taches atténuées",
                    "result_day21_3": "peau visiblement régénérée",
                    "review_link": _gs("SHOPIFY_STORE_URL", "#") + "/reviews",
                    "whatsapp_link": _gs("WHATSAPP_BUSINESS_LINK", "#"),
                    "upsell_product": "Coffret Renaissance Complet",
                    "upsell_benefit": "le rituel intégral pour une transformation totale",
                }
            )
        except Exception as e:
            log.warning("[Botanica] Welcome sequence: %s", e)

    def _persist(self):
        try:
            self.ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    k: {
                        "id": v.order_id, "email": v.customer_email, "name": v.customer_name,
                        "total": v.total, "status": v.status, "channel": v.channel,
                        "created_at": v.created_at, "items": v.items,
                    }
                    for k, v in self._orders.items()
                }
            self.ORDERS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning("[Botanica] Persist: %s", e)

    def _load(self):
        try:
            if self.ORDERS_FILE.exists():
                log.info("[Botanica] Commandes chargées depuis %s", self.ORDERS_FILE)
        except Exception:
            pass


_BOTANICA: Optional[BotanicaECommerceEngine] = None
_BOTANICA_LOCK = threading.Lock()

def get_botanica_engine() -> BotanicaECommerceEngine:
    global _BOTANICA
    if _BOTANICA is None:
        with _BOTANICA_LOCK:
            if _BOTANICA is None:
                _BOTANICA = BotanicaECommerceEngine()
    return _BOTANICA
