"""
NAYA SUPREME V19.5 — AMÉLIORATION #3 : DELIVERABILITY MONITOR
═══════════════════════════════════════════════════════════════
Surveillance continue de la délivrabilité email.
Si la réputation chute → pause automatique + alerte Telegram.

Métriques surveillées :
  - Bounce rate (hard + soft)
  - Spam complaint rate
  - Open rate trend
  - Inbox placement estimate
  - Domain reputation score

RÈGLE CRÉATRICE : "Ce que je crains le plus : que le système génère
du spam et détruise ma réputation."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.DELIVERABILITY")


class ReputationLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


class AlertType(Enum):
    BOUNCE_SPIKE = "bounce_spike"
    SPAM_COMPLAINT = "spam_complaint"
    OPEN_RATE_DROP = "open_rate_drop"
    REPUTATION_DEGRADED = "reputation_degraded"
    SENDING_PAUSED = "sending_paused"


@dataclass
class EmailEvent:
    message_id: str
    recipient: str
    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliverabilityReport:
    total_sent: int
    total_delivered: int
    total_bounced: int
    total_spam_complaints: int
    total_opened: int
    bounce_rate: float
    spam_rate: float
    open_rate: float
    reputation: ReputationLevel
    is_sending_paused: bool
    alerts: List[str]
    recommendation: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


THRESHOLDS = {
    "bounce_rate_warning": 0.03,
    "bounce_rate_critical": 0.05,
    "bounce_rate_block": 0.08,
    "spam_rate_warning": 0.001,
    "spam_rate_critical": 0.003,
    "spam_rate_block": 0.005,
    "open_rate_minimum": 0.15,
    "open_rate_healthy": 0.25,
}


class DeliverabilityMonitor:
    """
    Surveillance temps réel de la délivrabilité email.
    Pause automatique si la réputation est menacée.
    """

    def __init__(self) -> None:
        self.events: List[EmailEvent] = []
        self.is_sending_paused: bool = False
        self.pause_reason: str = ""
        self.alerts: List[Dict[str, Any]] = []
        self._counters = {
            "sent": 0,
            "delivered": 0,
            "bounced_hard": 0,
            "bounced_soft": 0,
            "spam_complaint": 0,
            "opened": 0,
            "clicked": 0,
            "unsubscribed": 0,
        }

    def record_event(self, event: EmailEvent) -> Optional[str]:
        """
        Enregistre un événement email et vérifie les seuils.
        Retourne une alerte si un seuil est dépassé.
        """
        self.events.append(event)

        if event.event_type == "sent":
            self._counters["sent"] += 1
        elif event.event_type == "delivered":
            self._counters["delivered"] += 1
        elif event.event_type == "bounce_hard":
            self._counters["bounced_hard"] += 1
        elif event.event_type == "bounce_soft":
            self._counters["bounced_soft"] += 1
        elif event.event_type == "spam_complaint":
            self._counters["spam_complaint"] += 1
        elif event.event_type == "opened":
            self._counters["opened"] += 1
        elif event.event_type == "clicked":
            self._counters["clicked"] += 1
        elif event.event_type == "unsubscribed":
            self._counters["unsubscribed"] += 1

        return self._check_thresholds()

    def _check_thresholds(self) -> Optional[str]:
        sent = self._counters["sent"]
        if sent < 20:
            return None

        bounce_rate = self._bounce_rate()
        spam_rate = self._spam_rate()
        open_rate = self._open_rate()

        if bounce_rate >= THRESHOLDS["bounce_rate_block"]:
            return self._pause_sending(
                f"Bounce rate critique: {bounce_rate:.1%} (seuil: {THRESHOLDS['bounce_rate_block']:.1%})"
            )
        if spam_rate >= THRESHOLDS["spam_rate_block"]:
            return self._pause_sending(
                f"Spam rate critique: {spam_rate:.3%} (seuil: {THRESHOLDS['spam_rate_block']:.3%})"
            )
        if bounce_rate >= THRESHOLDS["bounce_rate_critical"]:
            return self._add_alert(
                AlertType.BOUNCE_SPIKE,
                f"Bounce rate élevé: {bounce_rate:.1%} — réduire le volume d'envoi",
            )
        if spam_rate >= THRESHOLDS["spam_rate_critical"]:
            return self._add_alert(
                AlertType.SPAM_COMPLAINT,
                f"Spam complaints élevés: {spam_rate:.3%} — vérifier le contenu",
            )
        if sent >= 50 and open_rate < THRESHOLDS["open_rate_minimum"]:
            return self._add_alert(
                AlertType.OPEN_RATE_DROP,
                f"Open rate faible: {open_rate:.1%} — vérifier sujets et délivrabilité",
            )
        return None

    def _pause_sending(self, reason: str) -> str:
        self.is_sending_paused = True
        self.pause_reason = reason
        alert_msg = f"ENVOI EN PAUSE: {reason}"
        self._add_alert(AlertType.SENDING_PAUSED, alert_msg)
        log.critical(alert_msg)
        return alert_msg

    def _add_alert(self, alert_type: AlertType, message: str) -> str:
        self.alerts.append({
            "type": alert_type.value,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        log.warning(message)
        return message

    def can_send(self) -> bool:
        return not self.is_sending_paused

    def resume_sending(self) -> str:
        if not self.is_sending_paused:
            return "Envoi déjà actif"
        self.is_sending_paused = False
        reason = self.pause_reason
        self.pause_reason = ""
        log.info("Envoi repris après pause: %s", reason)
        return f"Envoi repris (était en pause: {reason})"

    def _bounce_rate(self) -> float:
        sent = self._counters["sent"]
        if sent == 0:
            return 0.0
        return (self._counters["bounced_hard"] + self._counters["bounced_soft"]) / sent

    def _spam_rate(self) -> float:
        sent = self._counters["sent"]
        if sent == 0:
            return 0.0
        return self._counters["spam_complaint"] / sent

    def _open_rate(self) -> float:
        delivered = self._counters["delivered"]
        if delivered == 0:
            return 0.0
        return self._counters["opened"] / delivered

    def get_reputation(self) -> ReputationLevel:
        bounce = self._bounce_rate()
        spam = self._spam_rate()
        if self.is_sending_paused:
            return ReputationLevel.BLOCKED
        if bounce >= THRESHOLDS["bounce_rate_critical"] or spam >= THRESHOLDS["spam_rate_critical"]:
            return ReputationLevel.CRITICAL
        if bounce >= THRESHOLDS["bounce_rate_warning"] or spam >= THRESHOLDS["spam_rate_warning"]:
            return ReputationLevel.WARNING
        if self._open_rate() >= THRESHOLDS["open_rate_healthy"]:
            return ReputationLevel.EXCELLENT
        return ReputationLevel.GOOD

    def generate_report(self) -> DeliverabilityReport:
        reputation = self.get_reputation()
        bounce_rate = self._bounce_rate()
        spam_rate = self._spam_rate()
        open_rate = self._open_rate()

        if reputation == ReputationLevel.BLOCKED:
            recommendation = "URGENT: Envoi en pause. Nettoyer la liste, vérifier SPF/DKIM, réduire le volume."
        elif reputation == ReputationLevel.CRITICAL:
            recommendation = "Réduire le volume de 50%. Vérifier les listes de rebond. Auditer le contenu."
        elif reputation == ReputationLevel.WARNING:
            recommendation = "Surveiller de près. Supprimer les adresses en bounce. Optimiser les sujets."
        elif reputation == ReputationLevel.EXCELLENT:
            recommendation = "Réputation excellente. Maintenir le cap. Volume peut être augmenté de 20%."
        else:
            recommendation = "Réputation stable. Continuer le monitoring."

        return DeliverabilityReport(
            total_sent=self._counters["sent"],
            total_delivered=self._counters["delivered"],
            total_bounced=self._counters["bounced_hard"] + self._counters["bounced_soft"],
            total_spam_complaints=self._counters["spam_complaint"],
            total_opened=self._counters["opened"],
            bounce_rate=bounce_rate,
            spam_rate=spam_rate,
            open_rate=open_rate,
            reputation=reputation,
            is_sending_paused=self.is_sending_paused,
            alerts=[a["message"] for a in self.alerts[-10:]],
            recommendation=recommendation,
        )

    def generate_telegram_report(self) -> str:
        r = self.generate_report()
        status_emoji = {
            ReputationLevel.EXCELLENT: "OK",
            ReputationLevel.GOOD: "OK",
            ReputationLevel.WARNING: "ATTENTION",
            ReputationLevel.CRITICAL: "CRITIQUE",
            ReputationLevel.BLOCKED: "BLOQUE",
        }
        return (
            "NAYA DELIVERABILITY — Rapport\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Réputation    : {status_emoji.get(r.reputation, '?')} ({r.reputation.value})\n"
            f"Envoyés       : {r.total_sent}\n"
            f"Bounce rate   : {r.bounce_rate:.1%}\n"
            f"Spam rate     : {r.spam_rate:.3%}\n"
            f"Open rate     : {r.open_rate:.1%}\n"
            f"Envoi actif   : {'OUI' if not r.is_sending_paused else 'NON - EN PAUSE'}\n"
            f"Action        : {r.recommendation}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )


deliverability_monitor = DeliverabilityMonitor()
