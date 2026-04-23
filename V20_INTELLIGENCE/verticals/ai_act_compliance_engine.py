"""
NAYA V20 — AI Act Compliance Engine
══════════════════════════════════════════════════════════════════════════════
EU AI Act risk classification and compliance gap assessment.

DOCTRINE:
  The EU AI Act entered into force on 1 August 2024.  Industrial companies
  deploying AI in transport, energy, manufacturing and healthcare face HIGH
  risk obligations with fines up to €35M or 7% of global turnover.

  NAYA sells AI Act compliance assessment as an add-on to OT audit packages
  (€15k–€50k per system assessed).

RISK TIERS:
  UNACCEPTABLE — Prohibited outright (social scoring, subliminal manipulation)
  HIGH         — Full conformity assessment, technical docs, human oversight
  LIMITED      — Transparency obligations only (chatbots, deepfakes)
  MINIMAL      — No specific obligation

DEADLINES:
  2025-02-02 — UNACCEPTABLE risk provisions apply
  2026-08-02 — HIGH risk (Annex I) provisions apply
  2027-08-02 — All remaining provisions apply
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.AI_ACT_COMPLIANCE")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "ai_act_compliance_engine.json"

HIGH_RISK_SECTORS = ["transport", "energy", "healthcare", "manufacturing"]

HIGH_RISK_OBLIGATIONS = [
    "conformity_assessment",
    "technical_documentation",
    "human_oversight",
    "data_governance",
    "accuracy_robustness",
]

_UNACCEPTABLE_CAPS = {
    "social_scoring",
    "subliminal_manipulation",
    "real_time_biometric_public",
}
_HIGH_RISK_CAPS = {
    "biometric",
    "critical_infrastructure",
    "employment",
    "education",
    "law_enforcement",
}
_LIMITED_CAPS = {"chatbot", "deepfake", "emotion_recognition"}

_DEADLINES = [
    {"deadline": "2025-02-02", "applies_to": "UNACCEPTABLE risk systems"},
    {"deadline": "2026-08-02", "applies_to": "HIGH risk systems"},
    {"deadline": "2027-08-02", "applies_to": "All AI systems"},
]


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AIActAssessment:
    """EU AI Act risk classification result for a single AI system."""

    assessment_id: str
    company: str
    system_name: str
    use_case: str
    sector: str
    risk_category: str               # UNACCEPTABLE | HIGH | LIMITED | MINIMAL
    applicable_obligations: List[str]
    compliance_gap_score: int        # 0-100, higher = more gaps
    estimated_remediation_eur: float
    deadline_applicable: str
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIActComplianceEngine:
    """
    Classifies AI systems under the EU AI Act and produces compliance gap reports.

    Thread-safe singleton.  Persists all assessments to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._assessments: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._assessments = data.get("assessments", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "assessments": self._assessments,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def assess_ai_system(
        self,
        company: str,
        system_name: str,
        use_case: str,
        sector: str,
        capabilities: List[str],
    ) -> AIActAssessment:
        """
        Classify an AI system under the EU AI Act risk framework.

        Args:
            company: Deploying company name.
            system_name: AI system name/identifier.
            use_case: Short description of the use case.
            sector: Industry sector of deployment.
            capabilities: List of capability labels (e.g. ["biometric", "chatbot"]).

        Returns:
            AIActAssessment with risk category, obligations and remediation estimate.
        """
        assessment_id = _sha256(company + system_name)[:12]
        cap_set = set(capabilities)

        # Classify risk tier (descending severity)
        if cap_set & _UNACCEPTABLE_CAPS:
            risk_category = "UNACCEPTABLE"
        elif sector in HIGH_RISK_SECTORS or cap_set & _HIGH_RISK_CAPS:
            risk_category = "HIGH"
        elif cap_set & _LIMITED_CAPS:
            risk_category = "LIMITED"
        else:
            risk_category = "MINIMAL"

        # Obligations
        obligations_map = {
            "HIGH": HIGH_RISK_OBLIGATIONS,
            "LIMITED": ["transparency_notice"],
            "MINIMAL": [],
            "UNACCEPTABLE": ["prohibited_deployment_ban"],
        }
        applicable_obligations = obligations_map[risk_category]

        # Gap score and remediation cost
        gap_map = {"UNACCEPTABLE": 100, "HIGH": 75, "LIMITED": 40, "MINIMAL": 10}
        cost_map = {"HIGH": 50_000.0, "LIMITED": 15_000.0, "MINIMAL": 2_000.0, "UNACCEPTABLE": 0.0}
        deadline_map = {
            "UNACCEPTABLE": "2025-02-02",
            "HIGH": "2026-08-02",
            "LIMITED": "2027-08-02",
            "MINIMAL": "2027-08-02",
        }

        assessment = AIActAssessment(
            assessment_id=assessment_id,
            company=company,
            system_name=system_name,
            use_case=use_case,
            sector=sector,
            risk_category=risk_category,
            applicable_obligations=applicable_obligations,
            compliance_gap_score=gap_map[risk_category],
            estimated_remediation_eur=cost_map[risk_category],
            deadline_applicable=deadline_map[risk_category],
        )

        with self._lock:
            self._assessments[assessment_id] = asdict(assessment)
        self._save()
        return assessment

    def get_upcoming_deadlines(self) -> List[Dict]:
        """
        Return the AI Act compliance deadline schedule.

        Returns:
            List of dicts with deadline (ISO date str) and applies_to description.
        """
        return list(_DEADLINES)

    def generate_compliance_brief(self, assessment_id: str) -> str:
        """
        Generate a human-readable compliance brief for a stored assessment.

        Args:
            assessment_id: Target assessment identifier.

        Returns:
            Multi-line text brief.

        Raises:
            ValueError: If assessment_id is not found.
        """
        with self._lock:
            data = self._assessments.get(assessment_id)
        if not data:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        lines = [
            "═══════════════════════════════════════════════════════",
            "  EU AI ACT — COMPLIANCE BRIEF",
            "═══════════════════════════════════════════════════════",
            f"  Entreprise        : {data['company']}",
            f"  Système IA        : {data['system_name']}",
            f"  Cas d'usage       : {data['use_case']}",
            f"  Secteur           : {data['sector']}",
            f"  Catégorie risque  : {data['risk_category']}",
            f"  Score de gaps     : {data['compliance_gap_score']}/100",
            f"  Coût remédiation  : {data['estimated_remediation_eur']:,.0f} EUR",
            f"  Deadline clé      : {data['deadline_applicable']}",
            "",
            "  OBLIGATIONS APPLICABLES:",
        ]
        for ob in data["applicable_obligations"]:
            lines.append(f"    - {ob}")
        lines.append("═══════════════════════════════════════════════════════")
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_assessments, high_risk_count, avg_gap_score.
        """
        with self._lock:
            assessments = list(self._assessments.values())
        total = len(assessments)
        high_risk = sum(1 for a in assessments if a["risk_category"] == "HIGH")
        avg_gap = (
            sum(a["compliance_gap_score"] for a in assessments) / total
            if total > 0
            else 0.0
        )
        return {
            "total_assessments": total,
            "high_risk_count": high_risk,
            "avg_gap_score": round(avg_gap, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_ai_act: Optional[AIActComplianceEngine] = None


def get_ai_act_compliance_engine() -> AIActComplianceEngine:
    """Return the process-wide singleton AIActComplianceEngine instance."""
    global _ai_act
    if _ai_act is None:
        _ai_act = AIActComplianceEngine()
    return _ai_act
