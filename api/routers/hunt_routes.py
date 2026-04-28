"""
NAYA V19 — Hunt API Routes
Endpoints: /hunt/run, /hunt/prospects, /hunt/signals
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/hunt", tags=["Hunting V19"])


class HuntRequest(BaseModel):
    categories: Optional[List[str]] = None  # None = toutes les catégories
    max_prospects: int = 20
    countries: Optional[List[str]] = None


@router.post("/run")
async def run_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    """Lance un cycle de chasse complet en arrière-plan."""
    background_tasks.add_task(_do_hunt, req.categories, req.max_prospects, req.countries)
    return {"status": "hunt_started", "message": "Chasse lancée en arrière-plan"}


@router.get("/signals")
async def get_signals():
    """Derniers signaux de douleur détectés."""
    try:
        from NAYA_CORE.integrations.serper_hunter import get_serper
        serper = get_serper()
        if serper.available:
            signals = serper.hunt_pains(["restructuration", "marchés_publics", "polynesie"])
            return {"status": "ok", "count": len(signals), "signals": signals[:20]}
        return {"status": "serper_unavailable", "signals": [], "tip": "Set SERPER_API_KEY in SECRETS/keys/serper.json"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/prospects")
async def get_prospects(limit: int = 10):
    """Prospects Apollo.io enrichis."""
    try:
        from NAYA_CORE.integrations.apollo_hunter import get_apollo
        apollo = get_apollo()
        if not apollo.available:
            return {"status": "apollo_unavailable", "prospects": [], "tip": "Set APOLLO_API_KEY"}
        prospects = apollo.search_people(
            job_titles=["Directeur SI", "DSI", "CTO", "CEO", "DG", "Directeur général"],
            countries=["France", "Morocco", "Senegal", "Ivory Coast"],
            limit=limit
        )
        return {
            "status": "ok",
            "count": len(prospects),
            "prospects": [vars(p) for p in prospects]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/stats")
async def hunt_stats():
    """Statistiques de chasse."""
    result = {}
    try:
        from NAYA_CORE.integrations.serper_hunter import get_serper
        result["serper"] = get_serper().stats()
    except Exception as e:
        result["serper"] = {"error": str(e)}
    try:
        from NAYA_CORE.integrations.apollo_hunter import get_apollo
        result["apollo"] = get_apollo().stats()
    except Exception as e:
        result["apollo"] = {"error": str(e)}
    return result


async def _do_hunt(categories, max_prospects, countries):
    """Cycle de chasse complet async."""
    import logging
    log = logging.getLogger("NAYA.HUNT.CYCLE")
    log.info("[HUNT] Starting autonomous hunt cycle...")
    try:
        from NAYA_CORE.integrations.serper_hunter import get_serper
        from NAYA_CORE.integrations.telegram_notifier import get_notifier
        signals = get_serper().hunt_pains(categories)
        if signals:
            get_notifier().alert_system(
                f"🎯 Chasse terminée\n{len(signals)} signaux détectés",
                "SUCCESS"
            )
        log.info(f"[HUNT] Cycle done — {len(signals)} signals")
    except Exception as e:
        log.warning(f"[HUNT] Cycle failed: {e}")
