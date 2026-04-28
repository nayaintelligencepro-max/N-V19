"""
GAP-003 RÉSOLU — Scheduleur optimisé par fuseau horaire.

Planifie les actions commerciales (emails, relances, appels) en fonction
du fuseau horaire du prospect pour maximiser les taux d'ouverture et de réponse.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


TIMEZONE_OFFSETS: Dict[str, int] = {
    "Pacific/Tahiti": -10,
    "America/Los_Angeles": -7,
    "America/New_York": -4,
    "America/Sao_Paulo": -3,
    "Europe/London": 1,
    "Europe/Paris": 2,
    "Europe/Berlin": 2,
    "Europe/Helsinki": 3,
    "Asia/Dubai": 4,
    "Asia/Kolkata": 5,
    "Asia/Singapore": 8,
    "Asia/Tokyo": 9,
    "Australia/Sydney": 10,
}

OPTIMAL_WINDOWS: Dict[str, List[Tuple[int, int]]] = {
    "email_first_touch": [(9, 10), (14, 15)],
    "email_followup": [(8, 9), (10, 11), (15, 16)],
    "email_urgency": [(7, 8), (17, 18)],
    "linkedin_message": [(8, 9), (12, 13), (17, 18)],
    "phone_call": [(10, 12), (14, 16)],
}

WEEKDAY_WEIGHTS: Dict[int, float] = {
    0: 0.90,  # Lundi
    1: 1.00,  # Mardi (optimal)
    2: 0.95,  # Mercredi
    3: 1.00,  # Jeudi (optimal)
    4: 0.70,  # Vendredi
    5: 0.10,  # Samedi
    6: 0.05,  # Dimanche
}


@dataclass
class ScheduledAction:
    """Une action planifiée avec timing optimisé."""
    action_id: str
    prospect_id: str
    action_type: str
    scheduled_utc: datetime
    prospect_local_time: str
    confidence_score: float
    timezone_name: str
    weekday: str
    window_used: str


class TimezoneAwareScheduler:
    """
    Optimise le timing de chaque action commerciale en fonction du fuseau
    horaire du prospect, du jour de la semaine et du type d'action.

    Objectif: maximiser les taux d'ouverture (+40% vs envoi aléatoire).
    """

    WEEKDAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    def __init__(self) -> None:
        self._scheduled: List[ScheduledAction] = []
        self._creator_tz_offset: int = -10  # Polynésie
        logger.info("[TimezoneAwareScheduler] Initialisé — fenêtres optimales multi-TZ chargées")

    def _resolve_offset(self, timezone_name: str) -> int:
        """Résout un nom de timezone en offset UTC."""
        return TIMEZONE_OFFSETS.get(timezone_name, 1)

    def _find_next_optimal_window(
        self,
        action_type: str,
        prospect_tz_offset: int,
        from_utc: Optional[datetime] = None,
    ) -> Tuple[datetime, str, float]:
        """Trouve le prochain créneau optimal en UTC pour le prospect."""
        now_utc = from_utc or datetime.now(timezone.utc)
        windows = OPTIMAL_WINDOWS.get(action_type, OPTIMAL_WINDOWS["email_first_touch"])

        best_time: Optional[datetime] = None
        best_window = ""
        best_score = 0.0

        for day_offset in range(7):
            candidate_date = now_utc + timedelta(days=day_offset)
            weekday = candidate_date.weekday()
            weekday_weight = WEEKDAY_WEIGHTS.get(weekday, 0.5)

            if weekday_weight < 0.2:
                continue

            for start_hour, end_hour in windows:
                prospect_hour_utc = start_hour - prospect_tz_offset
                prospect_hour_utc = prospect_hour_utc % 24

                candidate = candidate_date.replace(
                    hour=prospect_hour_utc, minute=0, second=0, microsecond=0
                )

                if candidate <= now_utc:
                    continue

                score = weekday_weight * (1.0 if start_hour in (9, 10, 14, 15) else 0.8)

                if best_time is None or score > best_score:
                    best_time = candidate
                    best_window = f"{start_hour}:00-{end_hour}:00 local"
                    best_score = score

            if best_time is not None:
                break

        if best_time is None:
            best_time = now_utc + timedelta(hours=24)
            best_window = "fallback_24h"
            best_score = 0.3

        return best_time, best_window, best_score

    def schedule(
        self,
        prospect_id: str,
        action_type: str,
        timezone_name: str = "Europe/Paris",
        from_utc: Optional[datetime] = None,
    ) -> ScheduledAction:
        """Planifie une action au moment optimal pour le prospect."""
        tz_offset = self._resolve_offset(timezone_name)
        scheduled_utc, window_used, confidence = self._find_next_optimal_window(
            action_type, tz_offset, from_utc
        )

        prospect_local = scheduled_utc + timedelta(hours=tz_offset)
        weekday_name = self.WEEKDAY_NAMES[scheduled_utc.weekday()]

        action = ScheduledAction(
            action_id=f"sched_{prospect_id}_{int(scheduled_utc.timestamp())}",
            prospect_id=prospect_id,
            action_type=action_type,
            scheduled_utc=scheduled_utc,
            prospect_local_time=prospect_local.strftime("%A %H:%M"),
            confidence_score=round(confidence, 3),
            timezone_name=timezone_name,
            weekday=weekday_name,
            window_used=window_used,
        )

        self._scheduled.append(action)
        logger.info(
            f"[TimezoneAwareScheduler] {action_type} pour {prospect_id} planifié: "
            f"{scheduled_utc.isoformat()} UTC ({timezone_name} {window_used})"
        )
        return action

    def batch_schedule(
        self,
        prospects: List[Dict[str, str]],
        action_type: str,
    ) -> List[ScheduledAction]:
        """Planifie une action pour plusieurs prospects."""
        results = []
        for p in prospects:
            result = self.schedule(
                prospect_id=p["prospect_id"],
                action_type=action_type,
                timezone_name=p.get("timezone", "Europe/Paris"),
            )
            results.append(result)
        results.sort(key=lambda a: a.scheduled_utc)
        return results

    def stats(self) -> Dict[str, Any]:
        tz_dist = {}
        for s in self._scheduled:
            tz_dist[s.timezone_name] = tz_dist.get(s.timezone_name, 0) + 1
        return {
            "total_scheduled": len(self._scheduled),
            "timezone_distribution": tz_dist,
        }


timezone_aware_scheduler = TimezoneAwareScheduler()
