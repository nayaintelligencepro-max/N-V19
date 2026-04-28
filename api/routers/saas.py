"""
NAYA API — /api/v1/saas
Routes SaaS : NIS2 Checker, IEC 62443 Portal, API Marketplace, Subscriptions.
Revenus récurrents MRR : objectif 10 000 EUR/mois à M6.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger("NAYA.API.SAAS")

router = APIRouter(tags=["saas"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class NIS2AssessmentRequest(BaseModel):
    company: str = Field(..., json_schema_extra={"example": "Enedis"})
    sector: str = Field(..., json_schema_extra={"example": "energie_utilities"})
    contact_email: str = Field(..., json_schema_extra={"example": "rssi@enedis.fr"})
    answers: Dict[str, bool] = Field(
        ...,
        json_schema_extra={"example": {"Q01": True, "Q02": False, "Q03": True}},
    )
    freemium: bool = Field(default=True, description="True = score seul, False = rapport complet")


class IEC62443AnalysisRequest(BaseModel):
    company: str
    sector: str
    contact_email: str
    responses: Dict[str, str] = Field(
        ...,
        description="Mapping {requirement_id: 'compliant'|'partial'|'missing'}",
        json_schema_extra={"example": {"SL1-01": "compliant", "SL1-02": "partial"}},
    )


class SubscriptionRequest(BaseModel):
    company: str
    contact_email: str
    plan: str = Field(..., json_schema_extra={"example": "nis2_starter"})
    payment_method: str = Field(default="paypal", pattern="^(deblok|paypal)$")


class PaymentWebhookRequest(BaseModel):
    subscription_id: str
    event: str  # payment_succeeded|payment_failed
    amount_eur: int


class MeetingBookRequest(BaseModel):
    prospect_id: str
    company: str
    contact_name: str
    contact_email: str
    sector: str
    deal_value_eur: int = Field(default=15_000, ge=1_000)
    context: str = Field(default="")


class PostCallRequest(BaseModel):
    meeting_id: str
    summary: str
    next_steps: List[str]
    outcome: str = Field(default="positive", pattern="^(positive|neutral|negative)$")


# ── NIS2 Checker ──────────────────────────────────────────────────────────────

@router.get("/saas/nis2/questions")
async def get_nis2_questions():
    """Retourne les 20 questions NIS2."""
    try:
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        checker = get_nis2_checker()
        questions = checker.get_questions()
        return {
            "count": len(questions),
            "questions": [
                {
                    "id": q.id,
                    "category": q.category,
                    "weight": q.weight,
                    "text": q.text,
                    "yes_label": q.yes_label,
                    "no_label": q.no_label,
                    "guidance": q.guidance,
                }
                for q in questions
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/nis2/assess")
async def create_nis2_assessment(req: NIS2AssessmentRequest):
    """Crée un assessment NIS2 et retourne le score de conformité."""
    try:
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        checker = get_nis2_checker()
        assessment = checker.create_assessment(
            company=req.company,
            sector=req.sector,
            contact_email=req.contact_email,
            answers=req.answers,
            freemium=req.freemium,
        )
        result = {
            "assessment_id": assessment.assessment_id,
            "company": assessment.company,
            "score": assessment.score,
            "tier": assessment.tier,
            "freemium": assessment.freemium,
            "gaps_preview": assessment.gaps[:3],
        }
        if not assessment.freemium:
            result["gaps"] = assessment.gaps
            result["recommendations"] = assessment.recommendations
            # Générer rapport PDF
            try:
                from SAAS_NIS2.report_generator import get_report_generator
                gen = get_report_generator()
                report_path = gen.generate(assessment)
                result["report_path"] = report_path
            except Exception as exc:
                logger.warning("Rapport PDF non généré: %s", exc)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/nis2/assessment/{assessment_id}")
async def get_nis2_assessment(assessment_id: str):
    try:
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        assessment = get_nis2_checker().get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment non trouvé")
        return assessment.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/nis2/stats")
async def get_nis2_stats():
    try:
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        return get_nis2_checker().get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── IEC 62443 Portal ──────────────────────────────────────────────────────────

@router.get("/saas/iec62443/requirements")
async def get_iec62443_requirements():
    """Retourne les exigences IEC 62443 par niveau SL1-SL4."""
    try:
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        return get_iec62443_portal().get_requirements()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/iec62443/analyze")
async def analyze_iec62443_compliance(req: IEC62443AnalysisRequest):
    """Analyse la conformité IEC 62443 et génère un rapport avec roadmap."""
    try:
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        portal = get_iec62443_portal()
        report = portal.analyze_compliance(
            company=req.company,
            sector=req.sector,
            contact_email=req.contact_email,
            responses=req.responses,
        )
        return {
            "report_id": report.report_id,
            "company": report.company,
            "overall_score": report.overall_score,
            "compliance_scores": report.compliance_scores,
            "gaps_count": len(report.gaps),
            "roadmap": report.roadmap,
            "estimated_remediation_eur": report.estimated_remediation_eur,
            "upsell_proposal": report.upsell_proposal,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/iec62443/report/{report_id}")
async def get_iec62443_report(report_id: str):
    try:
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        report = get_iec62443_portal().get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Rapport non trouvé")
        return report.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Subscription Manager ──────────────────────────────────────────────────────

@router.get("/saas/plans")
async def get_plans():
    """Retourne les plans d'abonnement disponibles."""
    try:
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        return get_subscription_manager().get_plans()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/subscribe")
async def create_subscription(req: SubscriptionRequest):
    """Crée un abonnement SaaS."""
    try:
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        sub = mgr.create_subscription(
            company=req.company,
            contact_email=req.contact_email,
            plan=req.plan,
            payment_method=req.payment_method,
        )
        return {
            "subscription_id": sub.subscription_id,
            "company": sub.company,
            "plan": sub.plan,
            "price_eur": sub.price_eur,
            "status": sub.status,
            "payment_required": sub.price_eur > 0,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/webhook/payment")
async def payment_webhook(req: PaymentWebhookRequest):
    """Webhook PayPal/Deblock pour confirmation paiement abonnement."""
    try:
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        return get_subscription_manager().handle_payment_webhook(
            subscription_id=req.subscription_id,
            event=req.event,
            amount_eur=req.amount_eur,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/mrr")
async def get_mrr():
    """MRR (Monthly Recurring Revenue) temps réel."""
    try:
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        return get_subscription_manager().get_mrr()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Meeting Booker ────────────────────────────────────────────────────────────

@router.post("/saas/meeting/book")
async def book_meeting(req: MeetingBookRequest):
    """Crée un lien de réservation Calendly personnalisé."""
    try:
        from OUTREACH.meeting_booker import get_meeting_booker
        booker = get_meeting_booker()
        meeting = booker.create_booking_link(
            prospect_id=req.prospect_id,
            company=req.company,
            contact_name=req.contact_name,
            contact_email=req.contact_email,
            sector=req.sector,
            deal_value_eur=req.deal_value_eur,
            prospect_context=req.context,
        )
        return {
            "meeting_id": meeting.meeting_id,
            "booking_url": meeting.booking_url,
            "pre_brief": meeting.pre_brief,
            "status": meeting.status,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/meeting/{meeting_id}/confirm")
async def confirm_meeting(meeting_id: str, scheduled_at: str):
    try:
        from OUTREACH.meeting_booker import get_meeting_booker
        success = get_meeting_booker().confirm_meeting(meeting_id, scheduled_at)
        if not success:
            raise HTTPException(status_code=404, detail="Meeting non trouvé")
        return {"success": True, "meeting_id": meeting_id, "scheduled_at": scheduled_at}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/saas/meeting/post-call")
async def post_call_summary(req: PostCallRequest):
    try:
        from OUTREACH.meeting_booker import get_meeting_booker
        return get_meeting_booker().record_post_call_summary(
            meeting_id=req.meeting_id,
            summary=req.summary,
            next_steps=req.next_steps,
            outcome=req.outcome,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/meeting/stats")
async def meeting_stats():
    try:
        from OUTREACH.meeting_booker import get_meeting_booker
        return get_meeting_booker().get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── LLM Router V2 ─────────────────────────────────────────────────────────────

@router.post("/saas/llm/generate")
async def llm_generate(body: Dict):
    """Génère du texte via le routeur LLM V2 optimal."""
    try:
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router_v2 = get_llm_router_v2()
        resp = router_v2.generate(
            task=body.get("task", "content_generation"),
            prompt=body.get("prompt", ""),
            sector=body.get("sector"),
            context=body.get("context"),
            pain=body.get("pain"),
        )
        return {
            "text": resp.text,
            "model_used": resp.model_used,
            "latency_ms": resp.latency_ms,
            "from_cache": resp.from_cache,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/saas/llm/stats")
async def llm_stats():
    try:
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        return get_llm_router_v2().get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── API Marketplace ───────────────────────────────────────────────────────────

@router.get("/saas/marketplace")
async def marketplace_catalog():
    """Catalogue de l'API Marketplace NAYA (pay-per-use)."""
    return {
        "apis": [
            {
                "name": "Pain Hunter API",
                "endpoint": "/api/v1/acceleration/hunt",
                "price": "300 EUR/mois",
                "description": "Détection douleurs OT en temps réel (Serper+Apollo+LinkedIn+CVE+Shodan)",
            },
            {
                "name": "Audit Automatisé API",
                "endpoint": "/api/v1/saas/iec62443/analyze",
                "price": "200 EUR/audit",
                "description": "Audit IEC 62443 automatisé avec rapport + roadmap",
            },
            {
                "name": "NIS2 Checker API",
                "endpoint": "/api/v1/saas/nis2/assess",
                "price": "500 EUR/mois",
                "description": "Score conformité NIS2 + rapport PDF + recommandations",
            },
            {
                "name": "Offer Generation API",
                "endpoint": "/api/v1/saas/llm/generate",
                "price": "100 EUR/100 offres",
                "description": "Génération offres ultra-personnalisées via LLM Router V2",
            },
        ],
        "total_mrr_potential": "10 000 EUR/mois avec 20 clients",
        "contact": "naya@naya-supreme.com",
    }
