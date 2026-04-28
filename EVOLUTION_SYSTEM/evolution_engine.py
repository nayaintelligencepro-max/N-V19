"""
NAYA — Evolution Engine
Fait évoluer le système de façon continue et cumulative.
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class EvolutionType(Enum):
    PERFORMANCE = "performance"
    CAPABILITY = "capability"
    REVENUE = "revenue"
    EFFICIENCY = "efficiency"
    RESILIENCE = "resilience"

@dataclass
class EvolutionProposal:
    id: str; type: EvolutionType; description: str
    expected_impact: Dict[str, float]
    risk_level: float; priority: int
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class EvolutionEngine:
    """Fait évoluer NAYA de façon sécurisée et cumulative."""

    def __init__(self, proposal_generator=None):
        self.proposal_generator = proposal_generator
        self._history: List[EvolutionProposal] = []
        self._metrics_baseline: Dict = {}

    def propose_evolution(self, context: Dict, shi_level: str) -> List[EvolutionProposal]:
        if shi_level == "HIGH":
            return []  # Système en bonne santé, évolution normale
        proposals = []
        if context.get("revenue_growth", 0) < 0.1:
            proposals.append(EvolutionProposal(
                "EV001", EvolutionType.REVENUE,
                "Activer nouveaux canaux d'acquisition",
                {"revenue": 0.25, "clients": 0.20}, 0.2, 1))
        if context.get("automation_rate", 0) < 0.5:
            proposals.append(EvolutionProposal(
                "EV002", EvolutionType.EFFICIENCY,
                "Automatiser les tâches répétitives identifiées",
                {"time_saved": 0.40, "margin": 0.15}, 0.1, 2))
        if self.proposal_generator:
            proposals.extend(self.proposal_generator.generate_alternatives(context))
        return sorted(proposals, key=lambda p: p.priority)

    def apply_evolution(self, proposal: EvolutionProposal) -> Dict:
        proposal.status = "applied"
        self._history.append(proposal)
        return {"status": "applied", "id": proposal.id, "type": proposal.type.value,
                "expected_impact": proposal.expected_impact}

    def get_evolution_history(self) -> List[Dict]:
        return [{"id": p.id, "type": p.type.value, "status": p.status,
                 "created": p.created_at.isoformat()} for p in self._history]
