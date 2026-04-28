"""
NAYA V20 — Quantum Safe Advisor
══════════════════════════════════════════════════════════════════════════════
Post-quantum cryptography advisory based on NIST PQC standards (FIPS 203/204/205).

DOCTRINE:
  Industrial control systems have operational lifetimes of 15–30 years.
  Cryptographic algorithms deployed today must still be secure in 2040+.
  "Harvest now, decrypt later" attacks make migration urgent even before
  quantum computers exist at scale.

  NAYA sells PQC migration roadmaps as a €115k engagement
  (115 days × €1,500/day) to OIVs, defence contractors and energy operators.

NIST PQC STANDARDS (FIPS 2024):
  - CRYSTALS-Kyber  (FIPS 203) → Key Encapsulation
  - CRYSTALS-Dilithium (FIPS 204) → Digital Signatures
  - SPHINCS+ (FIPS 205) → Digital Signatures (hash-based)
  - FALCON → Digital Signatures (NTRU lattice)
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

log = logging.getLogger("NAYA.QUANTUM_SAFE_ADVISOR")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "quantum_safe_advisor.json"

VULNERABLE_ALGORITHMS = ["RSA", "ECDSA", "ECDH", "DH"]

NIST_PQC: List[Dict] = [
    {
        "name": "CRYSTALS-Kyber",
        "type": "KEM",
        "nist_level": 3,
        "use_case": "key_exchange",
        "fips": "203",
    },
    {
        "name": "CRYSTALS-Dilithium",
        "type": "signature",
        "nist_level": 3,
        "use_case": "digital_signatures",
        "fips": "204",
    },
    {
        "name": "SPHINCS+",
        "type": "signature",
        "nist_level": 3,
        "use_case": "digital_signatures",
        "fips": "205",
    },
    {
        "name": "FALCON",
        "type": "signature",
        "nist_level": 5,
        "use_case": "digital_signatures",
        "fips": "pending",
    },
]


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class CryptoAssessment:
    """Assessment of a company's quantum vulnerability."""

    assessment_id: str
    company: str
    sector: str
    vulnerable_algorithms: List[str]
    quantum_risk_score: int          # 0-100
    years_to_risk: int
    recommended_pqc: List[str]
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MigrationRoadmap:
    """Phased PQC migration plan derived from a CryptoAssessment."""

    roadmap_id: str
    assessment_id: str
    phases: List[Dict]
    total_effort_days: int
    estimated_cost_eur: float
    priority_actions: List[str]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QuantumSafeAdvisor:
    """
    Assesses industrial companies' quantum vulnerability and generates
    NIST-aligned PQC migration roadmaps.

    Thread-safe singleton.  Persists to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._assessments: Dict[str, Dict] = {}
        self._roadmaps: Dict[str, Dict] = {}
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
                    self._roadmaps = data.get("roadmaps", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "assessments": self._assessments,
                        "roadmaps": self._roadmaps,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def assess_crypto_posture(
        self,
        company: str,
        sector: str,
        crypto_inventory: List[Dict],
    ) -> CryptoAssessment:
        """
        Assess a company's quantum vulnerability based on its crypto inventory.

        Args:
            company: Company name.
            sector: Industry sector.
            crypto_inventory: List of dicts, each with at least {"algorithm": str}.

        Returns:
            CryptoAssessment with risk score and PQC recommendations.
        """
        assessment_id = _sha256(company + sector)[:12]

        vulnerable = [
            item["algorithm"]
            for item in crypto_inventory
            if item.get("algorithm") in VULNERABLE_ALGORITHMS
        ]

        quantum_risk_score = min(100, len(vulnerable) * 25)
        years_to_risk = max(3, 10 - len(vulnerable) * 2)
        recommended_pqc = [a["name"] for a in NIST_PQC][: len(vulnerable) + 1]

        assessment = CryptoAssessment(
            assessment_id=assessment_id,
            company=company,
            sector=sector,
            vulnerable_algorithms=vulnerable,
            quantum_risk_score=quantum_risk_score,
            years_to_risk=years_to_risk,
            recommended_pqc=recommended_pqc,
        )

        with self._lock:
            self._assessments[assessment_id] = asdict(assessment)
        self._save()
        return assessment

    def generate_migration_roadmap(self, assessment_id: str) -> MigrationRoadmap:
        """
        Generate a phased PQC migration roadmap for a given assessment.

        Args:
            assessment_id: ID returned by assess_crypto_posture().

        Returns:
            MigrationRoadmap with phases, cost and priority actions.

        Raises:
            ValueError: If assessment_id is not found.
        """
        if assessment_id not in self._assessments:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        roadmap_id = _sha256(assessment_id + str(time.time()))[:12]
        phases = [
            {"phase": 1, "name": "Inventory & Risk Assessment", "duration_days": 10},
            {"phase": 2, "name": "PQC Algorithm Selection", "duration_days": 15},
            {"phase": 3, "name": "Pilot Implementation", "duration_days": 30},
            {"phase": 4, "name": "Full Migration", "duration_days": 60},
        ]
        total_effort_days = sum(p["duration_days"] for p in phases)
        estimated_cost_eur = total_effort_days * 1_500.0
        priority_actions = [
            "Audit inventaire cryptographique",
            "Former équipes PQC",
            "Migrer PKI vers CRYSTALS-Dilithium",
        ]

        roadmap = MigrationRoadmap(
            roadmap_id=roadmap_id,
            assessment_id=assessment_id,
            phases=phases,
            total_effort_days=total_effort_days,
            estimated_cost_eur=estimated_cost_eur,
            priority_actions=priority_actions,
        )

        with self._lock:
            self._roadmaps[roadmap_id] = asdict(roadmap)
        self._save()
        return roadmap

    def get_pqc_algorithms(self) -> List[Dict]:
        """
        Return the full NIST PQC algorithm catalogue.

        Returns:
            List of algorithm dicts with name, type, nist_level, use_case.
        """
        return list(NIST_PQC)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_assessments and total_roadmaps.
        """
        with self._lock:
            return {
                "total_assessments": len(self._assessments),
                "total_roadmaps": len(self._roadmaps),
            }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_advisor: Optional[QuantumSafeAdvisor] = None


def get_quantum_safe_advisor() -> QuantumSafeAdvisor:
    """Return the process-wide singleton QuantumSafeAdvisor instance."""
    global _advisor
    if _advisor is None:
        _advisor = QuantumSafeAdvisor()
    return _advisor
