"""PAIN: Plateforme XR Custom — PROJECT_02 GOOGLE XR"""
PAIN = {
    "name": "Plateforme XR Propriétaire Custom",
    "description": "Grandes entreprises et éditeurs souhaitant intégrer XR dans leur produit core sans dépendance fournisseur",
    "urgency": "LOW",
    "price_range": (150000, 500000),
    "timeline": "8-16 semaines",
    "target_sectors": ["Éditeurs SaaS", "Médias", "Healthcare", "Real Estate Tech", "Defense"],
    "our_solution": "Développement plateforme XR white-label — SDK propriétaire + cloud rendering + analytics",
    "market_size": 2800000,
    "satisfaction_current": 0.15,
    "acquisition_channels": ["CTO LinkedIn", "Venture Builder events", "Tech PE funds"],
    "kpis": ["Time-to-market", "Coût par session XR", "NPS utilisateurs XR"],
}

PLATFORM_MODULES = {
    "sdk_mobile":     {"price": 80000,  "desc": "SDK iOS/Android natif ARKit + ARCore"},
    "cloud_render":   {"price": 120000, "desc": "Cloud rendering temps réel multi-utilisateurs"},
    "analytics":      {"price": 40000,  "desc": "Analytics immersif + heatmaps 3D"},
    "content_cms":    {"price": 50000,  "desc": "CMS gestion assets XR + versionning"},
    "white_label":    {"price": 60000,  "desc": "Whitelabel complet + store deployment"},
}

def get_platform_quote(modules: list = None) -> dict:
    if modules is None:
        modules = ["sdk_mobile", "cloud_render"]
    selected = {k: v for k, v in PLATFORM_MODULES.items() if k in modules}
    total = sum(v["price"] for v in selected.values())
    discount = 0.15 if len(modules) >= 4 else (0.10 if len(modules) >= 3 else 0)
    return {
        "modules": selected, "subtotal": total,
        "discount_pct": int(discount * 100),
        "total": round(total * (1 - discount) / 5000) * 5000,
        "timeline_weeks": len(modules) * 3 + 4,
        "ip_ownership": "Client 100%",
        "support": "24 mois inclus",
    }
