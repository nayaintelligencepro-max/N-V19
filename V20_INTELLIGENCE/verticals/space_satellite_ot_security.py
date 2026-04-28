"""
NAYA V20 — Space & Satellite OT Security
══════════════════════════════════════════════════════════════════════════════
LEO/GEO satellite link OT security assessment.

DOCTRINE:
  As LEO constellations (Starlink, OneWeb) replace MPLS for remote OT sites
  (offshore platforms, remote mines, power substations), the attack surface of
  industrial networks expands dramatically.
  
  A compromised satellite uplink can give an attacker direct access to
  SCADA systems with no physical presence required.

  NAYA targets satellite OT security as a €10k–€40k niche where zero
  competitors have specialised (as of 2024).

PROVIDERS COVERED:
  Starlink, OneWeb, Eutelsat, Viasat, Intelsat
  (PROVIDER_VULNS updated from public CVE/ICS-CERT disclosures)
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

log = logging.getLogger("NAYA.SPACE_SATELLITE_OT")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "space_satellite_ot_security.json"

PROVIDER_VULNS: Dict[str, List[str]] = {
    "Starlink": [
        "Unencrypted terminal management",
        "Default credentials on user terminal",
        "Physical tamper vulnerability",
    ],
    "OneWeb": [
        "BGP route hijacking",
        "Unencrypted management plane",
    ],
    "Eutelsat": [
        "Signal jamming risk",
        "Legacy encryption (DES/3DES)",
    ],
    "Viasat": [
        "Ka-band signal interception",
        "Modem firmware vulnerabilities",
    ],
    "Intelsat": [
        "C-band jamming",
        "GEO orbital predictability",
        "Legacy TT&C protocols",
    ],
}

_WEAK_ENCRYPTION = {"none", "WEP", "DES", "3DES", ""}
_HARDENING_CONTROLS = [
    "Segment OT from satellite link",
    "Enable MACsec/IPsec",
    "Monitor satellite link anomalies",
    "Rotate terminal credentials quarterly",
]


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SatelliteAssessment:
    """OT security assessment for a satellite-connected industrial site."""

    assessment_id: str
    company: str
    satellite_provider: str
    link_type: str
    attack_surface_score: int        # 0-100
    critical_vulnerabilities: List[str]
    recommended_controls: List[str]
    estimated_hardening_eur: float
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SpaceSatelliteOTSecurity:
    """
    Assesses cyber risks introduced by satellite links in OT environments
    and generates hardening plans.

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

    def assess_satellite_link(
        self,
        company: str,
        satellite_provider: str,
        link_type: str,
        connected_ot_systems: List[str],
        encryption_in_use: str,
    ) -> SatelliteAssessment:
        """
        Assess the OT security risk of a satellite communication link.

        Args:
            company: Industrial company using the link.
            satellite_provider: Satellite operator name (see PROVIDER_VULNS).
            link_type: Link type (e.g. "LEO", "GEO", "VSAT").
            connected_ot_systems: List of OT system names reachable via the link.
            encryption_in_use: Encryption protocol in use (e.g. "IPsec", "none").

        Returns:
            SatelliteAssessment with attack surface score and hardening plan.
        """
        assessment_id = _sha256(company + satellite_provider)[:12]

        critical_vulnerabilities = list(
            PROVIDER_VULNS.get(satellite_provider, ["Unknown provider vulnerabilities"])
        )

        if encryption_in_use in _WEAK_ENCRYPTION:
            critical_vulnerabilities.append("Weak encryption")

        if connected_ot_systems:
            critical_vulnerabilities.append(
                "OT systems directly connected to satellite link"
            )

        attack_surface_score = min(100, 30 + len(critical_vulnerabilities) * 15)
        estimated_hardening_eur = (
            len(connected_ot_systems) * 5_000 + attack_surface_score * 200
        )

        assessment = SatelliteAssessment(
            assessment_id=assessment_id,
            company=company,
            satellite_provider=satellite_provider,
            link_type=link_type,
            attack_surface_score=attack_surface_score,
            critical_vulnerabilities=critical_vulnerabilities,
            recommended_controls=list(_HARDENING_CONTROLS),
            estimated_hardening_eur=round(estimated_hardening_eur, 2),
        )

        with self._lock:
            self._assessments[assessment_id] = asdict(assessment)
        self._save()
        return assessment

    def get_known_vulnerabilities(self, provider: str) -> List[Dict]:
        """
        Return the known vulnerability catalogue for a satellite provider.

        Args:
            provider: Satellite operator name.

        Returns:
            List of dicts with vulnerability description and severity label.
        """
        vulns = PROVIDER_VULNS.get(provider, [])
        return [{"vulnerability": v, "severity": "HIGH"} for v in vulns]

    def generate_hardening_plan(self, assessment_id: str) -> str:
        """
        Generate a formatted hardening plan for a stored assessment.

        Args:
            assessment_id: Target assessment identifier.

        Returns:
            Multi-line hardening plan text.

        Raises:
            ValueError: If assessment_id is not found.
        """
        with self._lock:
            data = self._assessments.get(assessment_id)
        if not data:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        lines = [
            "═══════════════════════════════════════════════════════",
            "  PLAN DE DURCISSEMENT — SATELLITE OT SECURITY",
            "═══════════════════════════════════════════════════════",
            f"  Entreprise   : {data['company']}",
            f"  Opérateur    : {data['satellite_provider']}",
            f"  Type de lien : {data['link_type']}",
            f"  Score surface: {data['attack_surface_score']}/100",
            f"  Coût estimé  : {data['estimated_hardening_eur']:,.0f} EUR",
            "",
            "  VULNÉRABILITÉS CRITIQUES:",
        ]
        for vuln in data["critical_vulnerabilities"]:
            lines.append(f"    ⚠ {vuln}")
        lines.append("")
        lines.append("  CONTRÔLES RECOMMANDÉS:")
        for ctrl in data["recommended_controls"]:
            lines.append(f"    ✓ {ctrl}")
        lines.append("═══════════════════════════════════════════════════════")
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_assessments, providers_covered, avg_attack_surface.
        """
        with self._lock:
            assessments = list(self._assessments.values())
        total = len(assessments)
        providers = {a["satellite_provider"] for a in assessments}
        avg_surface = (
            sum(a["attack_surface_score"] for a in assessments) / total
            if total > 0
            else 0.0
        )
        return {
            "total_assessments": total,
            "providers_covered": len(providers),
            "avg_attack_surface": round(avg_surface, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_satellite: Optional[SpaceSatelliteOTSecurity] = None


def get_space_satellite_ot_security() -> SpaceSatelliteOTSecurity:
    """Return the process-wide singleton SpaceSatelliteOTSecurity instance."""
    global _satellite
    if _satellite is None:
        _satellite = SpaceSatelliteOTSecurity()
    return _satellite
