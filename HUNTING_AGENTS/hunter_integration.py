"""
NAYA SUPREME — HUNTING AGENTS INTEGRATION
══════════════════════════════════════════════════════════════════════════════════
Pont d'intégration entre les 4 agents de chasse et le système NAYA existant.

Connecte:
  → NAYA_CORE.scheduler (jobs automatiques)
  → NAYA_CORE.cash_engine_real (injection deals)
  → NAYA_CORE.autonomous_engine (missions)
  → PERSISTENCE.database (stockage)
  → BUSINESS_ENGINES.discretion_protocol (mode phantom)
  → NAYA_EVENT_STREAM (diffusion TORI)

Usage:
  from HUNTING_AGENTS.hunter_integration import HuntingAgentsIntegration
  integration = HuntingAgentsIntegration()
  integration.boot()  # Connecte tout et démarre les cycles autonomes
══════════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, Dict, Any

log = logging.getLogger("NAYA.HUNTING.INTEGRATION")


class HuntingAgentsIntegration:
    """
    Intègre les 4 agents de chasse dans l'écosystème NAYA SUPREME.
    Un seul appel à boot() connecte tout.
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self._pain_hunter = None
        self._mega_hunter = None
        self._market_conqueror = None
        self._strategic_creator = None
        self._booted = False
        
        # Références NAYA
        self._db = None
        self._scheduler = None
        self._cash_engine = None
        self._discretion = None
        self._event_stream = None
        self._pricing_engine = None
    
    def boot(self,
             db=None,
             scheduler=None,
             cash_engine=None,
             discretion=None,
             event_stream=None,
             pricing_engine=None,
             auto_start: bool = True) -> Dict:
        """
        Boot complet des 4 agents + intégration NAYA.
        
        Args:
            db: DatabaseManager instance
            scheduler: NayaScheduler instance
            cash_engine: CashEngineReal instance
            discretion: DiscretionProtocol instance
            event_stream: EventStreamServer instance
            pricing_engine: StrategicPricingEngine instance
            auto_start: Démarrer les cycles autonomes immédiatement
        
        Returns:
            Status dict avec état de chaque agent
        """
        if self._booted:
            return {"status": "already_booted"}
        
        log.info("═══ HUNTING AGENTS — Boot séquence ═══")
        
        # Stocker références NAYA
        self._db = db
        self._scheduler = scheduler
        self._cash_engine = cash_engine
        self._discretion = discretion
        self._event_stream = event_stream
        self._pricing_engine = pricing_engine
        
        status = {"agents": {}, "errors": []}
        
        # ── Agent 1: PainHunterB2B ──────────────────────────────────────
        try:
            from .pain_hunter_b2b import PainHunterB2B
            self._pain_hunter = PainHunterB2B()
            if db: self._pain_hunter.set_database(db)
            if cash_engine: self._pain_hunter.set_cash_engine(cash_engine)
            if discretion: self._pain_hunter.set_discretion(discretion)
            if event_stream: self._pain_hunter.set_event_stream(event_stream)
            status["agents"]["pain_hunter_b2b"] = "ready"
            log.info("✓ PainHunterB2B — ready")
        except Exception as e:
            status["agents"]["pain_hunter_b2b"] = f"error: {e}"
            status["errors"].append(f"PainHunterB2B: {e}")
            log.error(f"✗ PainHunterB2B: {e}")
        
        # ── Agent 2: MegaProjectHunter ──────────────────────────────────
        try:
            from .mega_project_hunter import MegaProjectHunter
            self._mega_hunter = MegaProjectHunter()
            if db: self._mega_hunter.set_database(db)
            if discretion: self._mega_hunter.set_discretion(discretion)
            if event_stream: self._mega_hunter.set_event_stream(event_stream)
            status["agents"]["mega_project_hunter"] = "ready"
            log.info("✓ MegaProjectHunter — ready")
        except Exception as e:
            status["agents"]["mega_project_hunter"] = f"error: {e}"
            status["errors"].append(f"MegaProjectHunter: {e}")
            log.error(f"✗ MegaProjectHunter: {e}")
        
        # ── Agent 3: ForgottenMarketConqueror ───────────────────────────
        try:
            from .forgotten_market_conqueror import ForgottenMarketConqueror
            self._market_conqueror = ForgottenMarketConqueror()
            if db: self._market_conqueror.set_database(db)
            if discretion: self._market_conqueror.set_discretion(discretion)
            if event_stream: self._market_conqueror.set_event_stream(event_stream)
            if cash_engine: self._market_conqueror.set_cash_engine(cash_engine)
            status["agents"]["forgotten_market_conqueror"] = "ready"
            log.info("✓ ForgottenMarketConqueror — ready")
        except Exception as e:
            status["agents"]["forgotten_market_conqueror"] = f"error: {e}"
            status["errors"].append(f"ForgottenMarketConqueror: {e}")
            log.error(f"✗ ForgottenMarketConqueror: {e}")
        
        # ── Agent 4: StrategicBusinessCreator ───────────────────────────
        try:
            from .strategic_business_creator import StrategicBusinessCreator
            self._strategic_creator = StrategicBusinessCreator()
            if self._pain_hunter: self._strategic_creator.set_pain_hunter(self._pain_hunter)
            if self._mega_hunter: self._strategic_creator.set_mega_hunter(self._mega_hunter)
            if self._market_conqueror: self._strategic_creator.set_market_conqueror(self._market_conqueror)
            if db: self._strategic_creator.set_database(db)
            if discretion: self._strategic_creator.set_discretion(discretion)
            if event_stream: self._strategic_creator.set_event_stream(event_stream)
            if pricing_engine: self._strategic_creator.set_pricing_engine(pricing_engine)
            status["agents"]["strategic_business_creator"] = "ready"
            log.info("✓ StrategicBusinessCreator — ready")
        except Exception as e:
            status["agents"]["strategic_business_creator"] = f"error: {e}"
            status["errors"].append(f"StrategicBusinessCreator: {e}")
            log.error(f"✗ StrategicBusinessCreator: {e}")
        
        # ── Enregistrer dans le scheduler NAYA ──────────────────────────
        if scheduler:
            self._register_scheduler_jobs(scheduler)
        
        # ── Démarrer les cycles autonomes ───────────────────────────────
        if auto_start:
            self._start_all_autonomous()
        
        self._booted = True
        
        ready = sum(1 for v in status["agents"].values() if v == "ready")
        log.info(f"═══ HUNTING AGENTS — {ready}/4 agents opérationnels ═══")
        
        return status
    
    def _register_scheduler_jobs(self, scheduler):
        """Enregistre les jobs de chasse dans le scheduler NAYA."""
        try:
            if hasattr(scheduler, "add_job") or hasattr(scheduler, "_jobs"):
                # Pain Hunter: toutes les heures
                if self._pain_hunter and hasattr(scheduler, "_register_job"):
                    scheduler._register_job(
                        "hunt_pain_b2b",
                        self._pain_hunter.hunt_cycle,
                        3600,  # 1h
                        "Chasse douleurs B2B/B2A/Gouvernemental"
                    )
                    log.info("  → Job hunt_pain_b2b enregistré (1h)")
                
                # Mega Project: 1x/jour
                if self._mega_hunter and hasattr(scheduler, "_register_job"):
                    scheduler._register_job(
                        "hunt_mega_projects",
                        self._mega_hunter.hunt_cycle,
                        86400,  # 24h
                        "Chasse projets innovants 15M-40M€"
                    )
                    log.info("  → Job hunt_mega_projects enregistré (24h)")
                
                # Forgotten Markets: 2x/jour
                if self._market_conqueror and hasattr(scheduler, "_register_job"):
                    scheduler._register_job(
                        "hunt_forgotten_markets",
                        self._market_conqueror.hunt_cycle,
                        43200,  # 12h
                        "Conquête marchés oubliés"
                    )
                    log.info("  → Job hunt_forgotten_markets enregistré (12h)")
                
                # Strategic: toutes les 2h
                if self._strategic_creator and hasattr(scheduler, "_register_job"):
                    scheduler._register_job(
                        "strategic_business_cycle",
                        self._strategic_creator.strategic_cycle,
                        7200,  # 2h
                        "Création business stratégiques"
                    )
                    log.info("  → Job strategic_business_cycle enregistré (2h)")
                    
        except Exception as e:
            log.warning(f"Scheduler registration: {e}")
    
    def _start_all_autonomous(self):
        """Démarre tous les agents en mode autonome."""
        if self._pain_hunter:
            try: self._pain_hunter.start_autonomous(3600)
            except Exception as e: log.warning(f"Pain auto: {e}")
        
        if self._mega_hunter:
            try: self._mega_hunter.start_autonomous(86400)
            except Exception as e: log.warning(f"Mega auto: {e}")
        
        if self._market_conqueror:
            try: self._market_conqueror.start_autonomous(43200)
            except Exception as e: log.warning(f"Market auto: {e}")
        
        if self._strategic_creator:
            try: self._strategic_creator.start_autonomous(7200)
            except Exception as e: log.warning(f"Strategy auto: {e}")
    
    def stop_all(self):
        """Arrête tous les agents."""
        for agent in [self._pain_hunter, self._mega_hunter,
                      self._market_conqueror, self._strategic_creator]:
            if agent and hasattr(agent, "stop_autonomous"):
                try: agent.stop_autonomous()
                except Exception: pass
    
    # ── Accessors ────────────────────────────────────────────────────────────
    
    @property
    def pain_hunter(self): return self._pain_hunter
    
    @property
    def mega_hunter(self): return self._mega_hunter
    
    @property
    def market_conqueror(self): return self._market_conqueror
    
    @property
    def strategic_creator(self): return self._strategic_creator
    
    def get_all_stats(self) -> Dict:
        """Stats consolidées de tous les agents."""
        stats = {"integration_version": self.VERSION, "booted": self._booted, "agents": {}}
        for name, agent in [
            ("pain_hunter_b2b", self._pain_hunter),
            ("mega_project_hunter", self._mega_hunter),
            ("forgotten_market_conqueror", self._market_conqueror),
            ("strategic_business_creator", self._strategic_creator),
        ]:
            if agent:
                try: stats["agents"][name] = agent.get_stats()
                except: stats["agents"][name] = {"status": "error"}
            else:
                stats["agents"][name] = {"status": "not_loaded"}
        return stats
    
    def run_full_cycle(self) -> Dict:
        """Exécute un cycle complet de tous les agents séquentiellement."""
        results = {}
        
        if self._pain_hunter:
            try: results["pain_hunt"] = self._pain_hunter.hunt_cycle()
            except Exception as e: results["pain_hunt"] = {"error": str(e)}
        
        if self._mega_hunter:
            try: results["mega_hunt"] = self._mega_hunter.hunt_cycle()
            except Exception as e: results["mega_hunt"] = {"error": str(e)}
        
        if self._market_conqueror:
            try: results["market_hunt"] = self._market_conqueror.hunt_cycle()
            except Exception as e: results["market_hunt"] = {"error": str(e)}
        
        if self._strategic_creator:
            try: results["strategic_cycle"] = self._strategic_creator.strategic_cycle()
            except Exception as e: results["strategic_cycle"] = {"error": str(e)}
        
        return results
    
    def to_dict(self) -> Dict:
        return self.get_all_stats()
