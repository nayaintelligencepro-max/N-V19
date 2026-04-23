"""
NAYA SUPREME V19 — Closing Workflow (LangGraph)
Réponse prospect → Qualification → Objection → Négociation → Signature.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

log = logging.getLogger("NAYA.ClosingWorkflow")

MIN_CONTRACT_VALUE_EUR = 1_000


# ── State ─────────────────────────────────────────────────────────────────────

class ClosingState(TypedDict):
    prospect_id: str
    reply_text: str
    sentiment: str          # positive / neutral / negative / objection
    objection_type: str
    objection_response: str
    negotiation_round: int
    final_price_eur: float
    contract_url: str
    payment_url: str
    status: str             # analyzing / objecting / negotiating / won / lost


# ── Nodes ─────────────────────────────────────────────────────────────────────

def analyze_reply(state: ClosingState) -> ClosingState:
    """Analyse le sentiment et la nature de la réponse."""
    log.info("[ClosingWorkflow] analyze_reply — prospect %s", state.get("prospect_id"))
    text = state.get("reply_text", "").lower()

    if any(w in text for w in ["intéressé", "interested", "oui", "yes", "partant", "d'accord"]):
        state["sentiment"] = "positive"
    elif any(w in text for w in ["cher", "budget", "expensive", "prix", "coût"]):
        state["sentiment"] = "objection"
        state["objection_type"] = "price"
    elif any(w in text for w in ["non", "no", "pas intéressé", "not interested"]):
        state["sentiment"] = "negative"
    else:
        state["sentiment"] = "neutral"

    state["status"] = "analyzing"
    return state


def handle_objection(state: ClosingState) -> ClosingState:
    """Répond à l'objection avec la meilleure réponse mémorisée."""
    log.info("[ClosingWorkflow] handle_objection — type: %s", state.get("objection_type"))

    OBJECTION_RESPONSES = {
        "price": (
            "Je comprends votre préoccupation sur le budget. "
            "Nos clients constatent en moyenne un ROI de 3x en 6 mois grâce à la réduction "
            "des incidents OT. Nous pouvons proposer un paiement en 3 fois sans frais."
        ),
        "time": (
            "Notre méthodologie est conçue pour un impact minimal sur vos opérations. "
            "Le sprint initial de 5 jours peut se faire en dehors des heures de production."
        ),
        "trust": (
            "Voici 3 références vérifiables dans votre secteur. "
            "Nous proposons également un audit flash gratuit de 2h pour démontrer la valeur."
        ),
    }

    obj_type = state.get("objection_type", "price")
    state["objection_response"] = OBJECTION_RESPONSES.get(
        obj_type, OBJECTION_RESPONSES["price"]
    )
    state["status"] = "objecting"
    return state


def negotiate(state: ClosingState) -> ClosingState:
    """Gère la négociation avec garde-fou plancher 1 000 EUR."""
    log.info("[ClosingWorkflow] negotiate — round %d", state.get("negotiation_round", 0) + 1)
    state["negotiation_round"] = state.get("negotiation_round", 0) + 1

    price = state.get("final_price_eur", 15_000)

    # Max 1 discount of 10%, never below floor
    if state["negotiation_round"] == 1:
        price = max(price * 0.90, MIN_CONTRACT_VALUE_EUR)
    elif state["negotiation_round"] >= 2:
        # No further discount — hold position
        pass

    state["final_price_eur"] = price
    state["status"] = "negotiating"
    return state


def close_deal(state: ClosingState) -> ClosingState:
    """Génère le contrat et le lien de paiement."""
    log.info("[ClosingWorkflow] close_deal — %.0f EUR", state.get("final_price_eur", 0))

    price = state.get("final_price_eur", 0)
    if price < MIN_CONTRACT_VALUE_EUR:
        log.error("Prix %.0f EUR inférieur au plancher %d EUR — deal refusé", price, MIN_CONTRACT_VALUE_EUR)
        state["status"] = "lost"
        return state

    # In production: ContractGeneratorAgent + PaymentEngine
    state["contract_url"] = f"https://naya.app/contracts/{state['prospect_id']}"
    state["payment_url"] = f"https://deblok.me/naya/{state['prospect_id']}"
    state["status"] = "won"
    log.info("✅ Deal GAGNÉ — %s — %.0f EUR", state["prospect_id"], price)
    return state


def mark_lost(state: ClosingState) -> ClosingState:
    """Marque le prospect comme perdu et déclenche le recyclage."""
    log.info("[ClosingWorkflow] mark_lost — prospect %s", state.get("prospect_id"))
    state["status"] = "lost"
    return state


def route_after_analysis(state: ClosingState) -> str:
    """Routing conditionnel selon le sentiment."""
    sentiment = state.get("sentiment", "neutral")
    if sentiment == "positive":
        return "close"
    if sentiment == "objection":
        return "objection"
    if sentiment == "negative":
        return "lost"
    return "negotiate"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_closing_workflow():
    """Construit et retourne le graph LangGraph du closing workflow."""
    try:
        from langgraph.graph import StateGraph

        graph = StateGraph(ClosingState)
        graph.add_node("analyze", analyze_reply)
        graph.add_node("objection", handle_objection)
        graph.add_node("negotiate", negotiate)
        graph.add_node("close", close_deal)
        graph.add_node("lost", mark_lost)

        graph.set_entry_point("analyze")
        graph.add_conditional_edges("analyze", route_after_analysis, {
            "close": "close",
            "objection": "objection",
            "lost": "lost",
            "negotiate": "negotiate",
        })
        graph.add_edge("objection", "negotiate")
        graph.add_edge("negotiate", "close")
        graph.set_finish_point("close")
        graph.set_finish_point("lost")

        return graph.compile()
    except Exception as exc:
        log.warning("LangGraph closing workflow build failed: %s — fallback séquentiel", exc)
        return None


async def run_closing(
    prospect_id: str,
    reply_text: str,
    offer_price_eur: float = 15_000.0,
) -> ClosingState:
    """Point d'entrée : traite une réponse prospect et tente le closing."""
    state: ClosingState = {
        "prospect_id": prospect_id,
        "reply_text": reply_text,
        "sentiment": "",
        "objection_type": "",
        "objection_response": "",
        "negotiation_round": 0,
        "final_price_eur": offer_price_eur,
        "contract_url": "",
        "payment_url": "",
        "status": "init",
    }

    workflow = build_closing_workflow()
    if workflow:
        try:
            return await workflow.ainvoke(state)
        except Exception as exc:
            log.warning("Closing workflow async failed: %s — fallback", exc)

    # Fallback séquentiel
    state = analyze_reply(state)
    if state["sentiment"] == "objection":
        state = handle_objection(state)
        state = negotiate(state)
    elif state["sentiment"] == "negative":
        state = mark_lost(state)
        return state
    state = close_deal(state)
    return state
