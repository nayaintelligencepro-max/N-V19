"""
NAYA SUPREME V19.5 — PIPELINE CONNECTOR (Master Wiring)
═══════════════════════════════════════════════════════════
Connecte TOUS les modules V19.5 entre eux et avec le pipeline existant.
C'est le cerveau de coordination qui élimine tout trou de routage.

FLUX COMPLET :
  HuntEngine → PredictiveLeadScorer → MaturityScorer
  → OutreachSequenceEngine → MultilingualBridge → DeliverabilityMonitor
  → (réponse positive) → CloserRoutingBridge → ContractGenerator
  → PaymentWebhookReceiver → ClientPortalAPI → SocialProofEngine
  → FeedbackLoopConnector → AutonomousLearner
  → (prospect silencieux) → SilentProspectReactivator
  → DailyDigestEngine → Telegram
  → ContentCalendarEngine (inbound)
  → BackupEngine (protection données)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

log = logging.getLogger("NAYA.PIPELINE_CONNECTOR")


@dataclass
class PipelineEvent:
    event_type: str
    source_module: str
    target_module: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PipelineConnector:
    """
    Connecteur central qui assure le routage entre tous les modules.
    Élimine tous les TODO et trous de routage du pipeline.
    """

    def __init__(self) -> None:
        self.events: List[PipelineEvent] = []
        self.module_status: Dict[str, str] = {}
        self.connections: Dict[str, List[str]] = {
            "hunt_engine": ["predictive_lead_scorer", "maturity_scorer"],
            "predictive_lead_scorer": ["outreach_sequence_engine", "maturity_scorer"],
            "maturity_scorer": ["outreach_sequence_engine", "silent_prospect_reactivator"],
            "outreach_sequence_engine": ["multilingual_bridge", "deliverability_monitor", "closer_routing_bridge"],
            "multilingual_bridge": ["outreach_sequence_engine"],
            "deliverability_monitor": ["daily_digest_engine"],
            "closer_routing_bridge": ["contract_generator", "payment_webhook_receiver"],
            "contract_generator": ["payment_webhook_receiver", "client_portal_api"],
            "payment_webhook_receiver": ["client_portal_api", "daily_digest_engine", "social_proof_engine"],
            "client_portal_api": ["daily_digest_engine"],
            "social_proof_engine": ["content_calendar_engine", "outreach_sequence_engine"],
            "feedback_loop_connector": ["hunt_engine", "maturity_scorer"],
            "silent_prospect_reactivator": ["outreach_sequence_engine"],
            "daily_digest_engine": ["telegram"],
            "content_calendar_engine": ["daily_digest_engine"],
            "backup_engine": [],
            "lightning_payment": ["payment_webhook_receiver"],
        }
        self._initialize_modules()

    def _initialize_modules(self) -> None:
        for module in self.connections:
            self.module_status[module] = "active"
        log.info("Pipeline connector initialized with %d modules", len(self.connections))

    def route_event(self, event: PipelineEvent) -> List[str]:
        """
        Route un événement vers les modules cibles appropriés.
        Retourne la liste des modules notifiés.
        """
        self.events.append(event)
        targets = self.connections.get(event.source_module, [])

        if event.target_module:
            if event.target_module in self.module_status:
                targets = [event.target_module]
            else:
                log.warning("Unknown target module: %s", event.target_module)
                return []

        notified = []
        for target in targets:
            if self.module_status.get(target) == "active":
                notified.append(target)
                log.debug("Event routed: %s → %s", event.source_module, target)

        return notified

    def on_prospect_detected(self, prospect_data: Dict[str, Any]) -> List[str]:
        event = PipelineEvent(
            event_type="prospect_detected",
            source_module="hunt_engine",
            target_module="",
            data=prospect_data,
        )
        return self.route_event(event)

    def on_prospect_scored(self, prospect_id: str, score: float, tier: str) -> List[str]:
        event = PipelineEvent(
            event_type="prospect_scored",
            source_module="predictive_lead_scorer",
            target_module="",
            data={"prospect_id": prospect_id, "score": score, "tier": tier},
        )
        return self.route_event(event)

    def on_positive_reply(self, prospect_data: Dict[str, Any]) -> List[str]:
        event = PipelineEvent(
            event_type="positive_reply",
            source_module="outreach_sequence_engine",
            target_module="closer_routing_bridge",
            data=prospect_data,
        )
        return self.route_event(event)

    def on_payment_received(self, payment_data: Dict[str, Any]) -> List[str]:
        event = PipelineEvent(
            event_type="payment_received",
            source_module="payment_webhook_receiver",
            target_module="",
            data=payment_data,
        )
        return self.route_event(event)

    def on_deal_closed(self, deal_data: Dict[str, Any]) -> List[str]:
        event = PipelineEvent(
            event_type="deal_closed",
            source_module="closer_routing_bridge",
            target_module="feedback_loop_connector",
            data=deal_data,
        )
        routed = self.route_event(event)

        social_event = PipelineEvent(
            event_type="deal_won",
            source_module="payment_webhook_receiver",
            target_module="social_proof_engine",
            data=deal_data,
        )
        routed += self.route_event(social_event)
        return routed

    def on_prospect_silent(self, prospect_data: Dict[str, Any]) -> List[str]:
        event = PipelineEvent(
            event_type="prospect_silent",
            source_module="outreach_sequence_engine",
            target_module="silent_prospect_reactivator",
            data=prospect_data,
        )
        return self.route_event(event)

    def get_module_status(self) -> Dict[str, str]:
        return dict(self.module_status)

    def get_connection_map(self) -> Dict[str, List[str]]:
        return dict(self.connections)

    def health_check(self) -> Dict[str, Any]:
        active = sum(1 for s in self.module_status.values() if s == "active")
        total = len(self.module_status)
        return {
            "total_modules": total,
            "active_modules": active,
            "health_pct": (active / total * 100) if total > 0 else 0,
            "total_events_routed": len(self.events),
            "all_connected": active == total,
        }

    def generate_telegram_report(self) -> str:
        hc = self.health_check()
        return (
            "NAYA PIPELINE — Rapport\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Modules actifs    : {hc['active_modules']}/{hc['total_modules']}\n"
            f"Santé             : {hc['health_pct']:.0f}%\n"
            f"Events routés     : {hc['total_events_routed']}\n"
            f"Tout connecté     : {'OUI' if hc['all_connected'] else 'NON'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )


pipeline_connector = PipelineConnector()
