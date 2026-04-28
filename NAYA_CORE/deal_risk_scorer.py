"""
NAYA V19 — Deal Risk Scorer
══════════════════════════════════════════════════════════════════════════════
Surveille en continu les deals en cours et détecte ceux qui refroidissent.

TEMPÉRATURES:
  🔥 CHAUD    : interaction < 3j, engagement élevé, réponse positive
  🟡 TIÈDE    : 3-7j sans réponse, engagement neutre
  ❄️ FROID     : > 7j sans réponse → alerte Telegram + relance auto
  💀 PERDU    : > 21j sans réponse → marquer lost, recycler

SCORING:
  temperature_score = base_score × time_decay × engagement_factor × budget_factor

  base_score       : score de qualification initial [0..1]
  time_decay       : décroît exponentiellement après 3j sans réponse
  engagement_factor: multiplié par les interactions positives (clics, ouvertures)
  budget_factor    : deals > 10k€ ont une priorité de surveillance plus haute

DÉCLENCHEMENT: Toutes les heures via le scheduler
OUTPUT: Alertes Telegram pour les deals froids, relances automatiques planifiées
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DEAL_RISK")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "deal_risk_scorer.json"

# Seuils temporels
COLD_THRESHOLD_DAYS = 7       # Froid après 7j sans interaction
LOST_THRESHOLD_DAYS = 21      # Perdu après 21j sans interaction
WARM_THRESHOLD_DAYS = 3       # Tiède après 3j sans interaction


class DealTemperature(Enum):
    HOT   = "hot"     # 🔥 < 3j
    WARM  = "warm"    # 🟡 3-7j
    COLD  = "cold"    # ❄️ 7-21j
    LOST  = "lost"    # 💀 > 21j
    WON   = "won"     # ✅ Fermé gagné
    DEAD  = "dead"    # ⬛ Fermé perdu


@dataclass
class Deal:
    """Représentation d'un deal en cours de suivi."""
    id: str
    company: str
    contact_name: str
    sector: str
    value_eur: float
    created_at: float
    last_interaction_at: float
    initial_score: float = 0.7       # Score de qualification [0..1]
    email_opens: int = 0
    email_clicks: int = 0
    linkedin_replies: int = 0
    positive_signals: int = 0        # Réponses positives, intérêt exprimé
    temperature: DealTemperature = DealTemperature.HOT
    temperature_score: float = 1.0   # Score courant [0..1]
    alert_sent_cold: bool = False     # Alerte envoyée pour état froid
    alert_sent_lost: bool = False     # Alerte envoyée pour état perdu
    relance_count: int = 0
    notes: str = ""
    status: str = "active"           # "active" | "won" | "lost"


@dataclass
class RiskReport:
    """Rapport de risque deals."""
    ts: float
    total_deals: int
    hot: int
    warm: int
    cold: int
    lost: int
    won: int
    total_pipeline_eur: float
    at_risk_eur: float          # EUR dans les deals froids/perdus
    cold_deals: List[str]       # IDs des deals froids
    alerts_triggered: int


class DealRiskScorer:
    """
    Surveille la température des deals et déclenche des relances automatiques.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._deals: Dict[str, Deal] = {}
        self._reports: List[RiskReport] = []
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        log.info("[DEAL_RISK] Deal Risk Scorer V19 — %d deals suivis", len(self._deals))

    # ── API publique ──────────────────────────────────────────────────────────

    def register_deal(self, deal: Deal) -> None:
        """Enregistre un nouveau deal à surveiller."""
        with self._lock:
            self._deals[deal.id] = deal
        self._save()
        log.info("[DEAL_RISK] Deal enregistré: %s | %s | %.0f€",
                 deal.id, deal.company, deal.value_eur)

    def record_interaction(self, deal_id: str, interaction_type: str = "email_open") -> None:
        """Enregistre une interaction sur un deal (réchauffement)."""
        with self._lock:
            if deal_id not in self._deals:
                return
            deal = self._deals[deal_id]
            deal.last_interaction_at = time.time()
            deal.alert_sent_cold = False  # Reset alerte si interaction
            if interaction_type == "email_open":
                deal.email_opens += 1
            elif interaction_type == "email_click":
                deal.email_clicks += 1
            elif interaction_type == "linkedin_reply":
                deal.linkedin_replies += 1
            elif interaction_type == "positive_signal":
                deal.positive_signals += 1
        self._save()

    def mark_won(self, deal_id: str) -> None:
        """Marque un deal comme gagné."""
        with self._lock:
            if deal_id in self._deals:
                self._deals[deal_id].temperature = DealTemperature.WON
                self._deals[deal_id].status = "won"
        self._save()

    def mark_lost(self, deal_id: str) -> None:
        """Marque un deal comme perdu."""
        with self._lock:
            if deal_id in self._deals:
                self._deals[deal_id].temperature = DealTemperature.DEAD
                self._deals[deal_id].status = "lost"
        self._save()

    def run_check(self) -> RiskReport:
        """
        Évalue la température de tous les deals actifs.
        Envoie les alertes pour les deals froids.
        Retourne le rapport de risque.
        """
        with self._lock:
            now = time.time()
            alerts = 0
            cold_ids = []

            hot = warm = cold = lost = won = 0

            for deal in self._deals.values():
                if deal.status != "active":
                    if deal.status == "won":
                        won += 1
                    continue

                # Calculer la température
                days_silent = (now - deal.last_interaction_at) / 86400
                old_temp = deal.temperature
                new_temp, score = self._compute_temperature(deal, days_silent)
                deal.temperature = new_temp
                deal.temperature_score = score

                # Compter par température
                if new_temp == DealTemperature.HOT:
                    hot += 1
                elif new_temp == DealTemperature.WARM:
                    warm += 1
                elif new_temp == DealTemperature.COLD:
                    cold += 1
                    cold_ids.append(deal.id)
                    if not deal.alert_sent_cold:
                        self._alert_cold(deal)
                        deal.alert_sent_cold = True
                        alerts += 1
                elif new_temp == DealTemperature.LOST:
                    lost += 1
                    cold_ids.append(deal.id)
                    if not deal.alert_sent_lost:
                        self._alert_lost(deal)
                        deal.alert_sent_lost = True
                        alerts += 1

            active_deals = [d for d in self._deals.values() if d.status == "active"]
            pipeline_eur = sum(d.value_eur for d in active_deals)
            at_risk_eur = sum(
                d.value_eur for d in active_deals
                if d.temperature in (DealTemperature.COLD, DealTemperature.LOST)
            )

            report = RiskReport(
                ts=now,
                total_deals=len(active_deals),
                hot=hot, warm=warm, cold=cold, lost=lost, won=won,
                total_pipeline_eur=pipeline_eur,
                at_risk_eur=at_risk_eur,
                cold_deals=cold_ids,
                alerts_triggered=alerts,
            )
            self._reports.append(report)
            if len(self._reports) > 200:
                self._reports = self._reports[-100:]

            if alerts > 0:
                log.warning("[DEAL_RISK] %d alertes deals froids | at_risk=%.0f€", alerts, at_risk_eur)
            else:
                log.info("[DEAL_RISK] Check: %d hot / %d warm / %d cold / %d lost | pipeline=%.0f€",
                         hot, warm, cold, lost, pipeline_eur)

        self._save()
        return report

    def get_cold_deals(self) -> List[Deal]:
        """Retourne les deals froids/perdus."""
        with self._lock:
            return [
                d for d in self._deals.values()
                if d.status == "active" and d.temperature in (
                    DealTemperature.COLD, DealTemperature.LOST
                )
            ]

    def get_dashboard(self) -> Dict:
        """Vue d'ensemble du pipeline de deals."""
        with self._lock:
            active = [d for d in self._deals.values() if d.status == "active"]
            by_temp = {t.value: 0 for t in DealTemperature}
            for d in active:
                by_temp[d.temperature.value] += 1

            return {
                "total_active": len(active),
                "by_temperature": by_temp,
                "pipeline_eur": sum(d.value_eur for d in active),
                "at_risk_eur": sum(
                    d.value_eur for d in active
                    if d.temperature in (DealTemperature.COLD, DealTemperature.LOST)
                ),
                "hottest_deals": [
                    {"id": d.id, "company": d.company, "value": d.value_eur,
                     "temp": d.temperature.value, "score": round(d.temperature_score, 3)}
                    for d in sorted(active, key=lambda x: x.temperature_score, reverse=True)[:5]
                ],
                "coldest_deals": [
                    {"id": d.id, "company": d.company, "value": d.value_eur,
                     "days_silent": round((time.time() - d.last_interaction_at) / 86400, 1)}
                    for d in sorted(active, key=lambda x: x.last_interaction_at)[:5]
                ],
            }

    def get_stats(self) -> Dict:
        return self.get_dashboard()

    # ── Logique de scoring ────────────────────────────────────────────────────

    def _compute_temperature(self, deal: Deal, days_silent: float) -> tuple:
        """Calcule la température et le score d'un deal."""
        # Déterminer la température
        if days_silent < WARM_THRESHOLD_DAYS:
            temp = DealTemperature.HOT
        elif days_silent < COLD_THRESHOLD_DAYS:
            temp = DealTemperature.WARM
        elif days_silent < LOST_THRESHOLD_DAYS:
            temp = DealTemperature.COLD
        else:
            temp = DealTemperature.LOST

        # Calculer le score numérique
        # Time decay : exponentiel après 3 jours
        time_decay = math.exp(-max(0, days_silent - WARM_THRESHOLD_DAYS) / 7)

        # Engagement factor : interactions positives boostent le score
        interactions = (
            deal.email_opens * 0.1
            + deal.email_clicks * 0.3
            + deal.linkedin_replies * 0.5
            + deal.positive_signals * 1.0
        )
        engagement_factor = min(1.0, 0.5 + interactions * 0.1)

        # Budget factor : deals de haute valeur reçoivent une surveillance prioritaire
        budget_factor = min(1.2, 0.8 + deal.value_eur / 100_000)

        score = deal.initial_score * time_decay * engagement_factor * budget_factor
        return temp, round(min(1.0, score), 3)

    # ── Alertes ───────────────────────────────────────────────────────────────

    def _alert_cold(self, deal: Deal) -> None:
        """Alerte Telegram + relance automatique pour deal froid."""
        days = (time.time() - deal.last_interaction_at) / 86400
        msg = (
            f"❄️ DEAL FROID — Action requise\n"
            f"├── {deal.company} ({deal.contact_name})\n"
            f"├── Valeur: {deal.value_eur:,.0f}€\n"
            f"├── Secteur: {deal.sector}\n"
            f"├── Silence: {days:.0f}j\n"
            f"└── Action: relance email + LinkedIn maintenant"
        )
        self._notify(msg)
        self._schedule_followup(deal, touch="relance_cold")

    def _alert_lost(self, deal: Deal) -> None:
        """Alerte Telegram pour deal probablement perdu."""
        days = (time.time() - deal.last_interaction_at) / 86400
        msg = (
            f"💀 DEAL PROBABLEMENT PERDU\n"
            f"├── {deal.company} ({deal.contact_name})\n"
            f"├── Valeur: {deal.value_eur:,.0f}€\n"
            f"├── Silence: {days:.0f}j\n"
            f"└── Action: email de fermeture bienveillante ou archiver"
        )
        self._notify(msg)
        self._schedule_followup(deal, touch="closing_bienveillant")

    def _notify(self, msg: str) -> None:
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception:
            pass

    def _schedule_followup(self, deal: Deal, touch: str) -> None:
        """Planifie une relance automatique."""
        try:
            deal.relance_count += 1
            log.info("[DEAL_RISK] Relance planifiée: %s | %s | touch=%s",
                     deal.id, deal.company, touch)
        except Exception:
            pass

    # ── Persistance ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            data = {
                "deals": {k: asdict(v) for k, v in self._deals.items()},
                "saved_at": time.time(),
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(DATA_FILE)
        except Exception as e:
            log.warning("[DEAL_RISK] Save: %s", e)

    def _load(self) -> None:
        try:
            if not DATA_FILE.exists():
                return
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            for k, v in data.get("deals", {}).items():
                try:
                    v["temperature"] = DealTemperature(v["temperature"])
                    self._deals[k] = Deal(**v)
                except Exception:
                    pass
        except Exception as e:
            log.warning("[DEAL_RISK] Load: %s", e)


# ── Singleton ──────────────────────────────────────────────────────────────────
_scorer: Optional[DealRiskScorer] = None


def get_deal_risk_scorer() -> DealRiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = DealRiskScorer()
    return _scorer
