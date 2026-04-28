"""
NAYA REAL SALES — Point d'Entrée Principal
═══════════════════════════════════════════════════════════════
Lance le système complet de ventes réelles :
1. API FastAPI avec routes /sales et /webhook
2. Scheduler autonome pour exécution automatique
3. Challenge 10 ventes / 10 jours
4. Notifications Telegram temps réel
5. Décision autonome post-challenge
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes import router as sales_router
from .ten_day_challenge import get_ten_day_challenge
from .autonomous_sales_scheduler import get_autonomous_sales_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("NAYA.REAL_SALES_MAIN")


# ── Background Tasks ──────────────────────────────────────────────────────────


async def start_autonomous_scheduler():
    """Démarre le scheduler autonome en arrière-plan."""
    try:
        scheduler = get_autonomous_sales_scheduler()
        log.info("🚀 Starting autonomous sales scheduler...")
        await scheduler.start()
    except Exception as e:
        log.error("Failed to start scheduler: %s", e, exc_info=True)


async def initialize_challenge():
    """Initialise le challenge 10 jours si pas déjà actif."""
    try:
        challenge = get_ten_day_challenge()
        current_day = challenge.get_current_day()

        if current_day:
            log.info("✅ Challenge already active — Day %d/10", current_day.day_number)
        else:
            log.info("🎯 Challenge not active — will start when first sale created")

        stats = challenge.get_stats()
        log.info("Challenge stats: %s", stats)

    except Exception as e:
        log.error("Challenge initialization error: %s", e, exc_info=True)


# ── FastAPI Lifespan ──────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager : démarre les services au boot, les arrête au shutdown.
    """
    # Startup
    log.info("=" * 80)
    log.info("NAYA REAL SALES — PRODUCTION SYSTEM STARTING")
    log.info("=" * 80)

    # Initialiser le challenge
    await initialize_challenge()

    # Démarrer le scheduler autonome
    scheduler_task = asyncio.create_task(start_autonomous_scheduler())

    # Notification Telegram
    try:
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        bot._send_alert(
            "🚀 NAYA REAL SALES — SYSTEM ONLINE\n\n"
            "✅ API routes actives\n"
            "✅ Webhook paiements actifs\n"
            "✅ Scheduler autonome actif\n"
            "✅ Challenge 10 ventes / 10 jours actif\n\n"
            "Commandes disponibles :\n"
            "/challenge → Dashboard temps réel\n"
            "/status → État global système\n"
            "/velocity → Métriques ventes\n"
            "/ooda → Prochaine action recommandée"
        )
    except Exception as e:
        log.warning("Telegram notification failed: %s", e)

    log.info("✅ System fully operational")
    log.info("=" * 80)

    yield

    # Shutdown
    log.info("🛑 Shutting down NAYA REAL SALES system...")
    scheduler = get_autonomous_sales_scheduler()
    await scheduler.stop()
    scheduler_task.cancel()
    log.info("✅ Shutdown complete")


# ── FastAPI App ───────────────────────────────────────────────────────────────


app = FastAPI(
    title="NAYA REAL SALES API",
    description="Système de ventes réelles production-ready avec challenge 10 jours autonome",
    version="19.0.0",
    lifespan=lifespan,
)

# CORS pour TORI_APP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production : limiter aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(sales_router)


@app.get("/")
async def root():
    """Root endpoint : status système."""
    try:
        from .ten_day_challenge import get_ten_day_challenge
        from .real_sales_engine import get_real_sales_engine

        challenge = get_ten_day_challenge()
        engine = get_real_sales_engine()

        current_day = challenge.get_current_day()
        stats = engine.get_stats()

        return {
            "status": "online",
            "system": "NAYA REAL SALES v19.0.0",
            "challenge_active": current_day is not None,
            "challenge_day": current_day.day_number if current_day else None,
            "total_confirmed_sales": stats["confirmed_sales"],
            "total_confirmed_revenue_eur": stats["revenue_confirmed_eur"],
            "endpoints": {
                "create_sale": "POST /api/v1/sales/create",
                "sales_stats": "GET /api/v1/sales/stats",
                "challenge_status": "GET /api/v1/challenge/status",
                "webhook_paypal": "POST /api/v1/webhook/payment/paypal",
                "webhook_deblock": "POST /api/v1/webhook/payment/deblock",
            },
        }
    except Exception as e:
        log.error("Root endpoint error: %s", e, exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/health")
async def health():
    """Health check endpoint pour Railway/Render."""
    return {"status": "healthy", "system": "NAYA REAL SALES"}


# ── Entry Point ───────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn

    # Démarrer le serveur
    uvicorn.run(
        "NAYA_REAL_SALES.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Production : pas de reload
        log_level="info",
    )
