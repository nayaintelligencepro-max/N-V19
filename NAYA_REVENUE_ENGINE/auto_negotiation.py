"""
NAYA V19 - Auto Negotiation Engine
Negocie automatiquement avec les prospects selon des regles:
- Ne jamais descendre sous le plancher premium
- Proposer alternatives (echelonnement, scope reduit)
- Savoir quand closer vs relancer
"""
import time, logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.NEGOTIATION")

class NegotiationAction(Enum):
    HOLD_PRICE = "hold_price"
    OFFER_PAYMENT_PLAN = "offer_payment_plan"
    REDUCE_SCOPE = "reduce_scope"
    ADD_BONUS = "add_bonus"
    CLOSE_NOW = "close_now"
    WALK_AWAY = "walk_away"
    FOLLOW_UP_LATER = "follow_up_later"

@dataclass
class NegotiationState:
    prospect_id: str
    original_price: float
    current_offer: float
    prospect_counter: float
    rounds: int = 0
    max_rounds: int = 4
    floor_price: float = 1000
    prospect_objections: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)

@dataclass
class NegotiationResponse:
    action: NegotiationAction
    new_price: float
    message: str
    alternatives: List[Dict] = field(default_factory=list)
    should_close: bool = False

class AutoNegotiationEngine:
    """Negocie de maniere autonome en respectant le plancher premium."""

    ABSOLUTE_FLOOR = 1000
    MAX_DISCOUNT_PCT = 20  # Jamais plus de 20% de remise
    URGENCY_THRESHOLD = 3  # Apres 3 rounds, proposer un close

    def __init__(self):
        self._states: Dict[str, NegotiationState] = {}
        self._total_negotiations = 0
        self._total_closed = 0
        self._total_walked_away = 0

    def start_negotiation(self, prospect_id: str, price: float) -> NegotiationState:
        floor = max(self.ABSOLUTE_FLOOR, price * (1 - self.MAX_DISCOUNT_PCT / 100))
        state = NegotiationState(
            prospect_id=prospect_id,
            original_price=price,
            current_offer=price,
            prospect_counter=0,
            floor_price=floor
        )
        self._states[prospect_id] = state
        self._total_negotiations += 1
        return state

    def handle_counter(self, prospect_id: str, counter_price: float,
                       objection: str = "") -> NegotiationResponse:
        """Gere une contre-proposition du prospect."""
        state = self._states.get(prospect_id)
        if not state:
            state = self.start_negotiation(prospect_id, counter_price * 1.5)

        state.rounds += 1
        state.prospect_counter = counter_price
        if objection:
            state.prospect_objections.append(objection)

        # Strategie de negociation
        gap = state.current_offer - counter_price
        gap_pct = gap / state.current_offer if state.current_offer > 0 else 0

        # Cas 1: Le prospect accepte ou est tres proche
        if gap_pct <= 0.05:
            state.actions_taken.append("close")
            self._total_closed += 1
            return NegotiationResponse(
                action=NegotiationAction.CLOSE_NOW,
                new_price=max(counter_price, state.floor_price),
                message="Excellent! Nous avons un accord. Procedons a la mise en place.",
                should_close=True
            )

        # Cas 2: Contre trop basse (sous le floor)
        if counter_price < state.floor_price:
            if "budget" in objection.lower() or "cher" in objection.lower():
                # Proposer alternatives
                reduced_scope_price = state.floor_price
                payment_plan = state.current_offer
                state.actions_taken.append("offer_alternatives")
                return NegotiationResponse(
                    action=NegotiationAction.OFFER_PAYMENT_PLAN,
                    new_price=state.current_offer,
                    message="Je comprends votre contrainte budget. Voici ce que je peux proposer:",
                    alternatives=[
                        {"type": "payment_plan", "price": payment_plan,
                         "description": f"Echelonnement: 3x {payment_plan/3:.0f}EUR"},
                        {"type": "reduced_scope", "price": reduced_scope_price,
                         "description": f"Version essentielle a {reduced_scope_price:.0f}EUR"},
                    ]
                )
            else:
                state.actions_taken.append("hold_price")
                return NegotiationResponse(
                    action=NegotiationAction.HOLD_PRICE,
                    new_price=state.current_offer,
                    message=f"Notre tarif reflete la valeur reelle du service. A {state.current_offer:.0f}EUR, votre ROI est de {state.original_price * 5 / state.current_offer:.0f}x."
                )

        # Cas 3: Gap raisonnable - faire un pas
        if state.rounds <= 2:
            new_price = state.current_offer - (gap * 0.3)  # Conceder 30% du gap
            new_price = max(new_price, state.floor_price)
            state.current_offer = new_price
            state.actions_taken.append("concede_partial")
            return NegotiationResponse(
                action=NegotiationAction.HOLD_PRICE,
                new_price=new_price,
                message=f"En consideration de notre futur partenariat, je peux ajuster a {new_price:.0f}EUR. C est notre meilleure proposition."
            )

        # Cas 4: Trop de rounds - close ou walk
        if state.rounds >= self.URGENCY_THRESHOLD:
            final_price = max(state.floor_price, counter_price + (gap * 0.5))
            state.actions_taken.append("final_offer")
            return NegotiationResponse(
                action=NegotiationAction.CLOSE_NOW,
                new_price=final_price,
                message=f"Proposition finale: {final_price:.0f}EUR. Cette offre expire dans 48h.",
                should_close=True
            )

        # Default: hold
        return NegotiationResponse(
            action=NegotiationAction.HOLD_PRICE,
            new_price=state.current_offer,
            message="Maintenons notre proposition actuelle."
        )

    def get_stats(self) -> Dict:
        return {
            "total_negotiations": self._total_negotiations,
            "total_closed": self._total_closed,
            "total_walked_away": self._total_walked_away,
            "active": len(self._states),
            "close_rate": self._total_closed / self._total_negotiations if self._total_negotiations > 0 else 0
        }

_neg = None
def get_negotiation() -> AutoNegotiationEngine:
    global _neg
    if _neg is None:
        _neg = AutoNegotiationEngine()
    return _neg
