"""
TEN DAY CHALLENGE — Défi 10 Ventes en 10 Jours
═══════════════════════════════════════════════════════════════
Orchestrateur autonome pour générer 10 ventes réelles en 10 jours.
Stratégie adaptative : ajuste la prospection selon la performance quotidienne.
"""
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

log = logging.getLogger("NAYA.TEN_DAY_CHALLENGE")

ROOT = Path(__file__).resolve().parent.parent
CHALLENGE_DIR = ROOT / "data" / "real_sales"


@dataclass
class DayTarget:
    """Objectif pour un jour du challenge."""
    day: int
    date: str
    sales_target: int  # Nombre de ventes attendues
    revenue_target_eur: float
    offer_focus: str  # Type d'offre à privilégier
    sector_focus: str
    actions: List[str]
    status: str = "pending"  # pending | in_progress | completed | failed
    actual_sales: int = 0
    actual_revenue_eur: float = 0.0


class TenDayChallenge:
    """
    Challenge 10 jours pour générer des ventes réelles.
    S'adapte automatiquement si retard/avance sur objectifs.
    """

    def __init__(self, start_date: Optional[str] = None):
        self.config_path = CHALLENGE_DIR / "challenge_config.json"
        self.progress_path = CHALLENGE_DIR / "challenge_progress.json"

        if start_date:
            self.start_date = datetime.fromisoformat(start_date)
        else:
            self.start_date = datetime.now(timezone.utc)

        self.days: List[DayTarget] = []
        self._initialize_challenge()
        self._load_progress()

        log.info(
            "✅ TenDayChallenge initialized - Start: %s",
            self.start_date.strftime("%Y-%m-%d")
        )

    def _initialize_challenge(self) -> None:
        """Initialise les 10 jours du challenge avec objectifs."""

        # Stratégie progressive : deals faciles → deals complexes
        daily_targets = [
            {
                "day": 1,
                "sales_target": 1,
                "revenue_target_eur": 1500,
                "offer_focus": "Audit Express Quick",
                "sector_focus": "transport_logistique",
                "actions": [
                    "Scanner offres emploi RSSI transport",
                    "Outreach ultra-ciblé 20 prospects",
                    "Proposition audit flash 48h"
                ]
            },
            {
                "day": 2,
                "sales_target": 1,
                "revenue_target_eur": 2500,
                "offer_focus": "Formation OT 48h",
                "sector_focus": "manufacturing",
                "actions": [
                    "Contacter réseau existant",
                    "Proposition formation express",
                    "Closing rapide cash"
                ]
            },
            {
                "day": 3,
                "sales_target": 2,
                "revenue_target_eur": 4000,
                "offer_focus": "Audit + Conseil",
                "sector_focus": "energie_utilities",
                "actions": [
                    "LinkedIn outreach chaud",
                    "Email sequence J+3",
                    "Follow-up prospects qualifiés"
                ]
            },
            {
                "day": 4,
                "sales_target": 1,
                "revenue_target_eur": 6000,
                "offer_focus": "Pack Sécurité Mid-Tier",
                "sector_focus": "transport_logistique",
                "actions": [
                    "Rappels prospects intéressés",
                    "Démonstration NIS2 Checker",
                    "Proposition pack sécurité"
                ]
            },
            {
                "day": 5,
                "sales_target": 1,
                "revenue_target_eur": 8000,
                "offer_focus": "Mission NIS2 Compliance",
                "sector_focus": "energie_utilities",
                "actions": [
                    "Trigger deadline regulatory",
                    "Proposition conformité urgente",
                    "Closing deals warm"
                ]
            },
            {
                "day": 6,
                "sales_target": 1,
                "revenue_target_eur": 10000,
                "offer_focus": "Audit IEC 62443 SL-2",
                "sector_focus": "manufacturing",
                "actions": [
                    "Ciblage grands comptes",
                    "Proposition audit certifiant",
                    "Meeting décideur"
                ]
            },
            {
                "day": 7,
                "sales_target": 1,
                "revenue_target_eur": 12000,
                "offer_focus": "Consulting OT 3 mois",
                "sector_focus": "energie_utilities",
                "actions": [
                    "Upsell client existant",
                    "Extension mission en cours",
                    "Contrat récurrent"
                ]
            },
            {
                "day": 8,
                "sales_target": 1,
                "revenue_target_eur": 15000,
                "offer_focus": "Programme Cybersécurité OT",
                "sector_focus": "aerospace_defence",
                "actions": [
                    "CAC40 warm lead",
                    "Proposition programme complet",
                    "Négociation contrat cadre"
                ]
            },
            {
                "day": 9,
                "sales_target": 1,
                "revenue_target_eur": 18000,
                "offer_focus": "Pack Premium Full",
                "sector_focus": "gouvernement_critique",
                "actions": [
                    "Closing deal premium en cours",
                    "Démonstration ROI",
                    "Signature contrat"
                ]
            },
            {
                "day": 10,
                "sales_target": 1,
                "revenue_target_eur": 20000,
                "offer_focus": "Contrat Cadre 12 mois",
                "sector_focus": "industrie_lourde",
                "actions": [
                    "Best opportunity pipeline",
                    "Proposition contrat annuel",
                    "Fermeture challenge en beauté"
                ]
            }
        ]

        for target in daily_targets:
            date = self.start_date + timedelta(days=target["day"] - 1)
            day = DayTarget(
                day=target["day"],
                date=date.strftime("%Y-%m-%d"),
                sales_target=target["sales_target"],
                revenue_target_eur=target["revenue_target_eur"],
                offer_focus=target["offer_focus"],
                sector_focus=target["sector_focus"],
                actions=target["actions"]
            )
            self.days.append(day)

    def _load_progress(self) -> None:
        """Charge la progression du challenge."""
        if self.progress_path.exists():
            try:
                data = json.loads(self.progress_path.read_text())
                for i, day_data in enumerate(data.get("days", [])):
                    if i < len(self.days):
                        self.days[i].status = day_data.get("status", "pending")
                        self.days[i].actual_sales = day_data.get("actual_sales", 0)
                        self.days[i].actual_revenue_eur = day_data.get("actual_revenue_eur", 0.0)
            except Exception as e:
                log.warning("Progress load error: %s", e)

    def _save_progress(self) -> None:
        """Sauvegarde la progression."""
        try:
            data = {
                "start_date": self.start_date.isoformat(),
                "days": [asdict(d) for d in self.days]
            }
            self.progress_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            log.error("Progress save error: %s", e)

    def get_current_day(self) -> Optional[DayTarget]:
        """Retourne le jour actuel du challenge."""
        now = datetime.now(timezone.utc)
        days_elapsed = (now - self.start_date).days

        if 0 <= days_elapsed < 10:
            return self.days[days_elapsed]
        return None

    def update_day_progress(self, day: int, sales: int, revenue_eur: float) -> None:
        """Met à jour la progression d'un jour."""
        if 1 <= day <= 10:
            idx = day - 1
            self.days[idx].actual_sales = sales
            self.days[idx].actual_revenue_eur = revenue_eur

            # Déterminer le statut
            if sales >= self.days[idx].sales_target:
                self.days[idx].status = "completed"
            elif sales > 0:
                self.days[idx].status = "in_progress"
            else:
                self.days[idx].status = "pending"

            self._save_progress()

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du challenge."""
        total_sales = sum(d.actual_sales for d in self.days)
        total_revenue = sum(d.actual_revenue_eur for d in self.days)
        target_revenue = sum(d.revenue_target_eur for d in self.days)

        completed_days = sum(1 for d in self.days if d.status == "completed")
        current_day = self.get_current_day()

        return {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "current_day": current_day.day if current_day else 0,
            "days_completed": completed_days,
            "total_sales": total_sales,
            "total_revenue_eur": total_revenue,
            "target_revenue_eur": target_revenue,
            "progress_pct": (total_revenue / target_revenue * 100) if target_revenue > 0 else 0,
            "on_track": total_sales >= completed_days,
            "days_remaining": 10 - completed_days,
        }

    def get_daily_actions(self, day: int) -> List[str]:
        """Retourne les actions recommandées pour un jour."""
        if 1 <= day <= 10:
            return self.days[day - 1].actions
        return []

    def is_completed(self) -> bool:
        """Challenge terminé ?"""
        return sum(d.actual_sales for d in self.days) >= 10


# ── Singleton ─────────────────────────────────────────────────────────────────
_challenge: Optional[TenDayChallenge] = None


def get_ten_day_challenge(start_date: Optional[str] = None) -> TenDayChallenge:
    """Retourne l'instance singleton du TenDayChallenge."""
    global _challenge
    if _challenge is None:
        _challenge = TenDayChallenge(start_date)
    return _challenge
