"""P4 ENTERPRISE — 75k-200k€ — Livraison 1 semaine"""
from typing import Dict, List

P4_SERVICES = [
    {"id": "P4_01", "name": "Transformation opérationnelle complète PME",
     "price": 120000, "hours": 40, "timeline": "1 semaine conception + 4 semaines déploiement",
     "deliverable": "Nouveau modèle opérationnel + formation équipe + KPIs suivi 6 mois",
     "sectors": ["Industrie", "Distribution", "Services B2B"]},
    {"id": "P4_02", "name": "Déploiement IA & automatisation entreprise",
     "price": 150000, "hours": 60, "timeline": "10 jours",
     "deliverable": "5 processus automatisés + formation + ROI garanti",
     "sectors": ["Finance", "RH", "Supply Chain", "Comptabilité"]},
    {"id": "P4_03", "name": "Architecture décisionnelle groupe",
     "price": 100000, "hours": 50, "timeline": "1 semaine",
     "deliverable": "Système de reporting + dashboard + comité stratégique formé",
     "sectors": ["Groupes multi-filiales", "Holdings", "Franchises"]},
    {"id": "P4_04", "name": "Restructuration commerciale urgente",
     "price": 85000, "hours": 45, "timeline": "1 semaine",
     "deliverable": "Nouveau process commercial + CRM + formation force de vente",
     "sectors": ["B2B", "Distribution", "SaaS PME"]},
]

def get_p4_offer(pain: str, company_revenue: float = 5000000) -> Dict:
    scale = min(2.0, max(0.7, company_revenue / 5000000))
    best = P4_SERVICES[0]
    return {"service": best, "price": round(best["price"] * scale / 5000) * 5000,
            "timeline": "10 jours", "roi_guarantee": "ROI 3x en 12 mois ou remboursement",
            "payment": "50% avance, 50% livraison"}

def get_enterprise_package(modules: List[str] = None) -> Dict:
    if modules is None: modules = ["transformation", "ia_automation"]
    base_price = 120000
    module_pricing = {"transformation": 0, "ia_automation": 30000,
                      "decision_arch": 20000, "commercial": 15000}
    total = base_price + sum(module_pricing.get(m, 10000) for m in modules if m != "transformation")
    return {"modules": modules, "price": total, "timeline": "3 semaines",
            "discount_pct": 15 if len(modules) >= 3 else 0}
