"""NAYA V19 - Action Authority - Determine qui a autorite pour agir sur une douleur"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.ACTION_AUTHORITY")

class ActionAuthority:
    """Determine qui a autorite pour agir sur une douleur."""

    def __init__(self):
        self._log: List[Dict] = []

    AUTHORITY_MAP = {"internal_process": "operations_director", "budget": "cfo", "tech": "cto", "strategy": "ceo", "hr": "hr_director"}

    def identify_authority(self, pain_type: str) -> Dict:
        authority = self.AUTHORITY_MAP.get(pain_type, "general_manager")
        return {"pain_type": pain_type, "decision_maker": authority, "approach": f"Contact direct avec le {authority}"}

    def is_right_contact(self, contact_role: str, pain_type: str) -> bool:
        expected = self.AUTHORITY_MAP.get(pain_type, "")
        return contact_role.lower() == expected.lower() or contact_role.lower() in ("ceo", "founder", "owner")

    def get_stats(self) -> Dict:
        return {"module": "action_authority"}
