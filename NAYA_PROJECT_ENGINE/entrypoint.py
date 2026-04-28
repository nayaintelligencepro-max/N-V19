"""NAYA V19 - Project Engine Entrypoint."""
import logging
from typing import Dict, List

from NAYA_PROJECT_ENGINE.business.adaptive_business_hunt_engine import (
    adaptive_business_hunt_engine,
)
from NAYA_PROJECT_ENGINE.mission_10_days_engine import mission_10_days_engine

log = logging.getLogger("NAYA.PROJECTS")

class ProjectEngineEntrypoint:
    def __init__(self):
        self._projects: Dict[str, Dict] = {}
        self._load_projects()

    def _load_projects(self):
        PROJECTS = [
            {"id": "PROJECT_01", "name": "Cash Rapide", "status": "active"},
            {"id": "PROJECT_02", "name": "Google XR", "status": "active"},
            {"id": "PROJECT_03", "name": "Naya Botanica", "status": "active"},
            {"id": "PROJECT_04", "name": "Naya Tiny House", "status": "active"},
            {"id": "PROJECT_05", "name": "Marches Oublies", "status": "active"},
            {"id": "PROJECT_06", "name": "Acquisition Immobiliere", "status": "active"},
            {"id": "PROJECT_07", "name": "Naya Paye", "status": "incubation"},
            {"id": "PROJECT_08", "name": "Cash Rapid Queue", "status": "active"},
            {"id": "PROJECT_09", "name": "Trade Acceleration", "status": "active"},
            {"id": "PROJECT_10", "name": "Tech Transformation", "status": "active"},
            {"id": "PROJECT_11", "name": "Supply Chain", "status": "active"},
            {"id": "PROJECT_12", "name": "HR Scaling", "status": "active"},
            {"id": "PROJECT_13", "name": "Market Expansion", "status": "active"},
            {"id": "PROJECT_14", "name": "Fintech Solutions", "status": "incubation"},
            {"id": "PROJECT_15", "name": "Data Analytics", "status": "incubation"},
            {"id": "PROJECT_16", "name": "Sustainability", "status": "incubation"},
        ]
        for p in PROJECTS:
            self._projects[p["id"]] = p

    def get_all_projects(self) -> List[Dict]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> Dict:
        return self._projects.get(project_id, {})

    def get_stats(self) -> Dict:
        return {
            "total": len(self._projects),
            "active": sum(1 for p in self._projects.values() if p["status"] == "active"),
            "incubation": sum(1 for p in self._projects.values() if p["status"] == "incubation"),
        }

    def get_adaptive_ranked_projects(self, limit: int = 10) -> List[Dict]:
        """Retourne les projets classés par potentiel business/chasse go-live."""
        return adaptive_business_hunt_engine.rank_projects(limit=limit)

    def get_project_hunt_playbook(self, project_id: str) -> Dict:
        """Retourne le playbook de chasse adapté à un projet."""
        return adaptive_business_hunt_engine.build_hunt_playbook(project_id)

    def get_project_first_10_days_mission(self, project_id: str) -> Dict:
        """Retourne la mission J1→J10 du projet donné."""
        return adaptive_business_hunt_engine.build_first_10_days_mission(project_id)

    def launch_top10_missions_bundle(self) -> Dict:
        """Construit automatiquement les missions des 10 premiers projets."""
        return adaptive_business_hunt_engine.launch_top10_bundle()

    def get_mission_10_days_report(self) -> Dict:
        """Retourne le rapport global de mission 10 jours."""
        return mission_10_days_engine.report()

    def get_mission_10_days_daily_plan(self, day: int | None = None) -> Dict:
        """Retourne le plan journalier de mission 10 jours."""
        return mission_10_days_engine.daily_plan(day)

    def record_mission_sale(self, day: int, amount_eur: float, project_id: str, client: str, source: str = "manual") -> Dict:
        """Enregistre un encaissement réel mission 10 jours."""
        return mission_10_days_engine.record_sale(day, amount_eur, project_id, client, source)

_pe = None
def get_project_engine():
    global _pe
    if _pe is None:
        _pe = ProjectEngineEntrypoint()
    return _pe
