"""
NAYA API — /api/v1/acceleration
Routes pour le pipeline ultra-rapide V21 :
- BlitzHunter : chasse 5 sources async < 30s
- FlashOffer : offre personnalisée < 60s
- InstantCloser : lien paiement < 5min
- SalesVelocity : métriques ventes réelles
- AccelerationOrchestrator : pipeline complet < 4h
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("NAYA.API.ACCELERATION")

router = APIRouter(tags=["acceleration"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class HuntRequest(BaseModel):
    sectors: Optional[List[str]] = Field(
        default=None,
        json_schema_extra={"example": ["energie", "transport_logistique", "manufacturing", "iec62443"]},
    )


class FlashOfferRequest(BaseModel):
    company: str = Field(..., json_schema_extra={"example": "SNCF Voyageurs"})
    sector: str = Field(..., json_schema_extra={"example": "transport_logistique"})
    pain_description: str = Field(..., json_schema_extra={"example": "Audit NIS2 requis avant Q3 2026 sur réseau SCADA"})
    contact_name: str = Field(default="", json_schema_extra={"example": "Jean-Pierre MARTIN"})
    contact_title: str = Field(default="", json_schema_extra={"example": "RSSI"})
    budget_estimate_eur: int = Field(default=15_000, ge=1_000)
    urgency: str = Field(default="high", pattern="^(low|medium|high|critical)$")


class PaymentLinkRequest(BaseModel):
    offer_id: str
    company: str
    contact_email: str
    amount_eur: int = Field(..., ge=1_000)
    method: str = Field(default="paypal", pattern="^(paypal|deblok|bank_transfer)$")


class SaleRecordRequest(BaseModel):
    company: str
    amount_eur: int = Field(..., ge=1_000)
    sector: str
    pain_type: str
    contact_email: str = ""
    payment_method: str = "paypal"
    time_to_close_hours: float = 0.0
    signal_source: str = "blitz_hunter"


class AccelerationCycleRequest(BaseModel):
    sectors: Optional[List[str]] = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/hunt", summary="BlitzHunter — 5 sources async < 30s")
async def blitz_hunt(req: HuntRequest):
    """Lance la chasse BlitzHunter en parallèle sur 5 sources."""
    try:
        from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
        hunter = get_blitz_hunter()
        signals = await hunter.hunt(sectors=req.sectors)
        return {
            "status": "ok",
            "signals_count": len(signals),
            "signals": [s.to_dict() for s in signals],
        }
    except Exception as exc:
        logger.error(f"BlitzHunt error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/offer", summary="FlashOffer — offre personnalisée < 60s")
async def flash_offer(req: FlashOfferRequest):
    """Génère une offre ultra-personnalisée en < 60 secondes."""
    try:
        from NAYA_ACCELERATION.flash_offer import get_flash_offer
        generator = get_flash_offer()
        offer = await generator.generate(
            company=req.company,
            sector=req.sector,
            pain_description=req.pain_description,
            contact_name=req.contact_name,
            contact_title=req.contact_title,
            budget_estimate=req.budget_estimate_eur,
            urgency=req.urgency,
        )
        return {"status": "ok", "offer": offer.to_dict()}
    except Exception as exc:
        logger.error(f"FlashOffer error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/payment-link", summary="InstantCloser — lien paiement < 5min")
def generate_payment_link(req: PaymentLinkRequest):
    """Génère instantanément un lien de paiement."""
    try:
        from NAYA_ACCELERATION.instant_closer import get_instant_closer, PaymentMethod
        closer = get_instant_closer()
        pm = PaymentMethod(req.method)
        link = closer.generate_payment_link(
            offer_id=req.offer_id,
            company=req.company,
            contact_email=req.contact_email,
            amount_eur=req.amount_eur,
            method=pm,
        )
        return {"status": "ok", "payment_link": link.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"PaymentLink error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/payment/{payment_id}/confirm", summary="Confirme paiement encaissé")
def confirm_payment(payment_id: str):
    """Marque un paiement comme reçu et notifie Telegram."""
    try:
        from NAYA_ACCELERATION.instant_closer import get_instant_closer
        closer = get_instant_closer()
        found = closer.confirm_payment(payment_id)
        if not found:
            raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
        return {"status": "ok", "payment_id": payment_id, "confirmed": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/payments/pending", summary="Liste des paiements en attente")
def get_pending_payments():
    """Retourne tous les liens de paiement en attente de confirmation."""
    from NAYA_ACCELERATION.instant_closer import get_instant_closer
    closer = get_instant_closer()
    pending = closer.get_pending_payments()
    return {"status": "ok", "count": len(pending), "payments": pending}


@router.post("/sale", summary="Enregistre une vente réelle encaissée")
def record_sale(req: SaleRecordRequest):
    """Enregistre une vente réelle et met à jour les métriques velocity."""
    try:
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        tracker = get_velocity_tracker()
        record = tracker.record_sale(
            company=req.company,
            amount_eur=req.amount_eur,
            sector=req.sector,
            pain_type=req.pain_type,
            contact_email=req.contact_email,
            payment_method=req.payment_method,
            time_to_close_hours=req.time_to_close_hours,
            signal_source=req.signal_source,
        )
        return {"status": "ok", "sale": record.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/velocity", summary="Métriques velocity : ventes jour/mois/an + projections")
def get_velocity(prospects_count: int = Query(default=0, ge=0)):
    """Retourne les KPIs de vélocité commerciale."""
    from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
    tracker = get_velocity_tracker()
    metrics = tracker.get_metrics(prospects_count=prospects_count)
    return {"status": "ok", "metrics": metrics.to_dict()}


@router.get("/velocity/sales", summary="Liste ventes par période")
def get_sales_by_period(period: str = Query(default="month", pattern="^(today|week|month|year)$")):
    """Retourne les ventes pour today | week | month | year."""
    from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
    tracker = get_velocity_tracker()
    sales = tracker.get_sales_by_period(period)
    total = sum(s.get("amount_eur", 0) for s in sales)
    return {"status": "ok", "period": period, "count": len(sales), "total_eur": total, "sales": sales}


@router.post("/run", summary="Pipeline complet < 4h : Hunt → Offer → Payment")
async def run_acceleration_cycle(req: AccelerationCycleRequest):
    """Lance le cycle d'accélération complet (hunt + offres + liens paiement)."""
    try:
        from NAYA_ACCELERATION.acceleration_orchestrator import get_orchestrator
        orch = get_orchestrator()
        result = await orch.run_acceleration_cycle(sectors=req.sectors)
        return {"status": "ok", "pipeline": result.to_dict()}
    except Exception as exc:
        logger.error(f"AccelerationCycle error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard", summary="Dashboard accélération : pipeline + velocity + signaux")
async def get_acceleration_dashboard():
    """Vue complète : métriques velocity + statut pipeline."""
    from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
    from NAYA_ACCELERATION.instant_closer import get_instant_closer
    tracker = get_velocity_tracker()
    closer = get_instant_closer()
    metrics = tracker.get_metrics()
    pending = closer.get_pending_payments()
    return {
        "status": "ok",
        "velocity": metrics.to_dict(),
        "pending_payments_count": len(pending),
        "pending_value_eur": sum(p.get("amount_eur", 0) for p in pending),
        "target_pipeline_hours": 4.0,
        "ooda": metrics.ooda_recommendation,
    }
