"""NAYA — Capital Structure — Gestion de la structure du capital."""
from typing import Dict
from dataclasses import dataclass

@dataclass
class CapitalState:
    operational: float = 0.0   # Capital disponible pour opérations
    strategic: float = 0.0     # Réserve stratégique (investissements)
    emergency: float = 0.0     # Réserve urgence (ne jamais toucher)
    equity_pool: float = 0.0   # Pool d'équité pour croissance

class CapitalStructure:
    """Gère la structure financière de NAYA."""

    ALLOCATION_RULES = {
        "operational": 0.50,  # 50% pour opérations courantes
        "strategic": 0.30,    # 30% pour investissements
        "emergency": 0.15,    # 15% réserve intouchable
        "equity_pool": 0.05,  # 5% pour equity/partenariats
    }

    def __init__(self):
        self.state = CapitalState()

    def inject_revenue(self, amount: float) -> Dict:
        """Distribue le revenue selon les règles d'allocation."""
        allocations = {}
        for bucket, ratio in self.ALLOCATION_RULES.items():
            alloc = amount * ratio
            setattr(self.state, bucket, getattr(self.state, bucket) + alloc)
            allocations[bucket] = alloc
        return allocations

    def update_reserves(self, operational: float, strategic: float, equity: float):
        self.state.operational = operational
        self.state.strategic = strategic
        self.state.equity_pool = equity

    def reserve_ratio(self) -> float:
        total = self.state.operational + self.state.strategic
        return self.state.operational / total if total > 0 else 0

    def can_invest(self, amount: float) -> bool:
        return self.state.strategic >= amount

    def summary(self) -> Dict:
        total = (self.state.operational + self.state.strategic + 
                 self.state.emergency + self.state.equity_pool)
        return {"total": total, "operational": self.state.operational,
                "strategic": self.state.strategic, "reserve_ratio": self.reserve_ratio()}
