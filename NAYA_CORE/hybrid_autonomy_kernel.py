"""
NAYA HYBRID AUTONOMY KERNEL
══════════════════════════════════════════════════════════════════════════════
Couche d'unification pour rendre NAYA:
- hybride (règles + IA + scoring + signaux réglementaires)
- autonome (planification/exécution quotidienne)
- multi-lingue (incluant marchés oubliés)
- orienté cash rapide (24/48/72h) + premium (jusqu'à 150k+)
- capable d'orchestrer 4-5 projets en parallèle

Ce module ne remplace pas les moteurs existants: il les compose.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.HYBRID")
ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / "cache" / "hybrid_autonomy_kernel.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

MIN_PREMIUM_FLOOR_EUR = 1000
FAST_CASH_TIERS = [
    {"name": "cash_24h", "min": 1000, "max": 15000, "delivery_h": 24},
    {"name": "cash_48h", "min": 15000, "max": 60000, "delivery_h": 48},
    {"name": "cash_72h", "min": 60000, "max": 150000, "delivery_h": 72},
]

OVERLOOKED_MARKET_LANGS = [
    "fr", "en", "es", "pt", "ar", "wo", "sw", "ha", "ln", "bm", "am", "yo", "ig", "zu"
]

CHANNELS = [
    "linkedin", "email", "whatsapp", "telegram", "x", "youtube", "tiktok", "reddit", "community",
]


@dataclass
class ProjectSlot:
    slot: int
    project_id: str
    priority: int
    sector: str
    target_value_eur: int
    daily_actions: List[str] = field(default_factory=list)


@dataclass
class ChannelExecutionPlan:
    project_id: str
    languages: List[str]
    channels: List[str]
    visibility_story: str
    credibility_proofs: List[str]
    comment_response_templates: Dict[str, str]


@dataclass
class OfferBlueprint:
    prospect_name: str
    company: str
    sector: str
    detected_pain: str
    urgency_angle: str
    value_stack: Dict[str, Any]
    objection_preemptions: List[str]
    guarantee: str
    price_floor_eur: int
    recommended_price_eur: int
    delivery_window_h: int


class HybridAutonomyKernel:
    """Composition layer des moteurs NAYA pour exécution business totale."""

    def __init__(self, max_parallel_projects: int = 5) -> None:
        self.max_parallel_projects = max(4, min(5, max_parallel_projects))
        self._history: List[Dict[str, Any]] = []

    # ── Detection + Priorisation ───────────────────────────────────────────
    def detect_high_value_signals(self) -> Dict[str, Any]:
        """Agrège signaux ultra-discrets depuis les moteurs existants."""
        pain_hits: List[Dict[str, Any]] = []
        regulatory_hits: List[Dict[str, Any]] = []

        try:
            from NAYA_PROJECT_ENGINE.business.universal_pain_engine import universal_pain_engine
            pain_hits = universal_pain_engine.get_ultra_discrete(12)
        except Exception as exc:
            log.debug("pain engine unavailable: %s", exc)

        try:
            from NAYA_CORE.regulatory_trigger_engine import regulatory_trigger_engine
            regulatory_hits = [asdict(s) for s in regulatory_trigger_engine.scan()[:8]]
        except Exception as exc:
            log.debug("regulatory engine unavailable: %s", exc)

        return {
            "ultra_discrete_pains": pain_hits,
            "regulatory_triggers": regulatory_hits,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    def build_parallel_slots(self, ranked_projects: List[Dict[str, Any]]) -> List[ProjectSlot]:
        """Construit 4-5 slots d'exécution parallèle avec priorités."""
        slots: List[ProjectSlot] = []
        for i, p in enumerate(ranked_projects[: self.max_parallel_projects]):
            score = int(p.get("go_live_score", 50))
            target = int(p.get("avg_ticket_eur", 10000) * 1.8)
            slots.append(
                ProjectSlot(
                    slot=i,
                    project_id=p.get("project_id", f"PROJECT_{i}"),
                    priority=score,
                    sector=p.get("vertical", p.get("sector", "General")),
                    target_value_eur=max(MIN_PREMIUM_FLOOR_EUR, target),
                    daily_actions=[
                        "scan_pain_signals",
                        "activate_warm_path",
                        "send_offer_blueprint",
                        "publish_story_content",
                        "reply_comments_dm",
                    ],
                )
            )
        return slots

    # ── Channel/Language Intelligence ─────────────────────────────────────
    def channel_plan(self, project_id: str, sector: str) -> ChannelExecutionPlan:
        """Plan d'exécution multi-canaux + réponses préparées."""
        templates = {
            "linkedin": "Merci pour votre retour. Contexte {sector}: nous traitons ce point en 48h avec KPI mesurable.",
            "email": "Bonjour, votre question est clé. Voici le plan actionnable en 3 étapes pour {sector}.",
            "whatsapp": "Bien reçu 🙌. Je vous envoie un plan court + chiffrage dans l'heure.",
            "telegram": "Update validé ✅ prochaine action: déclenchement du workflow de conversion.",
            "x": "Point pertinent — on publie les métriques terrain sous 24h.",
        }
        return ChannelExecutionPlan(
            project_id=project_id,
            languages=OVERLOOKED_MARKET_LANGS,
            channels=CHANNELS,
            visibility_story=f"{project_id}: douleur réelle → solution chiffrée → preuve client",
            credibility_proofs=[
                "before_after_metrics",
                "regulatory_readiness_score",
                "roi_90_days_snapshot",
                "payment_verified_events",
            ],
            comment_response_templates={k: v.format(sector=sector) for k, v in templates.items()},
        )

    # ── Offer Intelligence ────────────────────────────────────────────────
    def build_irresistible_offer(
        self,
        prospect_name: str,
        company: str,
        sector: str,
        detected_pain: str,
        estimated_budget: int,
    ) -> OfferBlueprint:
        """Blueprint d'offre ultra personnalisée et non-jetable."""
        budget = max(MIN_PREMIUM_FLOOR_EUR, estimated_budget)
        tier = next((t for t in FAST_CASH_TIERS if t["min"] <= budget <= t["max"]), FAST_CASH_TIERS[-1])

        recommended = int(max(MIN_PREMIUM_FLOOR_EUR, budget * 0.9))
        return OfferBlueprint(
            prospect_name=prospect_name,
            company=company,
            sector=sector,
            detected_pain=detected_pain,
            urgency_angle="inaction_cost_vs_48h_outcome",
            value_stack={
                "diagnostic": "root_cause_map",
                "execution": "rapid_fix_sprint",
                "proof": "kpi_dashboard",
                "continuity": "retainer_optional",
            },
            objection_preemptions=[
                "budget_risk_mitigated_by_phased_delivery",
                "time_risk_mitigated_by_24_48_72h_sprints",
                "credibility_proof_by_sector_case",
            ],
            guarantee="No-Value-No-Fee on first milestone",
            price_floor_eur=MIN_PREMIUM_FLOOR_EUR,
            recommended_price_eur=recommended,
            delivery_window_h=tier["delivery_h"],
        )

    # ── Daily Autonomous Orchestration ────────────────────────────────────
    def daily_autonomous_brief(self) -> Dict[str, Any]:
        """Rapport quotidien pour Telegram + TORI_APP (compact, actionnable)."""
        signals = self.detect_high_value_signals()

        ranked: List[Dict[str, Any]] = []
        try:
            from NAYA_PROJECT_ENGINE.entrypoint import get_project_engine
            ranked = get_project_engine().get_adaptive_ranked_projects(16)
        except Exception as exc:
            log.debug("project engine unavailable: %s", exc)

        edge_report: Dict[str, Any] = {}
        try:
            from NAYA_CORE.sovereign_advantage_engine import sovereign_advantage_engine
            report = sovereign_advantage_engine.build_edge_report()
            edge_report = {
                "advantage_vector": asdict(report.advantage_vector),
                "top_hidden_markets": report.top_hidden_markets,
                "best_price_zone": report.best_price_zone,
                "anti_refusal_offer": report.anti_refusal_offer,
                "next_best_actions": report.next_best_actions,
                "positioning_statement": report.positioning_statement,
            }
        except Exception as exc:
            log.debug("advantage engine unavailable: %s", exc)

        slots = self.build_parallel_slots(ranked)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "parallel_slots": [asdict(s) for s in slots],
            "ultra_pains_count": len(signals.get("ultra_discrete_pains", [])),
            "regulatory_count": len(signals.get("regulatory_triggers", [])),
            "target_cash_72h_eur": sum(s.target_value_eur for s in slots),
            "telegram_message": (
                f"NAYA Briefing — {len(slots)} slots actifs | "
                f"{len(signals.get('ultra_discrete_pains', []))} pains ultra-discrets | "
                f"Objectif 72h: {sum(s.target_value_eur for s in slots):,} EUR"
            ),
            "dashboard_hint": "TORI_APP /tori/missions/today + /tori/launch_10d",
            "sovereign_edge": edge_report,
        }

        self._history.append(payload)
        if len(self._history) > 200:
            self._history = self._history[-100:]
        self._save(payload)
        return payload

    def _save(self, payload: Dict[str, Any]) -> None:
        CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


hybrid_autonomy_kernel = HybridAutonomyKernel()
