"""NAYA V19 - Governance Rules - Regles de gouvernance du systeme."""
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CONSTITUTION")

@dataclass
class GovernanceRule:
    rule_id: str
    name: str
    description: str
    enforced: bool = True
    priority: int = 1
    category: str = "general"

class GovernanceRules:
    """Regles de gouvernance fondamentales et immuables de NAYA."""

    CORE_RULES = [
        GovernanceRule("GOV_001", "Premium Floor", "Le prix plancher est 1000 EUR minimum, jamais en dessous", True, 1, "pricing"),
        GovernanceRule("GOV_002", "Stealth Mode", "Operations furtives par defaut, confidentialite geographique", True, 1, "operations"),
        GovernanceRule("GOV_003", "Non-Regression", "Aucune evolution ne peut reduire les capacites existantes", True, 1, "evolution"),
        GovernanceRule("GOV_004", "Zero Waste", "Toute creation est recyclee, clonee, reversionnee", True, 1, "creation"),
        GovernanceRule("GOV_005", "Autonomy First", "Le systeme fonctionne sans dependance a un outil/API/service", True, 1, "sovereignty"),
        GovernanceRule("GOV_006", "Founder Loyalty", "Loyaute et fidelite exclusives envers la fondatrice", True, 1, "identity"),
        GovernanceRule("GOV_007", "Non-Sale", "Le systeme n est pas vendable, personnel, transmissible aux enfants", True, 1, "identity"),
        GovernanceRule("GOV_008", "Continuous Revenue", "Le business ne s arrete jamais, la valeur est creee en continu", True, 1, "business"),
        GovernanceRule("GOV_009", "Legal Compliance", "Tout ce que le systeme execute doit etre legal", True, 1, "legal"),
        GovernanceRule("GOV_010", "Naya-Reapers Unity", "Naya et Reapers ne font qu un, ne se bloquent jamais", True, 1, "architecture"),
        GovernanceRule("GOV_011", "Parallel Execution", "Maximum 3-4 opportunites en parallele, reste en incubation", True, 2, "execution"),
        GovernanceRule("GOV_012", "Three Tier Classification", "Douleurs classees: immediat / 7 jours / long terme", True, 2, "hunting"),
    ]

    def __init__(self):
        self._rules = {r.rule_id: r for r in self.CORE_RULES}
        self._violations: List[Dict] = []

    def check_compliance(self, action: Dict) -> Dict:
        violations = []
        price = action.get("price", 0)
        if price > 0 and price < 1000:
            violations.append({"rule": "GOV_001", "message": f"Prix {price} EUR sous le plancher premium 1000 EUR"})
        if action.get("exposes_location", False):
            violations.append({"rule": "GOV_002", "message": "Action expose la localisation geographique"})
        if action.get("is_one_shot", False):
            violations.append({"rule": "GOV_004", "message": "Creation one-shot detectee - doit etre recyclable"})

        compliant = len(violations) == 0
        if not compliant:
            self._violations.extend(violations)
        return {"compliant": compliant, "violations": violations}

    def get_rule(self, rule_id: str) -> GovernanceRule:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[GovernanceRule]:
        return list(self._rules.values())

    def get_violations(self) -> List[Dict]:
        return self._violations.copy()

    def get_stats(self) -> Dict:
        return {
            "total_rules": len(self._rules),
            "enforced": sum(1 for r in self._rules.values() if r.enforced),
            "violations_count": len(self._violations)
        }
