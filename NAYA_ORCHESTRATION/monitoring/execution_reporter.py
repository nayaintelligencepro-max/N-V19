"""NAYA Orchestration — Execution Reporter"""
from typing import Dict, List, Any
from datetime import datetime, timezone

class ExecutionReporter:
    """Generates execution reports from completed plans."""

    def generate_summary(self, plan_dict: Dict[str, Any]) -> Dict:
        tasks = plan_dict.get("tasks", [])
        results = plan_dict.get("results", {})
        log = plan_dict.get("execution_log", [])
        completed = [t for t in tasks if t.get("id") in results]
        failed = [e for e in log if e.get("status") == "FAILED"]
        return {
            "plan_id": plan_dict.get("id", "unknown"),
            "status": plan_dict.get("status", "unknown"),
            "created_at": plan_dict.get("created_at"),
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "tasks_total": len(tasks),
            "tasks_completed": len(completed),
            "tasks_failed": len(failed),
            "success_rate_pct": round(len(completed) / max(len(tasks), 1) * 100, 1),
            "results_preview": {k: str(v)[:100] for k, v in list(results.items())[:5]},
        }

    def generate_batch_report(self, plans: List[Dict]) -> Dict:
        summaries = [self.generate_summary(p) for p in plans]
        total = len(plans)
        completed = sum(1 for s in summaries if s["status"] == "completed")
        return {
            "total_plans": total, "completed": completed, "failed": total - completed,
            "global_success_rate_pct": round(completed / max(total, 1) * 100, 1),
            "summaries": summaries,
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        }
