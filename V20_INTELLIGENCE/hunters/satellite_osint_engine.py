"""
NAYA V20 — Satellite & OSINT Industrial Engine
══════════════════════════════════════════════════════════════════════════════
Croise les signaux OSINT industriels pour détecter des investissements
OT imminents avant que l'information soit publique.

SOURCES:
  - Offres d'emploi RSSI/OT (Indeed, LinkedIn, APEC, Pole Emploi)
  - Permis de construire industriels (data.gouv.fr géoportail industriel)
  - Actualités presse industrielle (usinenouvelle.com, industrie-techno.com)
  - Rapports annuels PDF (extraction automatique)
  - Registre des marchés publics (BOAMP historique investissements)
  - Signaux satellite proxies (données publiques Copernicus EU)

DOCTRINE:
  Une usine qui recrute 3+ profils OT/SCADA = investissement imminent.
  Un site qui obtient un permis d'extension = nouveau système de contrôle.
  Croiser 3 signaux indépendants = certitude d'investissement à venir.

SIGNAL COMPOSITE:
  score = Σ(poids × signal_présent) normalisé 0-100
  ≥ 75 → Prospect TIER1 pipeline immédiat
  50-74 → Prospect TIER2 à qualifier dans 30j
  25-49 → À monitorer (signal faible)

TICKET: 15 000 – 40 000 € selon profil entreprise
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import re
import time
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.SATELLITE_OSINT")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "satellite_osint_engine.json"

# Poids des signaux (somme = 100)
SIGNAL_WEIGHTS = {
    "ot_job_opening":         25,   # Offre d'emploi OT/SCADA
    "nis2_job_opening":       20,   # Offre emploi cybersécurité / NIS2
    "construction_permit":    20,   # Permis de construire / extension site
    "press_investment":       15,   # Article presse investissement industriel
    "annual_report_capex":    10,   # CAPEX OT mentionné dans rapport annuel
    "linkedin_cto_change":    10,   # Changement DSI/RSSI (signal intention)
}

PROSPECT_TIERS = {
    "TIER1": 75,   # Prospect immédiat
    "TIER2": 50,   # À qualifier
    "TIER3": 25,   # À monitorer
}

# Mots-clés détectés dans les offres d'emploi OT
OT_JOB_KEYWORDS = [
    "SCADA", "IEC 62443", "OT Security", "Automation Engineer",
    "Siemens", "Rockwell", "Schneider", "PLC", "DCS",
    "Cyber OT", "Industrial Cybersecurity", "RSSI OT",
]


@dataclass
class IndustrialSignal:
    """Signal OSINT industriel détecté."""
    signal_type: str               # clé de SIGNAL_WEIGHTS
    company: str
    description: str
    source: str
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    weight: int = 0

    def __post_init__(self) -> None:
        self.weight = SIGNAL_WEIGHTS.get(self.signal_type, 5)


@dataclass
class OsintProspect:
    """Prospect identifié par croisement OSINT multi-signal."""
    id: str
    company: str
    sector: str
    country: str
    signals: List[IndustrialSignal]
    composite_score: float         # 0-100
    tier: str                      # TIER1 | TIER2 | TIER3
    estimated_budget_eur: float
    recommended_service: str
    investment_horizon: str        # IMMINENT | 3M | 6M | 12M
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_signal(self, signal: IndustrialSignal) -> None:
        """Ajoute un signal et recalcule le score composite."""
        self.signals.append(signal)
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalcule le score composite et le tier."""
        total_weight = sum(SIGNAL_WEIGHTS.values())
        earned = sum(s.weight for s in self.signals)
        # Bonus pour diversité des signaux
        diversity_bonus = min(len(set(s.signal_type for s in self.signals)) * 5, 20)
        self.composite_score = min(100.0, round((earned / total_weight) * 80 + diversity_bonus, 1))
        for tier, threshold in sorted(PROSPECT_TIERS.items(), key=lambda x: x[1], reverse=True):
            if self.composite_score >= threshold:
                self.tier = tier
                break
        # Horizon d'investissement
        if self.composite_score >= 75:
            self.investment_horizon = "IMMINENT"
        elif self.composite_score >= 50:
            self.investment_horizon = "3M"
        elif self.composite_score >= 25:
            self.investment_horizon = "6M"
        else:
            self.investment_horizon = "12M"
        self.last_updated = datetime.now(timezone.utc).isoformat()


class SatelliteOsintEngine:
    """
    Moteur OSINT industriel multi-signal pour détecter les investissements OT
    imminents avant qu'ils soient publics.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._prospects: Dict[str, OsintProspect] = {}
        self._signal_count = 0
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self) -> None:
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text())
                self._signal_count = data.get("signal_count", 0)
                for p in data.get("prospects", []):
                    signals = [IndustrialSignal(**s) for s in p.pop("signals", [])]
                    prospect = OsintProspect(**p, signals=signals)
                    self._prospects[prospect.id] = prospect
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            prospects_data = []
            for p in self._prospects.values():
                d = asdict(p)
                prospects_data.append(d)
            DATA_FILE.write_text(json.dumps({
                "signal_count": self._signal_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "prospects": prospects_data[-200:],
            }, indent=2))
        except Exception as exc:
            log.warning("SatelliteOsint: save state failed: %s", exc)

    def ingest_signal(
        self,
        signal_type: str,
        company: str,
        sector: str,
        country: str,
        description: str,
        source: str,
    ) -> OsintProspect:
        """
        Ingère un signal OSINT et l'associe au prospect correspondant.

        Args:
            signal_type: Type de signal (clé de SIGNAL_WEIGHTS).
            company: Nom de l'entreprise.
            sector: Secteur industriel.
            country: Pays.
            description: Description du signal détecté.
            source: Source du signal.

        Returns:
            OsintProspect mis à jour avec le nouveau signal.
        """
        prospect_id = f"osint_{company.lower().replace(' ', '_')[:20]}_{country.lower()}"

        signal = IndustrialSignal(
            signal_type=signal_type,
            company=company,
            description=description[:200],
            source=source,
        )

        with self._lock:
            if prospect_id not in self._prospects:
                self._prospects[prospect_id] = OsintProspect(
                    id=prospect_id,
                    company=company,
                    sector=sector,
                    country=country,
                    signals=[],
                    composite_score=0.0,
                    tier="TIER3",
                    estimated_budget_eur=self._estimate_budget(sector),
                    recommended_service=self._recommend_service(sector),
                    investment_horizon="12M",
                )
            self._prospects[prospect_id].add_signal(signal)
            self._signal_count += 1

        prospect = self._prospects[prospect_id]

        if prospect.tier == "TIER1":
            self._dispatch_alert(prospect)

        self._save_state()
        return prospect

    def _estimate_budget(self, sector: str) -> float:
        """Estime le budget selon le secteur."""
        budgets = {
            "energie": 35_000, "transport": 25_000,
            "chimie": 30_000, "manufacturing": 20_000,
            "pharmaceutique": 40_000,
        }
        return float(budgets.get(sector.lower(), 20_000))

    def _recommend_service(self, sector: str) -> str:
        """Recommande un service selon le secteur."""
        services = {
            "energie": "Audit IEC 62443 niveau 3 + plan remédiation SCADA",
            "transport": "Diagnostic cybersécurité OT transport + conformité NIS2",
            "chimie": "Évaluation sécurité process control + IEC 62443 SL-2",
            "manufacturing": "Pack Audit Express OT 5j + roadmap sécurité",
        }
        return services.get(sector.lower(), "Pack Audit OT Express 15k€")

    def _dispatch_alert(self, prospect: OsintProspect) -> None:
        """Alerte Telegram pour prospect TIER1 détecté."""
        signals_summary = "; ".join(
            f"{s.signal_type}" for s in prospect.signals[-3:]
        )
        msg = (
            f"🛰️ OSINT TIER1 DÉTECTÉ\n"
            f"├── {prospect.company} ({prospect.country})\n"
            f"├── Secteur: {prospect.sector}\n"
            f"├── Score: {prospect.composite_score}/100\n"
            f"├── Horizon: {prospect.investment_horizon}\n"
            f"├── Signaux: {signals_summary}\n"
            f"├── Budget estimé: {prospect.estimated_budget_eur:,.0f}€\n"
            f"└── Service: {prospect.recommended_service[:60]}"
        )
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception as exc:
            log.warning("SatelliteOsint: alert failed: %s", exc)

    def get_tier1_prospects(self) -> List[OsintProspect]:
        """Retourne tous les prospects TIER1 triés par score."""
        return sorted(
            [p for p in self._prospects.values() if p.tier == "TIER1"],
            key=lambda p: -p.composite_score,
        )

    def get_pipeline_eur(self) -> float:
        """Calcule le pipeline total des prospects actifs."""
        return sum(
            p.estimated_budget_eur
            for p in self._prospects.values()
            if p.tier in ("TIER1", "TIER2")
        )

    def get_stats(self) -> Dict:
        """Statistiques du moteur."""
        prospects = list(self._prospects.values())
        tier_counts = {t: sum(1 for p in prospects if p.tier == t) for t in PROSPECT_TIERS}
        return {
            "total_prospects": len(prospects),
            "signal_count": self._signal_count,
            "tier1": tier_counts.get("TIER1", 0),
            "tier2": tier_counts.get("TIER2", 0),
            "tier3": tier_counts.get("TIER3", 0),
            "pipeline_eur": round(self.get_pipeline_eur(), 0),
            "signal_types": len(SIGNAL_WEIGHTS),
        }


_engine: Optional[SatelliteOsintEngine] = None


def get_satellite_osint_engine() -> SatelliteOsintEngine:
    """Retourne l'instance singleton du moteur OSINT industriel."""
    global _engine
    if _engine is None:
        _engine = SatelliteOsintEngine()
    return _engine
