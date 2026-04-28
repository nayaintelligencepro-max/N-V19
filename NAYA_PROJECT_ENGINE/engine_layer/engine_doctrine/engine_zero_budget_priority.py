"""NAYA V19 - Priorite zero budget - Priorise les actions a cout zero"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_ZERO_BUDGET_PRIORITY")

class EngineZeroBudgetPriority:
    """Priorise les actions a cout zero."""

    def __init__(self):
        self._log: List[Dict] = []

    ZERO_COST_ACTIONS = [
        "email_outreach", "linkedin_organic", "content_creation",
        "referral_request", "case_study_writing", "seo_optimization",
        "partnership_outreach", "community_engagement"
    ]

    def prioritize(self, actions: list, budget: float = 0) -> list:
        if budget <= 0:
            return [a for a in actions if a.get("cost", 0) == 0]
        return sorted(actions, key=lambda a: a.get("cost", 0))

    def suggest_free_alternatives(self, paid_action: str) -> list:
        ALTERNATIVES = {"paid_ads": ["seo", "content_marketing", "referral"],
                       "paid_tools": ["open_source", "free_tier", "manual"],
                       "agency": ["in_house", "freelance_exchange", "partnership"]}
        return ALTERNATIVES.get(paid_action, ["manual_approach"])

    def get_stats(self) -> Dict:
        return {"module": "engine_zero_budget_priority", "log_size": len(self._log)}
