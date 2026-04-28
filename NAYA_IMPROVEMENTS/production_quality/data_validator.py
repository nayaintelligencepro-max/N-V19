"""
QUALITÉ #5 — Validateur de données production-grade.

Valide toutes les données entrantes et sortantes du système
pour garantir l'intégrité et la cohérence.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    field: str
    valid: bool
    value: Any
    error: Optional[str] = None


class DataValidator:
    """
    Validateur de données pour le système NAYA.

    Valide les emails, montants, prospects, contrats et toutes les données
    critiques avant traitement.
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    URL_REGEX = re.compile(r"^https?://[^\s<>\"']+$")
    PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{8,20}$")

    MINIMUM_CONTRACT_EUR = 1000

    def __init__(self) -> None:
        self._validations_run: int = 0
        self._validations_failed: int = 0
        logger.info("[DataValidator] Initialisé — validations multi-champs activées")

    def validate_email(self, email: str) -> ValidationResult:
        self._validations_run += 1
        if not email or not self.EMAIL_REGEX.match(email):
            self._validations_failed += 1
            return ValidationResult("email", False, email, "Format email invalide")
        return ValidationResult("email", True, email)

    def validate_amount(self, amount: float, field_name: str = "amount") -> ValidationResult:
        self._validations_run += 1
        if amount < self.MINIMUM_CONTRACT_EUR:
            self._validations_failed += 1
            return ValidationResult(
                field_name, False, amount,
                f"Montant {amount} EUR < plancher {self.MINIMUM_CONTRACT_EUR} EUR",
            )
        if amount > 10_000_000:
            self._validations_failed += 1
            return ValidationResult(field_name, False, amount, "Montant anormalement élevé — vérification requise")
        return ValidationResult(field_name, True, amount)

    def validate_prospect(self, prospect: Dict[str, Any]) -> List[ValidationResult]:
        """Valide un prospect complet."""
        results: List[ValidationResult] = []

        if "email" in prospect:
            results.append(self.validate_email(prospect["email"]))

        if "company_name" in prospect:
            self._validations_run += 1
            name = prospect["company_name"]
            if not name or len(name) < 2:
                self._validations_failed += 1
                results.append(ValidationResult("company_name", False, name, "Nom d'entreprise trop court"))
            else:
                results.append(ValidationResult("company_name", True, name))

        if "budget_eur" in prospect:
            results.append(self.validate_amount(prospect["budget_eur"], "budget_eur"))

        return results

    def validate_contract(self, contract: Dict[str, Any]) -> List[ValidationResult]:
        """Valide un contrat avant génération."""
        results: List[ValidationResult] = []

        required_fields = ["client_name", "service", "amount_eur"]
        for field_name in required_fields:
            self._validations_run += 1
            if field_name not in contract or not contract[field_name]:
                self._validations_failed += 1
                results.append(ValidationResult(field_name, False, None, f"Champ requis '{field_name}' manquant"))
            else:
                results.append(ValidationResult(field_name, True, contract[field_name]))

        if "amount_eur" in contract:
            results.append(self.validate_amount(contract["amount_eur"], "contract_amount"))

        return results

    def is_valid(self, results: List[ValidationResult]) -> bool:
        return all(r.valid for r in results)

    def stats(self) -> Dict[str, Any]:
        return {
            "validations_run": self._validations_run,
            "validations_failed": self._validations_failed,
            "success_rate_pct": round(
                ((self._validations_run - self._validations_failed) / max(self._validations_run, 1)) * 100, 1
            ),
        }


data_validator = DataValidator()
