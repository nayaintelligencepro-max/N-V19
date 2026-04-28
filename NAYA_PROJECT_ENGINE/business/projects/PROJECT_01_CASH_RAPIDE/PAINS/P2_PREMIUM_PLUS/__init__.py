"""P2 PREMIUM PLUS — 5k-25k€ — Livraison 48H"""
from typing import Dict, List

P2_SERVICES = [
    {"id": "P2_01", "name": "Setup système facturation PME", "price": 8000, "hours": 12,
     "deliverable": "Système opérationnel + formation + 1 mois support"},
    {"id": "P2_02", "name": "Audit logistique complet", "price": 12000, "hours": 20,
     "deliverable": "Rapport + procédures + formation équipe"},
    {"id": "P2_03", "name": "Refonte CRO site e-commerce", "price": 10000, "hours": 15,
     "deliverable": "Rapport + implémentations + A/B tests"},
    {"id": "P2_04", "name": "Setup automation N8N/Zapier", "price": 7000, "hours": 16,
     "deliverable": "5 automations opérationnelles + doc"},
    {"id": "P2_05", "name": "Cabinet médical — système admin complet", "price": 15000, "hours": 20,
     "deliverable": "Agenda + rappels + admin auto + formation"},
]

def get_p2_offer(pain: str, client_revenue: float = 200000) -> Dict:
    price = min(25000, max(5000, client_revenue * 0.05))
    return {"price": round(price/1000)*1000, "timeline": "48H",
            "services": [s for s in P2_SERVICES if s["price"] <= price * 1.2][:2]}
