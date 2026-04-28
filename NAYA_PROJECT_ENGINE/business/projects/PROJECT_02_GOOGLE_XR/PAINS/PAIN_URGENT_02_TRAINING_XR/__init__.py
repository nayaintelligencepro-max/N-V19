"""PAIN: Formation XR Urgente — PROJECT_02 GOOGLE XR"""
PAIN = {
    "name": "Formation Immersive XR Urgente",
    "description": "Entreprises incapables de former rapidement leurs équipes sans solutions XR adaptées",
    "urgency": "HIGH",
    "price_range": (25000, 80000),
    "timeline": "1-3 semaines",
    "target_sectors": ["Industrie", "Santé", "Formation professionnelle", "Aviation"],
    "our_solution": "Modules de formation XR clé-en-main Google ARCore + WebXR + LMS intégré",
    "market_size": 3200000,
    "satisfaction_current": 0.25,
    "acquisition_channels": ["Linkedin HR Directors", "OPCO / Qualiopi", "Salons formation"],
    "kpis": ["Taux complétion formation", "Score rétention 30j", "Heures économisées/an"],
}

def get_offer(headcount: int = 50) -> dict:
    base = 30000
    per_user = 400
    price = base + (headcount * per_user)
    return {
        "solution": PAIN["our_solution"],
        "price": round(min(price, 80000) / 1000) * 1000,
        "timeline": PAIN["timeline"],
        "modules": ["Onboarding XR", "HSE immersif", "Procédures opérationnelles 3D"],
        "certification": "Qualiopi éligible OPCO",
        "guarantee": "Formation opérationnelle J+7 ou remboursement",
    }
