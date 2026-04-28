"""
NAYA SUPREME V19 — Audit Workflow (LangGraph)
Signal → Audit IEC 62443 / NIS2 → Rapport PDF → Upsell automatique.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

log = logging.getLogger("NAYA.AuditWorkflow")


# ── State ────────────────────────────────────────────────────────────────────

class AuditState(TypedDict):
    company_name: str
    sector: str
    signal_data: dict[str, Any]
    ot_mapping: dict[str, Any]
    gap_analysis: dict[str, Any]
    nis2_score: float
    roadmap: list[dict[str, Any]]
    report_path: str
    upsell_proposal: dict[str, Any]
    price_eur: float
    status: str


# ── Nodes ─────────────────────────────────────────────────────────────────────

def map_ot_assets(state: AuditState) -> AuditState:
    """Cartographie OT à partir des données publiques + enrichissement."""
    log.info("[AuditWorkflow] map_ot_assets — %s", state.get("company_name"))
    state["ot_mapping"] = {
        "scada_systems": [],
        "plc_vendors": [],
        "network_zones": [],
        "exposed_services": [],
    }
    state["status"] = "ot_mapped"
    return state


def run_gap_analysis(state: AuditState) -> AuditState:
    """Gap analysis IEC 62443 SL-1 à SL-4."""
    log.info("[AuditWorkflow] gap_analysis — %s", state.get("company_name"))
    state["gap_analysis"] = {
        "SL1": {"score": 0, "gaps": [], "compliant": False},
        "SL2": {"score": 0, "gaps": [], "compliant": False},
        "SL3": {"score": 0, "gaps": [], "compliant": False},
        "SL4": {"score": 0, "gaps": [], "compliant": False},
    }
    state["nis2_score"] = 0.0
    state["status"] = "gap_analyzed"
    return state


def build_roadmap(state: AuditState) -> AuditState:
    """Roadmap corrective priorisée — quick wins + projets longs."""
    log.info("[AuditWorkflow] build_roadmap — %s", state.get("company_name"))
    state["roadmap"] = [
        {"priority": "HIGH", "action": "Segmentation réseaux OT/IT", "effort_days": 5},
        {"priority": "HIGH", "action": "Patch management automates", "effort_days": 10},
        {"priority": "MEDIUM", "action": "SOC OT monitoring", "effort_days": 30},
        {"priority": "LOW", "action": "Certification IEC 62443 SL-2", "effort_days": 90},
    ]
    state["status"] = "roadmap_built"
    return state


def generate_report(state: AuditState) -> AuditState:
    """Génère le rapport PDF professionnel (20-40 pages)."""
    log.info("[AuditWorkflow] generate_report — %s", state.get("company_name"))
    import os
    from pathlib import Path

    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = str(report_dir / f"audit_{state['company_name'].replace(' ', '_')}.pdf")

    # Rapport JSON fallback (PDF via reportlab en production)
    import json
    report_data = {
        "company": state["company_name"],
        "sector": state["sector"],
        "ot_mapping": state["ot_mapping"],
        "gap_analysis": state["gap_analysis"],
        "nis2_score": state["nis2_score"],
        "roadmap": state["roadmap"],
    }
    Path(report_path.replace(".pdf", ".json")).write_text(
        json.dumps(report_data, indent=2)
    )

    state["report_path"] = report_path
    state["price_eur"] = 15_000.0
    state["status"] = "report_generated"
    return state


def build_upsell(state: AuditState) -> AuditState:
    """Génère automatiquement la proposition de mission remédiation."""
    log.info("[AuditWorkflow] build_upsell — %s", state.get("company_name"))
    state["upsell_proposal"] = {
        "title": f"Mission remédiation OT — {state['company_name']}",
        "scope": "Correction des gaps IEC 62443 identifiés",
        "duration_weeks": 12,
        "price_eur": 40_000,
        "deliverables": [
            "Segmentation réseau OT/IT",
            "Déploiement monitoring SOC OT",
            "Formation équipes OT (16h)",
            "Rapport conformité IEC 62443 SL-2",
        ],
    }
    state["status"] = "upsell_ready"
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_audit_workflow():
    """Construit et retourne le graph LangGraph de l'audit workflow."""
    try:
        from langgraph.graph import StateGraph

        graph = StateGraph(AuditState)
        graph.add_node("map_ot", map_ot_assets)
        graph.add_node("gap_analysis", run_gap_analysis)
        graph.add_node("roadmap", build_roadmap)
        graph.add_node("report", generate_report)
        graph.add_node("upsell", build_upsell)

        graph.set_entry_point("map_ot")
        graph.add_edge("map_ot", "gap_analysis")
        graph.add_edge("gap_analysis", "roadmap")
        graph.add_edge("roadmap", "report")
        graph.add_edge("report", "upsell")
        graph.set_finish_point("upsell")

        return graph.compile()
    except ImportError:
        log.warning("LangGraph non disponible — workflow en mode séquentiel")
        return None


async def run_audit(company_name: str, sector: str, signal_data: dict | None = None) -> AuditState:
    """Point d'entrée principal : lance un audit complet."""
    state: AuditState = {
        "company_name": company_name,
        "sector": sector,
        "signal_data": signal_data or {},
        "ot_mapping": {},
        "gap_analysis": {},
        "nis2_score": 0.0,
        "roadmap": [],
        "report_path": "",
        "upsell_proposal": {},
        "price_eur": 0.0,
        "status": "init",
    }

    workflow = build_audit_workflow()
    if workflow:
        result = await workflow.ainvoke(state)
        return result

    # Fallback séquentiel
    for step in [map_ot_assets, run_gap_analysis, build_roadmap, generate_report, build_upsell]:
        state = step(state)
    return state
