"""
NAYA — Autonomous Mission Engine
Le cœur de l'autonomie : NAYA s'assigne et exécute ses propres missions.
Sans intervention humaine. Sans limite.
"""
import os
import time
import uuid
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from datetime import datetime

log = logging.getLogger("NAYA.AUTONOMOUS")

# ── Super Brain V6 ──────────────────────────────────────────────────────────
try:
    from NAYA_CORE.super_brain_hybrid_v6_0 import (
        hunt_and_create as v6_hunt, create_cash_ladder, get_super_brain as get_v6_brain
    )
    _V6_AVAILABLE = True
except ImportError:
    _V6_AVAILABLE = False



class MissionType(Enum):
    HUNT_OPPORTUNITIES = "hunt_opportunities"
    CREATE_BUSINESS = "create_business"
    GENERATE_PROPOSAL = "generate_proposal"
    ANALYZE_MARKET = "analyze_market"
    PRICE_OFFER = "price_offer"
    SEND_ALERT = "send_alert"
    EVOLVE_SYSTEM = "evolve_system"
    MONITOR_HEALTH = "monitor_health"
    RECYCLE_WASTE = "recycle_waste"
    # V6 — Autonomie étendue
    EXECUTE_PROJECT = "execute_project"
    GENERATE_CONTENT = "generate_content"
    PERCEPTION_SCAN = "perception_scan"
    PROCESS_SHOPIFY = "process_shopify"
    SYNC_NOTION = "sync_notion"


class MissionStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Mission:
    id: str = field(default_factory=lambda: f"M_{uuid.uuid4().hex[:10].upper()}")
    type: MissionType = MissionType.HUNT_OPPORTUNITIES
    status: MissionStatus = MissionStatus.QUEUED
    priority: int = 5          # 1=critical, 10=low
    payload: Dict = field(default_factory=dict)
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority,
            "duration_s": round(self.duration_seconds, 2),
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "result_summary": str(self.result)[:200] if self.result else None,
            "error": self.error,
        }


class AutonomousEngine:
    """
    Moteur d'exécution autonome de NAYA.

    En mode autonome :
    1. Hunt d'opportunités toutes les N secondes
    2. Crée des business sur les meilleures opportunités
    3. Génère des propositions
    4. Notifie le propriétaire
    5. Fait évoluer le système en continu
    """

    ACTIVE_PROJECTS = [
        {"id": "P01", "name": "Cash Rapide", "type": "services", "floor_eur": 1000},
        {"id": "P02", "name": "Google XR", "type": "tech", "floor_eur": 5000},
        {"id": "P03", "name": "Botanica", "type": "ecommerce", "floor_eur": 1000},
        {"id": "P04", "name": "Tiny House", "type": "immobilier", "floor_eur": 3000},
        {"id": "P05", "name": "Marchés Oubliés", "type": "marketplace", "floor_eur": 2000},
        {"id": "P06", "name": "Acquisition Immobilière", "type": "immobilier", "floor_eur": 5000},
    ]

    HUNT_SECTORS = [
        "PME & artisans", "Restaurants & food", "E-commerce",
        "Immobilier", "Santé & bien-être", "BTP & construction",
        "Logistique & transport", "Cabinet comptable",
        "Agences & consultants", "Startups tech",
    ]

    def __init__(self):
        self._missions: Dict[str, Mission] = {}
        self._queue: List[Mission] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._hunt_interval = int(os.environ.get("NAYA_AUTO_HUNT_INTERVAL_SECONDS", 3600))
        self._autonomous_mode = os.environ.get("NAYA_AUTONOMOUS_MODE", "true").lower() == "true"
        self._last_hunt = 0.0
        self._cycle = 0
        self._stats = {
            "missions_total": 0, "missions_completed": 0,
            "missions_failed": 0, "businesses_created": 0,
            "proposals_generated": 0, "hunt_cycles": 0,
        }
        self._notifier = None
        self._factory = None
        self._brain = None
        self._init_components()

    def _init_components(self):
        try:
            from NAYA_CORE.business_factory import get_factory
            self._factory = get_factory()
        except Exception as e:
            log.debug(f"Factory: {e}")
        try:
            from NAYA_CORE.execution.naya_brain import get_brain
            self._brain = get_brain()
        except Exception as e:
            log.debug(f"Brain: {e}")
        try:
            from NAYA_CORE.notifier import get_notifier
            self._notifier = get_notifier()
        except Exception as e:
            log.debug(f"Notifier: {e}")

    # ── Start / Stop ───────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._autonomous_loop,
            daemon=True,
            name="NAYA-AUTONOMOUS-ENGINE",
        )
        self._thread.start()
        log.info(f"🤖 Autonomous Engine STARTED — hunt every {self._hunt_interval}s")

    def stop(self):
        self._running = False
        log.info("Autonomous Engine stopped")

    # ── Mission Submission ─────────────────────────────────────────────────────

    def submit(self, mission_type: MissionType, payload: Dict = None, priority: int = 5) -> Mission:
        mission = Mission(type=mission_type, payload=payload or {}, priority=priority)
        with self._lock:
            self._queue.append(mission)
            self._queue.sort(key=lambda m: m.priority)
            self._missions[mission.id] = mission
        self._stats["missions_total"] += 1
        log.info(f"[AUTONOMOUS] Queued: {mission.type.value} ({mission.id})")
        return mission

    # ── Autonomous Loop ────────────────────────────────────────────────────────

    def _autonomous_loop(self):
        """Main loop — runs forever, drives all autonomous behavior."""
        log.info("[AUTONOMOUS] Loop started")

        while self._running:
            self._cycle += 1

            try:
                # Execute queued missions
                self._process_queue()

                # Schedule autonomous hunts
                if self._autonomous_mode:
                    self._schedule_hunts()

                # Health check every 10 cycles
                if self._cycle % 10 == 0:
                    self.submit(MissionType.MONITOR_HEALTH, priority=3)

                # Evolution check every 20 cycles
                if self._cycle % 20 == 0:
                    self.submit(MissionType.EVOLVE_SYSTEM, priority=7)

            except Exception as e:
                log.error(f"[AUTONOMOUS] Loop error (cycle {self._cycle}): {e}")

            time.sleep(30)

    def _schedule_hunts(self):
        """Schedule hunt missions based on interval."""
        now = time.time()
        if now - self._last_hunt >= self._hunt_interval:
            import random
            sector = random.choice(self.HUNT_SECTORS)
            self.submit(MissionType.HUNT_OPPORTUNITIES, {"sector": sector}, priority=4)
            self._last_hunt = now
            self._stats["hunt_cycles"] += 1
            log.info(f"[AUTONOMOUS] Scheduled hunt: {sector}")

    def _process_queue(self):
        """Process next mission in queue."""
        with self._lock:
            if not self._queue:
                return
            mission = self._queue.pop(0)

        mission.status = MissionStatus.RUNNING
        mission.started_at = time.time()

        try:
            result = self._execute_mission(mission)
            mission.result = result
            mission.status = MissionStatus.COMPLETED
            self._stats["missions_completed"] += 1
        except Exception as e:
            mission.error = str(e)
            mission.status = MissionStatus.FAILED
            self._stats["missions_failed"] += 1
            log.warning(f"[AUTONOMOUS] Mission {mission.id} failed: {e}")
        finally:
            mission.completed_at = time.time()

    def _execute_mission(self, mission: Mission) -> Dict:
        """Execute a single mission."""
        t = mission.type

        if t == MissionType.HUNT_OPPORTUNITIES:
            # V6: Silent Pain Detection
            if _V6_AVAILABLE:
                sector = mission.payload.get("sector", "pme_b2b")
                signals = mission.payload.get("signals", [])
                revenue = float(mission.payload.get("revenue_eur", 500000))
                try:
                    v6_result = v6_hunt(sector, signals, revenue)
                    if v6_result.get("status") == "opportunity_found":
                        return v6_result
                except Exception as e:
                    log.debug(f"V6 hunt: {e}")
            return self._exec_hunt(mission.payload)

        elif t == MissionType.CREATE_BUSINESS:
            return self._exec_create_business(mission.payload)

        elif t == MissionType.GENERATE_PROPOSAL:
            return self._exec_generate_proposal(mission.payload)

        elif t == MissionType.ANALYZE_MARKET:
            return self._exec_analyze_market(mission.payload)

        elif t == MissionType.PRICE_OFFER:
            return self._exec_price_offer(mission.payload)

        elif t == MissionType.SEND_ALERT:
            return self._exec_send_alert(mission.payload)

        elif t == MissionType.MONITOR_HEALTH:
            return self._exec_monitor_health()

        elif t == MissionType.EVOLVE_SYSTEM:
            return self._exec_evolve()

        elif t == MissionType.RECYCLE_WASTE:
            return self._exec_recycle_waste(mission.payload)

        elif t == MissionType.EXECUTE_PROJECT:
            return self._exec_execute_project(mission.payload)

        elif t == MissionType.GENERATE_CONTENT:
            return self._exec_generate_content(mission.payload)

        elif t == MissionType.PERCEPTION_SCAN:
            return self._exec_perception_scan(mission.payload)

        elif t == MissionType.PROCESS_SHOPIFY:
            return self._exec_process_shopify(mission.payload)

        elif t == MissionType.SYNC_NOTION:
            return self._exec_sync_notion(mission.payload)

        return {"status": "unknown_mission_type"}

    # ── Mission Executors ──────────────────────────────────────────────────────

    def _exec_hunt(self, payload: Dict) -> Dict:
        sector = payload.get("sector", "PME & artisans")
        log.info(f"[HUNT] Scanning sector: {sector}")

        blueprints = []
        if self._factory:
            blueprints = self._factory.hunt_and_create(sector)
            self._stats["businesses_created"] += len(blueprints)

            # Notify best opportunity
            if blueprints and self._notifier:
                best = max(blueprints, key=lambda b: b.price_recommended)
                self._notifier.notify_opportunity(
                    name=best.name,
                    value=best.price_recommended,
                    sector=sector,
                    actions=best.first_actions_72h,
                )

            # Auto-create proposals for best blueprints
            for bp in blueprints[:2]:
                self.submit(MissionType.GENERATE_PROPOSAL, {"blueprint_id": bp.id}, priority=5)

        return {
            "sector": sector,
            "opportunities_found": len(blueprints),
            "blueprints": [b.id for b in blueprints],
        }

    def _exec_create_business(self, payload: Dict) -> Dict:
        brief = payload.get("brief", "Business générique")
        category = payload.get("category", "consulting")

        if not self._factory:
            return {"error": "Factory not available"}

        bp = self._factory.create_from_brief(brief, category)
        self._stats["businesses_created"] += 1

        if self._notifier:
            self._notifier.notify_business_created(bp.name, bp.price_recommended, bp.first_actions_72h)

        return {"blueprint_id": bp.id, "name": bp.name, "price": bp.price_recommended}

    def _exec_generate_proposal(self, payload: Dict) -> Dict:
        blueprint_id = payload.get("blueprint_id", "")
        client_name = payload.get("client_name", "")

        if not self._factory:
            return {"error": "Factory not available"}

        proposal = self._factory.generate_proposal(blueprint_id, client_name)
        self._stats["proposals_generated"] += 1

        log.info(f"[PROPOSAL] Generated for {blueprint_id}")
        return {"blueprint_id": blueprint_id, "proposal_length": len(proposal)}

    def _exec_analyze_market(self, payload: Dict) -> Dict:
        sector = payload.get("sector", "")
        if self._brain and self._brain.available:
            from NAYA_CORE.execution.naya_brain import TaskType
            response = self._brain.think(
                f"Analyse le marché: {sector}. Donne les 3 meilleures opportunités avec taille de marché et barrières.",
                TaskType.ANALYSIS,
            )
            return {"sector": sector, "analysis": response.text[:500]}
        return {"sector": sector, "analysis": "LLM non configuré"}

    def _exec_price_offer(self, payload: Dict) -> Dict:
        try:
            from BUSINESS_ENGINES.strategic_pricing_engine.pricing_engine import StrategicPricingEngine
            engine = StrategicPricingEngine()
            price = engine.calculate_price(
                payload.get("pain_value", 50000),
                payload.get("client_capacity", 20000),
                payload.get("service_type", "consulting"),
                payload.get("urgency", 0.7),
            )
            return {"price": price, "anchor": round(price * 1.4 / 1000) * 1000}
        except Exception as e:
            return {"error": str(e)}

    def _exec_send_alert(self, payload: Dict) -> Dict:
        if self._notifier:
            self._notifier.send(
                payload.get("title", "NAYA Alert"),
                payload.get("message", ""),
                payload.get("level", "info"),
            )
        return {"sent": True}

    def _exec_monitor_health(self) -> Dict:
        health = {"timestamp": time.time(), "cycle": self._cycle, "queue_size": len(self._queue)}
        return health

    def _exec_evolve(self) -> Dict:
        try:
            from EVOLUTION_SYSTEM.evolution_engine import EvolutionEngine
            engine = EvolutionEngine()
            proposals = engine.propose_evolution({"revenue_growth": 0.15, "automation_rate": 0.6}, "MEDIUM")
            return {"proposals": len(proposals)}
        except Exception as e:
            return {"error": str(e)}

    def _exec_recycle_waste(self, payload: Dict) -> Dict:
        """ZeroWaste complet: recycle deals perdus + monetise sous-produits + optimise marges."""
        results = {"recycled_deals": 0, "by_products": [], "margin_fixes": [], "reactivations": []}
        try:
            from EXECUTIVE_ARCHITECTURE.zero_waste import ZeroWaste
            zw = ZeroWaste()
            # Recycler deals perdus
            lost_deals = payload.get("lost_deals", [])
            for deal in lost_deals:
                r = zw.recycle_lost_deal(deal)
                results["recycled_deals"] += 1
                results["reactivations"].append(r)
            # Si pas de deals fournis, créer un deal générique
            if not lost_deals:
                r = zw.recycle_lost_deal({"loss_reason": payload.get("reason", "not_ready"),
                                          "sector": payload.get("sector", "pme_b2b")})
                results["recycled_deals"] = 1
                results["reactivations"].append(r)
            # Monetiser sous-produits
            ops = payload.get("operations", [{"id": "auto", "data_generated": True, "process_documented": True}])
            results["by_products"] = zw.monetize_by_products(ops)
            # Optimiser marges si service fourni
            if payload.get("service"):
                results["margin_fixes"] = zw.optimize_margin(payload["service"]).get("fixes", [])
            return results
        except Exception as e:
            return {"error": str(e), **results}

    def _exec_execute_project(self, payload: Dict) -> Dict:
        project_id = payload.get("project_id", "")
        project = next((p for p in self.ACTIVE_PROJECTS if p["id"] == project_id), None)
        if not project:
            return {"error": f"Project {project_id} not found"}
        if self._brain and self._brain.available:
            from NAYA_CORE.execution.naya_brain import TaskType
            prompt = f"Génère un plan d'actions 72h pour le projet {project['name']} ({project['type']}). Floor: {project['floor_eur']}€. Actions concrètes uniquement."
            r = self._brain.think(prompt, TaskType.STRATEGIC)
            return {"project_id": project_id, "name": project["name"], "actions": r.text[:1000]}
        return {"project_id": project_id, "name": project["name"], "status": "LLM non configuré"}

    def _exec_generate_content(self, payload: Dict) -> Dict:
        platform = payload.get("platform", "instagram")
        topic = payload.get("topic", "")
        project = payload.get("project", "")
        if self._brain and self._brain.available:
            from NAYA_CORE.execution.naya_brain import TaskType
            prompt = f"Crée un post {platform} pour le projet NAYA '{project}'. Sujet: {topic}. Ton: professionnel et engageant. Include hashtags pertinents."
            r = self._brain.think(prompt, TaskType.CREATIVE)
            return {"platform": platform, "content": r.text, "project": project}
        return {"platform": platform, "content": "LLM non configuré — ajoute ANTHROPIC_API_KEY", "project": project}

    def _exec_perception_scan(self, payload: Dict) -> Dict:
        sector = payload.get("sector", "général")
        if _V6_AVAILABLE:
            try:
                result = v6_hunt(sector, [], 500000)
                return {"sector": sector, "scan": result}
            except Exception as e:
                log.debug(f"Perception scan V6: {e}")
        if self._brain and self._brain.available:
            from NAYA_CORE.execution.naya_brain import TaskType
            prompt = f"Scanne le marché '{sector}'. Identifie 3 douleurs silencieuses non résolues. Pour chaque: douleur, coût estimé, solution possible en 72h."
            r = self._brain.think(prompt, TaskType.HUNT)
            return {"sector": sector, "perception": r.text}
        return {"sector": sector, "perception": "LLM requis"}

    def _exec_process_shopify(self, payload: Dict) -> Dict:
        try:
            from NAYA_CORE.integrations.shopify_integration import ShopifyIntegration
            shopify = ShopifyIntegration()
            return shopify.process(payload)
        except Exception as e:
            return {"status": "shopify_not_configured", "hint": "Configure SHOPIFY_API_KEY dans .env", "error": str(e)}

    def _exec_sync_notion(self, payload: Dict) -> Dict:
        try:
            from NAYA_CORE.integrations.notion_integration import NotionIntegration
            notion = NotionIntegration()
            return notion.sync(payload)
        except Exception as e:
            return {"status": "notion_not_configured", "hint": "Configure NOTION_API_KEY dans .env", "error": str(e)}

    # ── Status & Monitoring ────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        with self._lock:
            queue_size = len(self._queue)
        return {
            "running": self._running,
            "autonomous_mode": self._autonomous_mode,
            "cycle": self._cycle,
            "queue_size": queue_size,
            "hunt_interval_seconds": self._hunt_interval,
            "next_hunt_in_seconds": max(0, int(self._hunt_interval - (time.time() - self._last_hunt))),
            "stats": self._stats,
            "llm_available": self._brain.available if self._brain else False,
        }

    def get_recent_missions(self, n: int = 20) -> List[Dict]:
        missions = sorted(self._missions.values(), key=lambda m: m.created_at, reverse=True)
        return [m.to_dict() for m in missions[:n]]


# ── Singleton ──────────────────────────────────────────────────────────────────
_engine: Optional[AutonomousEngine] = None


def get_autonomous_engine() -> AutonomousEngine:
    global _engine
    if _engine is None:
        _engine = AutonomousEngine()
    return _engine
