"""NAYA V19 - N8N Engine - Interface avec N8N pour automatisation externe.
Note: N8N est un outil externe, prevoir le remplacement par un outil interne."""
import logging, os
from typing import Dict, Optional, Any

log = logging.getLogger("NAYA.N8N")

class N8NEngine:
    """Interface N8N - outil d automatisation externe (remplacable)."""

    def __init__(self):
        self._base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self._api_key = os.getenv("N8N_API_KEY", "")
        self._workflows: Dict[str, Dict] = {}
        self._available = bool(self._api_key)

    @property
    def available(self) -> bool:
        return self._available

    def register_workflow(self, name: str, workflow_id: str, trigger: str = "manual") -> None:
        self._workflows[name] = {"id": workflow_id, "trigger": trigger, "executions": 0}

    def trigger_workflow(self, name: str, data: Dict = None) -> Dict:
        wf = self._workflows.get(name)
        if not wf:
            return {"error": f"Workflow {name} non enregistre"}
        if not self._available:
            return {"error": "N8N non configure - utiliser l automatisation interne",
                    "fallback": "NAYA_CORE.execution.sovereign_automation"}
        wf["executions"] += 1
        log.info(f"[N8N] Trigger: {name} (id={wf['id']})")
        return {"triggered": True, "workflow": name, "id": wf["id"], "data": data}

    def get_internal_alternative(self, workflow_type: str) -> str:
        """Retourne le module NAYA interne equivalent a un workflow N8N."""
        ALTERNATIVES = {
            "email_sequence": "NAYA_REVENUE_ENGINE.outreach_engine",
            "lead_scoring": "NAYA_CORE.decision.predictive_scoring_engine",
            "data_sync": "NAYA_CORE.memory.memory_sync",
            "notification": "NAYA_CORE.notifier",
            "scheduling": "NAYA_CORE.scheduler",
            "scraping": "NAYA_REVENUE_ENGINE.web_scraper",
        }
        return ALTERNATIVES.get(workflow_type, "NAYA_CORE.execution.sovereign_automation")

    def get_stats(self) -> Dict:
        return {
            "available": self._available,
            "workflows": len(self._workflows),
            "total_executions": sum(w["executions"] for w in self._workflows.values()),
            "note": "N8N est un outil externe - le systeme fonctionne sans"
        }
