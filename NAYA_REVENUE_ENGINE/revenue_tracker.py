"""
NAYA V19 — Revenue Tracker
Suivi temps réel du revenu : EUR/semaine, EUR/mois, pipeline, objectifs.
Notifie Telegram sur chaque milestone.
"""
import json, time, logging, threading, uuid
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.REVENUE.TRACKER")

DATA_FILE = Path("data/cache/revenue_tracker.json")

MILESTONES_EUR = {
    "M1_WEEK":   1200,    # Mois 1 — 1 200€/semaine
    "M1_MONTH":  5000,    # Mois 1 — 5 000€/mois
    "M3_MONTH":  15000,   # Mois 2-3 — 15 000€/mois
    "M6_MONTH":  30000,   # Mois 6+ — 30 000€/mois
    "M9_MONTH":  60000,   # Mois 9-12 — 60 000€/mois
}


@dataclass
class RevenueEntry:
    entry_id: str
    amount_eur: float
    source: str          # cash_rapide / mega_project / ecommerce / fintech / real_estate
    client: str = ""
    payment_method: str = "paypal"  # paypal / deblock
    timestamp: float = field(default_factory=time.time)
    note: str = ""


class RevenueTracker:
    """Tracker revenu production-ready avec objectifs, notifications, rapports."""

    def __init__(self):
        self._entries: List[RevenueEntry] = []
        self._lock = threading.RLock()
        self._milestones_hit: set = set()
        self._load()

    def record(self, amount: float, source: str, client: str = "",
               method: str = "paypal", note: str = "") -> str:
        eid = str(uuid.uuid4())[:12]
        entry = RevenueEntry(
            entry_id=eid, amount_eur=amount, source=source,
            client=client, payment_method=method, note=note
        )
        with self._lock:
            self._entries.append(entry)
        self._save()
        self._check_milestones()
        log.info(f"[TRACKER] +{amount}€ ({source}) — {client}")
        return eid

    def _week_revenue(self) -> float:
        cutoff = time.time() - 604800  # 7 jours
        with self._lock:
            return sum(e.amount_eur for e in self._entries if e.timestamp > cutoff)

    def _month_revenue(self) -> float:
        cutoff = time.time() - 2592000  # 30 jours
        with self._lock:
            return sum(e.amount_eur for e in self._entries if e.timestamp > cutoff)

    def _total_revenue(self) -> float:
        with self._lock:
            return sum(e.amount_eur for e in self._entries)

    def _check_milestones(self):
        week = self._week_revenue()
        month = self._month_revenue()

        checks = [
            ("M1_WEEK", week, MILESTONES_EUR["M1_WEEK"]),
            ("M1_MONTH", month, MILESTONES_EUR["M1_MONTH"]),
            ("M3_MONTH", month, MILESTONES_EUR["M3_MONTH"]),
            ("M6_MONTH", month, MILESTONES_EUR["M6_MONTH"]),
            ("M9_MONTH", month, MILESTONES_EUR["M9_MONTH"]),
        ]
        for name, current, target in checks:
            if current >= target and name not in self._milestones_hit:
                self._milestones_hit.add(name)
                self._notify_milestone(name, current, target)

    def _notify_milestone(self, name: str, current: float, target: float):
        try:
            import os
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if not token or not chat_id:
                return
            msg = (
                f"🎯 MILESTONE ATTEINT — NAYA V19\n"
                f"Objectif: {name} ({target:,.0f}€)\n"
                f"Réalisé: {current:,.0f}€\n"
                f"🚀 Prochain palier activé !"
            )
            import urllib.request, urllib.parse
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode()
            urllib.request.urlopen(url, data=data, timeout=10)
        except Exception as e:
            log.debug(f"[TRACKER] Telegram notify failed: {e}")

    def dashboard(self) -> Dict:
        week = self._week_revenue()
        month = self._month_revenue()
        total = self._total_revenue()

        # Prochain objectif
        next_target = None
        for name, target in sorted(MILESTONES_EUR.items(), key=lambda x: x[1]):
            if month < target and name not in self._milestones_hit:
                next_target = {"name": name, "target": target, "gap": round(target - month, 2)}
                break

        by_source: Dict[str, float] = {}
        with self._lock:
            for e in self._entries:
                by_source[e.source] = by_source.get(e.source, 0) + e.amount_eur

        return {
            "week_revenue": round(week, 2),
            "month_revenue": round(month, 2),
            "total_revenue": round(total, 2),
            "entries_count": len(self._entries),
            "milestones_hit": list(self._milestones_hit),
            "next_target": next_target,
            "by_source": {k: round(v, 2) for k, v in by_source.items()},
        }

    def _load(self):
        try:
            if DATA_FILE.exists():
                raw = json.loads(DATA_FILE.read_text())
                self._entries = [RevenueEntry(**e) for e in raw.get("entries", [])]
                self._milestones_hit = set(raw.get("milestones_hit", []))
        except Exception as e:
            log.debug(f"[TRACKER] Load: {e}")

    def _save(self):
        try:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                raw = {
                    "entries": [vars(e) for e in self._entries],
                    "milestones_hit": list(self._milestones_hit),
                }
            DATA_FILE.write_text(json.dumps(raw, indent=2))
        except Exception as e:
            log.debug(f"[TRACKER] Save: {e}")


_instance: Optional[RevenueTracker] = None

def get_tracker() -> RevenueTracker:
    global _instance
    if _instance is None:
        _instance = RevenueTracker()
    return _instance
