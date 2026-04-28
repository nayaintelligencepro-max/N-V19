"""
NAYA — Executive Engine
Moteur exécutif central — prend et applique les décisions stratégiques.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class ExecutiveDecision(Enum):
    LAUNCH_MISSION = "launch_mission"
    PAUSE_MISSION = "pause_mission"
    ESCALATE = "escalate"
    PIVOT = "pivot"
    ACCELERATE = "accelerate"
    TERMINATE = "terminate"

@dataclass
class ExecutiveOrder:
    id: str; decision: ExecutiveDecision; target: str
    rationale: str; parameters: Dict = field(default_factory=dict)
    priority: int = 5; created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ExecutiveEngine:
    """Moteur exécutif — décide et agit sans hésitation."""

    def __init__(self):
        self._orders: List[ExecutiveOrder] = []
        self._capital = {"operational": 0, "strategic": 0, "reserve": 0}

    def issue_order(self, decision: str, target: str, rationale: str,
                    params: Dict = None) -> ExecutiveOrder:
        order = ExecutiveOrder(
            id=f"EXO_{len(self._orders)+1:04d}",
            decision=ExecutiveDecision(decision),
            target=target, rationale=rationale,
            parameters=params or {}
        )
        self._orders.append(order)
        return order

    def evaluate_opportunity(self, opp: Dict) -> Dict:
        """Évalue une opportunité et prend une décision executive."""
        revenue = opp.get("revenue", 0)
        urgency = opp.get("urgency", 0.5)
        risk = opp.get("risk", 0.5)
        score = revenue * 0.5 + urgency * 0.3 - risk * 0.2
        if score >= 5000 and risk < 0.7:
            return {"decision": "LAUNCH", "score": score, "priority": "HIGH" if urgency > 0.7 else "NORMAL"}
        if risk >= 0.7:
            return {"decision": "DEFER", "reason": "Risque trop élevé"}
        return {"decision": "MONITOR", "review_in_days": 7}

    def allocate_capital(self, amount: float, purpose: str) -> Dict:
        available = self._capital["operational"]
        if amount > available * 0.3:
            return {"approved": False, "reason": "Dépasse 30% capital opérationnel"}
        self._capital["operational"] -= amount
        return {"approved": True, "allocated": amount, "purpose": purpose}

    def get_active_orders(self) -> List[ExecutiveOrder]:
        return [o for o in self._orders if o.decision != ExecutiveDecision.TERMINATE]
