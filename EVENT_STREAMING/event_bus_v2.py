"""
NAYA V21 — Enhanced Event Bus
Chain réactions automatiques : Pain → Enrich → Offer → Outreach → Closing.
Remplace RabbitMQ par un bus async in-process (zéro dépendance externe).
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

log = logging.getLogger("NAYA.EVENT_BUS_V2")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "events"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class EventType(str, Enum):
    # ── Pipeline V21 ───────────────────────────────────────────────────────────
    PAIN_DETECTED = "pain.detected"
    LEAD_ENRICHED = "lead.enriched"
    OFFER_GENERATED = "offer.generated"
    OFFER_SENT = "offer.sent"
    REPLY_RECEIVED = "reply.received"
    OBJECTION_DETECTED = "objection.detected"
    CLOSING_TRIGGERED = "closing.triggered"
    DEAL_SIGNED = "deal.signed"
    PAYMENT_RECEIVED = "payment.received"
    CONTRACT_GENERATED = "contract.generated"
    # ── Système ────────────────────────────────────────────────────────────────
    MEETING_BOOKED = "meeting.booked"
    MEETING_COMPLETED = "meeting.completed"
    SUBSCRIPTION_CREATED = "subscription.created"
    PAYMENT_FAILED = "payment.failed"
    AGENT_ERROR = "agent.error"
    HEALTH_CHECK = "health.check"
    SCORE_THRESHOLD = "score.threshold"


@dataclass
class Event:
    """Événement NAYA V21."""
    event_type: EventType
    source: str
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d


HandlerFunc = Callable[[Event], Coroutine[Any, Any, None]]


class EventBusV2:
    """
    Bus d'événements async V21 — connecte les 11 agents via chain réactions.
    Pain détecté → event → Researcher enrichit → event → Offer Writer génère
    → event → Outreach envoie → event → Closer gère réponse → event → Contrat.
    """

    def __init__(self, persist_events: bool = True, max_history: int = 1000):
        self._handlers: Dict[EventType, List[HandlerFunc]] = {}
        self._event_history: List[Event] = []
        self._persist = persist_events
        self._max_history = max_history
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        log.info("✅ EventBusV2 initialisé")

    # ── Subscription ──────────────────────────────────────────────────────────
    def subscribe(self, event_type: EventType, handler: HandlerFunc) -> None:
        """Abonne un handler à un type d'événement."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        log.debug("Handler abonné à %s: %s", event_type, handler.__name__)

    def subscribe_multi(self, event_types: List[EventType], handler: HandlerFunc) -> None:
        """Abonne un handler à plusieurs types d'événements."""
        for et in event_types:
            self.subscribe(et, handler)

    # ── Publishing ────────────────────────────────────────────────────────────
    async def publish(self, event: Event) -> None:
        """Publie un événement — déclenche tous les handlers abonnés."""
        self._add_to_history(event)
        if self._persist:
            self._save_event(event)
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            log.debug("No handlers for %s", event.event_type)
            return
        tasks = [asyncio.create_task(self._safe_handle(h, event)) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    def publish_sync(self, event: Event) -> None:
        """Publie un événement en mode synchrone (non-async context)."""
        self._add_to_history(event)
        if self._persist:
            self._save_event(event)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.publish(event))
            else:
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # Nouveau loop si besoin
            asyncio.run(self.publish(event))

    async def emit(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Crée et publie un événement en une ligne."""
        event = Event(
            event_type=event_type,
            source=source,
            data=data,
            correlation_id=correlation_id,
        )
        await self.publish(event)
        return event

    # ── Pipeline chains ───────────────────────────────────────────────────────
    def register_pipeline_chain(self) -> None:
        """
        Enregistre la chaîne pipeline V21 complète.
        Pain → Enrich → Offer → Outreach → Close → Contract.
        """
        self.subscribe(EventType.PAIN_DETECTED, self._on_pain_detected)
        self.subscribe(EventType.LEAD_ENRICHED, self._on_lead_enriched)
        self.subscribe(EventType.OFFER_GENERATED, self._on_offer_generated)
        self.subscribe(EventType.REPLY_RECEIVED, self._on_reply_received)
        self.subscribe(EventType.DEAL_SIGNED, self._on_deal_signed)
        self.subscribe(EventType.SCORE_THRESHOLD, self._on_score_threshold)
        log.info("✅ Pipeline chain V21 enregistrée (5 nœuds)")

    async def _on_pain_detected(self, event: Event) -> None:
        """Pain détecté → déclencher enrichissement."""
        pain = event.data
        score = pain.get("score", 0)
        log.info("Pain détecté: %s score=%d → enrichissement", pain.get("company", "?"), score)
        if score >= 70:
            await self.emit(
                EventType.SCORE_THRESHOLD,
                source="pain_chain",
                data={**pain, "threshold": 70, "action": "generate_offer"},
                correlation_id=event.event_id,
            )

    async def _on_lead_enriched(self, event: Event) -> None:
        """Lead enrichi → générer offre si score ≥ 70."""
        lead = event.data
        score = lead.get("score", 0)
        log.info("Lead enrichi: %s score=%d", lead.get("company", "?"), score)
        if score >= 70:
            await self.emit(
                EventType.SCORE_THRESHOLD,
                source="enrichment_chain",
                data={**lead, "threshold": 70, "action": "generate_offer"},
                correlation_id=event.event_id,
            )

    async def _on_offer_generated(self, event: Event) -> None:
        """Offre générée → envoyer outreach."""
        offer = event.data
        log.info(
            "Offre générée: %s %d EUR → outreach",
            offer.get("company", "?"), offer.get("price_eur", 0),
        )
        # L'outreach sera déclenché par le scheduler ou l'orchestrateur

    async def _on_reply_received(self, event: Event) -> None:
        """Réponse prospect reçue → trigger closing immédiat."""
        reply = event.data
        log.info(
            "Réponse reçue de %s → closing immédiat",
            reply.get("company", "?"),
        )
        # Signal achat détecté → escalader
        sentiment = reply.get("sentiment", "neutral")
        if sentiment in ("positive", "buying_signal"):
            await self.emit(
                EventType.CLOSING_TRIGGERED,
                source="reply_chain",
                data={**reply, "priority": "immediate"},
                correlation_id=event.event_id,
            )

    async def _on_deal_signed(self, event: Event) -> None:
        """Deal signé → générer contrat + notifier."""
        deal = event.data
        log.info(
            "DEAL SIGNÉ 🎉 %s — %d EUR",
            deal.get("company", "?"), deal.get("amount_eur", 0),
        )
        # Notifier Telegram
        try:
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
            bot = get_telegram_bot_v2()
            bot.send_sale_notification(
                company=deal.get("company", "?"),
                amount_eur=deal.get("amount_eur", 0),
                sector=deal.get("sector", "OT"),
            )
        except Exception as exc:
            log.warning("Telegram notification error: %s", exc)
        # Déclencher génération contrat
        await self.emit(
            EventType.CONTRACT_GENERATED,
            source="deal_chain",
            data=deal,
            correlation_id=event.event_id,
        )

    async def _on_score_threshold(self, event: Event) -> None:
        """Score ≥ 70 → générer offre FlashOffer en background."""
        data = event.data
        action = data.get("action", "generate_offer")
        if action == "generate_offer":
            log.info(
                "Score threshold: %s → FlashOffer en background",
                data.get("company", "?"),
            )
            try:
                from NAYA_ACCELERATION.flash_offer import get_flash_offer
                flash = get_flash_offer()
                offer = flash.generate(
                    company=data.get("company", "Unknown"),
                    sector=data.get("sector", "iec62443"),
                    pain_description=data.get("pain", "Conformité NIS2 requise"),
                    contact_name=data.get("contact_name", ""),
                    contact_title=data.get("contact_title", "RSSI"),
                    budget_estimate_eur=data.get("budget_estimate", 15_000),
                )
                await self.emit(
                    EventType.OFFER_GENERATED,
                    source="score_chain",
                    data={"offer_id": offer.offer_id, "company": data.get("company"), "price_eur": offer.price_eur},
                    correlation_id=event.event_id,
                )
            except Exception as exc:
                log.warning("FlashOffer error dans chain: %s", exc)

    # ── History & Persistence ─────────────────────────────────────────────────
    def _add_to_history(self, event: Event) -> None:
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def _save_event(self, event: Event) -> None:
        try:
            events_file = DATA_DIR / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with events_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            log.debug("Event persist error: %s", exc)

    async def _safe_handle(self, handler: HandlerFunc, event: Event) -> None:
        try:
            await handler(event)
        except Exception as exc:
            log.error("Handler %s error on %s: %s", handler.__name__, event.event_type, exc)

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50) -> List[Dict]:
        history = self._event_history
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        return [e.to_dict() for e in history[-limit:]]

    def get_stats(self) -> Dict:
        by_type: Dict[str, int] = {}
        for e in self._event_history:
            key = e.event_type.value
            by_type[key] = by_type.get(key, 0) + 1
        return {
            "total_events": len(self._event_history),
            "handlers_registered": sum(len(h) for h in self._handlers.values()),
            "event_types_with_handlers": len(self._handlers),
            "by_type": by_type,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_bus: Optional[EventBusV2] = None


def get_event_bus_v2() -> EventBusV2:
    global _bus
    if _bus is None:
        _bus = EventBusV2()
        _bus.register_pipeline_chain()
    return _bus
