"""NAYA V19 — Business API Router — Production Ready"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.post("/offer/generate")
async def generate_offer(data: dict) -> Dict:
    """Génère une offre commerciale personnalisée pour un prospect."""
    prospect_id = data.get("prospect_id", "UNKNOWN")
    sector = data.get("sector", "pme")
    pain_type = data.get("pain_type", "operational")
    budget_eur = float(data.get("budget_eur", 5000))
    company = data.get("company", "Prospect")
    urgency = data.get("urgency", "medium")

    # Enforce plancher inviolable
    MIN = 1000.0
    if budget_eur < MIN:
        return {"status": "error", "error": f"Budget {budget_eur}€ inférieur au plancher {MIN}€"}

    # Tier selection based on budget
    if budget_eur >= 20000:
        tier = "TIER3_CONTRAT_LONG"
        delivery_days = 21
        pack_name = "Pack Premium Full"
    elif budget_eur >= 5000:
        tier = "TIER2_PROJET_COURT"
        delivery_days = 14
        pack_name = "Pack Sécurité Avancée"
    else:
        tier = "TIER1_QUICK_WIN"
        delivery_days = 7
        pack_name = "Pack Audit Express"

    # Try to use OfferSelector for richer response
    try:
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import OfferSelector
        selector = OfferSelector()
        selected = selector.select(budget_eur * 2, budget_eur * 10)
        pack_name = selected.get("offer", {}).get("name", pack_name)
    except Exception:
        pass

    offer = {
        "status": "generated",
        "prospect_id": prospect_id,
        "company": company,
        "sector": sector,
        "pain_type": pain_type,
        "urgency": urgency,
        "offer": {
            "name": pack_name,
            "tier": tier,
            "price_eur": budget_eur,
            "delivery_days": delivery_days,
            "currency": "EUR",
            "plancher_respected": budget_eur >= MIN,
        },
        "next_steps": [
            f"Envoyer proposition commerciale à {company}",
            "Planifier appel de découverte (30 min)",
            f"Délai de livraison estimé : {delivery_days} jours",
        ],
    }
    return offer


@router.get("/projects")
async def list_projects() -> Dict:
    """Liste tous les projets NAYA actifs."""
    projects = {
        "PROJECT_001_CASH_RAPIDE": {
            "name": "Cash Rapide",
            "description": "Services rapides 1k-100k EUR, livraison 24-72H",
            "status": "active",
            "revenue_target_monthly": 50000,
            "types": ["audit_digital", "chatbot", "saas_custom", "automation"],
        },
        "PROJECT_002_MEGA_PROJECTS": {
            "name": "Mega Projects",
            "description": "Projets stratégiques 100k-5M EUR",
            "status": "hunting",
            "revenue_target_monthly": 100000,
        },
        "PROJECT_003_BOTANICA": {
            "name": "NAYA Botanica",
            "description": "E-commerce produits naturels (perte poids, soins peau, parfums)",
            "status": "sourcing",
            "revenue_target_monthly": 20000,
            "products": ["weight_loss", "skin_repair", "skin_lightening", "mini_perfumes"],
        },
        "PROJECT_004_TINY_HOUSE": {
            "name": "NAYA Tiny House",
            "description": "Maison modulaire 20m2 solaire pliable anti-cyclone",
            "status": "design",
            "revenue_target_monthly": 30000,
            "first_units": "personal_use",
        },
        "PROJECT_005_MARCHES_OUBLIES": {
            "name": "Marchés Oubliés",
            "description": "Diaspora, Polynésie, Afrique, Latam, Maghreb",
            "status": "active",
            "revenue_target_monthly": 40000,
        },
        "PROJECT_006_IMMOBILIER": {
            "name": "Immobilier Polynésie",
            "description": "Investissement immobilier your region",
            "status": "research",
            "revenue_target_monthly": 50000,
        },
        "PROJECT_007_NAYA_PAYE": {
            "name": "Naya Paye",
            "description": "Fintech Polynésie (PayPal + Deblock)",
            "status": "concept",
            "revenue_target_monthly": 100000,
        },
    }
    total_target = sum(p.get("revenue_target_monthly", 0) for p in projects.values())
    return {
        "projects": projects,
        "total": len(projects),
        "total_monthly_target_eur": total_target,
    }


@router.get("/pricing/calculate")
async def calculate_pricing(
    pain_annual_cost: float = 50000,
    company_revenue: float = 500000,
) -> Dict:
    """Calcule le prix optimal pour une opportunité."""
    try:
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import OfferSelector
        selector = OfferSelector()
        return selector.select(pain_annual_cost, company_revenue)
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/forgotten-markets")
async def forgotten_markets_stats() -> Dict:
    """Statistiques des marchés oubliés."""
    try:
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import ForgottenMarketsEngine
        engine = ForgottenMarketsEngine()
        return engine.get_market_stats()
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/constitution")
async def constitution() -> Dict:
    """Invariants constitutionnels de NAYA."""
    return {
        "invariants": [
            {"rule": "PREMIUM_FLOOR", "value": "1000 EUR minimum", "enforced": True},
            {"rule": "STEALTH_DEFAULT", "value": "Mode discret par défaut", "enforced": True},
            {"rule": "ZERO_WASTE", "value": "Tout est recyclé/cloné", "enforced": True},
            {"rule": "NON_VENDABLE", "value": "Système personnel, non-vendable", "enforced": True},
            {"rule": "TRANSMISSIBLE", "value": "Transmissible aux enfants du fondateur", "enforced": True},
            {"rule": "LEGAL_ONLY", "value": "Opérations 100% légales uniquement", "enforced": True},
        ],
        "revenue_targets": {
            "weekly_eur": 60000,
            "monthly_eur": 300000,
            "note": "Objectifs aspirationnels — progression réaliste Phase 1→4",
        },
    }
