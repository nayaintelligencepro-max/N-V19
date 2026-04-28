"""
NAYA V20 — Annual Report Parser
══════════════════════════════════════════════════════════════════════════════
Extracts cyber budget signals from industrial annual reports using regex
heuristics applied to raw text extracted from PDF files.

DOCTRINE:
  Companies that disclose a cyber budget in their annual report have already
  approved spending.  Identifying the RSSI/CTO name from the same document
  gives NAYA a named contact and a budget anchor in a single step.

SIGNALS EXTRACTED:
  - Cyber / security budget mentions (EUR amounts with M/k multipliers)
  - Past security incidents (sentences with breach/incident keywords)
  - OT digitalisation ambitions (SCADA, ICS, Industrie 4.0 mentions)
  - RSSI and CTO names (regex on title patterns)

SCORING:
  investment_score 0–100
    base   20
    +30    if cyber_budget > 0
    +20    if past incidents found
    +15    if OT ambitions found
    +15    if RSSI name found
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import math
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.ANNUAL_REPORT_PARSER")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "annual_report_parser.json"

# Regex that captures a numeric amount followed by a multiplier and a
# cyber-related keyword within 30 characters.
_BUDGET_RE = re.compile(
    r"(\d[\d\s]{0,8})[\s]*(M€|M EUR|million|k€|k EUR|thousand)"
    r"[\s\S]{0,30}(cyber|sécurité|security)",
    re.IGNORECASE,
)
_INCIDENT_RE = re.compile(
    r"[^\.\n]*(?:incident|attaque|compromis|breach)[^\.\n]*",
    re.IGNORECASE,
)
_OT_RE = re.compile(
    r"[^\.\n]*(?:SCADA|ICS|OT\b|industrie 4\.0|digitalisation)[^\.\n]*",
    re.IGNORECASE,
)
_RSSI_RE = re.compile(
    r"(?:RSSI|CISO|Responsable\s+Sécurité)[^\n]*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.IGNORECASE,
)
_CTO_RE = re.compile(
    r"(?:CTO|DSI|Directeur\s+(?:des\s+)?Systèmes)[^\n]*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.IGNORECASE,
)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _parse_amount(number_str: str, multiplier: str) -> float:
    """Convert a raw number string and multiplier token to a float EUR amount."""
    try:
        raw = float(number_str.replace(" ", "").replace("\xa0", ""))
    except ValueError:
        return 0.0
    multiplier_lower = multiplier.lower()
    if multiplier_lower in ("m€", "m eur", "million"):
        return raw * 1_000_000
    if multiplier_lower in ("k€", "k eur", "thousand"):
        return raw * 1_000
    return raw


@dataclass
class ParsedReport:
    """Structured intelligence extracted from an industrial annual report."""

    company: str
    year: int
    sector: str
    cyber_budget_mentioned_eur: float
    past_incidents: List[str]
    ot_ambitions: List[str]
    rssi_name: str
    cto_name: str
    key_signals: List[str]
    investment_score: int     # 0-100
    parsed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnnualReportParser:
    """
    Ingests PDF text extracts from industrial annual reports and extracts
    structured intelligence signals for the NAYA prospecting pipeline.

    Thread-safe singleton.  Persists parsed reports to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._reports: List[Dict] = []
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._reports = data.get("reports", [])
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "reports": self._reports,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def ingest_report(
        self,
        company: str,
        year: int,
        sector: str,
        pdf_text_extract: str,
    ) -> ParsedReport:
        """
        Parse a raw PDF text extract and store the structured intelligence.

        Args:
            company: Company name (e.g. "Airbus SE").
            year: Fiscal year of the report.
            sector: Industry sector label.
            pdf_text_extract: Raw text extracted from the annual report PDF.

        Returns:
            ParsedReport with all extracted fields populated.
        """
        # --- Cyber budget ---------------------------------------------------
        cyber_budget = 0.0
        for m in _BUDGET_RE.finditer(pdf_text_extract):
            amount = _parse_amount(m.group(1), m.group(2))
            if amount > cyber_budget:
                cyber_budget = amount

        # --- Past incidents -------------------------------------------------
        past_incidents = [
            m.group(0).strip()[:200]
            for m in _INCIDENT_RE.finditer(pdf_text_extract)
        ]

        # --- OT ambitions ---------------------------------------------------
        ot_ambitions = [
            m.group(0).strip()[:200]
            for m in _OT_RE.finditer(pdf_text_extract)
        ]

        # --- Named executives -----------------------------------------------
        rssi_match = _RSSI_RE.search(pdf_text_extract)
        rssi_name = rssi_match.group(1).strip() if rssi_match else ""

        cto_match = _CTO_RE.search(pdf_text_extract)
        cto_name = cto_match.group(1).strip() if cto_match else ""

        # --- Investment score -----------------------------------------------
        investment_score = 20
        if cyber_budget > 0:
            investment_score += 30
        if past_incidents:
            investment_score += 20
        if ot_ambitions:
            investment_score += 15
        if rssi_name:
            investment_score += 15
        investment_score = min(100, investment_score)

        # --- Key signals ----------------------------------------------------
        key_signals = [f"budget_cyber:{cyber_budget:.0f}€"]
        key_signals += [inc[:80] for inc in past_incidents[:2]]
        key_signals += [amb[:80] for amb in ot_ambitions[:2]]

        report = ParsedReport(
            company=company,
            year=year,
            sector=sector,
            cyber_budget_mentioned_eur=cyber_budget,
            past_incidents=past_incidents,
            ot_ambitions=ot_ambitions,
            rssi_name=rssi_name,
            cto_name=cto_name,
            key_signals=key_signals,
            investment_score=investment_score,
        )

        with self._lock:
            self._reports.append(asdict(report))
        self._save()
        return report

    def get_high_value_companies(
        self, min_cyber_budget: float = 500_000
    ) -> List[ParsedReport]:
        """
        Return reports where cyber_budget_mentioned_eur >= min_cyber_budget.

        Args:
            min_cyber_budget: Minimum budget threshold in EUR.

        Returns:
            List of ParsedReport objects sorted by budget descending.
        """
        with self._lock:
            filtered = [
                r for r in self._reports
                if r["cyber_budget_mentioned_eur"] >= min_cyber_budget
            ]
        filtered.sort(key=lambda r: r["cyber_budget_mentioned_eur"], reverse=True)
        return [ParsedReport(**r) for r in filtered]

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_reports, high_value_count (budget >= 500k EUR),
            sectors (distinct list).
        """
        with self._lock:
            total = len(self._reports)
            high_value = sum(
                1 for r in self._reports
                if r["cyber_budget_mentioned_eur"] >= 500_000
            )
            sectors = list({r["sector"] for r in self._reports})
        return {
            "total_reports": total,
            "high_value_count": high_value,
            "sectors": sectors,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_parser: Optional[AnnualReportParser] = None


def get_annual_report_parser() -> AnnualReportParser:
    """Return the process-wide singleton AnnualReportParser instance."""
    global _parser
    if _parser is None:
        _parser = AnnualReportParser()
    return _parser
