"""
NAYA V20 — Insurance Advisory Engine
══════════════════════════════════════════════════════════════════════════════
Critical infrastructure cyber insurance advisory and audit referral.

DOCTRINE:
  Cyber insurance underwriters require OT audits before issuing policies to
  industrial operators.  NAYA positions itself as the preferred pre-audit
  partner for insurers, generating a dual revenue stream:
    1. Audit fee from the industrial company (€5k–€20k)
    2. Referral commission from the insurer (12% of audit fee)

  Insurability score drives the upsell: low score → mandatory OT audit
  before any insurer will quote → NAYA audit.

PARTNER INSURERS:
  AXA XL, Beazley, Chubb, Hiscox, Tokio Marine
  (introductions facilitated through NAYA's advisory network)
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

log = logging.getLogger("NAYA.INSURANCE_ADVISORY")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "insurance_advisory_engine.json"

PARTNER_INSURERS = ["AXA XL", "Beazley", "Chubb", "Hiscox", "Tokio Marine"]

_COMMISSION_RATE = 0.12


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class InsurabilityAssessment:
    """Cyber insurability assessment for an industrial operator."""

    assessment_id: str
    company: str
    sector: str
    insurability_score: int          # 0-100
    estimated_premium_eur: float
    required_audits: List[str]
    blocking_factors: List[str]
    recommended_insurers: List[str]
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InsuranceAdvisoryEngine:
    """
    Evaluates the cyber insurability of industrial operators and generates
    pre-audit reports to support underwriting conversations.

    Thread-safe singleton.  Persists to DATA_FILE.
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

    def assess_insurability(
        self,
        company: str,
        sector: str,
        revenue_eur: float,
        has_ot_audit: bool,
        last_incident_years_ago: int,
        certifications: List[str],
    ) -> InsurabilityAssessment:
        """
        Evaluate a company's cyber insurability profile.

        Args:
            company: Company name.
            sector: Industry sector.
            revenue_eur: Annual revenue in EUR (used to price premium).
            has_ot_audit: True if a recent OT audit was conducted.
            last_incident_years_ago: Years since last confirmed security incident
                                     (999 if never).
            certifications: List of held certifications (ISO27001, IEC62443…).

        Returns:
            InsurabilityAssessment with score, premium estimate and recommendations.
        """
        assessment_id = _sha256(company + sector)[:12]

        score = 50
        if has_ot_audit:
            score += 20
        if "ISO27001" in certifications:
            score += 10
        if "IEC62443" in certifications:
            score += 10
        if last_incident_years_ago < 2:
            score -= 30
        elif last_incident_years_ago < 5:
            score -= 10

        score = max(0, min(100, score))

        estimated_premium = revenue_eur * 0.005 * (1 + (100 - score) / 100)

        required_audits = ["IEC 62443 OT Audit"]
        if score < 60:
            required_audits.append("NIS2 Gap Analysis")

        blocking_factors = []
        if last_incident_years_ago < 2:
            blocking_factors.append("Incident récent < 2 ans")

        recommended_insurers = (
            PARTNER_INSURERS[:3] if score >= 60 else PARTNER_INSURERS[:2]
        )

        assessment = InsurabilityAssessment(
            assessment_id=assessment_id,
            company=company,
            sector=sector,
            insurability_score=score,
            estimated_premium_eur=round(estimated_premium, 2),
            required_audits=required_audits,
            blocking_factors=blocking_factors,
            recommended_insurers=recommended_insurers,
        )

        with self._lock:
            self._assessments[assessment_id] = asdict(assessment)
        self._save()
        return assessment

    def generate_pre_audit_report(self, assessment_id: str) -> str:
        """
        Generate a pre-audit report suitable for sharing with an insurer.

        Args:
            assessment_id: Target assessment identifier.

        Returns:
            Multi-line formatted report text.

        Raises:
            ValueError: If assessment_id is not found.
        """
        with self._lock:
            data = self._assessments.get(assessment_id)
        if not data:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        lines = [
            "═══════════════════════════════════════════════════════",
            "  PRÉ-RAPPORT D'ASSURANCE CYBER OT — NAYA ADVISORY",
            "═══════════════════════════════════════════════════════",
            f"  Entreprise            : {data['company']}",
            f"  Secteur               : {data['sector']}",
            f"  Score assurabilité    : {data['insurability_score']}/100",
            f"  Prime estimée         : {data['estimated_premium_eur']:,.0f} EUR/an",
            "",
            "  AUDITS REQUIS AVANT SOUSCRIPTION:",
        ]
        for audit in data["required_audits"]:
            lines.append(f"    ✓ {audit}")
        if data["blocking_factors"]:
            lines.append("")
            lines.append("  FACTEURS BLOQUANTS:")
            for bf in data["blocking_factors"]:
                lines.append(f"    ✗ {bf}")
        lines.append("")
        lines.append("  ASSUREURS RECOMMANDÉS:")
        for ins in data["recommended_insurers"]:
            lines.append(f"    → {ins}")
        lines.append("═══════════════════════════════════════════════════════")
        return "\n".join(lines)

    def get_partner_insurers(self) -> List[Dict]:
        """
        Return the list of partner insurers.

        Returns:
            List of dicts with name and specialty.
        """
        return [{"name": insurer, "specialty": "cyber_ot"} for insurer in PARTNER_INSURERS]

    def calculate_commission(self, audit_fee_eur: float) -> float:
        """
        Calculate NAYA's referral commission for a given audit fee.

        Args:
            audit_fee_eur: Audit invoice amount in EUR.

        Returns:
            Commission amount in EUR (12% of audit_fee_eur).
        """
        return round(audit_fee_eur * _COMMISSION_RATE, 2)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_assessments, avg_score, total_commission_potential_eur.
        """
        with self._lock:
            assessments = list(self._assessments.values())
        total = len(assessments)
        avg_score = (
            sum(a["insurability_score"] for a in assessments) / total
            if total > 0
            else 0.0
        )
        # Commission potential: assume average audit fee of €10k
        commission_potential = sum(
            self.calculate_commission(10_000) for _ in assessments
        )
        return {
            "total_assessments": total,
            "avg_score": round(avg_score, 2),
            "total_commission_potential_eur": commission_potential,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_insurance: Optional[InsuranceAdvisoryEngine] = None


def get_insurance_advisory_engine() -> InsuranceAdvisoryEngine:
    """Return the process-wide singleton InsuranceAdvisoryEngine instance."""
    global _insurance
    if _insurance is None:
        _insurance = InsuranceAdvisoryEngine()
    return _insurance
