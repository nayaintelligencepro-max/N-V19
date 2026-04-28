"""
NAYA — SOVEREIGN ENGINE v3 — COMPLET
═══════════════════════════════════════════════════════════════════
Cycle amélioré: SCORE → FILTER → DETECT → CREATE → STORY → PUBLISH → PERSIST → NOTIFY → STREAM → REMEMBER
Nouvelles capacités v3:
  - PainIntensityScoring: priorise les secteurs CRITICAL en premier
  - StorytellingEngine: génère LinkedIn + cold email + pitch à chaque douleur
  - PublicationOrchestrator: programme la publication automatique
  - EventStreamServer: diffuse chaque action vers TORI en temps réel
  - ZeroWaste: recycle les signaux faibles
"""
import os, time, uuid, threading, logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone

log = logging.getLogger("NAYA.SOVEREIGN")


class CycleStatus(Enum):
    SUCCESS   = "success"
    PARTIAL   = "partial"
    NO_SIGNAL = "no_signal"
    ERROR     = "error"


@dataclass
class SovereignCycle:
    id: str = field(default_factory=lambda: f"SOV_{uuid.uuid4().hex[:10].upper()}")
    started_at: float = field(default_factory=time.time)
    status: CycleStatus = CycleStatus.SUCCESS
    sectors_scanned: int = 0
    pains_detected: int = 0
    offers_created: int = 0
    content_generated: int = 0
    revenue_pipeline: float = 0.0
    noise_filtered: int = 0
    guardian_mode: bool = False
    errors: List[str] = field(default_factory=list)
    completed_at: Optional[float] = None

    @property
    def duration_seconds(self):
        return round((self.completed_at or time.time()) - self.started_at, 2)

    def complete(self, status=None):
        self.completed_at = time.time()
        if status: self.status = status
        elif self.pains_detected == 0: self.status = CycleStatus.NO_SIGNAL

    def to_dict(self):
        return {
            "id": self.id, "status": self.status.value,
            "duration_s": self.duration_seconds,
            "sectors_scanned": self.sectors_scanned,
            "pains_detected": self.pains_detected,
            "offers_created": self.offers_created,
            "content_generated": self.content_generated,
            "revenue_pipeline": self.revenue_pipeline,
            "noise_filtered": self.noise_filtered,
            "guardian": self.guardian_mode,
            "ts": datetime.fromtimestamp(self.started_at, timezone.utc).isoformat() + "Z",
        }


DEFAULT_SECTORS = [
    ("artisan_trades",        ["impayés", "devis papier", "facturation manuelle"],              180000),
    ("liberal_professions",   ["rendez-vous perdus", "no-show", "agenda chaos"],               250000),
    ("restaurant_food",       ["food cost", "marges baissent", "gaspillage"],                  400000),
    ("pme_b2b",               ["trésorerie tendue", "impayés clients", "relances manuelles"],  600000),
    ("ecommerce",             ["panier abandonné", "taux retour", "marge nette faible"],        300000),
    ("startup_scaleup",       ["burn rate", "CAC trop élevé", "churn"],                        800000),
    ("healthcare_wellness",   ["rdv non honorés", "administratif lourd", "surcharge"],          350000),
    ("diaspora_markets",      ["accès services", "offres inexistantes", "sous-bancarisé"],      200000),
    ("real_estate_investors", ["actif dormant", "gestion locative", "fiscalité complexe"],      500000),
]

# Signaux par secteur pour PainIntensityScoring
SECTOR_SIGNALS = {
    "artisan_trades":        {"financial_impact": 0.65, "urgency": 0.55, "frequency": 0.70, "emotional_cost": 0.50, "alternatives_quality": 0.30},
    "liberal_professions":   {"financial_impact": 0.70, "urgency": 0.65, "frequency": 0.60, "emotional_cost": 0.45, "alternatives_quality": 0.35},
    "restaurant_food":       {"financial_impact": 0.75, "urgency": 0.80, "frequency": 0.85, "emotional_cost": 0.60, "alternatives_quality": 0.25},
    "pme_b2b":               {"financial_impact": 0.90, "urgency": 0.85, "frequency": 0.80, "emotional_cost": 0.55, "alternatives_quality": 0.20},
    "ecommerce":             {"financial_impact": 0.70, "urgency": 0.60, "frequency": 0.75, "emotional_cost": 0.40, "alternatives_quality": 0.45},
    "startup_scaleup":       {"financial_impact": 0.95, "urgency": 0.90, "frequency": 0.70, "emotional_cost": 0.70, "alternatives_quality": 0.30},
    "healthcare_wellness":   {"financial_impact": 0.65, "urgency": 0.75, "frequency": 0.80, "emotional_cost": 0.65, "alternatives_quality": 0.30},
    "diaspora_markets":      {"financial_impact": 0.60, "urgency": 0.50, "frequency": 0.70, "emotional_cost": 0.75, "alternatives_quality": 0.15},
    "real_estate_investors": {"financial_impact": 0.80, "urgency": 0.65, "frequency": 0.55, "emotional_cost": 0.45, "alternatives_quality": 0.35},
}


class NayaSovereignEngine:
    """Moteur souverain autonome de NAYA — V3 COMPLET."""

    def __init__(self):
        self._db = None
        self._notifier = None
        self._brain = None
        self._intention = None
        self._guardian = None
        self._memory = None
        self._diagnostic = None
        self._event_stream = None       # NEW: EventStreamServer
        self._storytelling = None       # NEW: StorytellingEngine
        self._publication = None        # NEW: PublicationOrchestrator
        self._pain_scorer = None        # NEW: PainIntensityScoring
        self._zero_waste = None         # NEW: ZeroWaste
        self._cash_engine = None        # V8: Pipeline deals réels
        self._conv_engine = None        # V8: Scripts de conversion
        self._rev_intel = None          # V8: Intelligence revenus
        self._money_notifier_v8 = None  # V8: Alertes argent réel
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cycles: List[SovereignCycle] = []
        self._total_pipeline = 0.0
        self._total_offers = 0
        self._total_content = 0
        self._last_human_ts = time.time()
        self._interval = int(os.environ.get("NAYA_AUTO_HUNT_INTERVAL_SECONDS", 3600))
        self._extra_sectors: List[tuple] = []

    def wire(self, db=None, notifier=None, brain=None,
             intention=None, guardian=None, memory=None, diagnostic=None,
             event_stream=None):
        if db:           self._db = db
        if notifier:     self._notifier = notifier
        if brain:        self._brain = brain
        if intention:    self._intention = intention
        if guardian:     self._guardian = guardian
        if memory:       self._memory = memory
        if diagnostic:   self._diagnostic = diagnostic
        if event_stream: self._event_stream = event_stream

        # Auto-chargement des nouveaux modules
        self._load_enrichment_modules()
        log.info(f"[SOVEREIGN V3] Wired: db={bool(db)} brain={bool(brain)} "
                 f"event_stream={bool(event_stream)} storytelling={bool(self._storytelling)} "
                 f"pain_scorer={bool(self._pain_scorer)}")

    def _load_enrichment_modules(self):
        """Charge tous les modules d'enrichissement."""
        # StorytellingEngine
        try:
            from CHANNEL_INTELLIGENCE.storytelling_engine import StorytellingEngine
            self._storytelling = StorytellingEngine()
            log.info("[SOVEREIGN V3] ✅ StorytellingEngine chargé")
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] StorytellingEngine: {e}")

        # PublicationOrchestrator
        try:
            from CHANNEL_INTELLIGENCE.publication_orchestrator import PublicationOrchestrator
            self._publication = PublicationOrchestrator()
            log.info("[SOVEREIGN V3] ✅ PublicationOrchestrator chargé")
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] PublicationOrchestrator: {e}")

        # PainIntensityScoring
        try:
            from NAYA_PROJECT_ENGINE.engine_layer.engine_pain_silence.pain_intensity_scoring import PainIntensityScoring
            self._pain_scorer = PainIntensityScoring()
            log.info("[SOVEREIGN V3] ✅ PainIntensityScoring chargé")
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] PainIntensityScoring: {e}")

        # ZeroWaste
        try:
            from EXECUTIVE_ARCHITECTURE.zero_waste import ZeroWaste
            self._zero_waste = ZeroWaste()
            log.info("[SOVEREIGN V3] ✅ ZeroWaste chargé")
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] ZeroWaste: {e}")

        # EventStreamServer (si non injecté par wire)
        if not self._event_stream:
            try:
                from NAYA_EVENT_STREAM.ws_server import get_event_stream_server
                self._event_stream = get_event_stream_server()
                log.info("[SOVEREIGN V3] ✅ EventStreamServer auto-chargé")
            except Exception as e:
                log.debug(f"[SOVEREIGN V3] EventStreamServer: {e}")

        # V8: Cash Engine Real
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            self._cash_engine = get_cash_engine()
            log.info("[SOVEREIGN V8] ✅ CashEngineReal")
        except Exception as e:
            log.debug(f"[SOVEREIGN V8] CashEngineReal: {e}")
        # V8: Conversion Engine
        try:
            from NAYA_CORE.conversion_engine import get_conversion_engine
            self._conv_engine = get_conversion_engine()
            log.info("[SOVEREIGN V8] ✅ ConversionEngine")
        except Exception as e:
            log.debug(f"[SOVEREIGN V8] ConversionEngine: {e}")
        # V8: Revenue Intelligence
        try:
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            self._rev_intel = get_revenue_intelligence()
            log.info("[SOVEREIGN V8] ✅ RevenueIntelligence")
        except Exception as e:
            log.debug(f"[SOVEREIGN V8] RevenueIntelligence: {e}")
        # V8: Money Notifier
        try:
            from NAYA_CORE.money_notifier import get_money_notifier
            self._money_notifier_v8 = get_money_notifier()
            log.info("[SOVEREIGN V8] ✅ MoneyNotifier")
        except Exception as e:
            log.debug(f"[SOVEREIGN V8] MoneyNotifier: {e}")

    def _score_and_sort_sectors(self, sectors: List[tuple]) -> List[tuple]:
        """Priorise les secteurs par score PainIntensity — CRITICAL en premier."""
        if not self._pain_scorer:
            return sectors

        scored = []
        for name, signals, revenue in sectors:
            sector_signals = SECTOR_SIGNALS.get(name, {
                "financial_impact": 0.5, "urgency": 0.5, "frequency": 0.5,
                "emotional_cost": 0.5, "alternatives_quality": 0.5
            })
            result = self._pain_scorer.score(sector_signals)
            scored.append((name, signals, revenue, result["score"], result["tier"]))

        # Trier par score décroissant (CRITICAL = 80+, HIGH = 60+, MEDIUM = 40+)
        scored.sort(key=lambda x: x[3], reverse=True)
        log.info(f"[SOVEREIGN V3] Secteurs priorisés: {[(s[0], s[4]) for s in scored[:3]]}")
        return [(n, s, r) for n, s, r, score, tier in scored]

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="NAYA-SOVEREIGN", daemon=True)
        self._thread.start()
        self._stream_event("SOVEREIGN_STARTED", {"version": "v3", "interval_s": self._interval})
        log.info(f"[SOVEREIGN V3] Démarré — intervalle {self._interval}s")

    def stop(self): self._running = False

    def register_human_activity(self):
        self._last_human_ts = time.time()
        if self._guardian and hasattr(self._guardian, "register_human_activity"):
            self._guardian.register_human_activity()

    def add_sector(self, name: str, signals: List[str], revenue_eur: float):
        self._extra_sectors.append((name, signals, revenue_eur))
        log.info(f"[SOVEREIGN V3] Secteur ajouté: {name}")

    def trigger_now(self) -> SovereignCycle:
        return self.run_full_cycle()

    def run_full_cycle(self) -> SovereignCycle:
        """Lance un cycle complet de prospection souveraine."""
        cycle = SovereignCycle()
        self._stream_event("CYCLE_STARTED", {"cycle_id": cycle.id})
        try:
            self._prepare_cycle(cycle)
            all_sectors = self._get_prioritized_sectors()
            cycle.sectors_scanned = len(all_sectors)
            self._run_sectors(cycle, all_sectors)
            self._finalize_cycle(cycle)
        except Exception as e:
            cycle.errors.append(str(e)[:80])
            cycle.complete(CycleStatus.ERROR)
            self._stream_event("CYCLE_ERROR", {"error": str(e)[:100]})
            log.error(f"[SOVEREIGN V3] Cycle error: {e}")
        log.info(f"[SOVEREIGN V3] {cycle.id} | {cycle.status.value} | "
                 f"{cycle.pains_detected}🎯 | {cycle.content_generated}✍ | "
                 f"EUR{cycle.revenue_pipeline:,.0f} | {cycle.duration_seconds:.2f}s")
        return cycle

    def _prepare_cycle(self, cycle: "SovereignCycle") -> None:
        """Initialise Guardian mode et intervalle de chasse."""
        if self._guardian and hasattr(self._guardian, "check"):
            cycle.guardian_mode = self._guardian.check()
            gmode = self._guardian.enforce()
            self._interval = gmode.get("hunt_interval_s", self._interval)

    def _get_prioritized_sectors(self) -> list:
        """Retourne les secteurs ordonnés par score de douleur."""
        all_sectors = list(DEFAULT_SECTORS) + list(self._extra_sectors)
        if self._memory and hasattr(self._memory, "get_best_sectors"):
            try:
                best = [s["sector"] for s in self._memory.get_best_sectors(5)]
                all_sectors = sorted(all_sectors, key=lambda x: (x[0] not in best, x[0]))
            except Exception:
                pass
        return self._score_and_sort_sectors(all_sectors)

    def _run_sectors(self, cycle: "SovereignCycle", all_sectors: list) -> None:
        """Traite chaque secteur : hunt → qualify → content → notify."""
        from NAYA_CORE.super_brain_hybrid_v6_0 import hunt_and_create, NoiseFilter
        nf = NoiseFilter()
        for name, signals, revenue in all_sectors:
            try:
                clean = self._filter_noise(signals, nf, cycle)
                result = hunt_and_create(name, clean, float(revenue))
                if result.get("qualified") and result.get("offer"):
                    self._process_qualified(cycle, result, name)
                else:
                    self._process_unqualified(result, name, clean)
            except Exception as e:
                cycle.errors.append(f"{name}: {str(e)[:50]}")

    def _filter_noise(self, signals: list, nf, cycle: "SovereignCycle") -> list:
        """Filtre les signaux parasites, met à jour le compteur bruit."""
        filtered = nf.filter(signals)
        if isinstance(filtered, dict):
            cycle.noise_filtered += len(filtered.get("noise", []))
            return filtered.get("real", signals) or signals
        return signals

    def _process_qualified(self, cycle: "SovereignCycle", result: dict, name: str) -> None:
        """Traite un résultat qualifié : métriques, contenu, persistance, notification."""
        price = float(result["offer"].get("price", 0))
        cycle.pains_detected += 1
        cycle.offers_created  += 1
        cycle.revenue_pipeline += price
        self._total_pipeline   += price
        self._total_offers     += 1
        if result.get("top_pain"):
            self._stream_event("PAIN_DETECTED", {
                **result.get("top_pain", {}), "sector": name, "price": price
            })
        content = self._generate_content(result, name, price)
        if content:
            cycle.content_generated += 1
            self._total_content += 1
            self._stream_event("CONTENT_GENERATED", {
                "sector": name, "types": list(content.keys())
            })
        self._persist_result(result, name)
        self._persist_content(content, name)
        self._notify_opportunity(result, name, content)
        self._record_memory(result, name, price)

    def _record_memory(self, result: dict, name: str, price: float) -> None:
        """Enregistre la douleur dans la mémoire narrative."""
        if self._memory and hasattr(self._memory, "record_pain"):
            try:
                self._memory.record_pain(
                    sector=name,
                    category=result.get("top_pain", {}).get("category", name),
                    annual_cost=float(result.get("top_pain", {}).get("annual_cost_eur", 0)),
                    offer_price=price,
                )
            except Exception:
                pass

    def _process_unqualified(self, result: dict, name: str, signals: list) -> None:
        """Recycle les signaux faibles via ZeroWaste."""
        if self._zero_waste and result.get("top_pain"):
            try:
                recycled = self._zero_waste.recycle_lost_deal({
                    "loss_reason": "no_signal", "sector": name, "signals": signals
                })
                log.debug(f"[SOVEREIGN V3] ZeroWaste {name}: {recycled.get('action','?')}")
            except Exception:
                pass

    def _finalize_cycle(self, cycle: "SovereignCycle") -> None:
        """Clôture le cycle, persiste et stream vers TORI."""
        cycle.complete()
        self._cycles.append(cycle)
        if len(self._cycles) > 200:
            self._cycles = self._cycles[-200:]
        if self._db and hasattr(self._db, "log_event"):
            try:
                self._db.log_event("SOVEREIGN_CYCLE", cycle.to_dict(), source="sovereign")
            except Exception:
                pass
        if self._memory and hasattr(self._memory, "record_cycle"):
            try:
                self._memory.record_cycle(cycle.to_dict())
            except Exception:
                pass
        self._stream_event("CYCLE_COMPLETED", cycle.to_dict())

    def _generate_content(self, result: dict, sector: str, price: float) -> dict:
        """Génère LinkedIn post + cold email + pitch via StorytellingEngine."""
        if not self._storytelling:
            return {}
        try:
            pain  = result.get("top_pain", {})
            offer = result.get("offer", {})
            pain_desc = pain.get("category", sector)
            solution  = offer.get("title", f"Solution {sector}")
            result_desc = f"€{price:,.0f} économisés en {offer.get('delivery_hours', 48)}H"

            content = {}

            # LinkedIn post
            try:
                content["linkedin"] = self._storytelling.generate_linkedin_post(
                    pain=pain_desc,
                    solution=solution,
                    result=result_desc
                )
            except Exception: pass

            # Cold email
            try:
                content["cold_email"] = self._storytelling.generate_cold_email(
                    company=f"PME {sector}", pain=pain_desc,
                    service=solution, result=result_desc
                )
            except Exception: pass

            # Pitch
            try:
                content["pitch"] = self._storytelling.generate_pitch({
                    "pain": pain_desc, "solution": solution,
                    "price": price, "result": result_desc
                })
            except Exception: pass

            # Programme publication via PublicationOrchestrator
            if self._publication and content.get("linkedin"):
                try:
                    from datetime import datetime
                    plan = self._publication.create_plan(
                        content=content["linkedin"],
                        channels=["linkedin", "email"],
                        start=datetime.now(timezone.utc),
                        weeks=2
                    )
                    content["publication_plan"] = {
                        "publications": len(plan.schedule),
                        "estimated_reach": plan.estimated_reach,
                        "estimated_leads": plan.estimated_leads
                    }
                except Exception: pass

            return content
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] Content generation: {e}")
            return {}

    def _persist_result(self, result, sector):
        if not self._db: return
        try:
            pain  = result.get("top_pain", {})
            offer = result.get("offer", {})
            if hasattr(self._db, "save_pain") and pain:
                self._db.save_pain({**pain, "sector": sector, "ts": time.time()})
            if hasattr(self._db, "save_offer") and offer:
                self._db.save_offer({**offer, "sector": sector, "ts": time.time()})
        except Exception as e:
            log.debug(f"[SOVEREIGN V3] Persist: {e}")
        # V8: Pipeline
        self._inject_to_pipeline(result, sector)
    def _inject_to_pipeline(self, result: dict, sector: str):
        """V8: Injecte dans le pipeline cash réel + conversion scoring."""
        if not self._cash_engine: return
        try:
            deal = self._cash_engine.inject_from_hunt(result, sector)
            if not deal: return
            # Intelligence revenus
            if self._rev_intel:
                self._rev_intel.record_detection(sector, deal.pain_category, deal.offer_price)
            # Score conversion
            conv_score = {}
            if self._conv_engine:
                conv_score = self._conv_engine.score_deal_conversion_potential(deal.to_dict())
                if conv_score.get("tier") == "HOT":
                    script = self._conv_engine.build_conversion_script(deal.to_dict())
                    deal.cold_email_subject = script.email_subject
                    deal.cold_email_body = script.email_opening
                    deal.linkedin_post = script.linkedin_hook
                    deal.pitch_script = script.call_opener
            # Notifier
            if self._money_notifier_v8:
                self._money_notifier_v8.alert_deal_detected(deal.to_dict(), conv_score)
            # Stream TORI
            self._stream_event("DEAL_PIPELINE", {
                "deal_id": deal.id, "price": deal.offer_price,
                "sector": sector, "roi": deal.roi_ratio,
                "conv_score": conv_score.get("score", 0),
                "tier": conv_score.get("tier", "WARM"),
            })
            log.info(f"[V8] 💎 Deal {deal.id} | {deal.offer_price:,.0f}€ | {conv_score.get('tier','?')}")
        except Exception as e:
            log.debug(f"[V8] Pipeline inject: {e}")

    def _persist_content(self, content: dict, sector: str):
        """Persiste le contenu généré en DB."""
        if not content or not self._db: return
        try:
            if hasattr(self._db, "log_event"):
                self._db.log_event("CONTENT_GENERATED", {
                    "sector": sector, "types": list(content.keys()),
                    "linkedin": content.get("linkedin", "")[:500],
                    "cold_email_subject": content.get("cold_email", {}).get("subject", "") if isinstance(content.get("cold_email"), dict) else "",
                    "publication_plan": content.get("publication_plan", {}),
                    "ts": time.time()
                }, source="storytelling")
        except Exception: pass

    def _notify_opportunity(self, result: dict, sector: str, content: dict = None):
        if not self._notifier: return
        try:
            offer = result.get("offer", {})
            pain  = result.get("top_pain", {})
            price = float(offer.get("price", 0))
            cat   = pain.get("category", sector)

            actions = [f"€{price:,.0f} | {offer.get('delivery_hours','?')}H"]
            if content and content.get("publication_plan"):
                plan = content["publication_plan"]
                actions.append(f"📢 {plan.get('publications',0)} publications prévues → {plan.get('estimated_leads',0)} leads estimés")

            self._notifier.notify_opportunity(
                name=cat, value=price, sector=sector, actions=actions
            )
        except Exception: pass

    def _stream_event(self, kind: str, payload: dict):
        """Publie un événement vers TORI via EventStreamServer."""
        if not self._event_stream: return
        try:
            source_map = {
                "CYCLE_STARTED": "SOVEREIGN", "CYCLE_COMPLETED": "SOVEREIGN",
                "CYCLE_ERROR": "SOVEREIGN", "SOVEREIGN_STARTED": "SOVEREIGN",
                "PAIN_DETECTED": "HUNT", "CONTENT_GENERATED": "STORYTELLING"
            }
            source = source_map.get(kind, "SOVEREIGN")
            level = "ERROR" if "ERROR" in kind else "SUCCESS" if kind in ("PAIN_DETECTED", "OFFER_CREATED", "CONTENT_GENERATED") else "INFO"
            self._event_stream.publish(
                source=source, module="naya_sovereign_engine",
                kind=kind, level=level, payload=payload,
                tags=["sovereign", kind.lower()]
            )
        except Exception: pass

    def _loop(self):
        time.sleep(15)
        while self._running:
            try: self.run_full_cycle()
            except Exception as e: log.error(f"[SOVEREIGN V3] Loop: {e}")
            for _ in range(self._interval):
                if not self._running: break
                time.sleep(1)

    def get_stats(self):
        return {
            "running": self._running,
            "version": "v3",
            "total_cycles": len(self._cycles),
            "total_pipeline_eur": self._total_pipeline,
            "total_offers": self._total_offers,
            "total_content_generated": self._total_content,
            "sectors_monitored": len(DEFAULT_SECTORS) + len(self._extra_sectors),
            "interval_s": self._interval,
            "guardian_active": bool(self._guardian and getattr(self._guardian, "active", False)),
            "storytelling_active": bool(self._storytelling),
            "pain_scorer_active": bool(self._pain_scorer),
            "publication_active": bool(self._publication),
            "zero_waste_active": bool(self._zero_waste),
            "event_stream_active": bool(self._event_stream),
            "cash_engine_active": bool(self._cash_engine),
            "conversion_engine_active": bool(self._conv_engine),
            "revenue_intel_active": bool(self._rev_intel),
        }

    def get_recent_cycles(self, n=10):
        return [c.to_dict() for c in self._cycles[-n:]]

    @property
    def active(self): return self._running


_SOVEREIGN: Optional[NayaSovereignEngine] = None
_SOVEREIGN_lock = __import__('threading').Lock()

def get_sovereign() -> NayaSovereignEngine:
    global _SOVEREIGN
    if _SOVEREIGN is None:
        with _SOVEREIGN_lock:
            if _SOVEREIGN is None:
                _SOVEREIGN = NayaSovereignEngine()
    return _SOVEREIGN
