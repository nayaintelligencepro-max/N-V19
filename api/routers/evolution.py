"""NAYA V19 — Evolution API Router — Expose evolution, anticipation et learner."""
import asyncio
import logging
from fastapi import APIRouter
from typing import Dict

log = logging.getLogger("NAYA.API.EVOLUTION")
router = APIRouter()


@router.get("/status")
async def evolution_status() -> Dict:
    """État complet du système d'évolution : orchestrator + scaler + guard."""
    def _collect():
        result: Dict = {}

        try:
            from EVOLUTION_SYSTEM.evolution_orchestrator import get_evolution_orchestrator
            result["orchestrator"] = get_evolution_orchestrator().get_stats()
        except Exception as e:
            result["orchestrator"] = {"error": str(e)[:80]}

        try:
            from EVOLUTION_SYSTEM.regression_guard import get_regression_guard
            result["regression_guard"] = get_regression_guard().get_stats()
        except Exception as e:
            result["regression_guard"] = {"error": str(e)[:80]}

        try:
            from PARALLEL_ENGINE.dynamic_scaler import get_dynamic_scaler
            result["dynamic_scaler"] = get_dynamic_scaler().get_stats()
        except Exception as e:
            result["dynamic_scaler"] = {"error": str(e)[:80]}

        try:
            from EVOLUTION_SYSTEM.shi_engine import SHIEngine
            result["shi"] = SHIEngine().calculate_shi()
        except Exception as e:
            result["shi"] = {"error": str(e)[:80]}

        return result

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, _collect)
    return {"evolution": data}


@router.get("/anticipation/roadmap")
async def anticipation_roadmap() -> Dict:
    """Roadmap 36 mois + opportunités anticipées dans les 90 prochains jours."""
    def _collect():
        try:
            from EVOLUTION_SYSTEM.anticipation_engine import get_anticipation_engine
            engine = get_anticipation_engine()
            return {
                "roadmap": engine.get_3year_roadmap(),
                "current_milestone": {
                    "month": engine.get_current_milestone().month,
                    "target_eur": engine.get_current_milestone().target_eur,
                    "achieved_eur": engine.get_current_milestone().achieved_eur,
                    "status": engine.get_current_milestone().status,
                    "focus": engine.get_current_milestone().focus,
                },
                "opportunities_90d": [
                    {
                        "label": o.label,
                        "sector": o.sector,
                        "horizon_days": o.horizon_days,
                        "expected_value_eur": o.expected_value,
                        "probability": o.probability,
                        "action": o.action_required,
                        "priority": o.priority_score,
                    }
                    for o in engine.get_upcoming_opportunities(90)[:10]
                ],
                "stats": engine.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/learner/params")
async def learner_params() -> Dict:
    """Paramètres de chasse optimisés par l'apprentissage continu."""
    def _collect():
        try:
            from EVOLUTION_SYSTEM.autonomous_learner import get_learner
            learner = get_learner()
            params = learner.get_optimized_hunt_params()
            return {
                "params": {
                    "version": params.version,
                    "min_ticket_eur": params.min_ticket_eur,
                    "target_ticket_eur": params.target_ticket_eur,
                    "top_sectors": params.top_sectors,
                    "top_signal_types": params.top_signal_types,
                    "preferred_tiers": params.preferred_tiers,
                    "min_quality_score": params.min_quality_score,
                    "quality_multiplier": params.quality_multiplier,
                    "based_on_n_deals": params.based_on_n_deals,
                },
                "summary": learner.get_learning_summary(),
                "sector_ranking": learner.get_sector_ranking(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/deals/risk")
async def deals_risk() -> Dict:
    """Dashboard de risque des deals en cours."""
    def _collect():
        try:
            from NAYA_CORE.deal_risk_scorer import get_deal_risk_scorer
            return get_deal_risk_scorer().get_dashboard()
        except Exception as e:
            return {"error": str(e)[:120]}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.post("/evolution/run")
async def run_evolution_cycle() -> Dict:
    """Déclenche manuellement un cycle d'évolution (via TORI_APP ou Telegram)."""
    def _run():
        try:
            from EVOLUTION_SYSTEM.evolution_orchestrator import get_evolution_orchestrator
            cycle = get_evolution_orchestrator().run()
            return {
                "cycle_id": cycle.cycle_id,
                "status": cycle.status,
                "proposals_applied": cycle.proposals_applied,
                "slots_before": cycle.slots_before,
                "slots_after": cycle.slots_after,
                "duration_s": cycle.duration_s,
                "summary": cycle.summary,
            }
        except Exception as e:
            return {"error": str(e)[:120]}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)
