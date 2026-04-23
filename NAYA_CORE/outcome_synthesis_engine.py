"""
NAYA — Outcome Synthesis Engine
Takes detected pain signals + qualified prospects, synthesizes:
1. Business model proposals (service packages with pricing)
2. Decision synthesis (go/no-go with reasoning)
3. Mutation proposals (adapt strategy based on outcomes)
"""
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

log = logging.getLogger("NAYA.SYNTHESIS")


@dataclass
class BusinessModel:
    model_id: str = ""
    title: str = ""
    pain_addressed: str = ""
    service_type: str = "consulting"
    price_floor_eur: float = 500.0
    price_ceiling_eur: float = 50000.0
    recommended_price_eur: float = 2500.0
    delivery_days: int = 14
    margin_percent: float = 85.0
    confidence: float = 0.7
    channels: List[str] = field(default_factory=lambda: ["email", "linkedin"])
    value_propositions: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict: return asdict(self)


@dataclass
class DecisionOutcome:
    decision: str = "hold"  # go / no-go / hold
    score: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommended_action: str = ""
    urgency: str = "normal"  # low / normal / high / critical


@dataclass
class MutationProposal:
    mutation_id: str = ""
    target_module: str = ""
    change_type: str = ""  # pricing / channel / timing / scope
    current_value: str = ""
    proposed_value: str = ""
    expected_impact: str = ""
    confidence: float = 0.5


# ─── Pricing matrices by sector ──────────────────────────────
# Seul le plancher (floor) est inviolable. Pas de plafond (ceiling) — illimité vers le haut.
_SECTOR_PRICING = {
    "technology":  {"floor": 2000, "base": 5000},
    "finance":     {"floor": 3000, "base": 8000},
    "healthcare":  {"floor": 2500, "base": 6000},
    "retail":      {"floor": 1000, "base": 3000},
    "manufacturing":{"floor": 1500, "base": 4000},
    "default":     {"floor": 1000, "base": 2500},
}

_SERVICE_TYPES = {
    "audit": {"multiplier": 1.0, "days": 7},
    "consulting": {"multiplier": 1.5, "days": 14},
    "implementation": {"multiplier": 2.5, "days": 30},
    "managed_service": {"multiplier": 3.0, "days": 90},
    "emergency": {"multiplier": 2.0, "days": 3},
}


class OutcomeSynthesisEngine:
    """Synthesizes hunt results into actionable business outcomes."""

    def __init__(self):
        self._decisions_made = 0
        self._models_generated = 0
        self._mutations_proposed = 0
        self._history: List[Dict] = []

    def synthesize_decision(self, data: Dict[str, Any]) -> DecisionOutcome:
        """
        Analyze prospect data and produce a go/no-go decision.
        data keys: company, sector, pain_signals, estimated_value, confidence, score
        """
        self._decisions_made += 1
        outcome = DecisionOutcome()
        reasoning = []
        risks = []

        score = data.get("score", 0)
        confidence = data.get("confidence", 0.5)
        value = data.get("estimated_value", 0)
        pain_count = len(data.get("pain_signals", []))
        sector = data.get("sector", "").lower()

        # Score-based decision
        if score >= 75 and confidence >= 0.7:
            outcome.decision = "go"
            reasoning.append(f"High score ({score}) with strong confidence ({confidence:.0%})")
        elif score >= 50 and confidence >= 0.5:
            outcome.decision = "go"
            reasoning.append(f"Moderate score ({score}) — viable opportunity")
        elif score >= 35:
            outcome.decision = "hold"
            reasoning.append(f"Borderline score ({score}) — monitor and re-evaluate")
        else:
            outcome.decision = "no-go"
            reasoning.append(f"Low score ({score}) — not worth pursuing now")

        # Value check
        if value > 10000:
            reasoning.append(f"High-value opportunity: {value}EUR potential")
            if outcome.decision == "hold":
                outcome.decision = "go"
        elif value < 500:
            risks.append("Very low estimated value — may not cover acquisition cost")

        # Pain signal density
        if pain_count >= 3:
            reasoning.append(f"Multiple pain signals detected ({pain_count})")
        elif pain_count == 0:
            risks.append("No pain signals — cold prospect")
            if outcome.decision == "go":
                outcome.decision = "hold"

        # Urgency assessment
        if score >= 85 and pain_count >= 2:
            outcome.urgency = "critical"
            outcome.recommended_action = "Contact within 24h — high conversion probability"
        elif score >= 65:
            outcome.urgency = "high"
            outcome.recommended_action = "Schedule outreach within 48h"
        elif outcome.decision == "go":
            outcome.urgency = "normal"
            outcome.recommended_action = "Add to weekly outreach pipeline"
        else:
            outcome.urgency = "low"
            outcome.recommended_action = "Archive and revisit in 30 days"

        outcome.score = score
        outcome.reasoning = reasoning
        outcome.risks = risks

        self._history.append({
            "type": "decision", "company": data.get("company", ""),
            "decision": outcome.decision, "score": score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        log.info("[SYNTHESIS] Decision: %s for %s (score=%s, urgency=%s)",
                 outcome.decision, data.get("company", "?"), score, outcome.urgency)
        return outcome

    def generate_business_model(self, market_data: Dict[str, Any]) -> BusinessModel:
        """
        Generate a service package/business model for a prospect.
        market_data keys: company, sector, pain_type, pain_description, estimated_value, company_size
        """
        self._models_generated += 1
        sector = market_data.get("sector", "default").lower()
        pain_type = market_data.get("pain_type", "operational")
        pain_desc = market_data.get("pain_description", "business optimization")
        company_size = market_data.get("company_size", "sme")
        estimated_value = market_data.get("estimated_value", 5000)

        # Get pricing from sector matrix
        pricing = _SECTOR_PRICING.get(sector, _SECTOR_PRICING["default"])

        # Determine service type based on pain
        if "urgent" in pain_desc.lower() or "critical" in pain_desc.lower():
            svc_type = "emergency"
        elif "audit" in pain_desc.lower() or "diagnostic" in pain_desc.lower():
            svc_type = "audit"
        elif "implement" in pain_desc.lower() or "build" in pain_desc.lower():
            svc_type = "implementation"
        elif "manage" in pain_desc.lower() or "ongoing" in pain_desc.lower():
            svc_type = "managed_service"
        else:
            svc_type = "consulting"

        svc_config = _SERVICE_TYPES[svc_type]

        # Size multiplier
        size_mult = {"startup": 0.6, "sme": 1.0, "mid-market": 1.8, "enterprise": 3.0}.get(company_size, 1.0)

        # Calculate recommended price — floor enforced, no ceiling
        base = pricing["base"] * svc_config["multiplier"] * size_mult
        recommended = max(pricing["floor"], round(base, -2))

        # Generate value propositions
        value_props = self._generate_value_props(pain_type, sector, estimated_value)

        # Unique ID
        uid = hashlib.md5(f"{market_data.get('company','')}{time.time()}".encode()).hexdigest()[:12]

        model = BusinessModel(
            model_id=f"BM-{uid}",
            title=f"{svc_type.replace('_',' ').title()} — {pain_type.title()} Optimization",
            pain_addressed=pain_desc[:200],
            service_type=svc_type,
            price_floor_eur=float(pricing["floor"]),
            price_ceiling_eur=0.0,  # Pas de plafond — illimité vers le haut
            recommended_price_eur=float(recommended),
            delivery_days=svc_config["days"],
            margin_percent=85.0 if svc_type in ("consulting", "audit") else 70.0,
            confidence=min(0.95, 0.6 + (estimated_value / 100000)),
            channels=self._select_channels(company_size, sector),
            value_propositions=value_props,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._history.append({
            "type": "model", "model_id": model.model_id,
            "price": model.recommended_price_eur,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        log.info("[SYNTHESIS] Model %s: %s @ %sEUR (%s days)",
                 model.model_id, model.title, model.recommended_price_eur, model.delivery_days)
        return model

    def propose_mutation(self, current_state: Dict[str, Any]) -> List[MutationProposal]:
        """
        Analyze current performance and propose strategic mutations.
        current_state keys: conversion_rate, avg_deal_size, pipeline_count,
                           top_channel, response_rate, win_rate
        """
        self._mutations_proposed += 1
        proposals = []

        conv_rate = current_state.get("conversion_rate", 0)
        avg_deal = current_state.get("avg_deal_size", 0)
        pipeline = current_state.get("pipeline_count", 0)
        response_rate = current_state.get("response_rate", 0)
        win_rate = current_state.get("win_rate", 0)

        # Low conversion → suggest pricing adjustment
        if conv_rate < 0.05 and avg_deal > 3000:
            proposals.append(MutationProposal(
                mutation_id=f"MUT-price-{int(time.time())}",
                target_module="pricing_engine",
                change_type="pricing",
                current_value=f"{avg_deal}EUR avg",
                proposed_value=f"{avg_deal * 0.7:.0f}EUR avg (-30%)",
                expected_impact="Increase conversion rate by 40-60%",
                confidence=0.7,
            ))

        # Low pipeline → suggest channel expansion
        if pipeline < 10:
            proposals.append(MutationProposal(
                mutation_id=f"MUT-channel-{int(time.time())}",
                target_module="channel_intelligence",
                change_type="channel",
                current_value=current_state.get("top_channel", "email"),
                proposed_value="Add LinkedIn + Telegram outreach",
                expected_impact=f"Increase pipeline from {pipeline} to {pipeline * 3}+",
                confidence=0.65,
            ))

        # Low response rate → suggest timing change
        if response_rate < 0.1:
            proposals.append(MutationProposal(
                mutation_id=f"MUT-timing-{int(time.time())}",
                target_module="scheduler",
                change_type="timing",
                current_value="Current outreach schedule",
                proposed_value="Shift to Tuesday-Thursday 9-11AM local time",
                expected_impact="Improve response rate by 25-40%",
                confidence=0.6,
            ))

        # High win rate but low volume → scale up
        if win_rate > 0.3 and pipeline < 20:
            proposals.append(MutationProposal(
                mutation_id=f"MUT-scale-{int(time.time())}",
                target_module="hunt_engine",
                change_type="scope",
                current_value=f"{pipeline} prospects in pipeline",
                proposed_value="Increase hunt frequency to 3x/day, expand sectors",
                expected_impact=f"Revenue potential +{win_rate * avg_deal * 10:.0f}EUR/month",
                confidence=0.75,
            ))

        if not proposals:
            proposals.append(MutationProposal(
                mutation_id=f"MUT-maintain-{int(time.time())}",
                target_module="system",
                change_type="scope",
                current_value="Current configuration",
                proposed_value="Maintain current strategy — performing within norms",
                expected_impact="Stable revenue trajectory",
                confidence=0.8,
            ))

        log.info("[SYNTHESIS] %d mutations proposed", len(proposals))
        return proposals

    def _generate_value_props(self, pain_type: str, sector: str, value: float) -> List[str]:
        """Generate contextual value propositions."""
        props = []
        if value > 10000:
            props.append(f"Estimated ROI: {value * 3:.0f}EUR over 12 months")
        props.append(f"Specialized {sector} expertise with proven methodology")
        if pain_type in ("financial", "operational"):
            props.append("Measurable cost reduction within 30 days")
        if pain_type == "technical":
            props.append("Technical implementation with full documentation and training")
        props.append("Satisfaction guarantee — results or money back")
        return props

    def _select_channels(self, company_size: str, sector: str) -> List[str]:
        """Select optimal outreach channels."""
        if company_size in ("enterprise", "mid-market"):
            return ["linkedin", "email", "direct_call"]
        if sector in ("technology", "finance"):
            return ["linkedin", "email"]
        return ["email", "linkedin", "whatsapp"]

    def get_stats(self) -> Dict:
        return {
            "decisions_made": self._decisions_made,
            "models_generated": self._models_generated,
            "mutations_proposed": self._mutations_proposed,
            "history_size": len(self._history),
            "last_actions": self._history[-5:] if self._history else [],
        }


# Singleton
_ENGINE: Optional[OutcomeSynthesisEngine] = None
_LOCK = __import__("threading").Lock()

def get_synthesis_engine() -> OutcomeSynthesisEngine:
    global _ENGINE
    if _ENGINE is None:
        with _LOCK:
            if _ENGINE is None:
                _ENGINE = OutcomeSynthesisEngine()
    return _ENGINE
