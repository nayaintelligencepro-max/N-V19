"""
NAYA V19 - Temporal Orchestration Engine
Time les approches pour maximiser les conversions.
Sait quand chaque secteur achete, quels jours/heures sont optimaux.
"""
import time, logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

log = logging.getLogger("NAYA.TEMPORAL")

@dataclass
class TemporalWindow:
    sector: str
    best_months: List[int]    # 1-12
    best_weekdays: List[int]  # 0=lundi, 6=dimanche
    best_hours_utc: List[int] # 0-23
    budget_cycle_month: int   # Mois de renouvellement budget
    avoid_months: List[int]   # Mois a eviter
    notes: str = ""

class TemporalOrchestrator:
    """Orchestre le timing des actions pour maximiser les conversions."""

    SECTOR_TIMING = {
        "pme": TemporalWindow("pme", [1,2,3,9,10,11], [1,2,3], [9,10,14,15], 1, [7,8,12], "PME: debut d annee et rentre"),
        "gouvernement": TemporalWindow("gouvernement", [1,2,3,4,9,10], [1,2,3,4], [9,10,11], 1, [7,8], "Budgets votes T1"),
        "finance": TemporalWindow("finance", [1,4,7,10], [1,2,3], [8,9,10], 1, [12], "Debut de trimestre"),
        "tech": TemporalWindow("tech", [1,2,3,4,5,9,10,11], [1,2,3,4], [10,11,14,15], 1, [12], "Tech: toute l annee sauf fetes"),
        "sante": TemporalWindow("sante", [1,2,3,9,10,11], [1,2,3], [8,9,14], 1, [7,8], "Sante: hors vacances"),
        "restaurant": TemporalWindow("restaurant", [1,2,9,10], [1,2], [10,11,14,15], 1, [6,7,8,12], "Apres rush ete/fetes"),
        "immobilier": TemporalWindow("immobilier", [2,3,4,5,9,10], [1,2,3,4], [9,10,14], 1, [7,8,12], "Printemps et rentree"),
        "industrie": TemporalWindow("industrie", [1,2,3,4,9,10], [1,2,3], [8,9,10], 1, [7,8], "Budget planifie T1"),
        "education": TemporalWindow("education", [3,4,5,9,10,11], [1,2,3], [9,10,14], 9, [7,8], "Rentree scolaire"),
    }

    def __init__(self):
        self._override_windows: Dict[str, TemporalWindow] = {}
        self._action_log: List[Dict] = []

    def is_good_time(self, sector: str, target_tz_offset: int = 0) -> Dict:
        """Verifie si c est le bon moment pour contacter ce secteur."""
        now = datetime.now(timezone.utc) + timedelta(hours=target_tz_offset)
        window = self._override_windows.get(sector) or self.SECTOR_TIMING.get(sector)

        if not window:
            return {"good_time": True, "confidence": 0.3, "reason": "Secteur inconnu, timing par defaut"}

        month_ok = now.month in window.best_months
        day_ok = now.weekday() in window.best_weekdays
        hour_ok = (now.hour + target_tz_offset) % 24 in window.best_hours_utc
        avoid = now.month in window.avoid_months

        if avoid:
            return {"good_time": False, "confidence": 0.8,
                    "reason": f"Mois {now.month} a eviter pour {sector}",
                    "next_window": self._next_good_window(window, now)}

        score = (0.4 if month_ok else 0) + (0.35 if day_ok else 0) + (0.25 if hour_ok else 0)
        good = score >= 0.6

        return {
            "good_time": good,
            "confidence": round(score, 2),
            "month_ok": month_ok, "day_ok": day_ok, "hour_ok": hour_ok,
            "reason": window.notes,
            "recommendation": "ENVOYER" if good else "ATTENDRE",
            "next_window": None if good else self._next_good_window(window, now)
        }

    def best_time_for(self, sector: str, tz_offset: int = 0) -> Dict:
        """Retourne le prochain creneau optimal pour ce secteur."""
        window = self.SECTOR_TIMING.get(sector)
        if not window:
            return {"next_best": "Mardi 10h", "confidence": 0.3}

        best_day = window.best_weekdays[0] if window.best_weekdays else 1
        best_hour = window.best_hours_utc[0] if window.best_hours_utc else 10
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

        return {
            "best_day": days[best_day],
            "best_hour": f"{best_hour}h",
            "best_months": window.best_months,
            "avoid_months": window.avoid_months,
            "budget_cycle": window.budget_cycle_month,
            "notes": window.notes
        }

    def schedule_outreach(self, opportunities: List[Dict]) -> List[Dict]:
        """Planifie les outreach pour chaque opportunite au moment optimal."""
        scheduled = []
        for opp in opportunities:
            sector = opp.get("sector", "general")
            timing = self.is_good_time(sector, opp.get("tz_offset", 0))

            scheduled.append({
                "opportunity": opp,
                "timing": timing,
                "priority": "NOW" if timing["good_time"] else "SCHEDULE",
                "send_at": "now" if timing["good_time"] else timing.get("next_window", "demain 10h")
            })

        # Trier: NOW d abord, puis par confidence
        scheduled.sort(key=lambda s: (s["priority"] == "SCHEDULE", -s["timing"]["confidence"]))
        return scheduled

    def _next_good_window(self, window: TemporalWindow, now: datetime) -> str:
        for delta in range(1, 30):
            future = now + timedelta(days=delta)
            if future.month in window.best_months and future.weekday() in window.best_weekdays:
                best_h = window.best_hours_utc[0] if window.best_hours_utc else 10
                return future.strftime(f"%A %d/%m a {best_h}h")
        return "Dans les 30 prochains jours"

    def get_stats(self) -> Dict:
        return {
            "sectors_configured": len(self.SECTOR_TIMING),
            "custom_overrides": len(self._override_windows)
        }

_orch = None
def get_temporal_orchestrator() -> TemporalOrchestrator:
    global _orch
    if _orch is None:
        _orch = TemporalOrchestrator()
    return _orch
