"""NAYA V19 — System API Router — Production Ready"""
import asyncio
import os, sys, time
from datetime import datetime, timezone
from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/health")
async def system_health() -> Dict:
    try:
        import resource
        mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        mem_mb = 0
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "14.0.0",
        "pid": os.getpid(),
        "memory_mb": round(mem_mb, 1),
        "python": sys.version.split()[0],
    }


@router.get("/modules")
async def list_modules() -> Dict:
    checks = [
        ("intention_loop", "naya_intention_loop.intention_loop", "get_intention_loop"),
        ("narrative_memory", "naya_memory_narrative.narrative_memory", "get_narrative_memory"),
        ("self_diagnostic", "naya_self_diagnostic.diagnostic", "get_diagnostic"),
        ("guardian", "naya_guardian.guardian", "get_guardian"),
        ("pipeline", "NAYA_CORE.real_pipeline_orchestrator", "get_pipeline"),
        ("hunt_seeder", "NAYA_CORE.hunt.auto_hunt_seeder", "get_seeder"),
        ("contact_enricher", "NAYA_CORE.enrichment.contact_enricher", "get_contact_enricher"),
    ]

    def _load_modules():
        modules = {}
        for name, mod_path, getter in checks:
            try:
                mod = __import__(mod_path, fromlist=[getter])
                fn = getattr(mod, getter)
                inst = fn()
                stats = inst.get_stats() if hasattr(inst, "get_stats") else {"loaded": True}
                modules[name] = {"status": "active", "stats": stats}
            except Exception as e:
                modules[name] = {"status": "error", "error": str(e)[:80]}
        return modules

    loop = asyncio.get_event_loop()
    modules = await loop.run_in_executor(None, _load_modules)
    return {"modules": modules, "total": len(modules),
            "active": sum(1 for m in modules.values() if m["status"] == "active")}

@router.get("/secrets")
async def secrets_status() -> Dict:
    try:
        from SECRETS.secrets_loader import get_status
        return get_status()
    except Exception as e:
        return {"error": str(e)[:100]}


@router.get("/config")
async def system_config() -> Dict:
    return {
        "env": os.getenv("NAYA_ENV", "local"),
        "port": int(os.getenv("PORT", "8080")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "auto_outreach": os.getenv("NAYA_AUTO_OUTREACH", "false"),
        "hunt_interval_s": int(os.getenv("NAYA_AUTO_HUNT_INTERVAL_SECONDS", "3600")),
        "guardian_threshold_h": float(os.getenv("NAYA_GUARDIAN_THRESHOLD_H", "72")),
    }
