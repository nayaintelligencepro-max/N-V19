"""Mission 10 Days Engine — orchestrateur d'exécution J1→J10.

Objectif: 97 500 EUR encaissés réellement au jour 10.
Pilote 16 projets, produit le plan du jour, consolide les ventes,
et alimente Telegram + TORI_APP.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from NAYA_PROJECT_ENGINE.business.adaptive_business_hunt_engine import adaptive_business_hunt_engine


ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "mission_10_days_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

DAILY_TARGETS = [1500, 2500, 4000, 6000, 8000, 10000, 12000, 15000, 17000, 20000]
DAILY_FOCUS = [
    "Audit Express Quick",
    "Formation OT 48h",
    "Audit + Conseil",
    "Formation OT Avancée",
    "Consulting IEC62443",
    "Audit NIS2 Compliance",
    "Contrat IEC62443 Moyen",
    "Grand Audit Infrastructure",
    "Contrat Cadre 6 mois",
    "Contrat Cadre 12 mois",
]


@dataclass
class MissionSale:
    sale_id: str
    day: int
    amount_eur: float
    project_id: str
    client: str
    source: str = "manual"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Mission10DaysEngine:
    """Pilote mission 10 jours + reporting quotidien."""

    def __init__(self) -> None:
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        state = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "sales": [],
            "active": True,
        }
        self._save_state(state)
        return state

    def _save_state(self, state: Dict[str, Any] | None = None) -> None:
        state = state or self._state
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def current_day(self) -> int:
        started = datetime.fromisoformat(self._state["started_at"])
        delta = datetime.now(timezone.utc) - started
        return max(1, min(10, delta.days + 1))

    def portfolio_projects(self) -> List[Dict[str, Any]]:
        ranked = adaptive_business_hunt_engine.rank_projects(limit=16)
        return [
            {"id": p["project_id"], "name": p["name"], "status": "active", "vertical": p.get("vertical", "")}
            for p in ranked
        ]

    def portfolio_target(self) -> float:
        return float(sum(DAILY_TARGETS))

    def record_sale(self, day: int, amount_eur: float, project_id: str, client: str, source: str = "manual") -> Dict[str, Any]:
        sale = MissionSale(
            sale_id=f"sale_{len(self._state['sales'])+1:04d}",
            day=day,
            amount_eur=amount_eur,
            project_id=project_id,
            client=client,
            source=source,
        )
        self._state["sales"].append(asdict(sale))
        self._save_state()
        return asdict(sale)

    def total_cashed(self) -> float:
        return round(sum(float(s.get("amount_eur", 0)) for s in self._state["sales"]), 2)

    def total_cashed_day(self, day: int) -> float:
        return round(sum(float(s.get("amount_eur", 0)) for s in self._state["sales"] if int(s.get("day", 0)) == day), 2)

    def daily_plan(self, day: int | None = None) -> Dict[str, Any]:
        day = day or self.current_day()
        projects = adaptive_business_hunt_engine.rank_projects(limit=16)
        allocation = self._allocate_target(day, projects)
        return {
            "day": day,
            "target_eur": DAILY_TARGETS[day - 1],
            "focus": DAILY_FOCUS[day - 1],
            "allocated_projects": allocation,
        }

    def _allocate_target(self, day: int, ranked_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        target = DAILY_TARGETS[day - 1]
        if not ranked_projects:
            return []
        total_score = sum(float(p.get("go_live_score", 1)) for p in ranked_projects[:16]) or 1.0
        allocated: List[Dict[str, Any]] = []
        for p in ranked_projects[:16]:
            weight = float(p.get("go_live_score", 1)) / total_score
            allocated.append({
                "project_id": p["project_id"],
                "name": p["name"],
                "weight": round(weight, 4),
                "target_share_eur": round(target * weight, 2),
                "vertical": p.get("vertical", ""),
            })
        return allocated

    def report(self) -> Dict[str, Any]:
        day = self.current_day()
        daily_target = DAILY_TARGETS[day - 1]
        daily_cashed = self.total_cashed_day(day)
        all_projects = self.portfolio_projects()
        return {
            "mission": "10_days_cash_mission",
            "active": self._state.get("active", True),
            "current_day": day,
            "portfolio_projects_total": len(all_projects),
            "portfolio_target_eur": self.portfolio_target(),
            "total_cashed_eur": self.total_cashed(),
            "remaining_to_target_eur": round(self.portfolio_target() - self.total_cashed(), 2),
            "today": {
                "target_eur": daily_target,
                "cashed_eur": daily_cashed,
                "remaining_eur": round(max(0.0, daily_target - daily_cashed), 2),
                "focus": DAILY_FOCUS[day - 1],
                "plan": self.daily_plan(day),
            },
            "sales_count": len(self._state["sales"]),
            "latest_sales": self._state["sales"][-10:],
        }

    def morning_briefing_text(self, tori_url: str = "http://localhost:8080/tori/mission10d/report") -> str:
        report = self.report()
        today = report["today"]
        return (
            "☀️ <b>NAYA — BRIEFING MISSION 10 JOURS</b>\n"
            f"Jour: <b>{report['current_day']}/10</b>\n"
            f"Objectif du jour: <b>{today['target_eur']:,.0f} EUR</b>\n"
            f"Encaissé aujourd’hui: <b>{today['cashed_eur']:,.0f} EUR</b>\n"
            f"Restant aujourd’hui: <b>{today['remaining_eur']:,.0f} EUR</b>\n"
            f"Focus: <b>{today['focus']}</b>\n"
            f"Portefeuille projets: <b>{report['portfolio_projects_total']}</b>\n"
            f"Total encaissé mission: <b>{report['total_cashed_eur']:,.0f} EUR</b>\n"
            f"Rapport visible sur TORI_APP: {tori_url}\n"
            "✅ Si une vente est signée, l’encaissement doit être confirmé puis reporté."
        )


mission_10_days_engine = Mission10DaysEngine()
