"""NAYA V19 — Brain API Router — Production Ready"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/intention")
async def intention_status() -> Dict:
    try:
        from naya_intention_loop.intention_loop import get_intention_loop
        loop = get_intention_loop()
        return loop.get_stats()
    except Exception as e:
        return {"error": str(e)[:100]}


@router.post("/intention/evaluate")
async def evaluate_intention() -> Dict:
    """Force une évaluation d'intention immédiate."""
    try:
        from naya_intention_loop.intention_loop import get_intention_loop
        import time
        loop = get_intention_loop()
        status = {
            "seconds_since_hunt": time.time() - loop._last_hunt,
            "seconds_since_evolve": time.time() - loop._last_evolve,
            "hunt_interval": loop.hunt_interval,
        }
        decision = loop.evaluate(status)
        return {
            "intent": decision.intent.value,
            "reason": decision.reason,
            "urgency": decision.urgency,
        }
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/memory")
async def narrative_memory() -> Dict:
    try:
        from naya_memory_narrative.narrative_memory import get_narrative_memory
        mem = get_narrative_memory()
        return mem.get_stats()
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/diagnostic")
async def full_diagnostic() -> Dict:
    try:
        from naya_self_diagnostic.diagnostic import get_diagnostic
        diag = get_diagnostic()
        return diag.run()
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/guardian")
async def guardian_status() -> Dict:
    try:
        from naya_guardian.guardian import get_guardian
        g = get_guardian()
        g.check()
        return {**g.status, "enforcement": g.enforce()}
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/llm/status")
async def llm_status() -> Dict:
    """Statut des providers LLM disponibles."""
    try:
        from SECRETS.secrets_loader import is_configured
        providers = {
            "groq": is_configured("GROQ_API_KEY"),
            "deepseek": is_configured("DEEPSEEK_API_KEY"),
            "anthropic": is_configured("ANTHROPIC_API_KEY"),
            "openai": is_configured("OPENAI_API_KEY"),
            "huggingface": is_configured("HUGGINGFACE_API_KEY") or is_configured("HF_API_KEY"),
        }
        active = [k for k, v in providers.items() if v]
        return {
            "providers": providers,
            "active_count": len(active),
            "primary": active[0] if active else "none",
            "fallback_chain": active,
        }
    except Exception as e:
        return {"error": str(e)[:100]}
