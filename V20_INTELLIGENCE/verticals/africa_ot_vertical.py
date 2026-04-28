"""
NAYA V20 — Africa OT Vertical
══════════════════════════════════════════════════════════════════════════════
OT/IT convergence market intelligence for francophone African enterprises.

DOCTRINE:
  Francophone Africa is an under-served, rapidly industrialising market where:
    - IEC 62443 expertise is virtually absent (≤ 10 certified firms continent-wide)
    - Mining, oil & gas and utilities operate OT assets worth billions
    - Language, time zone and cultural alignment gives NAYA an asymmetric edge

  Target: 6 countries × 3 deals/year × average €35k = €630k/year
  Positioning: first-mover OT security specialist for francophone industrials

QUALIFICATION CRITERIA:
  - SCADA or PLC presence
  - ≥ 50 employees (proxy for dedicated ops team)
  - Sector with high OT risk (mining, oil_gas, utilities)

PRICING:
  Adjusted by country risk premium (exchange risk, payment risk, market depth)
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.AFRICA_OT_VERTICAL")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "africa_ot_vertical.json"

TARGET_COUNTRIES: List[Dict] = [
    {"name": "Sénégal",      "code": "SN", "risk_premium": 1.1, "language": "fr"},
    {"name": "Côte d'Ivoire","code": "CI", "risk_premium": 1.0, "language": "fr"},
    {"name": "Maroc",        "code": "MA", "risk_premium": 0.9, "language": "fr"},
    {"name": "Gabon",        "code": "GA", "risk_premium": 1.2, "language": "fr"},
    {"name": "Cameroun",     "code": "CM", "risk_premium": 1.1, "language": "fr"},
    {"name": "RDC",          "code": "CD", "risk_premium": 1.3, "language": "fr"},
]

_COUNTRY_PREMIUM: Dict[str, float] = {c["name"]: c["risk_premium"] for c in TARGET_COUNTRIES}
_COUNTRY_CODES: Dict[str, str] = {c["name"]: c["code"] for c in TARGET_COUNTRIES}

SECTOR_BUDGETS: Dict[str, Tuple[float, float]] = {
    "mining":         (40_000, 60_000),
    "oil_gas":        (50_000, 80_000),
    "agro_food":      (20_000, 35_000),
    "manufacturing":  (15_000, 30_000),
    "utilities":      (25_000, 45_000),
}

_HIGH_VALUE_SECTORS = {"mining", "oil_gas"}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AfricaProspect:
    """Qualified OT prospect in francophone Africa."""

    prospect_id: str
    company: str
    country: str
    sector: str
    employee_count: int
    has_scada: bool
    has_plc: bool
    ot_maturity_level: str           # NASCENT | EMERGING | DEVELOPING
    estimated_budget_eur: float
    recommended_service: str
    priority_score: int              # 0-100
    qualified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AfricaOTVertical:
    """
    Qualifies OT prospects in francophone Africa and generates localised pitches.

    Thread-safe singleton.  Persists all prospects to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._prospects: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._prospects = data.get("prospects", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "prospects": self._prospects,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def qualify_prospect(
        self,
        company: str,
        country: str,
        sector: str,
        employee_count: int,
        has_scada: bool,
        has_plc: bool,
    ) -> AfricaProspect:
        """
        Qualify an African industrial company as an OT security prospect.

        Args:
            company: Company name.
            country: Country name (must be in TARGET_COUNTRIES for premium lookup).
            sector: Industry sector key (see SECTOR_BUDGETS).
            employee_count: Approximate headcount.
            has_scada: True if SCADA systems are confirmed.
            has_plc: True if PLC/DCS systems are confirmed.

        Returns:
            AfricaProspect with maturity level, budget estimate, and priority score.
        """
        prospect_id = _sha256(company + country)[:12]

        # OT maturity classification
        if has_scada and has_plc:
            ot_maturity = "DEVELOPING"
        elif has_scada or has_plc:
            ot_maturity = "EMERGING"
        else:
            ot_maturity = "NASCENT"

        # Budget estimation
        low, high = SECTOR_BUDGETS.get(sector, (10_000, 20_000))
        mid = (low + high) / 2
        risk_premium = _COUNTRY_PREMIUM.get(country, 1.0)
        estimated_budget = mid * risk_premium

        # Recommended service
        service_map = {
            "DEVELOPING": "IEC 62443 Full Compliance",
            "EMERGING":   "OT Security Audit",
            "NASCENT":    "OT Risk Assessment",
        }
        recommended_service = service_map[ot_maturity]

        # Priority score
        priority_score = 40
        if has_scada:
            priority_score += 20
        if has_plc:
            priority_score += 15
        priority_score += min(15, employee_count // 100)
        if sector in _HIGH_VALUE_SECTORS:
            priority_score += 10

        prospect = AfricaProspect(
            prospect_id=prospect_id,
            company=company,
            country=country,
            sector=sector,
            employee_count=employee_count,
            has_scada=has_scada,
            has_plc=has_plc,
            ot_maturity_level=ot_maturity,
            estimated_budget_eur=round(estimated_budget, 2),
            recommended_service=recommended_service,
            priority_score=min(100, priority_score),
        )

        with self._lock:
            self._prospects[prospect_id] = asdict(prospect)
        self._save()
        return prospect

    def generate_localized_pitch(
        self, prospect_id: str, language: str = "fr"
    ) -> str:
        """
        Generate a localised sales pitch for a stored Africa prospect.

        Args:
            prospect_id: Target prospect identifier.
            language: Language code (currently "fr" only; extensible).

        Returns:
            Multi-line pitch text.

        Raises:
            ValueError: If prospect_id is not found.
        """
        with self._lock:
            data = self._prospects.get(prospect_id)
        if not data:
            raise ValueError(f"Prospect '{prospect_id}' not found.")

        pitch = (
            f"Bonjour,\n\n"
            f"Nous accompagnons des industriels {data['sector']} en {data['country']} "
            f"dans leur conformité cybersécurité OT.\n\n"
            f"Entreprise : {data['company']}\n"
            f"Maturité OT : {data['ot_maturity_level']}\n"
            f"Service recommandé : {data['recommended_service']}\n"
            f"Budget estimé : {data['estimated_budget_eur']:,.0f} EUR\n\n"
            f"Nous proposons une évaluation gratuite de 30 minutes pour identifier "
            f"vos principaux risques OT et les premières mesures à prendre.\n\n"
            f"Cordialement,\nL'équipe NAYA Cybersécurité OT"
        )
        return pitch

    def get_target_countries(self) -> List[Dict]:
        """
        Return the list of target African countries.

        Returns:
            List of country dicts with name, code, risk_premium, language.
        """
        return list(TARGET_COUNTRIES)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_prospects, countries list, avg_budget_eur.
        """
        with self._lock:
            prospects = list(self._prospects.values())
        total = len(prospects)
        countries = list({p["country"] for p in prospects})
        avg_budget = (
            sum(p["estimated_budget_eur"] for p in prospects) / total
            if total > 0
            else 0.0
        )
        return {
            "total_prospects": total,
            "countries": countries,
            "avg_budget_eur": round(avg_budget, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_africa: Optional[AfricaOTVertical] = None


def get_africa_ot_vertical() -> AfricaOTVertical:
    """Return the process-wide singleton AfricaOTVertical instance."""
    global _africa
    if _africa is None:
        _africa = AfricaOTVertical()
    return _africa
