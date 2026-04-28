"""NAYA V19 - System Reports - Rapports systeme pour le dashboard."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.REPORTS.SYSTEM")

class SystemReportGenerator:
    """Genere des rapports systeme complets."""

    def generate_full_report(self) -> Dict:
        report = {"generated_at": time.time(), "sections": {}}

        # System health
        try:
            from naya_self_diagnostic.diagnostic import get_diagnostic
            report["sections"]["health"] = get_diagnostic().get_report()
        except Exception as e:
            report["sections"]["health"] = {"error": str(e)[:50]}

        # Revenue
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            stats = get_narrative_memory().get_stats()
            report["sections"]["revenue"] = {
                "pipeline_eur": stats.get("total_pipeline_eur", 0),
                "total_pains": stats.get("total_pains", 0),
                "best_sectors": stats.get("best_sectors", [])
            }
        except Exception as e:
            report["sections"]["revenue"] = {"error": str(e)[:50]}

        # Guardian
        try:
            from naya_guardian.guardian import get_guardian
            report["sections"]["guardian"] = get_guardian().status
        except Exception:
            report["sections"]["guardian"] = {}

        return report

    def generate_weekly_summary(self) -> Dict:
        return {
            "type": "weekly_summary",
            "generated_at": time.time(),
            "note": "Rapport hebdomadaire - objectif 60-70k EUR/semaine"
        }
