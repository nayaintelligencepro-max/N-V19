"""
NAYA SUPREME V19.3 — AMELIORATION #6
Deal Temperature Alerts
=======================
Systeme d'alertes temps reel quand un deal refroidit.
Detecte les signes de stagnation et declenche des actions automatiques.

Unique a NAYA : scoring de temperature de deal avec alertes predictives
AVANT que le deal ne soit perdu.
"""
import time
import logging
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.DEAL_TEMP")


class DealTemperature(Enum):
    HOT = "hot"           # > 80: deal actif, reponses recentes
    WARM = "warm"         # 50-80: activite moderee
    COOLING = "cooling"   # 30-50: stagnation detectee
    COLD = "cold"         # 10-30: risque de perte
    FROZEN = "frozen"     # < 10: probablement perdu


@dataclass
class TemperatureAlert:
    deal_id: str
    company: str
    temperature: DealTemperature
    score: float  # 0-100
    days_since_last_activity: int
    alert_message: str
    recommended_action: str
    urgency: str  # immediate | today | this_week | informational
    created_at: float = field(default_factory=time.time)


@dataclass
class DealState:
    deal_id: str
    company: str
    amount: float
    stage: str
    last_email_sent: float = 0
    last_reply: float = 0
    last_meeting: float = 0
    last_activity: float = field(default_factory=time.time)
    emails_sent: int = 0
    emails_replied: int = 0
    meetings_count: int = 0
    proposal_sent: bool = False
    objections_count: int = 0


class DealTemperatureAlerts:
    """
    Moniteur de temperature des deals avec alertes automatiques.

    Facteurs de temperature :
    - Jours depuis derniere activite (poids: 40%)
    - Taux de reponse aux emails (poids: 25%)
    - Stage progression (poids: 20%)
    - Nombre de meetings (poids: 15%)

    Actions automatiques :
    - COOLING → envoyer relance personnalisee
    - COLD → escalader vers la fondatrice
    - FROZEN → recycler vers Zero Waste
    """

    STAGE_SCORES = {
        "discovery": 20,
        "proposal": 40,
        "negotiation": 60,
        "contract": 80,
        "won": 100,
        "lost": 0,
    }

    def __init__(self):
        self._deals: Dict[str, DealState] = {}
        self._alerts: List[TemperatureAlert] = []
        self._lock = threading.Lock()
        self._check_count: int = 0

    def register_deal(self, deal_id: str, company: str, amount: float,
                      stage: str = "discovery") -> None:
        """Enregistre un deal pour le monitoring de temperature."""
        with self._lock:
            self._deals[deal_id] = DealState(
                deal_id=deal_id, company=company, amount=amount, stage=stage
            )

    def record_activity(self, deal_id: str, activity_type: str, **kwargs) -> None:
        """Enregistre une activite sur un deal."""
        with self._lock:
            deal = self._deals.get(deal_id)
            if not deal:
                return
            now = time.time()
            deal.last_activity = now

            if activity_type == "email_sent":
                deal.emails_sent += 1
                deal.last_email_sent = now
            elif activity_type == "email_replied":
                deal.emails_replied += 1
                deal.last_reply = now
            elif activity_type == "meeting":
                deal.meetings_count += 1
                deal.last_meeting = now
            elif activity_type == "proposal_sent":
                deal.proposal_sent = True
            elif activity_type == "objection":
                deal.objections_count += 1
            elif activity_type == "stage_change":
                deal.stage = kwargs.get("new_stage", deal.stage)

    def check_temperatures(self) -> List[TemperatureAlert]:
        """Verifie la temperature de tous les deals et genere les alertes."""
        self._check_count += 1
        alerts: List[TemperatureAlert] = []
        now = time.time()

        with self._lock:
            deals = list(self._deals.values())

        for deal in deals:
            score = self._calculate_temperature(deal, now)
            temp = self._score_to_temperature(score)

            if temp in (DealTemperature.COOLING, DealTemperature.COLD, DealTemperature.FROZEN):
                days_inactive = int((now - deal.last_activity) / 86400)
                alert = self._create_alert(deal, temp, score, days_inactive)
                alerts.append(alert)

        with self._lock:
            self._alerts.extend(alerts)
            if len(self._alerts) > 500:
                self._alerts = self._alerts[-250:]

        if alerts:
            log.info(f"[TEMP] {len(alerts)} alertes generees sur {len(deals)} deals")

        return alerts

    def _calculate_temperature(self, deal: DealState, now: float) -> float:
        """Calcule le score de temperature d'un deal (0-100)."""
        # Facteur 1: Jours depuis derniere activite (40%)
        days_inactive = (now - deal.last_activity) / 86400
        if days_inactive <= 2:
            activity_score = 100
        elif days_inactive <= 7:
            activity_score = 80
        elif days_inactive <= 14:
            activity_score = 50
        elif days_inactive <= 30:
            activity_score = 20
        else:
            activity_score = 5

        # Facteur 2: Taux de reponse emails (25%)
        if deal.emails_sent > 0:
            reply_rate = deal.emails_replied / deal.emails_sent
            reply_score = min(100, reply_rate * 200)  # 50% reply rate = score 100
        else:
            reply_score = 50  # Neutre si pas encore d'emails

        # Facteur 3: Progression de stage (20%)
        stage_score = self.STAGE_SCORES.get(deal.stage, 20)

        # Facteur 4: Meetings (15%)
        if deal.meetings_count >= 3:
            meeting_score = 100
        elif deal.meetings_count >= 1:
            meeting_score = 70
        else:
            meeting_score = 30

        # Score pondere
        score = (
            activity_score * 0.40
            + reply_score * 0.25
            + stage_score * 0.20
            + meeting_score * 0.15
        )

        return round(score, 1)

    def _score_to_temperature(self, score: float) -> DealTemperature:
        if score > 80:
            return DealTemperature.HOT
        elif score > 50:
            return DealTemperature.WARM
        elif score > 30:
            return DealTemperature.COOLING
        elif score > 10:
            return DealTemperature.COLD
        else:
            return DealTemperature.FROZEN

    def _create_alert(self, deal: DealState, temp: DealTemperature,
                      score: float, days_inactive: int) -> TemperatureAlert:
        """Cree une alerte avec message et action recommandee."""
        if temp == DealTemperature.COOLING:
            msg = f"Deal {deal.company} ({deal.amount:.0f} EUR) refroidit — {days_inactive}j sans activite"
            action = "Envoyer une relance personnalisee avec nouvelle valeur ajoutee"
            urgency = "this_week"
        elif temp == DealTemperature.COLD:
            msg = f"ATTENTION: Deal {deal.company} ({deal.amount:.0f} EUR) FROID — {days_inactive}j sans activite"
            action = "Escalader: appel telephonique direct ou message LinkedIn personnel"
            urgency = "today"
        else:  # FROZEN
            msg = f"URGENT: Deal {deal.company} ({deal.amount:.0f} EUR) GELE — {days_inactive}j sans activite"
            action = "Recycler vers Zero Waste ou tenter un dernier outreach avec offre speciale"
            urgency = "immediate"

        return TemperatureAlert(
            deal_id=deal.deal_id, company=deal.company,
            temperature=temp, score=score,
            days_since_last_activity=days_inactive,
            alert_message=msg, recommended_action=action,
            urgency=urgency,
        )

    def get_dashboard(self) -> Dict:
        """Retourne un dashboard complet des temperatures."""
        now = time.time()
        temps = {}
        for deal in self._deals.values():
            score = self._calculate_temperature(deal, now)
            temp = self._score_to_temperature(score)
            if temp.value not in temps:
                temps[temp.value] = []
            temps[temp.value].append({
                "deal_id": deal.deal_id,
                "company": deal.company,
                "amount": deal.amount,
                "score": score,
                "stage": deal.stage,
            })
        return {
            "total_deals": len(self._deals),
            "temperatures": temps,
            "hot": len(temps.get("hot", [])),
            "warm": len(temps.get("warm", [])),
            "cooling": len(temps.get("cooling", [])),
            "cold": len(temps.get("cold", [])),
            "frozen": len(temps.get("frozen", [])),
            "total_alerts": len(self._alerts),
        }

    def get_stats(self) -> Dict:
        return {
            "deals_monitored": len(self._deals),
            "checks_run": self._check_count,
            "total_alerts": len(self._alerts),
        }


_monitor: Optional[DealTemperatureAlerts] = None


def get_deal_temperature() -> DealTemperatureAlerts:
    global _monitor
    if _monitor is None:
        _monitor = DealTemperatureAlerts()
    return _monitor
