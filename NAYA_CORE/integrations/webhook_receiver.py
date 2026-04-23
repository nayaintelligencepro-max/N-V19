"""
NAYA — Webhook Receiver
Point central de réception de tous les webhooks externes.
PayPal + Deblock (paiements), Telegram (messages entrants), LinkedIn (réponses).
Chaque webhook = action automatique dans le pipeline.

V19.3 : Stripe retiré (non disponible en Polynésie française).
"""
import os
import json
import logging
import time
from typing import Dict, Callable, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.WEBHOOKS")


@dataclass
class WebhookEvent:
    source: str = ""        # paypal / deblock / telegram / linkedin / sendgrid
    event_type: str = ""
    payload: Dict = field(default_factory=dict)
    received_at: float = field(default_factory=time.time)
    processed: bool = False
    result: Optional[Dict] = None


class WebhookReceiver:
    """
    Routeur central de webhooks NAYA.
    Chaque source a ses handlers enregistrés.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._events: List[WebhookEvent] = []
        self._processed_count = 0
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Enregistre les handlers par défaut."""
        # V19.3 : PayPal + Deblock au lieu de Stripe
        self.on("paypal.payment.completed", self._on_payment_received)
        self.on("deblock.payment.confirmed", self._on_payment_received)
        self.on("telegram.message", self._on_telegram_message)
        self.on("sendgrid.delivered", self._on_email_delivered)
        self.on("sendgrid.opened", self._on_email_opened)
        self.on("sendgrid.clicked", self._on_email_clicked)

    def on(self, event_key: str, handler: Callable):
        """Enregistre un handler pour un type d'événement."""
        if event_key not in self._handlers:
            self._handlers[event_key] = []
        self._handlers[event_key].append(handler)

    def process(self, source: str, event_type: str, payload: Dict) -> Dict:
        """Traite un webhook entrant."""
        event = WebhookEvent(source=source, event_type=event_type, payload=payload)
        self._events.append(event)

        key = f"{source}.{event_type}"
        handlers = self._handlers.get(key, []) + self._handlers.get(f"{source}.*", [])

        results = []
        for handler in handlers:
            try:
                result = handler(payload)
                results.append(result or {})
            except Exception as e:
                log.warning(f"[WEBHOOK] Handler {key} error: {e}")

        event.processed = True
        event.result = {"handlers_called": len(handlers), "results": results}
        self._processed_count += 1

        if not handlers:
            log.debug(f"[WEBHOOK] No handler for {key}")

        return event.result

    def _on_payment_received(self, payload: Dict) -> Dict:
        """Paiement PayPal/Deblock reçu → marquer deal WON + notifier."""
        # Format unifié : payload doit contenir amount_eur et payer_email
        amount = float(payload.get("amount_eur") or payload.get("amount", 0))
        if "amount" in payload and "amount_eur" not in payload:
            # Compat: certains webhooks renvoient en centimes
            if amount > 100000:  # heuristique
                amount = amount / 100.0
        email = payload.get("payer_email") or payload.get("receipt_email", "")
        provider = payload.get("provider", "paypal")
        tx_id = payload.get("transaction_id") or payload.get("id", "?")

        log.info(f"[WEBHOOK] 💰 Paiement {provider}: {amount:,.0f}€ — {email}")

        # Notifier via Telegram
        try:
            from NAYA_CORE.money_notifier import get_money_notifier
            mn = get_money_notifier()
            mn._send(
                f"✅ <b>PAIEMENT CONFIRMÉ</b>\n\n"
                f"💰 Montant: <b>{amount:,.0f}€</b>\n"
                f"💳 Provider: {provider.upper()}\n"
                f"📧 Client: {email}\n"
                f"🆔 TX: {tx_id}\n\n"
                f"<b>ACTION:</b> Marquer le deal WON dans le pipeline"
            )
        except Exception as e:
            log.warning(f"[WEBHOOK] Notif error: {e}")

        # Mettre à jour le pipeline si prospect correspondant trouvé
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            engine = get_cash_engine()
            for deal_id, deal in engine._deals.items():
                if hasattr(deal, "contact_email") and deal.contact_email == email:
                    engine.mark_won(deal_id, amount)
                    get_revenue_intelligence().record_win(
                        deal.sector, deal.pain_category, amount
                    )
                    break
        except Exception as e:
            log.debug(f"[WEBHOOK] Pipeline update: {e}")

        # Tracker dans revenue_tracker_agent
        try:
            import asyncio
            from NAYA_CORE.agents.revenue_tracker_agent import revenue_tracker_agent, RevenueStream
            loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else None
            if loop:
                asyncio.create_task(revenue_tracker_agent.track_revenue(
                    stream=RevenueStream.CONSULTING_OT,
                    amount_eur=amount,
                    client_company=email.split('@')[-1] if email else "unknown",
                    description=f"Payment {provider} TX {tx_id}",
                ))
        except Exception as e:
            log.debug(f"[WEBHOOK] Revenue track: {e}")

        return {"amount_eur": amount, "email": email, "provider": provider, "action": "deal_won"}

    def _on_telegram_message(self, payload: Dict) -> Dict:
        """Message Telegram reçu → analyser si réponse à une offre."""
        message = payload.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id", "")
        from_name = message.get("from", {}).get("first_name", "")

        log.info(f"[WEBHOOK] Telegram message de {from_name}: {text[:80]}")

        # Détecter les réponses positives
        positive_signals = ["oui", "yes", "intéressé", "interested", "ok", "d'accord",
                           "go", "allons-y", "contactez", "rappel", "rdv", "rendez-vous"]
        is_positive = any(s in text.lower() for s in positive_signals)

        if is_positive:
            log.info(f"[WEBHOOK] 🎯 Réponse positive détectée de {from_name}!")
            try:
                from NAYA_EVENT_STREAM.ws_server import get_event_stream_server
                get_event_stream_server().publish(
                    "INBOUND", "telegram_webhook", "POSITIVE_RESPONSE",
                    "SUCCESS", {"from": from_name, "text": text[:200]}, ["lead", "revenue"]
                )
            except Exception:
                pass

        return {"from": from_name, "is_positive": is_positive, "text": text[:200]}

    def _on_email_delivered(self, payload: Dict) -> Dict:
        """Email SendGrid livré → mettre à jour statut prospect."""
        email = payload.get("email", "")
        log.debug(f"[WEBHOOK] Email delivered: {email}")
        return {"delivered": True, "email": email}

    def _on_email_opened(self, payload: Dict) -> Dict:
        """Email ouvert → prospect chaud → priorité haute."""
        email = payload.get("email", "")
        subject = payload.get("subject", "")
        log.info(f"[WEBHOOK] 📬 Email ouvert: {email} — {subject[:50]}")

        # Remonter la priorité du prospect
        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            tracker = PipelineTracker()
            tracker.mark_email_opened(email)
        except Exception:
            pass

        return {"opened": True, "email": email, "action": "priority_upgraded"}

    def _on_email_clicked(self, payload: Dict) -> Dict:
        """Lien cliqué dans email → très chaud → alert immédiate."""
        email = payload.get("email", "")
        url = payload.get("url", "")
        log.info(f"[WEBHOOK] 🔥 Lien cliqué: {email} — {url[:80]}")

        try:
            from NAYA_CORE.money_notifier import get_money_notifier
            get_money_notifier()._send(
                f"🔥 <b>LIEN CLIQUÉ — PROSPECT CHAUD</b>\n\n"
                f"📧 Email: {email}\n"
                f"🔗 URL: {url[:80]}\n\n"
                f"<b>ACTION IMMÉDIATE:</b> Contacter dans les 2H !"
            )
        except Exception:
            pass

        return {"clicked": True, "email": email, "url": url, "action": "immediate_followup"}

    def get_stats(self) -> Dict:
        return {
            "total_events": len(self._events),
            "processed": self._processed_count,
            "handlers_registered": len(self._handlers),
            "recent_events": [
                {"source": e.source, "type": e.event_type,
                 "processed": e.processed, "age_s": int(time.time() - e.received_at)}
                for e in self._events[-10:]
            ],
        }


_receiver: Optional[WebhookReceiver] = None

def get_webhook_receiver() -> WebhookReceiver:
    global _receiver
    if _receiver is None:
        _receiver = WebhookReceiver()
    return _receiver
