"""NAYA Orchestration — Directive Splitter"""
import uuid
from typing import Dict, List, Any

class DirectiveSplitter:
    """Décompose les directives complexes en tâches atomiques exécutables."""

    TASK_TEMPLATES = {
        "create_business": ["analyze_market", "define_offer", "price_service", "create_proposal", "setup_channels"],
        "hunt_opportunities": ["scan_sector", "filter_by_pain", "score_leads", "prioritize_outreach"],
        "execute_project": ["load_project", "validate_resources", "deploy_tasks", "monitor_progress"],
        "generate_content": ["research_topic", "outline_content", "write_draft", "review_quality", "publish"],
    }

    def split(self, directive: str, payload: Dict = None) -> List[Dict]:
        """Split a directive into atomic tasks."""
        payload = payload or {}
        template_key = self._match_template(directive)
        task_names = self.TASK_TEMPLATES.get(template_key, [directive])
        tasks = []
        for i, name in enumerate(task_names):
            tasks.append({
                "id": f"T_{uuid.uuid4().hex[:8].upper()}",
                "name": name,
                "order": i,
                "directive": directive,
                "payload": payload,
                "dependencies": [tasks[i-1]["id"]] if i > 0 else [],
                "executor": self._assign_executor(name),
            })
        return tasks

    def _match_template(self, directive: str) -> str:
        d = directive.lower().replace("-", "_").replace(" ", "_")
        for key in self.TASK_TEMPLATES:
            if key in d or d in key:
                return key
        return "default"

    def _assign_executor(self, task_name: str) -> str:
        if any(k in task_name for k in ["scan", "hunt", "analyze"]):
            return "naya_brain"
        if any(k in task_name for k in ["publish", "deploy", "setup"]):
            return "automation"
        return "local"
