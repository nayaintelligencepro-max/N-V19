"""NAYA V19 - Workflow Registry - Registre des workflows automatises."""
import time, logging
from typing import Dict, List, Optional, Callable
log = logging.getLogger("NAYA.WORKFLOW")

class WorkflowRegistry:
    """Enregistre et gere les workflows d automatisation."""

    def __init__(self):
        self._workflows: Dict[str, Dict] = {}
        self._total_executions = 0

    def register(self, name: str, steps: List[str], handler: Callable = None,
                 schedule: str = "manual") -> None:
        self._workflows[name] = {
            "steps": steps, "handler": handler, "schedule": schedule,
            "executions": 0, "last_run": 0, "status": "registered"
        }

    def execute(self, name: str, params: Dict = None) -> Dict:
        wf = self._workflows.get(name)
        if not wf:
            return {"error": f"Workflow {name} non trouve"}
        wf["executions"] += 1
        wf["last_run"] = time.time()
        self._total_executions += 1
        if wf["handler"]:
            try:
                result = wf["handler"](params or {})
                wf["status"] = "completed"
                return {"success": True, "workflow": name, "result": result}
            except Exception as e:
                wf["status"] = "failed"
                return {"success": False, "error": str(e)}
        return {"success": True, "workflow": name, "steps": wf["steps"]}

    def get_all(self) -> Dict:
        return {n: {"steps": w["steps"], "executions": w["executions"], "schedule": w["schedule"]}
                for n, w in self._workflows.items()}

    def get_stats(self) -> Dict:
        return {"workflows": len(self._workflows), "total_executions": self._total_executions}
