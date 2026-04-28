"""NAYA V19 - Project Engine Bridge - Pont entre decision core et project engine"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.PROJECT_ENGINE_BRIDGE")

class ProjectEngineBridge:
    """Pont entre decision core et project engine."""

    def __init__(self):
        self._history: List[Dict] = []

    def route_to_project(self, opportunity: Dict) -> str:
        value = opportunity.get("value", 0)
        opp_type = opportunity.get("type", "service")
        if value >= 15000000:
            return "PROJECT_02_GOOGLE_XR"
        if opp_type == "ecommerce":
            return "PROJECT_03_NAYA_BOTANICA"
        if opp_type == "immobilier":
            return "PROJECT_06_ACQUISITION_IMMOBILIERE"
        if opp_type == "fintech":
            return "PROJECT_07_NAYA_PAYE"
        return "PROJECT_01_CASH_RAPIDE"

    def get_all_projects(self) -> list:
        return ["PROJECT_01", "PROJECT_02", "PROJECT_03", "PROJECT_04", "PROJECT_05", "PROJECT_06", "PROJECT_07"]

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
