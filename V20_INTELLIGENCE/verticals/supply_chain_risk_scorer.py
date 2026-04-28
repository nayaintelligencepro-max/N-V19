"""
NAYA V20 — Supply Chain Risk Scorer
══════════════════════════════════════════════════════════════════════════════
Cyber risk scoring for industrial supply chains under NIS2 Article 21.

DOCTRINE:
  NIS2 Directive (EU) 2022/2555, Article 21 mandates that essential entities
  assess and manage the cyber risks of their suppliers.  Non-compliance:
  up to €10M or 2% of global turnover.

  NAYA sells supply-chain risk assessments as standalone engagements
  (€8k–€25k per assessment) OR as mandatory add-ons to OT audit packages.

SCORING MODEL:
  Base 50 (neutral)
  Certifications reduce risk: ISO27001 (-15), IEC62443 (-10), SOC2 (-5)
  Known vulnerabilities increase risk: +5 per CVE (max +30)
  SME proxy (< 50 employees): +10 (no dedicated security team)
  Country risk (non-EU/CH): +5

RISK LEVELS:
  CRITICAL ≥ 80 | HIGH ≥ 60 | MEDIUM ≥ 40 | LOW < 40
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SUPPLY_CHAIN_RISK")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "supply_chain_risk_scorer.json"

_LOW_RISK_COUNTRIES = {
    "France", "Germany", "Netherlands", "UK", "Belgium", "Switzerland",
}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SupplierProfile:
    """Cyber risk profile for a single supplier."""

    supplier_id: str
    name: str
    country: str
    sector: str
    employee_count: int
    has_certifications: List[str]
    known_vulnerabilities: int
    cyber_risk_score: float    # 0-100
    risk_level: str            # CRITICAL | HIGH | MEDIUM | LOW
    last_scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SupplyChainReport:
    """Aggregate cyber risk report for a customer's full supplier base."""

    report_id: str
    customer_company: str
    total_suppliers: int
    critical_suppliers: int
    high_risk_suppliers: int
    overall_chain_score: float
    nis2_compliance_rate: float
    recommendations: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SupplyChainRiskScorer:
    """
    Registers suppliers, scores them individually, and generates NIS2-aligned
    supply-chain risk reports.

    Thread-safe singleton.  Persists to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._suppliers: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._suppliers = data.get("suppliers", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "suppliers": self._suppliers,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Scoring logic
    # ──────────────────────────────────────────────────────────────────────

    def score_supplier(self, supplier_id: str) -> float:
        """
        (Re)compute and persist the cyber risk score for a registered supplier.

        Args:
            supplier_id: Target supplier identifier.

        Returns:
            Computed risk score clamped to [0, 100].

        Raises:
            ValueError: If supplier_id is not found.
        """
        with self._lock:
            data = self._suppliers.get(supplier_id)
        if not data:
            raise ValueError(f"Supplier '{supplier_id}' not found.")

        certs = data.get("has_certifications", [])
        score = 50.0

        if "ISO27001" in certs:
            score -= 15
        if "IEC62443" in certs:
            score -= 10
        if "SOC2" in certs:
            score -= 5

        vuln_penalty = min(30, data.get("known_vulnerabilities", 0) * 5)
        score += vuln_penalty

        if data.get("employee_count", 0) < 50:
            score += 10

        if data.get("country", "") not in _LOW_RISK_COUNTRIES:
            score += 5

        score = max(0.0, min(100.0, score))

        if score >= 80:
            risk_level = "CRITICAL"
        elif score >= 60:
            risk_level = "HIGH"
        elif score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        with self._lock:
            self._suppliers[supplier_id]["cyber_risk_score"] = score
            self._suppliers[supplier_id]["risk_level"] = risk_level
            self._suppliers[supplier_id]["last_scored_at"] = datetime.now(timezone.utc).isoformat()

        self._save()
        return score

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def register_supplier(
        self,
        supplier_id: str,
        name: str,
        country: str,
        sector: str,
        employee_count: int,
        has_certifications: List[str],
        known_vulnerabilities: int = 0,
    ) -> SupplierProfile:
        """
        Register a supplier and immediately compute its cyber risk score.

        Args:
            supplier_id: Unique identifier.
            name: Supplier company name.
            country: Country of incorporation.
            sector: Industry sector.
            employee_count: Approximate headcount.
            has_certifications: List of held certifications (ISO27001, IEC62443, SOC2…).
            known_vulnerabilities: Number of publicly disclosed CVEs.

        Returns:
            SupplierProfile with score and risk level populated.
        """
        profile_data = {
            "supplier_id": supplier_id,
            "name": name,
            "country": country,
            "sector": sector,
            "employee_count": employee_count,
            "has_certifications": has_certifications,
            "known_vulnerabilities": known_vulnerabilities,
            "cyber_risk_score": 50.0,
            "risk_level": "MEDIUM",
            "last_scored_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._suppliers[supplier_id] = profile_data
        self.score_supplier(supplier_id)

        with self._lock:
            return SupplierProfile(**self._suppliers[supplier_id])

    def assess_supply_chain(
        self, customer_company: str, supplier_ids: List[str]
    ) -> SupplyChainReport:
        """
        Produce an aggregate NIS2-aligned report for a set of suppliers.

        Args:
            customer_company: Name of the entity commissioning the assessment.
            supplier_ids: List of registered supplier identifiers to include.

        Returns:
            SupplyChainReport with metrics and prioritised recommendations.
        """
        report_id = _sha256(customer_company + str(time.time()))[:12]

        with self._lock:
            supplier_data = [
                self._suppliers[sid]
                for sid in supplier_ids
                if sid in self._suppliers
            ]

        total = len(supplier_data)
        critical = sum(1 for s in supplier_data if s["risk_level"] == "CRITICAL")
        high = sum(1 for s in supplier_data if s["risk_level"] == "HIGH")

        overall_score = (
            sum(s["cyber_risk_score"] for s in supplier_data) / total
            if total > 0
            else 0.0
        )

        compliant = sum(
            1 for s in supplier_data
            if "ISO27001" in s["has_certifications"] or "IEC62443" in s["has_certifications"]
        )
        nis2_rate = compliant / total if total > 0 else 0.0

        recommendations = []
        if critical > 0:
            recommendations.append(
                f"Audit immédiat de {critical} fournisseur(s) CRITIQUE(S) — isoler ou remplacer."
            )
        if nis2_rate < 0.5:
            recommendations.append(
                "Moins de 50% des fournisseurs sont certifiés — plan de mise en conformité NIS2 requis."
            )
        if overall_score > 60:
            recommendations.append(
                "Score chaîne global élevé — envisager des clauses contractuelles de cybersécurité."
            )
        if not recommendations:
            recommendations.append("Chaîne d'approvisionnement à risque maîtrisé. Maintenir la surveillance annuelle.")

        report = SupplyChainReport(
            report_id=report_id,
            customer_company=customer_company,
            total_suppliers=total,
            critical_suppliers=critical,
            high_risk_suppliers=high,
            overall_chain_score=round(overall_score, 2),
            nis2_compliance_rate=round(nis2_rate, 4),
            recommendations=recommendations,
        )
        return report

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_suppliers, critical_count, avg_risk_score.
        """
        with self._lock:
            suppliers = list(self._suppliers.values())
        total = len(suppliers)
        critical = sum(1 for s in suppliers if s["risk_level"] == "CRITICAL")
        avg_score = (
            sum(s["cyber_risk_score"] for s in suppliers) / total
            if total > 0
            else 0.0
        )
        return {
            "total_suppliers": total,
            "critical_count": critical,
            "avg_risk_score": round(avg_score, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_scorer: Optional[SupplyChainRiskScorer] = None


def get_supply_chain_risk_scorer() -> SupplyChainRiskScorer:
    """Return the process-wide singleton SupplyChainRiskScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = SupplyChainRiskScorer()
    return _scorer
