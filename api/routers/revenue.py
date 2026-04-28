"""
NAYA SUPREME V14 — Revenue API Router (Production)
Tous les endpoints revenue : pipeline, hunt, follow-ups, Botanica, métriques.
"""
from fastapi import APIRouter, BackgroundTasks
from typing import Dict, Optional
import asyncio
import os
import time
import uuid

# Module-level imports for /sale/create endpoint (avoid per-request import overhead)
try:
    from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine as _PaymentEngine
    _payment_engine_cls = _PaymentEngine
except Exception:
    _payment_engine_cls = None

try:
    from NAYA_REVENUE_ENGINE.payment_tracker import PaymentTracker as _PaymentTracker
    _payment_tracker_cls = _PaymentTracker
except Exception:
    _payment_tracker_cls = None

router = APIRouter()


# ─── Pipeline Stats ─────────────────────────────────────────────────────────

@router.get("/pipeline/stats")
async def pipeline_stats() -> Dict:
    """Statistiques complètes du pipeline revenue (non-bloquant)."""
    def _collect_stats():
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            engine = get_cash_engine()
            stats = engine.get_stats() if hasattr(engine, "get_stats") else engine.get_pipeline_summary() if hasattr(engine, "get_pipeline_summary") else {}
        except Exception as e:
            stats = {"error": str(e)[:80]}

        followup_stats = {}
        try:
            from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine
            followup_stats = get_followup_engine().get_stats()
        except Exception:
            pass

        botanica_stats = {}
        try:
            from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
            botanica_stats = get_botanica_engine().get_metrics()
        except Exception:
            pass

        return {
            "pipeline": stats,
            "followup": followup_stats,
            "botanica": botanica_stats,
            "total_revenue_eur": (
                stats.get("total_revenue", 0) +
                followup_stats.get("total_revenue_eur", 0) +
                botanica_stats.get("total_revenue_eur", 0)
            ),
            "total": stats.get("total_deals", 0) + followup_stats.get("sequences_total", 0),
            "ts": time.time(),
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect_stats)


@router.get("/pipeline/deals")
async def list_deals(limit: int = 20) -> Dict:
    """Liste les deals actifs dans le pipeline."""
    try:
        from NAYA_CORE.cash_engine_real import get_cash_engine
        engine = get_cash_engine()
        deals = engine.get_active_deals(limit=limit) if hasattr(engine, "get_active_deals") else []
        return {"deals": deals, "count": len(deals)}
    except Exception as e:
        return {"deals": [], "error": str(e)[:80]}


@router.post("/pipeline/inject")
async def inject_prospect(data: dict, bg: BackgroundTasks) -> Dict:
    """Injecte manuellement un prospect dans le pipeline — retourne immédiatement.
    Le pipeline complet s'exécute en arrière-plan (fire-and-forget)."""
    exec_id = f"PIPE_{uuid.uuid4().hex[:8].upper()}"

    def _run_bg():
        try:
            from NAYA_CORE.real_pipeline_orchestrator import get_pipeline_orchestrator
            orch = get_pipeline_orchestrator()
            orch.execute_full_pipeline(data)
        except Exception:
            pass

    bg.add_task(_run_bg)
    return {"status": "pipeline_started", "execution_id": exec_id,
            "note": "Pipeline exécuté en arrière-plan"}


# ─── Hunt ────────────────────────────────────────────────────────────────────

@router.post("/hunt/trigger")
async def trigger_hunt(bg: BackgroundTasks, sector: Optional[str] = None) -> Dict:
    """Déclenche un cycle de chasse de douleurs."""
    def _hunt():
        try:
            from NAYA_CORE.hunt.auto_hunt_seeder import AutoHuntSeeder
            seeder = AutoHuntSeeder()
            queries = seeder.get_hunt_queries(sector=sector, limit=10) if hasattr(seeder, "get_hunt_queries") else []
            return len(queries)
        except Exception:
            pass

    bg.add_task(_hunt)
    return {"status": "hunt_started", "sector": sector or "all", "ts": time.time()}


# ─── Follow-Up Sequences ─────────────────────────────────────────────────────

@router.get("/followup/stats")
async def followup_stats() -> Dict:
    """Statistiques des séquences de follow-up."""
    try:
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine
        return get_followup_engine().get_stats()
    except Exception as e:
        return {"error": str(e)[:80]}


@router.post("/followup/create")
async def create_followup(data: dict) -> Dict:
    """Crée une nouvelle séquence de follow-up."""
    try:
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine, SequenceType
        engine = get_followup_engine()
        seq = engine.create_sequence(
            prospect_id=data.get("prospect_id", f"P_{int(time.time())}"),
            email=data["email"],
            first_name=data.get("first_name", ""),
            company=data.get("company", ""),
            sequence_type=SequenceType(data.get("sequence_type", "cold_outreach")),
            sector=data.get("sector", ""),
            pain_type=data.get("pain_type", ""),
            price_floor=float(data.get("price_floor", 1500)),
        )
        return {"status": "created", "sequence_id": seq.sequence_id, "touches": len(seq.touches)}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


@router.post("/followup/execute")
async def execute_followups(bg: BackgroundTasks) -> Dict:
    """Exécute tous les follow-ups en attente maintenant."""
    def _exec():
        try:
            from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine
            return get_followup_engine().execute_due_touches()
        except Exception:
            pass

    bg.add_task(_exec)
    return {"status": "executing", "ts": time.time()}


# ─── Email Deliverability ────────────────────────────────────────────────────

@router.get("/deliverability")
async def deliverability_report() -> Dict:
    """Rapport de délivrabilité email."""
    try:
        from NAYA_REVENUE_ENGINE.email_warmup_engine import get_warmup_engine
        engine = get_warmup_engine()
        return {
            "report": engine.get_deliverability_report(),
            "best_send_time": engine.get_best_send_time(),
        }
    except Exception as e:
        return {"error": str(e)[:80]}


@router.post("/deliverability/check-subject")
async def check_subject(data: dict) -> Dict:
    """Analyse un sujet d'email pour le spam score."""
    try:
        from NAYA_REVENUE_ENGINE.email_warmup_engine import get_warmup_engine
        return get_warmup_engine().check_subject_spam_score(data.get("subject", ""))
    except Exception as e:
        return {"error": str(e)[:80]}


# ─── Botanica ────────────────────────────────────────────────────────────────

@router.get("/botanica/metrics")
async def botanica_metrics() -> Dict:
    """Métriques e-commerce Botanica."""
    try:
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
        return get_botanica_engine().get_metrics()
    except Exception as e:
        return {"error": str(e)[:80]}


@router.get("/botanica/catalogue")
async def botanica_catalogue(category: Optional[str] = None) -> Dict:
    """Catalogue produits Botanica."""
    try:
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
        return {"products": get_botanica_engine().get_catalogue(category=category)}
    except Exception as e:
        return {"error": str(e)[:80]}


@router.post("/botanica/order")
async def create_botanica_order(data: dict) -> Dict:
    """Crée une commande Botanica."""
    try:
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
        engine = get_botanica_engine()
        order = engine.create_order(
            customer_email=data["email"],
            customer_name=data.get("name", ""),
            items_skus=data.get("items", []),
            skin_type=data.get("skin_type", ""),
            channel=data.get("channel", "api"),
        )
        return {
            "order_id": order.order_id,
            "total": order.total,
            "payment_link": order.payment_link,
            "status": order.status,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


@router.post("/botanica/cart-abandon")
async def botanica_cart_abandon(data: dict) -> Dict:
    """Déclenche la séquence abandon panier."""
    try:
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
        get_botanica_engine().create_cart_abandonment(
            email=data["email"],
            name=data.get("name", ""),
            sku=data.get("sku", "REN-001"),
        )
        return {"status": "sequence_started"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


# ─── Revenue Summary ─────────────────────────────────────────────────────────

@router.get("/summary")
async def revenue_summary() -> Dict:
    """Résumé financier global — tous projets confondus."""
    results = {"projects": {}, "grand_total_eur": 0.0, "ts": time.time()}

    # Botanica
    try:
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.botanica_ecommerce_engine import get_botanica_engine
        m = get_botanica_engine().get_metrics()
        results["projects"]["botanica"] = {"revenue_eur": m["total_revenue_eur"], "orders": m["paid_orders"]}
        results["grand_total_eur"] += m["total_revenue_eur"]
    except Exception:
        pass

    # Follow-ups / B2B
    try:
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine
        f = get_followup_engine().get_stats()
        results["projects"]["b2b_followup"] = {"revenue_eur": f["total_revenue_eur"], "sequences_won": f["sequences_won"]}
        results["grand_total_eur"] += f["total_revenue_eur"]
    except Exception:
        pass

    # Cash pipeline
    try:
        from NAYA_CORE.cash_engine_real import get_cash_engine
        c = get_cash_engine()
        s = c.get_stats() if hasattr(c, "get_stats") else {}
        results["projects"]["cash_rapide"] = {"revenue_eur": s.get("total_revenue", 0), "deals_won": s.get("won_deals", 0)}
        results["grand_total_eur"] += s.get("total_revenue", 0)
    except Exception:
        pass

    return results


# ─── Sale Creation (Sales Validation) ────────────────────────────────────────

@router.post("/sale/create")
async def create_sale(data: dict) -> Dict:
    """
    Crée une vente réelle: génère le lien de paiement (PayPal/Deblock),
    enregistre l'invoice et l'opportunité dans le pipeline.
    Plancher absolu: MIN_AMOUNT = 1 000 EUR.
    """
    MIN_AMOUNT = 1000.0
    amount = float(data.get("amount_eur", 0))

    if amount < MIN_AMOUNT:
        return {
            "status": "rejected",
            "reason": f"Montant {amount} EUR inférieur au plancher {MIN_AMOUNT} EUR (règle inviolable)",
            "min_amount_eur": MIN_AMOUNT,
        }

    prospect_id = data.get("prospect_id") or f"SALE_{uuid.uuid4().hex[:8].upper()}"
    company = data.get("company", "Prospect B2B")
    sector = data.get("sector", "ot_security")
    method = data.get("method", "paypal")
    description = data.get("description", f"Service B2B — {sector}")

    result: Dict = {
        "status": "ok",
        "sale_id": f"NAYA_SALE_{uuid.uuid4().hex[:8].upper()}",
        "prospect_id": prospect_id,
        "company": company,
        "sector": sector,
        "amount_eur": amount,
        "currency": "EUR",
        "method": method,
        "description": description,
        "plancher_respected": amount >= MIN_AMOUNT,
        "ts": time.time(),
    }

    # Generate payment link via PaymentEngine
    try:
        if _payment_engine_cls is None:
            raise ImportError("PaymentEngine not available")
        pe = _payment_engine_cls()
        link_data = pe.create_payment_link(amount, company, description)
        result["payment_url"] = link_data.get("url", "")
        result["payment_id"] = link_data.get("payment_id", "")
        result["payment_provider"] = link_data.get("provider", method)
        result["payment_reference"] = link_data.get("reference", "")
    except Exception as e:
        # Fallback: build URL from env var (PAYPAL_ME_URL), never hardcode username
        paypal_base = os.environ.get("PAYPAL_ME_URL", "").rstrip("/")
        result["payment_url"] = f"{paypal_base}/{amount:.2f}" if paypal_base else ""
        result["payment_id"] = f"PAY_{uuid.uuid4().hex[:8].upper()}"
        result["payment_provider"] = "paypal_fallback"
        result["payment_note"] = f"PaymentEngine error: {str(e)[:80]}"

    # Record invoice in PaymentTracker
    try:
        if _payment_tracker_cls is None:
            raise ImportError("PaymentTracker not available")
        tracker = _payment_tracker_cls()
        record = tracker.create_invoice(
            opp_id=prospect_id,
            prospect=company,
            amount=amount,
            method=method,
            due_days=data.get("due_days", 7),
        )
        result["invoice_id"] = record.payment_id
        result["invoice_status"] = record.status.value
    except Exception as e:
        result["invoice_id"] = f"INV_{uuid.uuid4().hex[:8].upper()}"
        result["invoice_status"] = "pending"
        result["invoice_note"] = f"Tracker error: {str(e)[:80]}"

    return result
