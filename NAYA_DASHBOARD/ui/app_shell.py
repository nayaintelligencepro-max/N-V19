"""NAYA V19 - App Shell - Shell principal de l application dashboard."""
import logging
from typing import Dict, List
log = logging.getLogger("NAYA.UI.SHELL")

class AppShell:
    """Shell de l application TORI - structure les vues et panels."""

    NAVIGATION = [
        {"id": "main", "label": "NAYA", "icon": "brain", "default": True},
        {"id": "projects", "label": "Projets", "icon": "folder"},
        {"id": "revenue", "label": "Revenue", "icon": "dollar"},
        {"id": "hunting", "label": "Chasse", "icon": "target"},
        {"id": "monitoring", "label": "Monitoring", "icon": "activity"},
        {"id": "security", "label": "Securite", "icon": "shield"},
        {"id": "settings", "label": "Config", "icon": "settings"},
    ]

    def __init__(self):
        self._current_view = "main"
        self._sidebar_collapsed = False
        self._notifications: List[Dict] = []

    def navigate(self, view_id: str) -> Dict:
        if view_id in [n["id"] for n in self.NAVIGATION]:
            old = self._current_view
            self._current_view = view_id
            return {"from": old, "to": view_id}
        return {"error": f"View {view_id} not found"}

    def add_notification(self, message: str, severity: str = "info") -> None:
        self._notifications.append({"message": message, "severity": severity, "ts": __import__("time").time()})
        if len(self._notifications) > 50:
            self._notifications = self._notifications[-25:]

    def get_layout(self) -> Dict:
        return {
            "navigation": self.NAVIGATION,
            "current_view": self._current_view,
            "sidebar_collapsed": self._sidebar_collapsed,
            "notifications": len(self._notifications)
        }

    def get_stats(self) -> Dict:
        return self.get_layout()
