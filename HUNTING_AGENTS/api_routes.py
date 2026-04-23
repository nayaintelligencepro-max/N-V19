"""
NAYA SUPREME — Hunting Agents API Routes
Routes FastAPI pour exposer les 4 agents de chasse.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

log = logging.getLogger("NAYA.API.HUNTING")

router = APIRouter(prefix="/api/hunting", tags=["hunting-agents"])

# Référence globale à l'intégration (set par main.py au boot)
_integration = None


def set_integration(integration):
    global _integration
    _integration = integration


def _get():
    if not _integration:
        raise HTTPException(503, "Hunting Agents not booted")
    return _integration


# ── Stats consolidées ────────────────────────────────────────────────────────

@router.get("/stats")
async def hunting_stats():
    """Stats consolidées de tous les agents de chasse."""
    return _get().get_all_stats()


@router.post("/run-full-cycle")
async def run_full_cycle():
    """Exécute un cycle complet de tous les agents."""
    return _get().run_full_cycle()


# ── Pain Hunter B2B ──────────────────────────────────────────────────────────

@router.get("/pain/stats")
async def pain_stats():
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    return h.get_stats()


@router.post("/pain/hunt")
async def pain_hunt(sectors: Optional[str] = None):
    """Lance un cycle de chasse de douleurs. sectors=pme_b2b,finance_banque,..."""
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    sector_list = sectors.split(",") if sectors else None
    return h.hunt_cycle(sectors=sector_list)


@router.get("/pain/cash-rapide")
async def pain_cash_rapide():
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    return {"category": "cash_rapide", "opportunities": h.get_cash_rapide()}


@router.get("/pain/moyen-terme")
async def pain_moyen_terme():
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    return {"category": "moyen_terme", "opportunities": h.get_moyen_terme()}


@router.get("/pain/long-terme")
async def pain_long_terme():
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    return {"category": "long_terme", "opportunities": h.get_long_terme()}


@router.get("/pain/top")
async def pain_top(n: int = 10):
    h = _get().pain_hunter
    if not h: raise HTTPException(503, "PainHunterB2B not loaded")
    return {"top_opportunities": h.get_top_opportunities(n)}


# ── Mega Project Hunter ──────────────────────────────────────────────────────

@router.get("/mega/stats")
async def mega_stats():
    h = _get().mega_hunter
    if not h: raise HTTPException(503, "MegaProjectHunter not loaded")
    return h.get_stats()


@router.post("/mega/hunt")
async def mega_hunt():
    h = _get().mega_hunter
    if not h: raise HTTPException(503, "MegaProjectHunter not loaded")
    return h.hunt_cycle()


@router.get("/mega/top")
async def mega_top(n: int = 5):
    h = _get().mega_hunter
    if not h: raise HTTPException(503, "MegaProjectHunter not loaded")
    return {"top_projects": h.get_top_projects(n)}


# ── Forgotten Market Conqueror ───────────────────────────────────────────────

@router.get("/markets/stats")
async def markets_stats():
    h = _get().market_conqueror
    if not h: raise HTTPException(503, "ForgottenMarketConqueror not loaded")
    return h.get_stats()


@router.post("/markets/hunt")
async def markets_hunt():
    h = _get().market_conqueror
    if not h: raise HTTPException(503, "ForgottenMarketConqueror not loaded")
    return h.hunt_cycle()


@router.get("/markets/top")
async def markets_top(n: int = 10):
    h = _get().market_conqueror
    if not h: raise HTTPException(503, "ForgottenMarketConqueror not loaded")
    return {"top_markets": h.get_top_markets(n)}


@router.get("/markets/quick-wins")
async def markets_quick_wins():
    h = _get().market_conqueror
    if not h: raise HTTPException(503, "ForgottenMarketConqueror not loaded")
    return {"quick_wins": h.get_quick_wins()}


# ── Strategic Business Creator ───────────────────────────────────────────────

@router.get("/strategy/stats")
async def strategy_stats():
    h = _get().strategic_creator
    if not h: raise HTTPException(503, "StrategicBusinessCreator not loaded")
    return h.get_stats()


@router.post("/strategy/cycle")
async def strategy_cycle():
    h = _get().strategic_creator
    if not h: raise HTTPException(503, "StrategicBusinessCreator not loaded")
    return h.strategic_cycle()


@router.get("/strategy/top")
async def strategy_top(n: int = 10):
    h = _get().strategic_creator
    if not h: raise HTTPException(503, "StrategicBusinessCreator not loaded")
    return {"top_blueprints": h.get_top_blueprints(n)}


@router.get("/strategy/cash-businesses")
async def strategy_cash():
    h = _get().strategic_creator
    if not h: raise HTTPException(503, "StrategicBusinessCreator not loaded")
    return {"cash_businesses": h.get_cash_businesses()}


@router.get("/strategy/empire-candidates")
async def strategy_empire():
    h = _get().strategic_creator
    if not h: raise HTTPException(503, "StrategicBusinessCreator not loaded")
    return {"empire_candidates": h.get_empire_candidates()}
