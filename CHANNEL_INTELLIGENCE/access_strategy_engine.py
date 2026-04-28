"""
NAYA — Access Strategy Engine
Définit comment atteindre les décideurs avec précision.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class DecisionMakerType(Enum):
    CEO = "ceo"; CFO = "cfo"; COO = "coo"
    DIRECTOR = "director"; MANAGER = "manager"; OWNER = "owner"

class AccessMethod(Enum):
    LINKEDIN_DM = "linkedin_dm"
    COLD_EMAIL = "cold_email"
    PHONE = "phone"
    IN_PERSON = "in_person"
    REFERRAL = "referral"
    EVENT = "event"
    CONTENT = "content"

@dataclass
class AccessStrategy:
    target: DecisionMakerType; method: AccessMethod
    sequence: List[str]; success_rate: float; avg_days_to_meeting: int

class AccessStrategyEngine:
    """Détermine la stratégie d'accès optimale pour chaque cible."""

    STRATEGIES = {
        (DecisionMakerType.CEO, "b2b"): AccessStrategy(
            DecisionMakerType.CEO, AccessMethod.LINKEDIN_DM,
            ["Connexion LinkedIn", "Message valeur J+2", "Suivi J+7", "Appel J+14"],
            0.12, 21),
        (DecisionMakerType.CFO, "finance"): AccessStrategy(
            DecisionMakerType.CFO, AccessMethod.COLD_EMAIL,
            ["Email J0", "Suivi J+3", "Appel J+7", "Proposition J+10"],
            0.09, 14),
        (DecisionMakerType.OWNER, "restaurant"): AccessStrategy(
            DecisionMakerType.OWNER, AccessMethod.IN_PERSON,
            ["Visite physique", "Diagnostic offert 30min", "Proposition 24h", "Signature"],
            0.25, 3),
    }

    def determine_strategy(self, channel: Dict) -> str:
        if channel.get("has_api"): return "DIRECT_API"
        if channel.get("decision_maker") == "owner": return "IN_PERSON"
        if channel.get("budget_confirmed"): return "FAST_CLOSE"
        return "NURTURE_SEQUENCE"

    def get_optimal_sequence(self, target_type: str, vertical: str) -> List[str]:
        dm = DecisionMakerType(target_type) if target_type in [d.value for d in DecisionMakerType] else DecisionMakerType.CEO
        key = (dm, vertical.lower())
        strategy = self.STRATEGIES.get(key, list(self.STRATEGIES.values())[0])
        return strategy.sequence

    def estimate_pipeline(self, prospects: int, target: str, vertical: str) -> Dict:
        dm = DecisionMakerType.CEO
        strategy = self.STRATEGIES.get((dm, vertical), list(self.STRATEGIES.values())[0])
        meetings = int(prospects * strategy.success_rate)
        closes = int(meetings * 0.3)
        return {"prospects": prospects, "meetings": meetings, "closes": closes,
                "expected_days": strategy.avg_days_to_meeting}
