"""
NAYA V19.6 — Constraint Validator
Core Module
Valide contraintes business et règles inviolables du système
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

class ConstraintLevel(Enum):
    """Niveaux de contrainte"""
    CRITICAL = "critical"  # Violation = arrêt immédiat
    HIGH = "high"           # Violation = escalade urgente
    MEDIUM = "medium"       # Violation = notification + log
    LOW = "low"            # Violation = log seulement

@dataclass
class Constraint:
    """Définition d'une contrainte"""
    constraint_id: str
    name: str
    description: str
    level: ConstraintLevel
    validation_fn: Callable
    error_message: str
    remediation_steps: List[str]

class ConstraintValidator:
    """
    Validateur de contraintes business V19.
    Applique 7 lois souveraines + contraintes métier.
    Arrête opérations si violation CRITICAL.
    """

    MIN_CONTRACT_VALUE_EUR = 1000
    DECISION_THRESHOLD_EUR = 500
    MAX_PARALLEL_PROJECTS = 4
    DAILY_BRIEFING_HOUR = 8  # UTC

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.constraints: Dict[str, Constraint] = {}
        self.violations: List[Dict] = []
        self._register_constraints()

    def _register_constraints(self) -> None:
        """Enregistre toutes les contraintes"""

        # CONTRAINTE 1: Plancher 1000 EUR inviolable
        self.register_constraint(Constraint(
            constraint_id="MIN_CONTRACT_VALUE",
            name="Minimum Contract Value",
            description="All contracts must be >= 1000 EUR (PLANCHER INVIOLABLE)",
            level=ConstraintLevel.CRITICAL,
            validation_fn=self._validate_min_contract_value,
            error_message="Contract value below 1000 EUR - FORBIDDEN",
            remediation_steps=[
                "Increase contract value to >= 1000 EUR",
                "Split offering into multiple contracts if needed",
                "Escalate to decision-maker if not possible"
            ]
        ))

        # CONTRAINTE 2: Revenus = validation
        self.register_constraint(Constraint(
            constraint_id="REVENUE_VALIDATION",
            name="Revenue Entry Validation",
            description="All revenue entries must be verified and sourced",
            level=ConstraintLevel.CRITICAL,
            validation_fn=self._validate_revenue_entry,
            error_message="Revenue entry missing source or verification",
            remediation_steps=[
                "Add revenue source documentation",
                "Get client confirmation",
                "Update entry with timestamp"
            ]
        ))

        # CONTRAINTE 3: Décisions > 500 EUR requièrent validation Telegram
        self.register_constraint(Constraint(
            constraint_id="DECISION_THRESHOLD",
            name="Decision Validation Threshold",
            description="Decisions > 500 EUR require Telegram validation",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_decision_threshold,
            error_message="Decision >= 500 EUR sent without Telegram validation",
            remediation_steps=[
                "Pause action",
                "Send Telegram validation request to owner",
                "Wait for /validate confirmation",
                "Resume after approval"
            ]
        ))

        # CONTRAINTE 4: Max 4 projets parallèles
        self.register_constraint(Constraint(
            constraint_id="MAX_PARALLEL_PROJECTS",
            name="Parallel Project Limit",
            description="Never exceed 4 active projects simultaneously",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_max_parallel,
            error_message="Attempt to exceed 4 parallel projects",
            remediation_steps=[
                "Complete or pause existing project",
                "Verify slot availability",
                "Queue new project if all slots full"
            ]
        ))

        # CONTRAINTE 5: Zéro hardcoding credentials
        self.register_constraint(Constraint(
            constraint_id="NO_HARDCODED_SECRETS",
            name="No Hardcoded Credentials",
            description="All credentials must come from SECRETS/ or environment",
            level=ConstraintLevel.CRITICAL,
            validation_fn=self._validate_no_hardcoded_secrets,
            error_message="Hardcoded credential detected in code",
            remediation_steps=[
                "Remove hardcoded secret immediately",
                "Move to SECRETS/keys/",
                "Rotate exposed credential if any",
                "Audit all recent commits"
            ]
        ))

        # CONTRAINTE 6: Guardian toujours actif
        self.register_constraint(Constraint(
            constraint_id="GUARDIAN_ACTIVE",
            name="Guardian Agent Always Active",
            description="Guardian (Agent 11) must run every 6 hours minimum",
            level=ConstraintLevel.CRITICAL,
            validation_fn=self._validate_guardian_active,
            error_message="Guardian agent missed scheduled run",
            remediation_steps=[
                "Check Guardian process status",
                "Review logs for failure reason",
                "Restart Guardian immediately",
                "Alert on Telegram if recovery fails"
            ]
        ))

        # CONTRAINTE 7: Mémoire vectorielle utilisée avant offre
        self.register_constraint(Constraint(
            constraint_id="MEMORY_BEFORE_OFFER",
            name="Vector Memory Consulted Before Offer",
            description="Must query offer_memory before generating any offer",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_memory_before_offer,
            error_message="Offer generated without consulting vector memory",
            remediation_steps=[
                "Query offer_memory for similar wins",
                "Include context in prompt",
                "Generate offer with memory insights",
                "Log interaction for future learning"
            ]
        ))

        # CONTRAINTE 8: Zéro TODO placeholder en code métier
        self.register_constraint(Constraint(
            constraint_id="NO_PLACEHOLDERS",
            name="No TODO Placeholders in Production Code",
            description="Production code must not contain '# TODO', 'pass', 'stub'",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_no_placeholders,
            error_message="TODO placeholder or stub found in production code",
            remediation_steps=[
                "Complete the implementation",
                "Or move code to /tests/ if unfinished",
                "Never deploy code with placeholders"
            ]
        ))

        # CONTRAINTE 9: Tous les agents < 10 secondes
        self.register_constraint(Constraint(
            constraint_id="AGENT_TIMEOUT",
            name="Agent Response Timeout",
            description="All agents must complete within 10 seconds (LLM_TIMEOUT_S)",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_agent_timeout,
            error_message="Agent exceeded 10-second timeout",
            remediation_steps=[
                "Profile agent code for slow operations",
                "Reduce payload sizes",
                "Switch to faster LLM if needed",
                "Activate fallback chain"
            ]
        ))

        # CONTRAINTE 10: 11 agents tous actifs minimum
        self.register_constraint(Constraint(
            constraint_id="AGENT_COUNT",
            name="All 11 Agents Active",
            description="System requires minimum 3 active agents; full operation = 11",
            level=ConstraintLevel.HIGH,
            validation_fn=self._validate_agent_count,
            error_message="Critical agent offline",
            remediation_steps=[
                "Check agent process logs",
                "Restart agent with exponential backoff",
                "Switch to degraded mode if persistent",
                "Alert on Telegram"
            ]
        ))

    def register_constraint(self, constraint: Constraint) -> None:
        """Enregistre nouvelle contrainte"""
        self.constraints[constraint.constraint_id] = constraint
        self.logger.info(f"Constraint registered: {constraint.name}")

    async def validate_offer_price(self, price_eur: float) -> bool:
        """Valide prix offre (plancher 1000 EUR)"""
        if not self._validate_min_contract_value(price_eur):
            violation = {
                "constraint": "MIN_CONTRACT_VALUE",
                "level": ConstraintLevel.CRITICAL.value,
                "value": price_eur,
                "required_min": self.MIN_CONTRACT_VALUE_EUR
            }
            self.violations.append(violation)
            await self._handle_violation(self.constraints["MIN_CONTRACT_VALUE"], violation)
            return False
        return True

    async def validate_decision_requires_approval(self, decision_value_eur: float) -> bool:
        """Valide si décision nécessite approbation Telegram"""
        return decision_value_eur >= self.DECISION_THRESHOLD_EUR

    async def validate_parallel_capacity(self, current_projects: int) -> bool:
        """Valide capacité parallèle"""
        if not self._validate_max_parallel(current_projects):
            return False
        return True

    def _validate_min_contract_value(self, price: float) -> bool:
        """Valide prix minimum"""
        return price >= self.MIN_CONTRACT_VALUE_EUR

    def _validate_revenue_entry(self, revenue: Dict) -> bool:
        """Valide entrée revenue"""
        return all(k in revenue for k in ["amount", "source", "client"])

    def _validate_decision_threshold(self, value: float) -> bool:
        """Valide seuil décision"""
        # Si > 500, nécessite validation
        return value < self.DECISION_THRESHOLD_EUR

    def _validate_max_parallel(self, count: int) -> bool:
        """Valide max projets parallèles"""
        return count <= self.MAX_PARALLEL_PROJECTS

    def _validate_no_hardcoded_secrets(self, code: str) -> bool:
        """Valide pas de secrets hardcodés"""
        forbidden_patterns = ["password=", "api_key=", "secret=", "token="]
        return not any(p in code.lower() for p in forbidden_patterns)

    def _validate_guardian_active(self, last_run_timestamp: float) -> bool:
        """Valide Guardian actif"""
        import time
        return (time.time() - last_run_timestamp) < (6 * 3600)  # 6 hours

    def _validate_memory_before_offer(self, offer_context: Dict) -> bool:
        """Valide mémoire consultée avant offre"""
        return offer_context.get("memory_consulted", False)

    def _validate_no_placeholders(self, code: str) -> bool:
        """Valide pas de placeholders"""
        forbidden = ["# TODO", "pass", "stub", "... ", "NotImplemented"]
        return not any(f in code for f in forbidden)

    def _validate_agent_timeout(self, duration_seconds: float) -> bool:
        """Valide timeout agent"""
        return duration_seconds < 10

    def _validate_agent_count(self, active_agents: int) -> bool:
        """Valide nombre agents"""
        return active_agents >= 3

    async def _handle_violation(self, constraint: Constraint, violation: Dict) -> None:
        """Gère violation selon niveau"""
        if constraint.level == ConstraintLevel.CRITICAL:
            self.logger.critical(f"CRITICAL VIOLATION: {constraint.name}")
            raise RuntimeError(constraint.error_message)

        elif constraint.level == ConstraintLevel.HIGH:
            self.logger.error(f"HIGH VIOLATION: {constraint.name}")
            try:
                from NAYA_CORE.integrations.telegram_notifier import TelegramNotifier
                notifier = TelegramNotifier()
                notifier.alert_system(
                    f"⚠️ VIOLATION HIGH: {constraint.name}\n"
                    f"→ {constraint.error_message}\n"
                    f"Remédiation: {'; '.join(constraint.remediation_steps[:2])}",
                    level="HIGH"
                )
            except Exception as e:
                self.logger.warning(f"Telegram alert failed for HIGH violation: {e}")

        else:
            self.logger.warning(f"VIOLATION: {constraint.name}")

    def get_violations_report(self) -> Dict:
        """Retourne rapport violations"""
        return {
            "total_violations": len(self.violations),
            "critical": len([v for v in self.violations if v.get("level") == "critical"]),
            "high": len([v for v in self.violations if v.get("level") == "high"]),
            "violations": self.violations[-10:]  # Last 10
        }

# Export
__all__ = ['ConstraintValidator', 'Constraint', 'ConstraintLevel']
