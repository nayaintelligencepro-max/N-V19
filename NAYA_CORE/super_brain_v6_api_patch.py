"""
NAYA V19 — API Endpoints Patch
Ajouter à main.py pour exposer les nouvelles fonctionnalités du Super Brain V6.
"""

# ─── Imports à ajouter dans main.py ───────────────────────────────────────────
#
# from NAYA_CORE.super_brain_hybrid_v6_0 import (
#     hunt_and_create, create_cash_ladder, recycle_rejection,
#     get_super_brain, get_executor, SilentPainDetector, PainCategory
# )
#
# ─── Endpoints à ajouter dans main.py ─────────────────────────────────────────

ENDPOINTS_TO_ADD = """

# ── Super Brain V6 — Silent Pain Detection ────────────────────────────────────
@api.post("/brain/hunt-pains", tags=["brain_v6"])
def hunt_silent_pains(payload: dict):
    \"\"\"Détecte les douleurs silencieuses dans un profil d'entreprise.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import hunt_and_create
    industry = payload.get("industry", "pme_b2b")
    signals = payload.get("signals", [])
    revenue = float(payload.get("revenue_eur", 500000))
    return hunt_and_create(industry, signals, revenue)

@api.post("/brain/cash-ladder", tags=["brain_v6"])
def cash_ladder(payload: dict):
    \"\"\"Crée l'escalier complet 5K→80K pour une opportunité.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import create_cash_ladder
    industry = payload.get("industry", "pme_b2b")
    signals = payload.get("signals", [])
    revenue = float(payload.get("revenue_eur", 500000))
    return {"ladder": create_cash_ladder(industry, signals, revenue)}

@api.post("/brain/recycle", tags=["brain_v6"])
def recycle_lost_deal(payload: dict):
    \"\"\"Recycle un refus ou deal perdu en nouvelle opportunité.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import recycle_rejection
    return recycle_rejection(payload.get("package", {}), payload.get("reason", ""))

@api.get("/brain/v6/stats", tags=["brain_v6"])
def brain_v6_stats():
    \"\"\"Stats du Super Brain V6 — détections, revenus pipeline, recyclage.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import get_super_brain, get_executor
    brain = get_super_brain()
    executor = get_executor()
    return {"brain": brain.get_stats(), "executor": executor.stats}

@api.get("/brain/pain-categories", tags=["brain_v6"])
def list_pain_categories():
    \"\"\"Liste toutes les catégories de douleurs détectables.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import INDUSTRY_PAIN_MAP, VERBAL_PAIN_SIGNALS
    return {
        "industries": list(INDUSTRY_PAIN_MAP.keys()),
        "verbal_signals_count": len(VERBAL_PAIN_SIGNALS),
        "pain_categories": [p.value for p in __import__('NAYA_CORE.super_brain_hybrid_v6_0',
            fromlist=['PainCategory']).PainCategory],
    }

@api.post("/brain/generate-proposal", tags=["brain_v6"])
def generate_full_proposal(payload: dict):
    \"\"\"Génère une proposition commerciale complète à partir d'un profil.\"\"\"
    from NAYA_CORE.super_brain_hybrid_v6_0 import hunt_and_create, get_executor
    industry = payload.get("industry", "pme_b2b")
    signals = payload.get("signals", [])
    revenue = float(payload.get("revenue_eur", 500000))
    client_name = payload.get("client_name", "")
    result = hunt_and_create(industry, signals, revenue)
    if result.get("status") == "opportunity_found" and result.get("package"):
        from NAYA_CORE.super_brain_hybrid_v6_0 import BusinessPackage, CashTier, get_executor
        executor = get_executor()
        return result.get("proposal", result)
    return result
"""
