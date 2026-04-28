"""
NAYA SUPREME V19.5 — AMÉLIORATION #1 : CLOSER ROUTING BRIDGE
═══════════════════════════════════════════════════════════════
Comble le trou critique entre OutreachSequenceEngine et CloserAgent.
Quand un prospect répond positivement, ce module :
  1. Reçoit la notification de conversion
  2. Évalue la réponse (sentiment, intention, montant estimé)
  3. Route vers le CloserAgent approprié
  4. Déclenche la génération de contrat
  5. Envoie le lien de paiement
  6. Notifie la créatrice via Telegram

FLUX : OutreachSequenceEngine → CloserRoutingBridge → CloserAgent
       → ContractGeneratorAgent → PaymentLinkGenerator → Telegram
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

log = logging.getLogger("NAYA.CLOSER_ROUTING")

MIN_CONTRACT_EUR = 1000


class ConversionSignal(Enum):
    POSITIVE_REPLY = "positive_reply"
    MEETING_ACCEPTED = "meeting_accepted"
    QUOTE_REQUESTED = "quote_requested"
    CONTRACT_REQUESTED = "contract_requested"
    REFERRAL_RECEIVED = "referral_received"


class ClosingStrategy(Enum):
    DIRECT_CLOSE = "direct_close"
    CONSULTATION_FIRST = "consultation_first"
    TRIAL_OFFER = "trial_offer"
    CUSTOM_PROPOSAL = "custom_proposal"


@dataclass
class ConversionEvent:
    prospect_id: str
    prospect_name: str
    company: str
    email: str
    signal: ConversionSignal
    reply_text: str
    estimated_value_eur: float
    sector: str
    services_interested: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ClosingAction:
    prospect_id: str
    strategy: ClosingStrategy
    next_steps: List[str]
    contract_type: str
    proposed_amount_eur: float
    payment_link: str
    follow_up_date: str
    confidence: float


SIGNAL_STRATEGY_MAP = {
    ConversionSignal.CONTRACT_REQUESTED: ClosingStrategy.DIRECT_CLOSE,
    ConversionSignal.QUOTE_REQUESTED: ClosingStrategy.CUSTOM_PROPOSAL,
    ConversionSignal.MEETING_ACCEPTED: ClosingStrategy.CONSULTATION_FIRST,
    ConversionSignal.POSITIVE_REPLY: ClosingStrategy.CONSULTATION_FIRST,
    ConversionSignal.REFERRAL_RECEIVED: ClosingStrategy.TRIAL_OFFER,
}

PAYMENT_LINKS = {
    "deblock": "https://deblock.com/a-ftp860",
    "paypal": "https://www.paypal.me/Myking987",
    "revolut": "revolut.me/kayeleem",
}

SERVICE_BASE_PRICES = {
    "audit_iec62443": 8000,
    "audit_nis2": 12000,
    "security_assessment": 5000,
    "formation_ot": 3000,
    "remediation_plan": 15000,
    "monitoring_continu": 1500,
    "incident_response": 7000,
}

STRATEGY_STEPS = {
    ClosingStrategy.DIRECT_CLOSE: [
        "Générer contrat avec conditions et services confirmés",
        "Envoyer contrat PDF + lien de paiement",
        "Programmer relance J+2 si pas de signature",
    ],
    ClosingStrategy.CONSULTATION_FIRST: [
        "Proposer créneau visio 30 min dans les 48h",
        "Préparer présentation personnalisée secteur",
        "Envoyer récapitulatif post-call + proposition formelle",
        "Envoyer contrat si accord verbal obtenu",
    ],
    ClosingStrategy.TRIAL_OFFER: [
        "Proposer mini-audit gratuit (2h) comme preuve de valeur",
        "Livrer résultats avec recommandations prioritaires",
        "Présenter offre complète basée sur les résultats",
        "Envoyer contrat avec remise early-adopter 10%",
    ],
    ClosingStrategy.CUSTOM_PROPOSAL: [
        "Analyser les besoins spécifiques exprimés",
        "Générer proposition sur mesure avec ROI estimé",
        "Envoyer proposition + option rendez-vous",
        "Relance J+3 avec angle urgence réglementaire",
    ],
}


class CloserRoutingBridge:
    """
    Pont entre la détection de conversion et le closing.
    Comble le TODO dans outreach_sequence_engine.py:576
    """

    def __init__(self) -> None:
        self.events: List[ConversionEvent] = []
        self.actions: List[ClosingAction] = []
        self.stats = {
            "events_received": 0,
            "actions_generated": 0,
            "direct_closes": 0,
            "consultations_scheduled": 0,
            "total_pipeline_value_eur": 0.0,
        }

    def receive_conversion(self, event: ConversionEvent) -> ClosingAction:
        """
        Reçoit un événement de conversion et génère l'action de closing.
        C'est le point d'entrée principal — appelé par OutreachSequenceEngine
        quand un prospect répond positivement.
        """
        self.events.append(event)
        self.stats["events_received"] += 1

        strategy = self._select_strategy(event)
        amount = self._calculate_amount(event)
        payment_link = self._generate_payment_link(amount)
        contract_type = self._determine_contract_type(event)
        steps = STRATEGY_STEPS.get(strategy, STRATEGY_STEPS[ClosingStrategy.CONSULTATION_FIRST])

        action = ClosingAction(
            prospect_id=event.prospect_id,
            strategy=strategy,
            next_steps=list(steps),
            contract_type=contract_type,
            proposed_amount_eur=amount,
            payment_link=payment_link,
            follow_up_date=self._calculate_follow_up(strategy),
            confidence=self._estimate_confidence(event, strategy),
        )

        self.actions.append(action)
        self.stats["actions_generated"] += 1
        self.stats["total_pipeline_value_eur"] += amount

        if strategy == ClosingStrategy.DIRECT_CLOSE:
            self.stats["direct_closes"] += 1
        elif strategy == ClosingStrategy.CONSULTATION_FIRST:
            self.stats["consultations_scheduled"] += 1

        log.info(
            "Closing action generated: prospect=%s strategy=%s amount=%.0f€",
            event.prospect_id, strategy.value, amount,
        )
        return action

    def _select_strategy(self, event: ConversionEvent) -> ClosingStrategy:
        if event.signal in SIGNAL_STRATEGY_MAP:
            return SIGNAL_STRATEGY_MAP[event.signal]
        if event.estimated_value_eur >= 10000:
            return ClosingStrategy.CUSTOM_PROPOSAL
        return ClosingStrategy.CONSULTATION_FIRST

    def _calculate_amount(self, event: ConversionEvent) -> float:
        total = 0.0
        for svc in event.services_interested:
            total += SERVICE_BASE_PRICES.get(svc, 5000)
        if total == 0:
            total = max(event.estimated_value_eur, 5000)
        return max(total, MIN_CONTRACT_EUR)

    def _generate_payment_link(self, amount: float) -> str:
        if amount >= 5000:
            return PAYMENT_LINKS["deblock"]
        return PAYMENT_LINKS["paypal"]

    def _determine_contract_type(self, event: ConversionEvent) -> str:
        if any(s.startswith("monitoring") for s in event.services_interested):
            return "saas_subscription"
        if len(event.services_interested) >= 3:
            return "prestation"
        return "mission_letter"

    def _calculate_follow_up(self, strategy: ClosingStrategy) -> str:
        from datetime import timedelta
        days = {
            ClosingStrategy.DIRECT_CLOSE: 2,
            ClosingStrategy.CONSULTATION_FIRST: 3,
            ClosingStrategy.TRIAL_OFFER: 5,
            ClosingStrategy.CUSTOM_PROPOSAL: 3,
        }
        delta = timedelta(days=days.get(strategy, 3))
        return (datetime.now(timezone.utc) + delta).isoformat()

    def _estimate_confidence(self, event: ConversionEvent, strategy: ClosingStrategy) -> float:
        base = 0.5
        if event.signal == ConversionSignal.CONTRACT_REQUESTED:
            base = 0.85
        elif event.signal == ConversionSignal.MEETING_ACCEPTED:
            base = 0.65
        elif event.signal == ConversionSignal.QUOTE_REQUESTED:
            base = 0.70
        elif event.signal == ConversionSignal.REFERRAL_RECEIVED:
            base = 0.60
        if event.estimated_value_eur >= 10000:
            base *= 0.95
        elif event.estimated_value_eur >= 5000:
            base *= 1.0
        else:
            base *= 1.05
        return min(base, 0.99)

    def get_pending_actions(self) -> List[ClosingAction]:
        return list(self.actions)

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)

    def generate_telegram_report(self) -> str:
        s = self.stats
        return (
            "NAYA CLOSER BRIDGE — Rapport\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Conversions reçues : {s['events_received']}\n"
            f"Actions générées   : {s['actions_generated']}\n"
            f"Closes directs     : {s['direct_closes']}\n"
            f"Consultations      : {s['consultations_scheduled']}\n"
            f"Pipeline total     : {s['total_pipeline_value_eur']:,.0f}€\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )


closer_routing_bridge = CloserRoutingBridge()
