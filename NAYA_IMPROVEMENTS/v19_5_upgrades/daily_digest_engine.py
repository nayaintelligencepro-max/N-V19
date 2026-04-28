"""
NAYA SUPREME V19.5 — AMÉLIORATION #5 : DAILY DIGEST ENGINE
═══════════════════════════════════════════════════════════════
Rapport Telegram automatique quotidien pour la créatrice.
Envoyé tous les jours à 20h heure Papeete (UTC-10 = 06h UTC).

Contenu du digest :
  - Revenus du jour / de la semaine
  - Nouveaux prospects détectés
  - Deals avancés dans le pipeline
  - Alertes et problèmes
  - Prochaines actions programmées
  - Santé du système
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.DAILY_DIGEST")

PAPEETE_UTC_OFFSET = -10
DIGEST_HOUR_LOCAL = 20
DIGEST_HOUR_UTC = (DIGEST_HOUR_LOCAL - PAPEETE_UTC_OFFSET) % 24


@dataclass
class DailyMetrics:
    date: str
    revenue_today_eur: float = 0.0
    revenue_week_eur: float = 0.0
    revenue_month_eur: float = 0.0
    new_prospects: int = 0
    prospects_qualified: int = 0
    emails_sent: int = 0
    emails_opened: int = 0
    replies_received: int = 0
    meetings_booked: int = 0
    proposals_sent: int = 0
    deals_won: int = 0
    deals_lost: int = 0
    pipeline_value_eur: float = 0.0
    system_uptime_pct: float = 100.0
    errors_today: int = 0
    alerts: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)


@dataclass
class DigestConfig:
    telegram_enabled: bool = True
    email_enabled: bool = False
    digest_hour_utc: int = DIGEST_HOUR_UTC
    include_details: bool = True
    min_revenue_alert_eur: float = 1000.0


class DailyDigestEngine:
    """
    Génère et envoie un rapport quotidien à la créatrice.
    Agrège toutes les métriques NAYA en un seul message clair.
    """

    def __init__(self, config: Optional[DigestConfig] = None) -> None:
        self.config = config or DigestConfig()
        self.history: List[DailyMetrics] = []
        self._current_metrics: Optional[DailyMetrics] = None
        self._last_digest_date: str = ""

    def start_day(self) -> DailyMetrics:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._current_metrics = DailyMetrics(date=today)
        return self._current_metrics

    def record_revenue(self, amount_eur: float) -> None:
        m = self._ensure_metrics()
        m.revenue_today_eur += amount_eur
        m.revenue_week_eur += amount_eur
        m.revenue_month_eur += amount_eur
        if amount_eur >= self.config.min_revenue_alert_eur:
            m.alerts.append(f"Revenu encaissé: {amount_eur:,.0f}€")

    def record_prospect(self, qualified: bool = False) -> None:
        m = self._ensure_metrics()
        m.new_prospects += 1
        if qualified:
            m.prospects_qualified += 1

    def record_email(self, opened: bool = False) -> None:
        m = self._ensure_metrics()
        m.emails_sent += 1
        if opened:
            m.emails_opened += 1

    def record_reply(self) -> None:
        m = self._ensure_metrics()
        m.replies_received += 1

    def record_meeting(self) -> None:
        m = self._ensure_metrics()
        m.meetings_booked += 1

    def record_proposal(self) -> None:
        m = self._ensure_metrics()
        m.proposals_sent += 1

    def record_deal(self, won: bool, value_eur: float = 0) -> None:
        m = self._ensure_metrics()
        if won:
            m.deals_won += 1
            m.pipeline_value_eur += value_eur
        else:
            m.deals_lost += 1

    def record_error(self, description: str = "") -> None:
        m = self._ensure_metrics()
        m.errors_today += 1
        if description:
            m.alerts.append(f"Erreur: {description}")

    def add_next_action(self, action: str) -> None:
        m = self._ensure_metrics()
        m.next_actions.append(action)

    def set_system_health(self, uptime_pct: float) -> None:
        m = self._ensure_metrics()
        m.system_uptime_pct = uptime_pct

    def _ensure_metrics(self) -> DailyMetrics:
        if self._current_metrics is None:
            self.start_day()
        return self._current_metrics

    def generate_digest(self) -> str:
        m = self._ensure_metrics()
        open_rate = (m.emails_opened / m.emails_sent * 100) if m.emails_sent > 0 else 0

        lines = [
            "NAYA SUPREME — Rapport Quotidien",
            f"Date : {m.date}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "REVENUS",
            f"  Aujourd'hui : {m.revenue_today_eur:,.0f}€",
            f"  Semaine     : {m.revenue_week_eur:,.0f}€",
            f"  Mois        : {m.revenue_month_eur:,.0f}€",
            "",
            "PIPELINE",
            f"  Nouveaux prospects : {m.new_prospects}",
            f"  Qualifiés          : {m.prospects_qualified}",
            f"  Emails envoyés     : {m.emails_sent} (open rate: {open_rate:.0f}%)",
            f"  Réponses reçues    : {m.replies_received}",
            f"  RDV bookés         : {m.meetings_booked}",
            f"  Propositions       : {m.proposals_sent}",
            f"  Deals WON          : {m.deals_won}",
            f"  Deals LOST         : {m.deals_lost}",
            f"  Valeur pipeline    : {m.pipeline_value_eur:,.0f}€",
            "",
            "SYSTEME",
            f"  Uptime : {m.system_uptime_pct:.1f}%",
            f"  Erreurs : {m.errors_today}",
        ]

        if m.alerts:
            lines.append("")
            lines.append("ALERTES")
            for a in m.alerts[-5:]:
                lines.append(f"  - {a}")

        if m.next_actions:
            lines.append("")
            lines.append("PROCHAINES ACTIONS")
            for a in m.next_actions[:5]:
                lines.append(f"  - {a}")

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("NAYA travaille pour toi 24h/24.")

        return "\n".join(lines)

    def close_day(self) -> DailyMetrics:
        m = self._ensure_metrics()
        self.history.append(m)
        self._last_digest_date = m.date
        digest = m
        self._current_metrics = None
        return digest

    def get_weekly_summary(self) -> Dict[str, Any]:
        last_7 = self.history[-7:] if len(self.history) >= 7 else self.history
        if not last_7:
            return {"days": 0, "total_revenue": 0, "total_deals_won": 0}
        return {
            "days": len(last_7),
            "total_revenue": sum(d.revenue_today_eur for d in last_7),
            "total_deals_won": sum(d.deals_won for d in last_7),
            "total_prospects": sum(d.new_prospects for d in last_7),
            "avg_open_rate": (
                sum(d.emails_opened for d in last_7) /
                max(sum(d.emails_sent for d in last_7), 1) * 100
            ),
        }

    def should_send_digest(self) -> bool:
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        return (
            now.hour == self.config.digest_hour_utc
            and today != self._last_digest_date
        )


daily_digest_engine = DailyDigestEngine()
