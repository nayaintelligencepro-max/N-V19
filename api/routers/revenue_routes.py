"""
NAYA V19 — Revenue API Routes
Endpoints: /revenue/dashboard, /revenue/record, /deblock/pay, /paypal/pay
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/revenue", tags=["Revenue V19"])


class RecordPaymentRequest(BaseModel):
    amount: float
    source: str = "cash_rapide"
    client: str = ""
    method: str = "paypal"  # paypal / deblock
    note: str = ""


class GenerateLinkRequest(BaseModel):
    amount: float
    description: str
    prospect_name: str = ""
    method: str = "paypal"  # paypal / deblock


@router.get("/dashboard")
async def revenue_dashboard():
    """Dashboard temps réel — euros semaine/mois, milestones, pipeline."""
    try:
        from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
        from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
        from NAYA_REVENUE_ENGINE.payment_tracker import PaymentTracker

        tracker_data = get_tracker().dashboard()
        deblock_data = get_deblock().dashboard()

        return {
            "status": "ok",
            "version": "V19",
            "revenue": tracker_data,
            "deblock": deblock_data,
            "targets": {
                "week_target_eur": 1200,
                "month_1_target_eur": 5000,
                "month_3_target_eur": 15000,
                "month_6_target_eur": 30000,
                "month_9_target_eur": 60000,
            }
        }
    except Exception as e:
        return {"status": "partial", "error": str(e)}


@router.post("/record")
async def record_payment(req: RecordPaymentRequest):
    """Enregistre un paiement reçu."""
    from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
    eid = get_tracker().record(
        amount=req.amount, source=req.source,
        client=req.client, method=req.method, note=req.note
    )
    return {"status": "recorded", "entry_id": eid, "amount": req.amount}


@router.post("/generate-link")
async def generate_payment_link(req: GenerateLinkRequest):
    """Génère un lien de paiement PayPal.me ou Deblock.me."""
    if req.method == "deblock":
        from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
        result = get_deblock().generate_link(req.amount, req.description, req.prospect_name)
        return {"status": "ok", "method": "deblock", **result}
    else:
        # PayPal.me link
        import os
        base = os.environ.get("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
        safe = req.description.replace(" ", "%20")[:80]
        link = f"{base}/{req.amount:.2f}EUR?note={safe}"
        return {"status": "ok", "method": "paypal", "link": link, "amount": req.amount}


@router.post("/deblock/confirm/{payment_id}")
async def confirm_deblock_payment(payment_id: str, amount: Optional[float] = None):
    """Confirme la réception d'un paiement Deblock."""
    from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
    ok = get_deblock().mark_paid(payment_id, amount)
    if not ok:
        raise HTTPException(404, f"Payment {payment_id} not found")
    if amount:
        from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
        get_tracker().record(amount, "deblock", method="deblock")
    return {"status": "confirmed", "payment_id": payment_id}


@router.get("/pending")
async def get_pending_payments():
    """Liste les paiements en attente."""
    from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
    pending = get_deblock().get_pending()
    overdue = get_deblock().get_overdue()
    return {
        "pending": [vars(p) for p in pending],
        "overdue": [vars(p) for p in overdue],
        "total_pending": len(pending),
        "total_overdue": len(overdue),
    }
