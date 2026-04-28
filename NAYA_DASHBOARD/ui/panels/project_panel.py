"""NAYA V19 - Project Panel - Affichage des projets dans le dashboard."""
import logging
from typing import Dict, List

log = logging.getLogger("NAYA.PANEL.PROJECT")

class ProjectPanel:
    """Panneau de visualisation des projets pour TORI."""

    PROJECT_DISPLAY = {
        "PROJECT_01": {"name": "Cash Rapide", "icon": "zap", "color": "green"},
        "PROJECT_02": {"name": "Google XR", "icon": "globe", "color": "blue"},
        "PROJECT_03": {"name": "Naya Botanica", "icon": "leaf", "color": "teal"},
        "PROJECT_04": {"name": "Naya Tiny House", "icon": "home", "color": "amber"},
        "PROJECT_05": {"name": "Marches Oublies", "icon": "map", "color": "purple"},
        "PROJECT_06": {"name": "Acquisition Immobiliere", "icon": "building", "color": "coral"},
        "PROJECT_07": {"name": "Naya Paye", "icon": "credit-card", "color": "pink"},
    }

    def __init__(self):
        self._projects: List[Dict] = []

    def load_projects(self) -> List[Dict]:
        try:
            from NAYA_PROJECT_ENGINE.entrypoint import get_project_engine
            raw = get_project_engine().get_all_projects()
            enriched = []
            for p in raw:
                display = self.PROJECT_DISPLAY.get(p.get("id", ""), {})
                enriched.append({**p, **display})
            self._projects = enriched
            return enriched
        except Exception as e:
            log.warning(f"[PROJECT-PANEL] Load failed: {e}")
            return []

    def get_panel_data(self) -> Dict:
        projects = self.load_projects()
        active = [p for p in projects if p.get("status") == "active"]
        incubation = [p for p in projects if p.get("status") == "incubation"]
        return {
            "panel": "projects",
            "total": len(projects),
            "active": len(active),
            "incubation": len(incubation),
            "projects": projects
        }

    def get_project_summary(self, project_id: str) -> Dict:
        for p in self._projects:
            if p.get("id") == project_id:
                return p
        return {"error": "Project not found"}

    def get_stats(self) -> Dict:
        return {"loaded": len(self._projects)}
