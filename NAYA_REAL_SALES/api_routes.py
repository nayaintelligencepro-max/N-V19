"""
NAYA REAL SALES — API Routes FastAPI
═══════════════════════════════════════════════════════════════
Routes API pour gérer les ventes réelles et le challenge 10 jours.
- POST /sales/create : Créer une vente
- POST /webhook/payment/{provider} : Webhooks paiements
- GET /challenge/status : Status du challenge
- GET /sales/stats : Statistiques ventes
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field

from .real_sales_engine import get_real_sales_engine
from .ten_day_challenge import get_ten_day_challenge
from .payment_validator import get_payment_validator

log = logging.getLogger("NAYA.REAL_SALES_API")

router = APIRouter(prefix="/api/v1", tags=["real_sales"])


# ── Request Models ────────────────────────────────────────────────────────────


class CreateSaleRequest(BaseModel):
    """Request pour créer une vente."""
    company: str = Field(..., description="Nom de l'entreprise cliente")
    sector: str = Field(..., description="Secteur (energie, transport, manufacturing)")
    amount_eur: int = Field(..., ge=1000, description="Montant en EUR (≥ 1000)")
    service_type: str = Field(..., description="Type de service (audit, consulting, saas)")
    payment_provider: str = Field(..., description="Provider (paypal, deblock)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SaleResponse(BaseModel):
    """Response après création de vente."""
    sale_id: str
    company: str
    amount_eur: int
    payment_status: str
    payment_url: Optional[str]
    message: str


# ── Sales Endpoints ───────────────────────────────────────────────────────────


@router.post("/sales/create", response_model=SaleResponse)
async def create_sale(request: CreateSaleRequest) -> SaleResponse:
    """
    Crée une nouvelle vente avec paiement en attente.

    La vente sera comptée dans les stats uniquement après confirmation paiement
    via webhook /webhook/payment/{provider}.
    """
    try:
        engine = get_real_sales_engine()

        sale = engine.create_sale_from_api(
            company=request.company,
            sector=request.sector,
            amount_eur=request.amount_eur,
            service_type=request.service_type,
            payment_provider=request.payment_provider,
            metadata=request.metadata,
        )

        # Générer le lien de paiement selon le provider
        payment_url = _generate_payment_url(
            provider=request.payment_provider,
            sale_id=sale.sale_id,
            amount_eur=request.amount_eur,
            company=request.company,
        )

        # Notifier sur Telegram
        try:
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
            bot = get_telegram_bot_v2()
            bot._send_alert(
                f"📝 NOUVELLE VENTE CRÉÉE\n"
                f"ID: {sale.sale_id}\n"
                f"Client: {request.company}\n"
                f"Secteur: {request.sector}\n"
                f"Montant: {request.amount_eur:,} EUR\n"
                f"Provider: {request.payment_provider}\n"
                f"→ En attente de paiement"
            )
        except Exception as e:
            log.warning("Telegram notification failed: %s", e)

        return SaleResponse(
            sale_id=sale.sale_id,
            company=sale.company,
            amount_eur=sale.amount_eur,
            payment_status=sale.payment_status,
            payment_url=payment_url,
            message=f"Vente créée. Paiement en attente via {request.payment_provider}.",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("Create sale error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.get("/sales/stats")
async def get_sales_stats() -> Dict[str, Any]:
    """
    Statistiques des ventes réelles.
    Seules les ventes avec paiement confirmé sont comptabilisées.
    """
    try:
        engine = get_real_sales_engine()
        stats = engine.get_stats()
        return stats
    except Exception as e:
        log.error("Get stats error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


# ── Webhook Endpoints ─────────────────────────────────────────────────────────


@router.post("/webhook/payment/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
) -> Dict[str, str]:
    """
    Webhook de confirmation de paiement.

    Providers supportés (V19.3 — Polynésie française):
    - paypal : signature HMAC-SHA256 dans header X-Signature
    - deblock : signature HMAC-SHA256 dans header X-Signature

    Payload doit contenir:
    - sale_id : ID de la vente
    - status : "completed" ou "failed"
    """
    try:
        body = await request.body()
        payload = await request.json()

        # Valider la signature selon le provider
        validator = get_payment_validator()

        is_valid = False
        if provider == "paypal":
            is_valid = validator.validate_paypal_webhook(payload, x_signature or "")
        elif provider == "deblock":
            is_valid = validator.validate_deblock_webhook(payload, x_signature or "")
        else:
            raise HTTPException(status_code=400, detail=f"Provider inconnu: {provider}")

        if not is_valid:
            log.warning("Invalid webhook signature from %s", provider)
            raise HTTPException(status_code=401, detail="Signature invalide")

        # Extraire sale_id du payload
        sale_id = None
        if provider == "paypal":
            sale_id = validator.extract_sale_id_from_paypal(payload)
        elif provider == "deblock":
            sale_id = validator.extract_sale_id_from_deblock(payload)

        if not sale_id:
            raise HTTPException(status_code=400, detail="sale_id manquant dans payload")

        # Confirmer le paiement
        engine = get_real_sales_engine()
        success = engine.confirm_payment(
            sale_id=sale_id,
            source="webhook",
            provider=provider,
            webhook_verified=True,
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Vente {sale_id} introuvable")

        # Récupérer la vente confirmée
        sale = next((s for s in engine.sales if s.sale_id == sale_id), None)
        if not sale:
            raise HTTPException(status_code=404, detail=f"Vente {sale_id} introuvable")

        # Notification Telegram
        try:
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
            bot = get_telegram_bot_v2()
            bot._send_alert(
                f"💰 PAIEMENT CONFIRMÉ\n"
                f"ID: {sale_id}\n"
                f"Client: {sale.company}\n"
                f"Secteur: {sale.sector}\n"
                f"Montant: {sale.amount_eur:,} EUR\n"
                f"Provider: {provider}\n"
                f"→ Vente VALIDÉE dans le ledger"
            )
        except Exception as e:
            log.warning("Telegram notification failed: %s", e)

        log.info("Payment confirmed: sale_id=%s, provider=%s, amount=%d EUR",
                 sale_id, provider, sale.amount_eur)

        return {
            "status": "success",
            "sale_id": sale_id,
            "message": "Paiement confirmé",
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error("Webhook error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


# ── Challenge Endpoints ───────────────────────────────────────────────────────


@router.get("/challenge/status")
async def get_challenge_status() -> Dict[str, Any]:
    """
    Status en temps réel du challenge 10 ventes / 10 jours.
    """
    try:
        challenge = get_ten_day_challenge()
        current_day = challenge.get_current_day()
        stats = challenge.get_stats()

        if not current_day:
            return {
                "status": "inactive",
                "message": "Challenge terminé ou non démarré",
                "stats": stats,
            }

        engine = get_real_sales_engine()
        confirmed = engine.get_confirmed_sales()
        pending = [s for s in engine.sales if s.payment_status == "pending"]

        total_confirmed_revenue = sum(s.amount_eur for s in confirmed)
        total_pending_revenue = sum(s.amount_eur for s in pending)

        progress_pct = (total_confirmed_revenue / stats['total_target_eur']) * 100 if stats['total_target_eur'] > 0 else 0

        return {
            "status": "active",
            "current_day": current_day.day_number,
            "current_day_focus": current_day.focus,
            "current_day_target_eur": current_day.target_eur,
            "confirmed_sales": len(confirmed),
            "confirmed_revenue_eur": total_confirmed_revenue,
            "pending_sales": len(pending),
            "pending_revenue_eur": total_pending_revenue,
            "total_target_eur": stats['total_target_eur'],
            "progress_pct": round(progress_pct, 2),
            "days_remaining": 10 - current_day.day_number,
            "recommended_actions": current_day.recommended_actions,
            "day_target_met": total_confirmed_revenue >= current_day.target_eur,
        }

    except Exception as e:
        log.error("Challenge status error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


# ── Internal Helpers ──────────────────────────────────────────────────────────


def _generate_payment_url(
    provider: str,
    sale_id: str,
    amount_eur: int,
    company: str,
) -> str:
    """Génère le lien de paiement selon le provider."""
    import os

    if provider == "paypal":
        # PayPal.me simple link
        paypal_username = os.getenv("PAYPALME_USERNAME", "nayasupreme")
        return f"https://www.paypal.me/{paypal_username}/{amount_eur}EUR?note={sale_id}"

    elif provider == "deblock":
        # Deblok.me Polynésie française
        deblock_url = os.getenv("DEBLOKME_PAYMENT_URL", "https://pay.deblok.me")
        return f"{deblock_url}?amount={amount_eur}&currency=EUR&ref={sale_id}"

    else:
        return f"#payment-{provider}-{sale_id}"
