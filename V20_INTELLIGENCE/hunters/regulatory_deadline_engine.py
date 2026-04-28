"""
NAYA V20 — Regulatory Deadline Engine
══════════════════════════════════════════════════════════════════════════════
Traque les délais réglementaires précis pour générer des outreach automatiques
90 jours avant chaque deadline critique.

RÉGLEMENTATIONS TRACÉES:
  - NIS2 (Network and Information Security 2) — transposition OCT 2024
  - CER Directive (Critical Entities Resilience) — JAN 2025
  - DORA (Digital Operational Resilience Act) — JAN 2025 financier
  - AI Act (Règlement IA Européen) — phases 2024-2027
  - IEC 62443 — cycles de certification (renouvellement 3 ans)
  - RGPD OT — application au secteur industriel
  - Arrêtés sectoriels ANSSI (OIV — Opérateurs d'Importance Vitale)
  - CyberScore (label cybersécurité PME — FR)

DOCTRINE:
  90j avant une deadline = entreprise avec budget alloué mais pas dépensé.
  C'est le moment optimal pour pitcher un service de mise en conformité.
  Taux de conversion estimé: 35-45% vs 8% hors contexte réglementaire.

TICKET: 15 000 – 40 000 € par mission de mise en conformité

OUTPUT:
  List[RegulatoryDeadline] triées par proximité temporelle
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import time
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.REG_DEADLINE")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "regulatory_deadline_engine.json"

ALERT_HORIZON_DAYS = 90   # Déclencher outreach 90j avant deadline
URGENT_HORIZON_DAYS = 30  # Urgence 30j avant


@dataclass
class RegulatoryDeadline:
    """Délai réglementaire avec contexte commercial."""
    reg_id: str
    regulation_name: str
    regulation_code: str
    deadline_date: str              # ISO date
    description: str
    target_sectors: List[str]
    target_company_sizes: List[str]  # PME | ETI | GE | OIV
    service_offer: str
    ticket_min_eur: float
    ticket_max_eur: float
    conversion_rate: float           # taux conv. estimé [0..1]
    geo_scope: List[str]             # FR | EU | GLOBAL
    days_until: int = 0
    urgency_level: str = "PLANIFIÉ"  # CRITIQUE | URGENT | PLANIFIÉ | PASSÉ

    def __post_init__(self) -> None:
        try:
            deadline = datetime.fromisoformat(self.deadline_date).replace(tzinfo=timezone.utc)
            self.days_until = max(0, (deadline - datetime.now(timezone.utc)).days)
        except Exception:
            self.days_until = 9999
        self.urgency_level = (
            "PASSÉ" if self.days_until == 0 and self.deadline_date < datetime.now(timezone.utc).isoformat()
            else "CRITIQUE" if self.days_until <= URGENT_HORIZON_DAYS
            else "URGENT" if self.days_until <= ALERT_HORIZON_DAYS
            else "PLANIFIÉ"
        )

    @property
    def expected_revenue_eur(self) -> float:
        """Revenu espéré = midpoint ticket × taux conversion."""
        mid = (self.ticket_min_eur + self.ticket_max_eur) / 2
        return mid * self.conversion_rate


# ─── Catalogue des réglementations trackées ──────────────────────────────────

REGULATORY_CATALOGUE: List[Dict] = [
    {
        "reg_id": "NIS2_EU_2024",
        "regulation_name": "Directive NIS2 — Transposition nationale",
        "regulation_code": "EU 2022/2555",
        "deadline_date": "2024-10-17",
        "description": (
            "Les États membres devaient transposer NIS2 avant le 17 octobre 2024. "
            "Les entités essentielles et importantes doivent se conformer aux mesures "
            "techniques et organisationnelles (Annexe X). Sanctions : 10M€ ou 2% CA global."
        ),
        "target_sectors": ["energie", "transport", "eau", "sante", "infrastructure_numerique",
                           "administration_publique", "espace", "alimentaire"],
        "target_company_sizes": ["GE", "ETI", "OIV"],
        "service_offer": "Audit NIS2 complet + plan de mise en conformité + accompagnement réglementaire",
        "ticket_min_eur": 15_000,
        "ticket_max_eur": 40_000,
        "conversion_rate": 0.40,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "NIS2_OSE_REPORTING_2025",
        "regulation_name": "NIS2 — Notification incidents 24h obligatoire",
        "regulation_code": "EU 2022/2555 Art.23",
        "deadline_date": "2025-01-01",
        "description": (
            "Obligation de notification des incidents significatifs à l'autorité nationale "
            "dans les 24h (alerte précoce), 72h (notification), 1 mois (rapport final). "
            "Nécessite un SOC OT et des procédures de gestion d'incidents formalisées."
        ),
        "target_sectors": ["energie", "transport", "eau", "sante"],
        "target_company_sizes": ["GE", "ETI", "OIV"],
        "service_offer": "Mise en place SOC OT + procédures NIS2 + playbooks incidents",
        "ticket_min_eur": 20_000,
        "ticket_max_eur": 60_000,
        "conversion_rate": 0.35,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "DORA_FIN_2025",
        "regulation_name": "DORA — Résilience opérationnelle numérique (Finance)",
        "regulation_code": "EU 2022/2554",
        "deadline_date": "2025-01-17",
        "description": (
            "Le règlement DORA s'applique à toutes les entités financières et leurs prestataires TIC "
            "critiques. Tests de résilience TLPT obligatoires, registre des incidents, "
            "gestion des risques tiers. Inclut les systèmes OT des bourses et chambres de compensation."
        ),
        "target_sectors": ["finance", "banque", "assurance", "infrastructure_marche"],
        "target_company_sizes": ["GE", "ETI"],
        "service_offer": "Audit DORA + programme de tests TLPT + gestion risques TIC tiers",
        "ticket_min_eur": 25_000,
        "ticket_max_eur": 80_000,
        "conversion_rate": 0.30,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "AI_ACT_HIGH_RISK_2025",
        "regulation_name": "AI Act — Systèmes IA à haut risque (entrée en vigueur)",
        "regulation_code": "EU 2024/1689",
        "deadline_date": "2025-08-02",
        "description": (
            "Entrée en application des obligations pour les systèmes IA à haut risque "
            "(Annexe III) : transport, infrastructure critique, industrie. "
            "Obligation d'évaluation de conformité, documentation technique, surveillance humaine."
        ),
        "target_sectors": ["transport", "energie", "manufacturing", "sante"],
        "target_company_sizes": ["GE", "ETI", "PME"],
        "service_offer": "Audit de conformité AI Act + documentation technique + certification",
        "ticket_min_eur": 15_000,
        "ticket_max_eur": 40_000,
        "conversion_rate": 0.35,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "AI_ACT_FULL_2026",
        "regulation_name": "AI Act — Application complète tous systèmes IA",
        "regulation_code": "EU 2024/1689",
        "deadline_date": "2026-08-02",
        "description": (
            "Application intégrale du Règlement IA à tous les systèmes couverts. "
            "Les PME industrielles utilisant des systèmes IA pour la maintenance prédictive, "
            "la détection d'anomalies OT, ou la gestion de production doivent se conformer."
        ),
        "target_sectors": ["manufacturing", "energie", "transport", "chimie"],
        "target_company_sizes": ["GE", "ETI", "PME"],
        "service_offer": "Programme de conformité AI Act 360° + formation équipes + audit annuel",
        "ticket_min_eur": 20_000,
        "ticket_max_eur": 50_000,
        "conversion_rate": 0.38,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "CER_DIRECTIVE_2025",
        "regulation_name": "Directive CER — Résilience entités critiques",
        "regulation_code": "EU 2022/2557",
        "deadline_date": "2025-01-17",
        "description": (
            "La directive CER oblige les entités critiques à réaliser des évaluations des risques, "
            "à notifier les incidents affectant leur résilience, et à mettre en œuvre des mesures "
            "de sécurité physique et cybernétique. Complémentaire à NIS2."
        ),
        "target_sectors": ["energie", "transport", "eau", "sante", "infrastructure_numerique", "espace"],
        "target_company_sizes": ["GE", "ETI", "OIV"],
        "service_offer": "Évaluation des risques CER + plan de résilience + exercices de crise",
        "ticket_min_eur": 18_000,
        "ticket_max_eur": 45_000,
        "conversion_rate": 0.32,
        "geo_scope": ["FR", "EU"],
    },
    {
        "reg_id": "IEC62443_RENEWAL_2025",
        "regulation_name": "IEC 62443 — Renouvellement certification 3 ans",
        "regulation_code": "IEC 62443-2-4 / 3-3",
        "deadline_date": "2025-06-30",
        "description": (
            "Les certifications IEC 62443 des intégrateurs et produits sont valables 3 ans. "
            "Les entreprises certifiées en 2022 doivent renouveler avant mi-2025. "
            "Opportunité de mise à niveau vers IEC 62443:2024."
        ),
        "target_sectors": ["manufacturing", "energie", "chimie", "pharmaceutique"],
        "target_company_sizes": ["GE", "ETI", "PME"],
        "service_offer": "Audit de renouvellement IEC 62443 + plan de mise à niveau + accompagnement certification",
        "ticket_min_eur": 12_000,
        "ticket_max_eur": 35_000,
        "conversion_rate": 0.45,
        "geo_scope": ["FR", "EU", "GLOBAL"],
    },
    {
        "reg_id": "ANSSI_OIV_2025",
        "regulation_name": "ANSSI — Arrêtés sectoriels OIV (cybersécurité)",
        "regulation_code": "LPM 2014 / IGI 1300",
        "deadline_date": "2025-03-31",
        "description": (
            "Les Opérateurs d'Importance Vitale (OIV) doivent appliquer les règles de sécurité "
            "des systèmes d'information d'importance vitale (SIIV). Mise à jour 2024 inclut "
            "les environnements OT/SCADA. Contrôles ANSSI prévus en 2025."
        ),
        "target_sectors": ["energie", "defense", "eau", "transport", "alimentation"],
        "target_company_sizes": ["OIV"],
        "service_offer": "Mise en conformité SIIV + préparation contrôle ANSSI + documentation technique",
        "ticket_min_eur": 30_000,
        "ticket_max_eur": 80_000,
        "conversion_rate": 0.42,
        "geo_scope": ["FR"],
    },
]


class RegulatoryDeadlineEngine:
    """
    Moteur de veille réglementaire qui déclenche des outreach ciblés
    90 jours avant chaque deadline critique.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._deadlines: List[RegulatoryDeadline] = []
        self._alerted_ids: set = set()
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()
        self._build_deadlines()

    def _build_deadlines(self) -> None:
        """Construit la liste des deadlines depuis le catalogue."""
        self._deadlines = [RegulatoryDeadline(**d) for d in REGULATORY_CATALOGUE]

    def _load_state(self) -> None:
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text())
                self._alerted_ids = set(data.get("alerted_ids", []))
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            DATA_FILE.write_text(json.dumps({
                "alerted_ids": list(self._alerted_ids),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, indent=2))
        except Exception as exc:
            log.warning("RegDeadlineEngine: save state failed: %s", exc)

    def get_upcoming(self, horizon_days: int = ALERT_HORIZON_DAYS) -> List[RegulatoryDeadline]:
        """
        Retourne les deadlines dans la fenêtre horizon_days, triées par urgence.

        Args:
            horizon_days: Nombre de jours à anticiper (défaut: 90).

        Returns:
            List[RegulatoryDeadline] triée par days_until croissant.
        """
        self._build_deadlines()
        return sorted(
            [d for d in self._deadlines if 0 <= d.days_until <= horizon_days],
            key=lambda d: d.days_until,
        )

    def get_urgent(self) -> List[RegulatoryDeadline]:
        """Deadlines à moins de 30 jours."""
        return [d for d in self._deadlines if 0 < d.days_until <= URGENT_HORIZON_DAYS]

    def check_and_alert(self) -> List[RegulatoryDeadline]:
        """
        Vérifie les deadlines et envoie des alertes Telegram pour les nouvelles
        réglementations entrant dans la fenêtre d'alerte.

        Returns:
            List des deadlines nouvellement alertées.
        """
        self._build_deadlines()
        newly_alerted = []

        for deadline in self._deadlines:
            if deadline.reg_id in self._alerted_ids:
                continue
            if 0 < deadline.days_until <= ALERT_HORIZON_DAYS:
                self._send_alert(deadline)
                with self._lock:
                    self._alerted_ids.add(deadline.reg_id)
                newly_alerted.append(deadline)

        if newly_alerted:
            self._save_state()

        return newly_alerted

    def _send_alert(self, deadline: RegulatoryDeadline) -> None:
        """Envoie une alerte Telegram pour une deadline entrante."""
        expected_eur = deadline.expected_revenue_eur
        msg = (
            f"⚖️ DEADLINE RÉGLEMENTAIRE J-{deadline.days_until}\n"
            f"├── {deadline.regulation_name}\n"
            f"├── Code: {deadline.regulation_code}\n"
            f"├── Secteurs: {', '.join(deadline.target_sectors[:3])}\n"
            f"├── Service: {deadline.service_offer[:80]}\n"
            f"├── Ticket: {deadline.ticket_min_eur:,.0f}–{deadline.ticket_max_eur:,.0f}€\n"
            f"├── Conv. estimée: {deadline.conversion_rate*100:.0f}%\n"
            f"└── Revenu espéré: {expected_eur:,.0f}€"
        )
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception as exc:
            log.warning("RegDeadlineEngine: alert failed: %s", exc)

    def generate_outreach_brief(self, deadline: RegulatoryDeadline) -> str:
        """
        Génère un brief d'outreach pour une deadline réglementaire.

        Args:
            deadline: La deadline pour laquelle générer le brief.

        Returns:
            Texte du brief d'outreach personnalisé.
        """
        return (
            f"Objet : {deadline.regulation_name} — J-{deadline.days_until}\n\n"
            f"Bonjour,\n\n"
            f"La date limite de conformité à {deadline.regulation_code} approche "
            f"dans {deadline.days_until} jours.\n\n"
            f"Contexte : {deadline.description[:300]}\n\n"
            f"Ce que nous proposons :\n"
            f"{deadline.service_offer}\n\n"
            f"Investissement : {deadline.ticket_min_eur:,.0f} – {deadline.ticket_max_eur:,.0f} €\n\n"
            f"Souhaitez-vous un audit de maturité gratuit de 30 minutes pour évaluer "
            f"votre niveau de conformité actuel ?"
        )

    def get_total_pipeline_eur(self) -> float:
        """Calcule le pipeline réglementaire total sur horizon 90j."""
        return sum(d.expected_revenue_eur for d in self.get_upcoming())

    def get_stats(self) -> Dict:
        """Statistiques du moteur."""
        upcoming = self.get_upcoming()
        urgent = self.get_urgent()
        return {
            "total_regulations": len(self._deadlines),
            "upcoming_90d": len(upcoming),
            "urgent_30d": len(urgent),
            "alerted_count": len(self._alerted_ids),
            "pipeline_eur_90d": round(self.get_total_pipeline_eur(), 0),
            "alert_horizon_days": ALERT_HORIZON_DAYS,
        }


_engine: Optional[RegulatoryDeadlineEngine] = None


def get_regulatory_deadline_engine() -> RegulatoryDeadlineEngine:
    """Retourne l'instance singleton du moteur de délais réglementaires."""
    global _engine
    if _engine is None:
        _engine = RegulatoryDeadlineEngine()
    return _engine
