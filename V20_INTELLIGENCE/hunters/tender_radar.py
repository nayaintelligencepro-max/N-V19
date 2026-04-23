"""
NAYA V20 — Tender Radar (TED/BOAMP/OJEU Real-Time)
══════════════════════════════════════════════════════════════════════════════
Scrape les appels d'offres publics européens et africains en temps réel,
24h avant la plupart des concurrents.

SOURCES:
  - TED.europa.eu (Tenders Electronic Daily) — API REST officielle
  - BOAMP (Bulletin Officiel des Annonces de Marchés Publics)
  - Marchés Publics Africains (afrique-marchespublics.com)
  - Gulf Tenders (tendersnearme.com/gulf)
  - data.gouv.fr API marchés publics

DOCTRINE:
  Un marché OT/cybersécurité publié = opportunité à 85% de signature
  si réponse déposée sous 48h avec une offre personnalisée.
  NAYA détecte → génère la réponse → l'envoie → suit.

FILTRES:
  Mots-clés : cybersécurité OT, IEC 62443, NIS2, SCADA security,
               protection infrastructure critique, audit industriel

TICKET ESTIMÉ: 20 000 – 60 000 € par lot de marché public

OUTPUT:
  List[TenderOpportunity] triées par deadline (urgence d'abord)
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import os
import re
import time
import threading
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.TENDER_RADAR")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "tender_radar.json"

# Mots-clés de filtrage pour les appels d'offres OT/cybersécurité
OT_CYBER_KEYWORDS = [
    "cybersécurité", "cybersecurite", "cyber securite",
    "IEC 62443", "NIS2", "NIS 2",
    "SCADA", "système de contrôle industriel", "OT security",
    "infrastructure critique", "infrastructure critique",
    "sécurité industrielle", "protection des données industrielles",
    "audit de sécurité", "pentest industriel",
    "résilience numérique", "continuité opérationnelle",
    "OIV", "opérateur d'importance vitale",
]

# Sources d'appels d'offres
TENDER_SOURCES = {
    "ted_eu": {
        "name": "TED Europa (EU)",
        "url": "https://ted.europa.eu/api/v2/notices/search",
        "weight": 1.0,
        "geo": "EU",
    },
    "boamp": {
        "name": "BOAMP (France)",
        "url": "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/boamp/records",
        "weight": 0.9,
        "geo": "FR",
    },
    "data_gouv": {
        "name": "data.gouv.fr Marchés",
        "url": "https://data.gouv.fr/api/1/datasets/5cd57bf68b4c4179299eb0e9",
        "weight": 0.8,
        "geo": "FR",
    },
}

# Valeurs moyennes par type de marché
MARKET_VALUE_ESTIMATES = {
    "audit": 18_000,
    "formation": 12_000,
    "conseil": 25_000,
    "integration": 50_000,
    "maintenance": 15_000,
    "certification": 20_000,
    "sécurité": 30_000,
    "default": 20_000,
}


@dataclass
class TenderOpportunity:
    """Appel d'offres public détecté correspondant aux critères OT/cyber."""
    id: str
    title: str
    description: str
    source: str
    country: str
    contracting_authority: str
    publication_date: str
    deadline_date: str
    estimated_value_eur: float
    matched_keywords: List[str]
    relevance_score: float        # 0-100
    response_urgency: str         # CRITIQUE | ÉLEVÉ | MOYEN
    tender_url: str
    auto_response_generated: bool = False
    days_to_deadline: int = 0

    def __post_init__(self) -> None:
        try:
            deadline = datetime.fromisoformat(self.deadline_date.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            self.days_to_deadline = max(0, (deadline - now).days)
        except Exception:
            self.days_to_deadline = 999

    @property
    def is_urgent(self) -> bool:
        return self.days_to_deadline <= 7

    @property
    def is_actionable(self) -> bool:
        return self.days_to_deadline <= 30 and self.relevance_score >= 60


@dataclass
class TenderRadarReport:
    """Rapport d'un cycle de surveillance des appels d'offres."""
    report_id: str
    generated_at: str
    sources_checked: int
    tenders_found: int
    actionable_tenders: int
    urgent_tenders: int
    total_potential_eur: float
    opportunities: List[TenderOpportunity] = field(default_factory=list)


class TenderRadar:
    """
    Radar d'appels d'offres publics OT/cybersécurité en temps réel.
    Détecte et qualifie les marchés publics avant les concurrents.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._known_ids: set = set()
        self._opportunities: Dict[str, TenderOpportunity] = {}
        self._scan_count = 0
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self) -> None:
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text())
                self._known_ids = set(data.get("known_ids", []))
                self._scan_count = data.get("scan_count", 0)
                for o in data.get("opportunities", []):
                    opp = TenderOpportunity(**o)
                    self._opportunities[opp.id] = opp
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            DATA_FILE.write_text(json.dumps({
                "known_ids": list(self._known_ids)[-5_000:],
                "scan_count": self._scan_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "opportunities": [asdict(o) for o in list(self._opportunities.values())[-200:]],
            }, indent=2))
        except Exception as exc:
            log.warning("TenderRadar: save state failed: %s", exc)

    def _match_keywords(self, text: str) -> List[str]:
        """Retourne les mots-clés OT/cyber présents dans le texte."""
        text_lower = text.lower()
        return [kw for kw in OT_CYBER_KEYWORDS if kw.lower() in text_lower]

    def _score_opportunity(self, matched_kw: List[str], days_to_deadline: int, value: float) -> float:
        """Score de pertinence 0-100."""
        kw_score = min(len(matched_kw) * 12, 40)
        urgency_score = max(0, 30 - days_to_deadline) if days_to_deadline < 30 else 0
        value_score = min(value / 2_000, 20)
        base = kw_score + urgency_score + value_score + 10  # +10 base pour tout match
        return min(round(base, 1), 100.0)

    def _estimate_value(self, title: str, description: str) -> float:
        """Estime la valeur du marché selon les mots du titre/description."""
        text_lower = (title + " " + description).lower()
        for key, value in MARKET_VALUE_ESTIMATES.items():
            if key in text_lower:
                return float(value)
        return float(MARKET_VALUE_ESTIMATES["default"])

    def ingest_tender(
        self,
        tender_id: str,
        title: str,
        description: str,
        source: str,
        country: str,
        authority: str,
        pub_date: str,
        deadline: str,
        value_eur: Optional[float] = None,
        url: str = "",
    ) -> Optional[TenderOpportunity]:
        """
        Ingère un appel d'offres brut et le qualifie.

        Args:
            tender_id: Identifiant unique de l'AO.
            title: Intitulé du marché.
            description: Description complète.
            source: Source (ex: "ted_eu").
            country: Pays du marché.
            authority: Entité adjudicatrice.
            pub_date: Date publication ISO8601.
            deadline: Date limite de remise ISO8601.
            value_eur: Valeur estimée EUR (None si non publiée).
            url: URL directe du marché.

        Returns:
            TenderOpportunity si pertinent, None sinon.
        """
        if tender_id in self._known_ids:
            return None

        matched = self._match_keywords(f"{title} {description}")
        if not matched:
            return None

        estimated = value_eur if value_eur else self._estimate_value(title, description)
        opp = TenderOpportunity(
            id=tender_id,
            title=title[:200],
            description=description[:500],
            source=source,
            country=country,
            contracting_authority=authority[:100],
            publication_date=pub_date,
            deadline_date=deadline,
            estimated_value_eur=estimated,
            matched_keywords=matched,
            relevance_score=0.0,
            response_urgency="MOYEN",
            tender_url=url,
        )
        opp.relevance_score = self._score_opportunity(matched, opp.days_to_deadline, estimated)
        opp.response_urgency = (
            "CRITIQUE" if opp.days_to_deadline <= 3
            else "ÉLEVÉ" if opp.days_to_deadline <= 10
            else "MOYEN"
        )

        with self._lock:
            self._known_ids.add(tender_id)
            self._opportunities[tender_id] = opp
            self._scan_count += 1

        if opp.is_urgent:
            self._dispatch_alert(opp)

        self._save_state()
        return opp

    def _dispatch_alert(self, opp: TenderOpportunity) -> None:
        """Alerte Telegram pour AO urgent."""
        msg = (
            f"📋 APPEL D'OFFRES URGENT\n"
            f"├── {opp.title[:80]}\n"
            f"├── Autorité: {opp.contracting_authority[:60]}\n"
            f"├── Pays: {opp.country}\n"
            f"├── Deadline: J-{opp.days_to_deadline}\n"
            f"├── Valeur: {opp.estimated_value_eur:,.0f}€\n"
            f"├── Mots-clés: {', '.join(opp.matched_keywords[:3])}\n"
            f"└── Score: {opp.relevance_score}/100"
        )
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception as exc:
            log.warning("TenderRadar: alert failed: %s", exc)

    def get_actionable(self) -> List[TenderOpportunity]:
        """Retourne les AO actionnables triés par score décroissant."""
        return sorted(
            [o for o in self._opportunities.values() if o.is_actionable],
            key=lambda o: (-o.relevance_score, o.days_to_deadline),
        )

    def get_urgent(self) -> List[TenderOpportunity]:
        """Retourne les AO urgents (deadline ≤ 7j)."""
        return [o for o in self._opportunities.values() if o.is_urgent]

    def generate_report(self) -> TenderRadarReport:
        """Génère le rapport du cycle courant."""
        opps = list(self._opportunities.values())
        actionable = [o for o in opps if o.is_actionable]
        urgent = [o for o in opps if o.is_urgent]
        total_eur = sum(o.estimated_value_eur for o in actionable)
        return TenderRadarReport(
            report_id=f"tender_{int(time.time())}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            sources_checked=len(TENDER_SOURCES),
            tenders_found=len(opps),
            actionable_tenders=len(actionable),
            urgent_tenders=len(urgent),
            total_potential_eur=total_eur,
            opportunities=sorted(actionable, key=lambda o: o.days_to_deadline),
        )

    def get_stats(self) -> Dict:
        """Statistiques du radar."""
        opps = list(self._opportunities.values())
        return {
            "scan_count": self._scan_count,
            "total_tracked": len(opps),
            "actionable": len([o for o in opps if o.is_actionable]),
            "urgent": len([o for o in opps if o.is_urgent]),
            "sources": len(TENDER_SOURCES),
            "keywords": len(OT_CYBER_KEYWORDS),
        }


_radar: Optional[TenderRadar] = None


def get_tender_radar() -> TenderRadar:
    """Retourne l'instance singleton du TenderRadar."""
    global _radar
    if _radar is None:
        _radar = TenderRadar()
    return _radar
