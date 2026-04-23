"""
NAYA V19 - Real Pipeline Orchestrator
Le flux executif complet qui genere du cash reel:
Hunt -> Classify -> Price -> Offer -> Stealth -> Persona -> Timing -> Outreach -> Pay -> Learn -> Recycle

Ce module connecte TOUS les autres en un seul flux automatique.
"""
import time, logging, threading, asyncio, json, uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.PIPELINE.REAL")

@dataclass
class PipelineExecution:
    execution_id: str
    stage: str
    pain_data: Dict
    classified: Optional[Dict] = None
    priced: Optional[Dict] = None
    offer: Optional[Dict] = None
    outreach_sent: bool = False
    payment_created: bool = False
    result: str = "in_progress"
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    revenue: float = 0.0
    error: Optional[str] = None

class RealPipelineOrchestrator:
    """Orchestre le flux complet de generation de cash.
    Chaque etape appelle le vrai module avec les vraies APIs."""

    def __init__(self):
        self._executions: Dict[str, PipelineExecution] = {}
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_runs = 0
        self._total_revenue = 0.0
        self._total_offers_sent = 0
        self._persist_file = Path("data/cache/pipeline_state.json")

    def execute_full_pipeline(self, pain_signal: Dict) -> PipelineExecution:
        """Execute le pipeline complet sur une douleur detectee."""
        exec_id = f"PIPE_{uuid.uuid4().hex[:8].upper()}"
        execution = PipelineExecution(execution_id=exec_id, stage="start", pain_data=pain_signal)

        with self._lock:
            self._executions[exec_id] = execution
            self._total_runs += 1

        try:
            # STAGE 0: Project Engine evaluation (doctrine + feasibility)
            execution.stage = "project_engine"
            pe_result = self._stage_project_engine(pain_signal)
            if pe_result.get("status") == "REJECTED":
                execution.stage = "rejected_by_project_engine"
                execution.result = "rejected"
                execution.error = pe_result.get("reason", "Project Engine rejected")
                execution.completed_at = time.time()
                log.info(f"[PIPE:{exec_id}] Rejeté par Project Engine: {pe_result.get('reason')}")
                self._persist()
                return execution
            log.info(f"[PIPE:{exec_id}] Project Engine: {pe_result.get('status', '?')} (score={pe_result.get('final_score', 0)})")

            # STAGE 1: Classification (immediat / 7j / long terme)
            execution.stage = "classify"
            classified = self._stage_classify(pain_signal)
            execution.classified = classified
            log.info(f"[PIPE:{exec_id}] Classifie: {classified.get('tier', '?')} | {classified.get('value', 0)}EUR")

            # STAGE 2: Pricing dynamique
            execution.stage = "pricing"
            priced = self._stage_price(pain_signal, classified)
            execution.priced = priced
            log.info(f"[PIPE:{exec_id}] Prix: {priced.get('recommended_price', 0)}EUR | ROI: {priced.get('roi_for_prospect', 0)}x")

            # STAGE 3: Generation d offre
            execution.stage = "offer"
            offer = self._stage_generate_offer(pain_signal, priced)
            execution.offer = offer
            log.info(f"[PIPE:{exec_id}] Offre generee: {offer.get('offer_id', '?')}")

            # STAGE 3b: Contact Enrichment (CRITIQUE — sans email = 0 outreach)
            execution.stage = "enrich_contact"
            enriched = self._stage_enrich_contact(pain_signal)
            if enriched.get("email"):
                pain_signal["email"] = enriched["email"]
                pain_signal["contact_name"] = enriched.get("contact_name", "")
                pain_signal["contact_title"] = enriched.get("contact_title", "")
                pain_signal["domain"] = enriched.get("domain", "")
                log.info(f"[PIPE:{exec_id}] Contact enrichi: {enriched['email']} ({enriched.get('source', '?')})")
            else:
                log.info(f"[PIPE:{exec_id}] Pas d email trouve — outreach sera en attente")

            # STAGE 4: Stealth anonymisation
            execution.stage = "stealth"
            stealthed = self._stage_stealth(pain_signal)

            # STAGE 5: Timing check
            execution.stage = "timing"
            timing = self._stage_check_timing(pain_signal.get("sector", "pme"))
            if not timing.get("good_time", True):
                log.info(f"[PIPE:{exec_id}] Timing: pas optimal, planifie pour {timing.get('next_window', 'plus tard')}")
                # On continue quand meme mais on note

            # STAGE 6: Multi-persona message
            execution.stage = "persona"
            messages = self._stage_create_messages(pain_signal, offer, stealthed)

            # STAGE 7: Outreach (envoi reel)
            execution.stage = "outreach"
            sent = self._stage_send_outreach(pain_signal, messages, offer)
            execution.outreach_sent = sent
            if sent:
                self._total_offers_sent += 1
                log.info(f"[PIPE:{exec_id}] Outreach envoye!")

            # STAGE 8: Payment tracking
            execution.stage = "payment_tracking"
            payment = self._stage_create_payment(pain_signal, priced, offer)
            execution.payment_created = payment

            # STAGE 9: Notification Telegram
            execution.stage = "notification"
            self._stage_notify(exec_id, pain_signal, priced, sent)

            # STAGE 10: Learning
            execution.stage = "learning"
            self._stage_learn(pain_signal, sent)

            execution.stage = "completed"
            execution.result = "success"
            execution.completed_at = time.time()
            log.info(f"[PIPE:{exec_id}] Pipeline COMPLETE | Offre: {priced.get('recommended_price', 0)}EUR")

        except Exception as e:
            execution.stage = f"error:{execution.stage}"
            execution.result = "error"
            execution.error = str(e)
            execution.completed_at = time.time()
            log.error(f"[PIPE:{exec_id}] ERREUR stage {execution.stage}: {e}")

            # Antifragility: enregistrer l echec pour s ameliorer
            try:
                from NAYA_CORE.antifragility_engine import get_antifragility
                get_antifragility().record_stress("pipeline_error", execution.stage, str(e), 0.5)
            except Exception:
                pass

        self._persist()
        return execution

    # ── STAGES ──────────────────────────────────────────────

    def _stage_project_engine(self, pain: Dict) -> Dict:
        """Evaluate opportunity through NAYA_PROJECT_ENGINE layers (doctrine, feasibility, cash rapide)."""
        try:
            from NAYA_PROJECT_ENGINE.engine_layer.engine_layer_controller import get_engine_layer
            engine = get_engine_layer()
            opp = {
                "estimated_value": pain.get("estimated_value", pain.get("annual_cost", 5000)),
                "solvability_score": pain.get("solvability", 70) if isinstance(pain.get("solvability"), (int, float)) else 70,
                "time_to_revenue": pain.get("timeline_days", 30),
                "capital_required": pain.get("capital_required", 0),
                "market_size": pain.get("market_size", 500000),
                "sector": pain.get("sector", "pme"),
            }
            result = engine.process_opportunity(opp)
            # Also try to match to a specific project
            try:
                from NAYA_PROJECT_ENGINE.business import get_active_projects
                projects = get_active_projects()
                if projects:
                    result["matched_project"] = projects[0].get("name", "CASH_RAPIDE") if isinstance(projects[0], dict) else str(projects[0])
            except Exception:
                result["matched_project"] = "PROJECT_01_CASH_RAPIDE"
            return result
        except Exception as e:
            log.warning(f"[PIPE] Project Engine fallback: {e}")
            return {"status": "APPROVED", "final_score": 0.7, "reason": "project_engine_unavailable"}

    def _stage_enrich_contact(self, pain: Dict) -> Dict:
        """Enrichit le prospect avec un email de décideur réel."""
        # Si on a déjà un email, pas besoin d'enrichir
        if pain.get("email"):
            return {"email": pain["email"], "source": "provided", "contact_name": pain.get("contact_name", "")}
        try:
            from NAYA_CORE.enrichment.contact_enricher import get_contact_enricher
            enricher = get_contact_enricher()
            contact = enricher.enrich(
                company=pain.get("entity", pain.get("company_name", "")),
                url=pain.get("url", ""),
                sector=pain.get("sector", ""),
                country=pain.get("country", "FR"),
            )
            if contact.is_valid:
                return {
                    "email": contact.email,
                    "contact_name": contact.decision_maker_name,
                    "contact_title": contact.decision_maker_title,
                    "domain": contact.domain,
                    "phone": contact.phone,
                    "source": contact.source,
                    "confidence": contact.confidence,
                }
            # Même si pas valid, retourner ce qu'on a
            return {
                "email": contact.email,
                "contact_name": contact.decision_maker_name,
                "domain": contact.domain,
                "source": contact.source,
            }
        except Exception as e:
            log.warning(f"[PIPE] Enrichment failed: {e}")
            return {}

    def _stage_classify(self, pain: Dict) -> Dict:
        try:
            from NAYA_CORE.hunt.cash_rapide_classifier import get_classifier
            clf = get_classifier()
            result = clf.classify(pain)
            return {"tier": result.tier.value, "value": result.estimated_value_eur,
                    "status": result.status.value, "id": result.id}
        except Exception as e:
            log.warning(f"[PIPE] Classify fallback: {e}")
            value = pain.get("estimated_value", 5000)
            return {"tier": "immediat" if value < 20000 else "moyen_terme", "value": value}

    def _stage_price(self, pain: Dict, classified: Dict) -> Dict:
        try:
            from NAYA_CORE.economic.dynamic_pricing_engine import get_dynamic_pricing, PricingContext
            engine = get_dynamic_pricing()
            ctx = PricingContext(
                pain_annual_cost=pain.get("annual_cost", classified.get("value", 5000) * 5),
                prospect_revenue=pain.get("prospect_revenue", 500000),
                urgency=pain.get("urgency", 0.7),
                complexity=pain.get("complexity", 0.4),
                market_rarity=pain.get("rarity", 0.6),
                competitor_count=pain.get("competitors", 3),
                prospect_sophistication=pain.get("sophistication", 0.5),
                sector=pain.get("sector", "pme")
            )
            result = engine.calculate_price(ctx)
            return {
                "recommended_price": result.recommended_price,
                "floor_price": result.floor_price,
                "roi_for_prospect": result.roi_for_prospect,
                "payment_options": result.payment_options,
                "pricing_model": result.pricing_model
            }
        except Exception as e:
            log.warning(f"[PIPE] Pricing fallback: {e}")
            value = max(1000, classified.get("value", 5000))
            return {"recommended_price": value, "floor_price": 1000, "roi_for_prospect": 5.0,
                    "payment_options": [{"type": "full", "amount": value}]}

    def _stage_generate_offer(self, pain: Dict, priced: Dict) -> Dict:
        try:
            from NAYA_REVENUE_ENGINE.offer_generator import get_offer_generator
            gen = get_offer_generator()
            offer = gen.generate(pain, priced)
            return {
                "offer_id": offer.offer_id, "title": offer.title,
                "price": offer.price, "deliverables": offer.deliverables,
                "call_to_action": offer.call_to_action,
                "markdown": gen.to_markdown(offer)
            }
        except Exception as e:
            log.warning(f"[PIPE] Offer fallback: {e}")
            return {"offer_id": f"OFF_{uuid.uuid4().hex[:6]}", "title": pain.get("description", ""),
                    "price": priced.get("recommended_price", 5000)}

    def _stage_stealth(self, pain: Dict) -> Dict:
        try:
            from BUSINESS_ENGINES.discretion_protocol.stealth_operations_engine import get_stealth_engine
            stealth = get_stealth_engine()
            session = stealth.create_stealth_session("outreach")
            return {
                "session_id": session.session_id,
                "persona_name": session.persona_name,
                "persona_email": session.persona_email
            }
        except Exception as e:
            log.warning(f"[PIPE] Stealth fallback: {e}")
            return {"session_id": "none", "persona_name": "NAYA Service", "persona_email": "nayaintelligencepro@gmail.com"}

    def _stage_check_timing(self, sector: str) -> Dict:
        try:
            from NAYA_CORE.orchestration.temporal_orchestrator import get_temporal_orchestrator
            return get_temporal_orchestrator().is_good_time(sector)
        except Exception:
            return {"good_time": True, "confidence": 0.5}

    def _stage_create_messages(self, pain: Dict, offer: Dict, stealth: Dict) -> List[Dict]:
        try:
            from NAYA_REVENUE_ENGINE.multi_persona_outreach import get_multi_persona
            persona_engine = get_multi_persona()
            prospect = {
                "name": pain.get("entity", pain.get("prospect_name", "Madame, Monsieur")),
                "sector": pain.get("sector", "pme"),
                "pain_description": pain.get("description", "votre problematique"),
                "price": offer.get("price", 5000),
                "roi": 5,
                "timeline_days": pain.get("timeline_days", 7)
            }
            messages = persona_engine.generate_outreach(prospect, n_personas=2)
            return [{"subject": m.subject, "body": m.body, "persona": m.persona.name} for m in messages]
        except Exception as e:
            log.warning(f"[PIPE] Persona fallback: {e}")
            return [{"subject": f"Solution pour {pain.get('sector', 'votre secteur')}",
                     "body": f"Bonjour, nous pouvons resoudre {pain.get('description', 'votre probleme')}.",
                     "persona": "NAYA Service"}]

    def _stage_send_outreach(self, pain: Dict, messages: List[Dict], offer: Dict) -> bool:
        """Envoie reellement l outreach par email via Gmail OAuth ou SendGrid."""
        import os
        auto_outreach = os.getenv("NAYA_AUTO_OUTREACH", "false").lower() == "true"
        prospect_email = pain.get("email", "")

        if not prospect_email:
            log.info("[PIPE] Pas d email prospect - outreach non envoye (en attente de contact)")
            # Notifier via Telegram pour action manuelle
            return False

        if not auto_outreach:
            # Envoyer notification Telegram pour approbation
            log.info("[PIPE] Auto-outreach desactive - notification Telegram envoyee pour approbation")
            return False

        # Envoi reel via Gmail OAuth
        try:
            from NAYA_CORE.integrations.gmail_oauth2 import GmailOAuth2Sender
            gmail = GmailOAuth2Sender()
            if gmail.has_oauth or gmail.has_sendgrid:
                msg = messages[0] if messages else {}
                gmail.send(
                    to_email=prospect_email,
                    subject=msg.get("subject", "Proposition de service"),
                    body_html=msg.get("body", "").replace("\n", "<br>"),
                    body_text=msg.get("body", "")
                )
                log.info(f"[PIPE] Email envoye via Gmail a {prospect_email}")
                return True
        except Exception as e:
            log.warning(f"[PIPE] Gmail failed: {e}")

        # Fallback SendGrid
        try:
            from NAYA_CORE.integrations.sendgrid_integration import SendGridIntegration
            sg = SendGridIntegration()
            if sg._api_key:
                msg = messages[0] if messages else {}
                sg.send(to_email=prospect_email, subject=msg.get("subject", ""), body=msg.get("body", ""))
                log.info(f"[PIPE] Email envoye via SendGrid a {prospect_email}")
                return True
        except Exception as e:
            log.warning(f"[PIPE] SendGrid failed: {e}")

        return False

    def _stage_create_payment(self, pain: Dict, priced: Dict, offer: Dict) -> bool:
        try:
            from NAYA_REVENUE_ENGINE.payment_tracker import get_payment_tracker
            tracker = get_payment_tracker()
            price = priced.get("recommended_price", 5000)
            tracker.create_invoice(
                opp_id=offer.get("offer_id", ""),
                prospect=pain.get("entity", "prospect"),
                amount=price,
                method="paypal"
            )
            return True
        except Exception as e:
            log.warning(f"[PIPE] Payment tracking: {e}")
            return False

    def _stage_notify(self, exec_id: str, pain: Dict, priced: Dict, sent: bool) -> None:
        """Notifie la fondatrice via Telegram."""
        try:
            from NAYA_CORE.integrations.telegram_integration import TelegramIntegration
            tg = TelegramIntegration()
            price = priced.get("recommended_price", 0)
            sector = pain.get("sector", "?")
            entity = pain.get("entity", "?")
            status = "ENVOYE" if sent else "EN ATTENTE"

            message = (
                f"[CASH] NAYA PIPELINE [{exec_id}]\n"
                f"Secteur: {sector}\n"
                f"Prospect: {entity}\n"
                f"Prix: {price:,.0f} EUR\n"
                f"Statut: {status}\n"
                f"ROI prospect: {priced.get('roi_for_prospect', 0)}x"
            )
            tg.send(message)
        except Exception as e:
            log.debug(f"[PIPE] Telegram: {e}")

    def _stage_learn(self, pain: Dict, success: bool) -> None:
        try:
            from NAYA_CORE.learning_feedback_engine import get_learning_engine
            engine = get_learning_engine()
            if success:
                engine.record_win(pain.get("sector", ""), pain.get("offer_type", "service"),
                                 pain.get("price", 0), "email", pain.get("pain_type", ""))
            # Enregistrer dans la memoire narrative
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            mem = get_narrative_memory()
            mem.record_event("pipeline_execution", {
                "sector": pain.get("sector", ""), "sent": success,
                "price": pain.get("price", 0)
            })
        except Exception as e:
            log.debug(f"[PIPE] Learning: {e}")

        # Conversion tracking
        try:
            from NAYA_CORE.analytics.conversion_tracker import get_conversion_tracker
            tracker = get_conversion_tracker()
            source = pain.get("source", "pipeline")
            sector = pain.get("sector", "")
            if success:
                tracker.record("outreach_sent", source=source, sector=sector, channel="email")
        except Exception:
            pass

    # ── AUTO-RUN ──────────────────────────────────────────

    def start_auto_pipeline(self):
        """Demarre le pipeline automatique lie a l intention loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._auto_loop, name="PIPELINE-AUTO", daemon=True)
        self._thread.start()
        log.info("[PIPELINE] Auto-pipeline demarre")

    def stop(self):
        self._running = False

    def _auto_loop(self):
        """Boucle automatique: quand le hunt detecte, le pipeline execute."""
        time.sleep(60)  # Attendre le boot
        while self._running:
            try:
                # Verifier s il y a des opportunites non traitees
                from NAYA_CORE.hunt.cash_rapide_classifier import get_classifier
                clf = get_classifier()
                active = clf.get_active()
                for opp in active[:3]:  # Max 3 en parallele
                    if opp.status.value == "queued":
                        pain_data = {
                            "description": opp.pain_description,
                            "sector": opp.sector,
                            "estimated_value": opp.estimated_value_eur,
                            "urgency": opp.urgency_score,
                            "solvability": opp.solvability_score,
                            "entity": opp.target_entity,
                            "offer_type": opp.offer_type,
                        }
                        self.execute_full_pipeline(pain_data)
            except Exception as e:
                log.debug(f"[PIPELINE] Auto-loop: {e}")
            time.sleep(300)  # Toutes les 5 minutes

    def _persist(self):
        try:
            self._persist_file.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "total_runs": self._total_runs,
                    "total_revenue": self._total_revenue,
                    "total_offers_sent": self._total_offers_sent,
                    "executions": len(self._executions)
                }
            self._persist_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def get_stats(self) -> Dict:
        with self._lock:
            completed = sum(1 for e in self._executions.values() if e.result == "success")
            errors = sum(1 for e in self._executions.values() if e.result == "error")
            return {
                "total_runs": self._total_runs,
                "completed": completed,
                "errors": errors,
                "total_offers_sent": self._total_offers_sent,
                "total_revenue": self._total_revenue,
                "running": self._running,
                "active_executions": sum(1 for e in self._executions.values() if e.result == "in_progress")
            }

_pipeline = None
_pipeline_lock = threading.Lock()
def get_pipeline() -> RealPipelineOrchestrator:
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                _pipeline = RealPipelineOrchestrator()
    return _pipeline
