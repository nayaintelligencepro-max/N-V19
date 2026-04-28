"""
NAYA V21 — IEC 62443 Compliance Portal
Dashboard self-service DSI/RSSI : upload docs → analyse gaps automatique.
Abonnement : 2 000 EUR/mois/client.
"""
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SAAS_NIS2.IEC62443_PORTAL")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "saas_nis2"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── IEC 62443 Security Levels ─────────────────────────────────────────────────
IEC62443_REQUIREMENTS = {
    "SL1": [
        {"id": "SL1-01", "req": "Identification et authentification des utilisateurs humains", "weight": 5},
        {"id": "SL1-02", "req": "Gestion des comptes et droits d'accès", "weight": 5},
        {"id": "SL1-03", "req": "Protection des communications (chiffrement basique)", "weight": 5},
        {"id": "SL1-04", "req": "Journalisation des événements de sécurité", "weight": 5},
        {"id": "SL1-05", "req": "Sauvegardes régulières avec tests de restauration", "weight": 5},
    ],
    "SL2": [
        {"id": "SL2-01", "req": "Authentification multi-facteurs pour accès privilégiés", "weight": 8},
        {"id": "SL2-02", "req": "Segmentation réseau OT/IT avec firewall industriel", "weight": 8},
        {"id": "SL2-03", "req": "Détection des intrusions (IDS/IPS) sur réseau OT", "weight": 8},
        {"id": "SL2-04", "req": "Gestion des correctifs avec fenêtres de maintenance", "weight": 7},
        {"id": "SL2-05", "req": "Contrôle de l'intégrité des logiciels et firmware", "weight": 7},
        {"id": "SL2-06", "req": "Protocole de réponse aux incidents documenté et testé", "weight": 8},
    ],
    "SL3": [
        {"id": "SL3-01", "req": "Zero-trust architecture pour accès OT", "weight": 10},
        {"id": "SL3-02", "req": "Surveillance comportementale (SIEM/SOC OT)", "weight": 10},
        {"id": "SL3-03", "req": "Analyse de vulnérabilités automatisée des composants SCADA", "weight": 10},
        {"id": "SL3-04", "req": "Plan de continuité OT avec RTO < 4h", "weight": 10},
        {"id": "SL3-05", "req": "Audit externe IEC 62443 par organisme accrédité", "weight": 10},
    ],
    "SL4": [
        {"id": "SL4-01", "req": "Isolation physique et logique des systèmes critiques (air-gap)", "weight": 15},
        {"id": "SL4-02", "req": "Cryptographie avancée (post-quantique recommandée)", "weight": 12},
        {"id": "SL4-03", "req": "Red team OT spécialisé tous les 6 mois", "weight": 12},
        {"id": "SL4-04", "req": "Résilience multi-sites avec basculement automatique", "weight": 12},
    ],
}


@dataclass
class ComplianceGap:
    """Un gap IEC 62443 identifié."""
    gap_id: str
    level: str       # SL1/SL2/SL3/SL4
    requirement: str
    status: str      # missing|partial|compliant
    priority: str    # critical|high|medium|low
    remediation_cost_eur: int
    remediation_weeks: int
    guidance: str


@dataclass
class IEC62443Report:
    """Rapport de conformité IEC 62443 complet."""
    report_id: str
    company: str
    sector: str
    contact_email: str
    compliance_scores: Dict[str, int]  # {SL1: 80, SL2: 45, SL3: 20, SL4: 0}
    overall_score: int
    gaps: List[ComplianceGap]
    roadmap: List[str]
    estimated_remediation_eur: int
    upsell_proposal: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class IEC62443Portal:
    """
    Portail IEC 62443 self-service.
    Analyse les réponses DSI/RSSI et génère un rapport de conformité complet.
    """

    def __init__(self):
        self._reports: Dict[str, IEC62443Report] = {}
        self._load_data()
        log.info("✅ IEC62443Portal initialisé")

    def _data_path(self) -> Path:
        return DATA_DIR / "iec62443_reports.json"

    def _load_data(self) -> None:
        p = self._data_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for k, v in raw.items():
                    v["gaps"] = [ComplianceGap(**g) for g in v.get("gaps", [])]
                    self._reports[k] = IEC62443Report(**v)
            except Exception as exc:
                log.warning("IEC62443 data load error: %s", exc)

    def _save_data(self) -> None:
        p = self._data_path()
        try:
            p.write_text(json.dumps(
                {k: v.to_dict() for k, v in self._reports.items()},
                ensure_ascii=False, indent=2,
            ))
        except Exception as exc:
            log.warning("IEC62443 save error: %s", exc)

    def get_requirements(self) -> Dict[str, List[Dict]]:
        """Retourne les exigences IEC 62443 par niveau."""
        return IEC62443_REQUIREMENTS

    def analyze_compliance(
        self,
        company: str,
        sector: str,
        contact_email: str,
        responses: Dict[str, str],  # {req_id: "compliant"|"partial"|"missing"}
    ) -> IEC62443Report:
        """
        Analyse la conformité IEC 62443 et génère un rapport complet avec roadmap.
        """
        compliance_scores: Dict[str, int] = {}
        all_gaps: List[ComplianceGap] = []

        for level, reqs in IEC62443_REQUIREMENTS.items():
            total_weight = sum(r["weight"] for r in reqs)
            earned = 0
            for req in reqs:
                status = responses.get(req["id"], "missing")
                if status == "compliant":
                    earned += req["weight"]
                elif status == "partial":
                    earned += req["weight"] // 2
                else:
                    # Gap identified
                    priority = self._compute_priority(level, req["weight"])
                    cost = self._estimate_cost(level, req["weight"])
                    gap = ComplianceGap(
                        gap_id=req["id"],
                        level=level,
                        requirement=req["req"],
                        status=status,
                        priority=priority,
                        remediation_cost_eur=cost,
                        remediation_weeks=self._estimate_weeks(level),
                        guidance=f"Implémenter {req['req']} — niveau {level}",
                    )
                    all_gaps.append(gap)

            score = round(earned * 100 / total_weight) if total_weight > 0 else 0
            compliance_scores[level] = score

        # Score global (pondéré SL1×40 + SL2×30 + SL3×20 + SL4×10)
        weights = {"SL1": 0.40, "SL2": 0.30, "SL3": 0.20, "SL4": 0.10}
        overall = round(sum(compliance_scores.get(lvl, 0) * w for lvl, w in weights.items()))

        # Roadmap priorisée
        roadmap = self._build_roadmap(all_gaps)

        # Total coût remédiation
        total_cost = sum(g.remediation_cost_eur for g in all_gaps)

        # Proposition upsell
        upsell = self._build_upsell(company, overall, total_cost)

        report = IEC62443Report(
            report_id=str(uuid.uuid4()),
            company=company,
            sector=sector,
            contact_email=contact_email,
            compliance_scores=compliance_scores,
            overall_score=overall,
            gaps=all_gaps,
            roadmap=roadmap,
            estimated_remediation_eur=total_cost,
            upsell_proposal=upsell,
        )
        self._reports[report.report_id] = report
        self._save_data()
        log.info(
            "IEC62443 Report %s: %s overall=%d%% gaps=%d cost=%dEUR",
            report.report_id, company, overall, len(all_gaps), total_cost,
        )
        return report

    def _compute_priority(self, level: str, weight: int) -> str:
        if level == "SL4" or (level == "SL3" and weight >= 10):
            return "critical"
        if level in ("SL2", "SL3"):
            return "high"
        if weight >= 7:
            return "medium"
        return "low"

    def _estimate_cost(self, level: str, weight: int) -> int:
        base = {"SL1": 2000, "SL2": 5000, "SL3": 12000, "SL4": 25000}
        return base.get(level, 5000) * (weight // 5 + 1)

    def _estimate_weeks(self, level: str) -> int:
        return {"SL1": 2, "SL2": 4, "SL3": 8, "SL4": 16}.get(level, 4)

    def _build_roadmap(self, gaps: List[ComplianceGap]) -> List[str]:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_gaps = sorted(gaps, key=lambda g: priority_order.get(g.priority, 4))
        roadmap = []
        phase = 1
        for chunk in [sorted_gaps[:3], sorted_gaps[3:8], sorted_gaps[8:]]:
            if not chunk:
                break
            items = " | ".join(f"{g.gap_id}:{g.requirement[:40]}" for g in chunk)
            roadmap.append(f"PHASE {phase}: {items}")
            phase += 1
        return roadmap

    def _build_upsell(self, company: str, overall: int, total_cost: int) -> str:
        if overall < 40:
            tier = "Pack Remédiation Complète"
            price = max(25_000, total_cost // 2)
        elif overall < 70:
            tier = "Pack Mise en Conformité"
            price = max(15_000, total_cost // 3)
        else:
            tier = "Pack Maintenance & Surveillance"
            price = 8_000
        return (
            f"Proposition pour {company}: {tier} — {price:,} EUR. "
            f"Score actuel {overall}% → cible 90%+ en 6 mois. "
            f"Contact NAYA pour devis personnalisé."
        )

    def get_report(self, report_id: str) -> Optional[IEC62443Report]:
        return self._reports.get(report_id)

    def get_stats(self) -> Dict:
        total = len(self._reports)
        if not total:
            return {"total": 0, "avg_score": 0}
        scores = [r.overall_score for r in self._reports.values()]
        return {
            "total": total,
            "avg_score": round(sum(scores) / total, 1),
            "total_upsell_opportunities": total,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_portal: Optional[IEC62443Portal] = None


def get_iec62443_portal() -> IEC62443Portal:
    global _portal
    if _portal is None:
        _portal = IEC62443Portal()
    return _portal
