"""NAYA V19 - Risk Classifier - Classe le risque des commandes entrantes."""
import logging
from typing import Dict

log = logging.getLogger("NAYA.GATEWAY.RISK")

class RiskClassifier:
    """Evalue le niveau de risque de chaque commande avant execution."""

    HIGH_RISK_COMMANDS = {"shutdown", "delete_data", "change_doctrine", "disable_reapers", "wipe_memory",
                          "expose_secrets", "change_floor", "remove_project"}
    MEDIUM_RISK_COMMANDS = {"modify_config", "change_schedule", "add_actor", "force_hunt", "override_pricing"}
    LOW_RISK_COMMANDS = {"status", "diagnostic", "stats", "list", "search", "monitor", "ping"}

    def classify(self, command: str, actor: str, params: Dict = None) -> Dict:
        cmd_lower = command.lower()
        if cmd_lower in self.HIGH_RISK_COMMANDS:
            level = "high"
            action = "require_founder_approval"
        elif cmd_lower in self.MEDIUM_RISK_COMMANDS:
            level = "medium"
            action = "log_and_proceed"
        elif cmd_lower in self.LOW_RISK_COMMANDS:
            level = "low"
            action = "proceed"
        else:
            level = "medium"
            action = "log_and_proceed"

        # Escalate if actor is not founder on high risk
        if level == "high" and actor != "founder":
            action = "block_and_alert"

        result = {
            "command": command, "actor": actor,
            "risk_level": level, "action": action,
            "blocked": action == "block_and_alert",
            "requires_confirmation": level == "high"
        }
        if result["blocked"]:
            log.warning(f"[RISK] BLOCKED: {command} by {actor} (high risk, non-founder)")
        return result

    def is_safe(self, command: str, actor: str) -> bool:
        result = self.classify(command, actor)
        return not result["blocked"]

    def get_stats(self) -> Dict:
        return {
            "high_risk_commands": len(self.HIGH_RISK_COMMANDS),
            "medium_risk_commands": len(self.MEDIUM_RISK_COMMANDS),
            "low_risk_commands": len(self.LOW_RISK_COMMANDS)
        }


_classifier = RiskClassifier()


def classify(command: str, actor: str = "system", params: dict = None) -> dict:
    """Classifie le risque d'une commande."""
    return _classifier.classify(command=command, actor=actor, params=params or {})

