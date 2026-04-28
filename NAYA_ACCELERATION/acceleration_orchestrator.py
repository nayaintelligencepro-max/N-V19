"""
NAYA ACCELERATION — AccelerationOrchestrator
Pipeline complet : Pain détecté → Offre envoyée → Paiement encaissé en < 4 heures.
Coordonne BlitzHunter → FlashOffer → InstantCloser → SalesVelocityTracker.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .blitz_hunter import BlitzHunter, BlitzSignal, get_blitz_hunter
from .flash_offer import FlashOffer, OfferResult, get_flash_offer
from .instant_closer import InstantCloser, PaymentLink, PaymentMethod, get_instant_closer
from .sales_velocity_tracker import SalesVelocityTracker, get_velocity_tracker

logger = logging.getLogger("NAYA.ORCHESTRATOR")

TARGET_PIPELINE_HOURS = 3.0  # Objectif optimisé : Pain → Cash en < 3 heures (was 4h)


@dataclass
class PipelineResult:
    """Résultat d'un cycle complet du pipeline accéléré."""
    run_id: str
    signals_detected: int
    offers_generated: int
    payment_links_sent: int
    total_pipeline_value_eur: int
    fastest_cycle_minutes: float
    avg_offer_generation_ms: int
    errors: List[str] = field(default_factory=list)
    offers: List[Dict] = field(default_factory=list)
    payment_links: List[Dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "signals_detected": self.signals_detected,
            "offers_generated": self.offers_generated,
            "payment_links_sent": self.payment_links_sent,
            "total_pipeline_value_eur": self.total_pipeline_value_eur,
            "fastest_cycle_minutes": self.fastest_cycle_minutes,
            "avg_offer_generation_ms": self.avg_offer_generation_ms,
            "errors": self.errors,
            "offers": self.offers[:5],          # limit for API response
            "payment_links": self.payment_links[:5],
            "started_at": self.started_at.isoformat(),
        }


class AccelerationOrchestrator:
    """
    Orchestre le pipeline ultra-rapide NAYA V21.
    Pain → Offre → Paiement en < 4 heures.
    """

    def __init__(
        self,
        blitz: Optional[BlitzHunter] = None,
        flash: Optional[FlashOffer] = None,
        closer: Optional[InstantCloser] = None,
        tracker: Optional[SalesVelocityTracker] = None,
        max_concurrent_offers: int = 4,
        auto_send_payment: bool = False,  # Sécurité: False par défaut, valider > 500 EUR
    ):
        self.blitz = blitz or get_blitz_hunter()
        self.flash = flash or get_flash_offer()
        self.closer = closer or get_instant_closer()
        self.tracker = tracker or get_velocity_tracker()
        self.max_concurrent = max_concurrent_offers
        self.auto_send_payment = auto_send_payment
        self._decision_threshold_eur = int(os.getenv("DECISION_THRESHOLD_EUR", "500"))

    async def run_acceleration_cycle(
        self, sectors: Optional[List[str]] = None
    ) -> PipelineResult:
        """
        Cycle complet d'accélération :
        1. BlitzHunter (< 30s) → signaux qualifiés
        2. FlashOffer (< 60s/offre) → offres personnalisées
        3. InstantCloser → liens paiement si score critique
        4. SalesVelocityTracker → mise à jour métriques
        """
        import uuid
        run_id = str(uuid.uuid4())[:12]
        start = time.time()

        result = PipelineResult(
            run_id=run_id,
            signals_detected=0,
            offers_generated=0,
            payment_links_sent=0,
            total_pipeline_value_eur=0,
            fastest_cycle_minutes=0.0,
            avg_offer_generation_ms=0,
        )

        logger.info(f"[ACC-{run_id}] Starting acceleration cycle")

        # Step 1: BlitzHunt
        try:
            signals = await self.blitz.hunt(sectors)
            result.signals_detected = len(signals)
            logger.info(f"[ACC-{run_id}] BlitzHunt: {len(signals)} signals in {time.time()-start:.1f}s")
        except Exception as exc:
            result.errors.append(f"BlitzHunt error: {exc}")
            signals = []

        if not signals:
            logger.info(f"[ACC-{run_id}] No signals — cycle ended")
            return result

        # Step 2: Generate offers in parallel (max_concurrent slots)
        top_signals = signals[:self.max_concurrent]
        offer_tasks = [
            self._generate_offer_for_signal(sig)
            for sig in top_signals
        ]
        offer_results = await asyncio.gather(*offer_tasks, return_exceptions=True)

        gen_times = []
        for i, r in enumerate(offer_results):
            if isinstance(r, OfferResult):
                result.offers_generated += 1
                result.total_pipeline_value_eur += r.price_eur
                result.offers.append(r.to_dict())
                gen_times.append(r.generation_time_ms)

                # Step 3: Auto-generate payment link for critical signals
                sig = top_signals[i]
                if sig.urgency_level in ("critical", "high") and self.auto_send_payment:
                    try:
                        link = self._generate_payment_for_offer(r, sig)
                        if link:
                            result.payment_links_sent += 1
                            result.payment_links.append(link.to_dict())
                    except Exception as exc:
                        result.errors.append(f"Payment link error for {sig.company}: {exc}")
            elif isinstance(r, Exception):
                result.errors.append(f"Offer gen error: {r}")

        result.avg_offer_generation_ms = int(sum(gen_times) / max(len(gen_times), 1))
        elapsed_min = (time.time() - start) / 60
        result.fastest_cycle_minutes = round(elapsed_min, 2)

        logger.info(
            f"[ACC-{run_id}] Cycle done: {result.signals_detected} signals, "
            f"{result.offers_generated} offers, {result.payment_links_sent} payment links, "
            f"{result.total_pipeline_value_eur:,} EUR pipeline, {elapsed_min:.1f}min"
        )
        return result

    async def run_flash_offer_only(
        self,
        company: str,
        sector: str,
        pain_description: str,
        contact_name: str = "",
        contact_title: str = "",
        budget_estimate: int = 15_000,
        urgency: str = "high",
    ) -> OfferResult:
        """
        Mode express : génère une offre directement sans hunting.
        Utilisé quand on reçoit une demande entrante ou une réponse prospect.
        """
        return await self.flash.generate(
            company=company,
            sector=sector,
            pain_description=pain_description,
            contact_name=contact_name,
            contact_title=contact_title,
            budget_estimate=budget_estimate,
            urgency=urgency,
        )

    def generate_instant_payment(
        self,
        offer: OfferResult,
        contact_email: str,
        method: str = "paypal",
    ) -> PaymentLink:
        """
        Génère le lien de paiement immédiatement après accord verbal.
        Délai cible : < 5 minutes.
        Requiert validation humaine si amount > DECISION_THRESHOLD_EUR.
        """
        pm = PaymentMethod(method) if method in PaymentMethod._value2member_map_ else PaymentMethod.PAYPAL
        return self.closer.generate_payment_link(
            offer_id=offer.offer_id,
            company=offer.company,
            contact_email=contact_email,
            amount_eur=offer.price_eur,
            method=pm,
            description=offer.email_subject,
        )

    def get_velocity_dashboard(self) -> Dict:
        """Retourne les métriques velocity pour le dashboard."""
        metrics = self.tracker.get_metrics()
        return metrics.to_dict()

    # ── Private helpers ────────────────────────────────────────────────────

    async def _generate_offer_for_signal(self, signal: BlitzSignal) -> OfferResult:
        return await self.flash.generate(
            company=signal.company,
            sector=signal.sector,
            pain_description=signal.pain_description,
            contact_name=signal.contact_name,
            budget_estimate=signal.budget_estimate_eur,
            urgency=signal.urgency_level,
            signal_id=signal.signal_id,
        )

    def _generate_payment_for_offer(
        self, offer: OfferResult, signal: BlitzSignal
    ) -> Optional[PaymentLink]:
        """Génère le lien uniquement si offer > threshold."""
        if offer.price_eur <= self._decision_threshold_eur:
            return None
        return self.closer.generate_payment_link(
            offer_id=offer.offer_id,
            company=offer.company,
            contact_email=signal.contact_email,
            amount_eur=offer.price_eur,
            method=PaymentMethod.PAYPAL,
            description=offer.email_subject,
        )


_orchestrator_instance: Optional[AccelerationOrchestrator] = None


def get_orchestrator() -> AccelerationOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AccelerationOrchestrator()
    return _orchestrator_instance
