"""NAYA Sovereign Advantage Engine.

Dernière couche transverse pour rendre NAYA plus fort techniquement,
commercialement et opérationnellement:
- détecte l'invisible rentable (blind spot index)
- mesure la probabilité réelle d'encaissement (cash likelihood)
- produit un moat score (vitesse + preuve + différenciation + récurrence)
- génère un angle d'offre anti-refus exploitable immédiatement
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


log = logging.getLogger("NAYA.ADVANTAGE")
ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / "cache" / "sovereign_advantage_engine.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AdvantageVector:
    blind_spot_index: float = 0.0
    cash_likelihood: float = 0.0
    moat_score: float = 0.0
    execution_readiness: float = 0.0
    anti_refusal_strength: float = 0.0
    recurrence_potential: float = 0.0


@dataclass
class SovereignEdgeReport:
    timestamp: str
    advantage_vector: AdvantageVector
    top_hidden_markets: List[Dict[str, Any]] = field(default_factory=list)
    best_price_zone: Dict[str, Any] = field(default_factory=dict)
    anti_refusal_offer: Dict[str, Any] = field(default_factory=dict)
    next_best_actions: List[str] = field(default_factory=list)
    positioning_statement: str = ""


class SovereignAdvantageEngine:
    """Compose les meilleurs moteurs NAYA pour produire un edge business actionnable."""

    def build_edge_report(self) -> SovereignEdgeReport:
        priority_sectors: List[Dict[str, Any]] = []
        best_price_zone: Dict[str, Any] = {}
        hidden_markets: List[Dict[str, Any]] = []
        learning_stats: Dict[str, Any] = {}

        try:
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            intel = get_revenue_intelligence()
            priority_sectors = intel.get_priority_sectors(5)
            best_price_zone = intel.get_best_price_range()
            hidden_markets = [
                s for s in priority_sectors
                if s.get("conversion_rate", 0) < 0.35 and s.get("priority_score", 0) >= 50
            ]
        except Exception as exc:
            log.debug("advantage revenue_intel unavailable: %s", exc)

        try:
            from NAYA_CORE.learning_feedback_engine import get_learning_engine
            learning_stats = get_learning_engine().get_stats()
        except Exception as exc:
            log.debug("advantage learning unavailable: %s", exc)

        vector = AdvantageVector(
            blind_spot_index=self._blind_spot_index(hidden_markets),
            cash_likelihood=self._cash_likelihood(priority_sectors, best_price_zone),
            moat_score=self._moat_score(priority_sectors, learning_stats),
            execution_readiness=self._execution_readiness(priority_sectors),
            anti_refusal_strength=self._anti_refusal_strength(best_price_zone),
            recurrence_potential=self._recurrence_potential(priority_sectors),
        )

        anti_refusal_offer = self._anti_refusal_offer(best_price_zone, priority_sectors)
        next_actions = self._next_best_actions(vector, priority_sectors)
        positioning = self._positioning_statement(vector)

        report = SovereignEdgeReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            advantage_vector=vector,
            top_hidden_markets=hidden_markets[:3],
            best_price_zone=best_price_zone,
            anti_refusal_offer=anti_refusal_offer,
            next_best_actions=next_actions,
            positioning_statement=positioning,
        )
        self._save(report)
        return report

    def _blind_spot_index(self, hidden_markets: List[Dict[str, Any]]) -> float:
        if not hidden_markets:
            return 52.0
        score = 45.0 + min(40.0, len(hidden_markets) * 12.0)
        score += sum(m.get("priority_score", 0) for m in hidden_markets[:3]) / 20.0
        return round(min(100.0, score), 1)

    def _cash_likelihood(self, sectors: List[Dict[str, Any]], best_price_zone: Dict[str, Any]) -> float:
        conv = sum(s.get("conversion_rate", 0) for s in sectors[:3]) / max(len(sectors[:3]), 1)
        price_boost = 0.12 if best_price_zone.get("best_bucket") in {"5k-15k", "15k-30k", "30k-60k"} else 0.05
        return round(min(1.0, 0.35 + conv + price_boost), 3)

    def _moat_score(self, sectors: List[Dict[str, Any]], learning_stats: Dict[str, Any]) -> float:
        sector_diversity = min(1.0, len(sectors) / 5)
        wins = min(1.0, learning_stats.get("total_wins", 0) / 25)
        revenue = min(1.0, learning_stats.get("total_revenue", 0) / 500000)
        return round((sector_diversity * 30 + wins * 35 + revenue * 35), 1)

    def _execution_readiness(self, sectors: List[Dict[str, Any]]) -> float:
        if not sectors:
            return 0.55
        recos = [s.get("recommendation", "") for s in sectors[:4]]
        aggressive = sum(1 for r in recos if r == "HUNT_AGGRESSIVELY")
        return round(min(1.0, 0.45 + aggressive * 0.12), 3)

    def _anti_refusal_strength(self, best_price_zone: Dict[str, Any]) -> float:
        bucket = best_price_zone.get("best_bucket", "5k-15k")
        mapping = {"1k-5k": 0.68, "5k-15k": 0.82, "15k-30k": 0.88, "30k-60k": 0.86, "60k+": 0.72}
        return mapping.get(bucket, 0.75)

    def _recurrence_potential(self, sectors: List[Dict[str, Any]]) -> float:
        recurring = {"pme_b2b", "healthcare_wellness", "startup_scaleup", "ecommerce"}
        hits = sum(1 for s in sectors[:5] if s.get("sector") in recurring)
        return round(min(1.0, 0.35 + hits * 0.14), 3)

    def _anti_refusal_offer(self, best_price_zone: Dict[str, Any], sectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        top_sector = sectors[0]["sector"] if sectors else "cross_sector"
        return {
            "primary_sector": top_sector,
            "pricing_zone": best_price_zone.get("best_bucket", "5k-15k"),
            "guarantee": "No-Value-No-Fee sur premier milestone",
            "offer_stack": [
                "diagnostic_risque_financier",
                "quick_win_24_48_72h",
                "preuve_kpi_avant_apres",
                "retainer_optionnel_apres_resultat",
            ],
            "objection_killers": [
                "paiement_phase_par_phase",
                "preuve_mesurable_avant_escalade_budget",
                "execution_immediate_not_consulting_only",
            ],
        }

    def _next_best_actions(self, vector: AdvantageVector, sectors: List[Dict[str, Any]]) -> List[str]:
        actions: List[str] = []
        if vector.blind_spot_index >= 70:
            actions.append("intensifier_hunt_sur_marches_oublies_prioritaires")
        if vector.cash_likelihood >= 0.70:
            actions.append("favoriser_offres_cash_24_48_72h_sur_top_3_secteurs")
        if vector.anti_refusal_strength >= 0.80:
            actions.append("utiliser_garantie_no_value_no_fee_par_defaut")
        if vector.recurrence_potential >= 0.60:
            actions.append("ajouter_retainer_ou_mrr_sur_chaque_signature")
        if not actions:
            actions.append("continuer_collecte_signaux_et_apprentissage")
        return actions

    def _positioning_statement(self, vector: AdvantageVector) -> str:
        return (
            f"NAYA opère avec un edge de marché {vector.blind_spot_index:.0f}/100, "
            f"une probabilité d'encaissement {vector.cash_likelihood*100:.0f}%, "
            f"et un moat score {vector.moat_score:.0f}/100 — combinaison rare vitesse+preuve+cash."
        )

    def _save(self, report: SovereignEdgeReport) -> None:
        CACHE_FILE.write_text(
            json.dumps(
                {
                    "timestamp": report.timestamp,
                    "advantage_vector": asdict(report.advantage_vector),
                    "top_hidden_markets": report.top_hidden_markets,
                    "best_price_zone": report.best_price_zone,
                    "anti_refusal_offer": report.anti_refusal_offer,
                    "next_best_actions": report.next_best_actions,
                    "positioning_statement": report.positioning_statement,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


sovereign_advantage_engine = SovereignAdvantageEngine()
