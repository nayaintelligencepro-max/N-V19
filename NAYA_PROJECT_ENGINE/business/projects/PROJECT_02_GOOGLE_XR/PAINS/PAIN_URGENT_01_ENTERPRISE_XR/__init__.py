"""PAIN: Déploiement AR Enterprise Urgent — PROJECT_02 GOOGLE XR"""
PAIN = {
    "name": "Déploiement AR Enterprise Urgent",
    "description": "Entreprises bloquées sans solution AR opérationnelle",
    "urgency": "CRITICAL",
    "price_range": (50000, 150000),
    "timeline": "2-4 semaines",
    "target_sectors": ["Industrie", "Logistique", "Maintenance"],
    "our_solution": "Déploiement clé-en-main Google Glass Enterprise + ARCore",
    "market_size": 5000000,
    "satisfaction_current": 0.30,
    "acquisition_channels": ["LinkedIn Enterprise", "Événements sectoriels", "Google Partner Network"],
    "kpis": ["Taux adoption XR", "Heures formation", "ROI client 12 mois"],
}

def get_offer(client_size: str = "medium") -> dict:
    multiplier = {"small": 0.7, "medium": 1.0, "large": 1.4, "enterprise": 2.0}.get(client_size, 1.0)
    return {
        "solution": PAIN["our_solution"],
        "price": round(85000 * multiplier / 1000) * 1000,
        "timeline": PAIN["timeline"],
        "guarantee": "Satisfaction ou remboursement 30 jours",
        "included": ["Setup complet", "Formation équipe", "Support 3 mois"],
    }
