"""PAIN: Visualisation Data XR — PROJECT_02 GOOGLE XR"""
PAIN = {
    "name": "Data Visualization Immersive & Analytics XR",
    "description": "Décideurs noyés dans des dashboards 2D sans capacité de comprendre données complexes multidimensionnelles",
    "urgency": "MEDIUM",
    "price_range": (30000, 100000),
    "timeline": "2-4 semaines",
    "target_sectors": ["Finance", "Logistique", "Retail", "Smart City", "R&D"],
    "our_solution": "Dashboard XR WebGL + ARCore — données 3D navigables en temps réel",
    "market_size": 4200000,
    "satisfaction_current": 0.30,
    "acquisition_channels": ["DSI / CDO LinkedIn", "Gartner / Forrester events", "Partenaires BI (Tableau, PowerBI)"],
    "kpis": ["Temps prise de décision", "Taux adoption dashboard", "Erreurs analytiques évitées"],
}

def get_offer(data_sources: int = 5, users: int = 10) -> dict:
    base_price = 35000
    per_source = 3000
    per_user = 800
    price = base_price + (data_sources * per_source) + (users * per_user)
    return {
        "solution": PAIN["our_solution"],
        "price": round(min(price, 100000) / 1000) * 1000,
        "data_sources": data_sources,
        "users": users,
        "connectors": ["Salesforce", "PowerBI", "BigQuery", "PostgreSQL", "REST API"],
        "delivery": f"{data_sources * 2 + 5} jours",
        "support": "12 mois inclus",
    }
