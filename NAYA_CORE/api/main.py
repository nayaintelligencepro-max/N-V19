"""
NAYA SUPREME V19.2 — FastAPI Main Application
Point d'entrée HTTP : tous les routers, middleware, health, CORS.
Commande : uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port 8000
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("NAYA.API")

# ── Startup / Shutdown ────────────────────────────────────────────────────────
_startup_time: float = 0.0


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialise les composants critiques au démarrage."""
    global _startup_time
    _startup_time = time.time()
    log.info("🚀  NAYA SUPREME V19 — démarrage API")

    # Chargement des secrets
    try:
        from SECRETS.secrets_loader import load_all_secrets
        load_all_secrets()
        log.info("✅  Secrets chargés")
    except Exception as exc:
        log.warning(f"⚠️  Secrets non chargés : {exc}")

    # Initialisation DB SQLite (légère, pas besoin de Postgres en local)
    try:
        from PERSISTENCE.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.initialize()
        log.info("✅  Base de données initialisée")
    except Exception as exc:
        log.warning(f"⚠️  DB init partielle : {exc}")

    # Lancement du guardian autonome (optionnel)
    try:
        if os.getenv("ENABLE_GUARDIAN", "true").lower() == "true":
            from naya_guardian.guardian import get_guardian
            guardian = get_guardian()
            guardian.check()
            log.info("✅  Guardian actif")
    except Exception as _guardian_exc:
        log.warning("⚠️  Guardian non disponible (optionnel): %s", _guardian_exc)

    yield  # ── Application running ──

    log.info("🛑  NAYA SUPREME V19.3 — arrêt API")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NAYA SUPREME V19.3",
    description="Système IA autonome de génération de revenue — 11 agents | SaaS NIS2 | Pipeline < 4h",
    version="19.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate-limiter middleware ────────────────────────────────────────────────────
try:
    from api.middleware import RateLimiterMiddleware
    app.add_middleware(RateLimiterMiddleware)
    log.info("✅  Rate-limiter actif")
except Exception as exc:
    log.warning(f"Rate-limiter non chargé : {exc}")

# ── Routers ───────────────────────────────────────────────────────────────────
_routers: list[tuple[str, str, str]] = [
    ("api.routers.system",        "router", "/api/v1"),
    ("api.routers.brain",         "router", "/api/v1/brain"),
    ("api.routers.revenue",       "router", "/api/v1/revenue"),
    ("api.routers.revenue_routes","router", "/api/v1/revenue"),
    ("api.routers.hunt_routes",   "router", "/api/v1/hunt"),
    ("api.routers.business",      "router", "/api/v1/business"),
    ("api.routers.integrations",  "router", "/api/v1/integrations"),
    ("api.routers.evolution",     "router", "/api/v1/evolution"),
    ("api.routers.v20",           "router", "/api/v1/v20"),
    ("api.routers.acceleration",  "router", "/api/v1/acceleration"),
    ("api.routers.saas",          "router", "/api/v1"),
]

for module_path, attr, prefix in _routers:
    try:
        import importlib
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        app.include_router(router, prefix=prefix)
        log.info(f"✅  Router {module_path} → {prefix}")
    except Exception as exc:
        log.warning(f"⚠️  Router {module_path} ignoré : {exc}")


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    return {
        "name": "NAYA SUPREME V19.2",
        "status": "operational",
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)[:200]},
    )


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "NAYA_CORE.api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        workers=1 if os.getenv("ENVIRONMENT", "production") == "development" else int(os.getenv("API_WORKERS", "2")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
