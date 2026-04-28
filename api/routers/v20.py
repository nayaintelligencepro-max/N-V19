"""NAYA V20 — API Router — Expose V20 Intelligence modules."""
import asyncio
import logging
from fastapi import APIRouter, Body
from typing import Dict

log = logging.getLogger("NAYA.API.V20")
router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# HUNTERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/hunters/dark-web/stats")
async def dark_web_stats() -> Dict:
    """Statistiques du scanner Dark Web OT."""
    def _collect():
        try:
            from V20_INTELLIGENCE.hunters.dark_web_ot_scanner import get_dark_web_scanner
            return get_dark_web_scanner().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/hunters/cve-shodan/stats")
async def cve_shodan_stats() -> Dict:
    """Statistiques CVE + Shodan intelligence."""
    def _collect():
        try:
            from V20_INTELLIGENCE.hunters.cve_shodan_intelligence import get_cve_shodan_intelligence
            return get_cve_shodan_intelligence().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/hunters/tenders/actionable")
async def tenders_actionable() -> Dict:
    """Appels d'offres actionnables (score élevé)."""
    def _collect():
        try:
            from V20_INTELLIGENCE.hunters.tender_radar import get_tender_radar
            radar = get_tender_radar()
            tenders = radar.get_actionable()
            return {
                "count": len(tenders),
                "tenders": [
                    {
                        "tender_id": t.tender_id,
                        "title": t.title,
                        "buyer": t.buyer,
                        "estimated_value_eur": t.estimated_value_eur,
                        "deadline": t.deadline,
                        "relevance_score": t.relevance_score,
                    }
                    for t in tenders[:20]
                ],
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/hunters/regulatory/upcoming")
async def regulatory_upcoming() -> Dict:
    """Deadlines réglementaires à venir (90 jours)."""
    def _collect():
        try:
            from V20_INTELLIGENCE.hunters.regulatory_deadline_engine import get_regulatory_deadline_engine
            engine = get_regulatory_deadline_engine()
            deadlines = engine.get_upcoming(horizon_days=90)
            return {
                "count": len(deadlines),
                "deadlines": [
                    {
                        "reg_id": d.reg_id,
                        "regulation_name": d.regulation_name,
                        "regulation_code": d.regulation_code,
                        "deadline_date": d.deadline_date,
                        "days_until": d.days_until,
                        "target_sectors": d.target_sectors,
                    }
                    for d in deadlines[:20]
                ],
                "stats": engine.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/hunters/osint/tier1")
async def osint_tier1() -> Dict:
    """Signaux OSINT satellite Tier-1 (haute valeur)."""
    def _collect():
        try:
            from V20_INTELLIGENCE.hunters.satellite_osint_engine import get_satellite_osint_engine
            engine = get_satellite_osint_engine()
            signals = engine.get_tier1_prospects()
            return {
                "count": len(signals),
                "signals": [
                    {
                        "prospect_id": s.id,
                        "company": s.company,
                        "sector": s.sector,
                        "tier": s.tier,
                        "estimated_value_eur": s.estimated_budget_eur,
                        "confidence": s.composite_score,
                    }
                    for s in signals[:20]
                ],
                "stats": engine.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


# ══════════════════════════════════════════════════════════════════════════════
# AI ADVANCED
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/ai/sentiment/hot-leads")
async def sentiment_hot_leads() -> Dict:
    """Hot leads détectés par le SentimentRadar (score ≥ 70)."""
    def _collect():
        try:
            from V20_INTELLIGENCE.ai_advanced.sentiment_radar import get_sentiment_radar
            radar = get_sentiment_radar()
            leads = radar.get_hot_leads(min_score=70)
            return {
                "count": len(leads),
                "hot_leads": [
                    {
                        "post_id": l.post_id,
                        "author_name": l.author_name,
                        "company": l.company,
                        "distress_score": l.distress_score,
                        "hot_keywords": l.hot_keywords,
                        "platform": l.platform,
                        "posted_at": l.posted_at,
                    }
                    for l in leads[:20]
                ],
                "stats": radar.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/ai/voice/stats")
async def voice_agent_stats() -> Dict:
    """Statistiques du Voice Agent Engine."""
    def _collect():
        try:
            from V20_INTELLIGENCE.ai_advanced.voice_agent_engine import get_voice_agent_engine
            return get_voice_agent_engine().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/ai/annual-reports/high-value")
async def annual_reports_high_value() -> Dict:
    """Rapports annuels avec budget cyber ≥ 500k€."""
    def _collect():
        try:
            from V20_INTELLIGENCE.ai_advanced.annual_report_parser import get_annual_report_parser
            parser = get_annual_report_parser()
            reports = parser.get_high_value_companies(min_cyber_budget=500_000)
            return {
                "count": len(reports),
                "companies": [
                    {
                        "company": r.company,
                        "year": r.year,
                        "sector": r.sector,
                        "cyber_budget_eur": r.cyber_budget_mentioned_eur,
                        "investment_score": r.investment_score,
                        "rssi_name": r.rssi_name,
                    }
                    for r in reports[:20]
                ],
                "stats": parser.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


# ══════════════════════════════════════════════════════════════════════════════
# ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/architecture/digital-twin/{prospect_id}")
async def digital_twin(prospect_id: str) -> Dict:
    """Twin digital d'un prospect."""
    def _collect():
        try:
            from V20_INTELLIGENCE.architecture.digital_twin_engine import get_digital_twin_engine
            engine = get_digital_twin_engine()
            twin = engine.get_twin(prospect_id)
            if twin is None:
                return {"error": f"Twin not found for {prospect_id}"}
            return {
                "prospect_id": twin.prospect_id,
                "company": twin.company,
                "contact_name": twin.contact_name,
                "role": twin.role,
                "preferred_channel": twin.preferred_channel,
                "best_contact_day": twin.best_contact_day,
                "best_contact_hour": twin.best_contact_hour,
                "communication_style": twin.communication_style,
                "response_rate": twin.response_rate,
                "twin_confidence": twin.twin_confidence,
                "optimal_window": engine.get_optimal_contact_window(prospect_id),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/architecture/zkp/stats")
async def zkp_stats() -> Dict:
    """Statistiques du moteur ZKP Audit."""
    def _collect():
        try:
            from V20_INTELLIGENCE.architecture.zkp_audit_engine import get_zkp_audit_engine
            return get_zkp_audit_engine().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


# ══════════════════════════════════════════════════════════════════════════════
# VERTICALS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/verticals/ai-act/stats")
async def ai_act_stats() -> Dict:
    """Statistiques AI Act Compliance Engine."""
    def _collect():
        try:
            from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import get_ai_act_compliance_engine
            engine = get_ai_act_compliance_engine()
            return {
                "stats": engine.get_stats(),
                "upcoming_deadlines": engine.get_upcoming_deadlines(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/verticals/africa/targets")
async def africa_targets() -> Dict:
    """Pays cibles Afrique francophone + prospects qualifiés."""
    def _collect():
        try:
            from V20_INTELLIGENCE.verticals.africa_ot_vertical import get_africa_ot_vertical
            vertical = get_africa_ot_vertical()
            return {
                "target_countries": vertical.get_target_countries(),
                "stats": vertical.get_stats(),
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.get("/verticals/supply-chain/stats")
async def supply_chain_stats() -> Dict:
    """Statistiques Supply Chain Risk Scorer."""
    def _collect():
        try:
            from V20_INTELLIGENCE.verticals.supply_chain_risk_scorer import get_supply_chain_risk_scorer
            return get_supply_chain_risk_scorer().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


# ══════════════════════════════════════════════════════════════════════════════
# FUTURE TECH
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/future/blockchain/stats")
async def blockchain_stats() -> Dict:
    """Statistiques Blockchain Proof of Audit."""
    def _collect():
        try:
            from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import get_blockchain_proof_of_audit
            return get_blockchain_proof_of_audit().get_stats()
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)


@router.post("/future/blockchain/register-audit")
async def blockchain_register_audit(
    audit_id: str = Body(...),
    company: str = Body(...),
    audit_type: str = Body(...),
    auditor: str = Body(...),
    scope: str = Body(...),
    result_summary: str = Body(...),
) -> Dict:
    """Enregistre un audit sur la blockchain simulée (Polygon Amoy testnet)."""
    def _register():
        try:
            from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import get_blockchain_proof_of_audit
            proof = get_blockchain_proof_of_audit().register_audit(
                audit_id=audit_id,
                company=company,
                audit_type=audit_type,
                auditor=auditor,
                scope=scope,
                result_summary=result_summary,
            )
            return {
                "proof_id": proof.proof_id,
                "audit_id": proof.audit_id,
                "company": proof.company,
                "content_hash": proof.content_hash,
                "tx_hash": proof.tx_hash,
                "chain_id": proof.chain_id,
                "is_verified": proof.is_verified,
                "block_timestamp": proof.block_timestamp,
            }
        except Exception as e:
            return {"error": str(e)[:120]}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _register)


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATE STATS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/stats")
async def v20_aggregate_stats() -> Dict:
    """Statistiques agrégées de tous les 25 modules V20."""
    def _collect():
        result: Dict = {}
        modules = [
            ("dark_web_scanner",        "V20_INTELLIGENCE.hunters.dark_web_ot_scanner",           "get_dark_web_scanner"),
            ("cve_shodan",              "V20_INTELLIGENCE.hunters.cve_shodan_intelligence",        "get_cve_shodan_intelligence"),
            ("tender_radar",            "V20_INTELLIGENCE.hunters.tender_radar",                   "get_tender_radar"),
            ("regulatory_deadlines",    "V20_INTELLIGENCE.hunters.regulatory_deadline_engine",     "get_regulatory_deadline_engine"),
            ("satellite_osint",         "V20_INTELLIGENCE.hunters.satellite_osint_engine",         "get_satellite_osint_engine"),
            ("local_llm_trainer",       "V20_INTELLIGENCE.ai_advanced.local_llm_trainer",          "get_local_llm_trainer"),
            ("decision_graph",          "V20_INTELLIGENCE.ai_advanced.decision_graph_engine",      "get_decision_graph"),
            ("sentiment_radar",         "V20_INTELLIGENCE.ai_advanced.sentiment_radar",            "get_sentiment_radar"),
            ("voice_agent",             "V20_INTELLIGENCE.ai_advanced.voice_agent_engine",         "get_voice_agent_engine"),
            ("annual_report_parser",    "V20_INTELLIGENCE.ai_advanced.annual_report_parser",       "get_annual_report_parser"),
            ("sovereign_vector_store",  "V20_INTELLIGENCE.architecture.sovereign_vector_store",    "get_sovereign_vector_store"),
            ("federated_learner",       "V20_INTELLIGENCE.architecture.federated_learner",         "get_federated_learner"),
            ("digital_twin",            "V20_INTELLIGENCE.architecture.digital_twin_engine",       "get_digital_twin_engine"),
            ("zkp_audit",               "V20_INTELLIGENCE.architecture.zkp_audit_engine",          "get_zkp_audit_engine"),
            ("quantum_safe",            "V20_INTELLIGENCE.architecture.quantum_safe_advisor",      "get_quantum_safe_advisor"),
            ("ai_act",                  "V20_INTELLIGENCE.verticals.ai_act_compliance_engine",     "get_ai_act_compliance_engine"),
            ("africa_ot",               "V20_INTELLIGENCE.verticals.africa_ot_vertical",           "get_africa_ot_vertical"),
            ("supply_chain",            "V20_INTELLIGENCE.verticals.supply_chain_risk_scorer",     "get_supply_chain_risk_scorer"),
            ("insurance_advisory",      "V20_INTELLIGENCE.verticals.insurance_advisory_engine",    "get_insurance_advisory_engine"),
            ("satellite_ot_security",   "V20_INTELLIGENCE.verticals.space_satellite_ot_security",  "get_space_satellite_ot_security"),
            ("agentic_orchestrator",    "V20_INTELLIGENCE.future_tech.agentic_orchestrator",       "get_agentic_orchestrator"),
            ("ambient_iot",             "V20_INTELLIGENCE.future_tech.ambient_iot_intelligence",   "get_ambient_iot_intelligence"),
            ("neuromorphic_scorer",     "V20_INTELLIGENCE.future_tech.neuromorphic_scorer",        "get_neuromorphic_scorer"),
            ("blockchain_audit",        "V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit",  "get_blockchain_proof_of_audit"),
            ("ar_ot_assessment",        "V20_INTELLIGENCE.future_tech.ar_ot_assessment",           "get_ar_ot_assessment"),
        ]
        for key, module_path, getter in modules:
            try:
                import importlib
                mod = importlib.import_module(module_path)
                instance = getattr(mod, getter)()
                result[key] = instance.get_stats()
            except Exception as e:
                result[key] = {"error": str(e)[:80]}
        result["total_modules"] = len(modules)
        return result

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect)
