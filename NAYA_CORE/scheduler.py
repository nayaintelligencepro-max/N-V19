"""
NAYA — Autonomous Scheduler
Planifie et déclenche toutes les tâches récurrentes automatiquement.
Zero intervention humaine requise.
"""
import os
import time
import threading
import logging
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger("NAYA.SCHEDULER")

def _gs(key, default=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__("os").environ.get(key, default)



@dataclass
class ScheduledJob:
    name: str
    fn: Callable
    interval_seconds: int
    last_run: float = 0.0
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True
    description: str = ""

    @property
    def next_run_in(self) -> int:
        return max(0, int(self.interval_seconds - (time.time() - self.last_run)))

    @property
    def is_due(self) -> bool:
        return self.enabled and (time.time() - self.last_run) >= self.interval_seconds


class NayaScheduler:
    """
    Scheduler autonome NAYA.
    9 jobs par défaut: hunt, health, evolution, memory_cleanup,
    portfolio_report, db_backup, content_generation,
    performance_check, notion_sync.
    """

    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._cycle = 0
        self._register_default_jobs()

    def _register_default_jobs(self):
        hunt_interval = int(_gs("NAYA_AUTO_HUNT_INTERVAL_SECONDS","3600") or 3600)  # Lu au boot
        quantum_interval = int(_gs("V192_QUANTUM_HUNT_INTERVAL_SECONDS","7200") or 7200)  # 2h par défaut
        jobs = [
            ("hunt_opportunities",    self._job_hunt,         hunt_interval,     "🎯 Hunt opportunités automatique"),
            ("quantum_hunt_v192",     self._job_quantum_hunt, quantum_interval,  "🌌 Quantum hunt marchés invisibles V19.2"),
            ("health_check",          self._job_health,       300,               "💓 Vérification santé système"),
            ("evolution_cycle",       self._job_evolution,    7200,              "🧬 Cycle évolution doctrine"),
            ("memory_cleanup",        self._job_memory,       86400,             "🧹 Nettoyage mémoire ancienne"),
            ("portfolio_report",      self._job_portfolio,    3600,              "📊 Rapport portfolio KPIs"),
            ("db_snapshot",           self._job_db_snapshot,  21600,             "💾 Snapshot base de données"),
            ("content_generation",    self._job_content,      14400,             "✍️  Génération contenu social"),
            ("performance_check",     self._job_performance,  1800,              "⚡ Check performance missions"),
            ("notion_sync",           self._job_notion_sync,  86400,             "📓 Sync Notion automatique"),
            ("predictive_check",      self._job_predictive,   1800,              "🔮 Prédictions revenue/churn/cash"),
            ("zero_waste_recycle",    self._job_zero_waste,   7200,              "♻️  Recyclage opportunités perdues"),
            ("storytelling_publish",  self._job_storytelling, 10800,             "✍️  Contenu LLM multi-canal"),
            ("pipeline_advance",      self._job_pipeline,     1800,              "💎 Avancement deals pipeline"),
            ("revenue_intel_report",  self._job_revenue_intel,14400,             "🧠 Intelligence revenus + directives"),
            ("pipeline_daily_report", self._job_pipeline_daily,86400,            "📊 Rapport pipeline quotidien"),
            ("paypal_followup",       self._job_paypal_followup,3600,            "💳 Relance liens PayPal non payés"),
            ("content_tiktok",        self._job_content_tiktok, 43200,           "📱 Script TikTok hebdo"),
            ("revenue_learn",         self._job_revenue_learn,  7200,            "📈 Apprentissage patterns de succès"),
            ("shopify_sync",           self._job_shopify_sync,   3600,            "Sync Shopify + commandes"),
            ("cognitive_scan",         self._job_cognitive_scan, 7200,            "Scan cognitif 10 couches"),
        ]
        for name, fn, interval, desc in jobs:
            self._jobs[name] = ScheduledJob(name=name, fn=fn, interval_seconds=interval, description=desc)
        log.info(f"✅ Scheduler: {len(self._jobs)} jobs enregistrés")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="NAYA-SCHEDULER")
        self._thread.start()
        log.info("🕐 NayaScheduler démarré")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self._cycle += 1
            with self._lock:
                due_jobs = [j for j in self._jobs.values() if j.is_due]
            for job in due_jobs:
                threading.Thread(target=self._run_job, args=(job,), daemon=True, name=f"JOB-{job.name}").start()
            time.sleep(60)  # Check chaque minute

    def _run_job(self, job: ScheduledJob):
        job.last_run = time.time()
        job.run_count += 1
        try:
            job.fn()
            log.info(f"[SCHEDULER] ✅ {job.name} (#{job.run_count})")
        except Exception as e:
            job.error_count += 1
            log.warning(f"[SCHEDULER] ❌ {job.name}: {e}")

    # ── Job Implementations ────────────────────────────────────────────────────

    def _job_hunt(self):
        try:
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            import random
            engine = get_autonomous_engine()
            sectors = ["PME & artisans", "Restaurants & food", "E-commerce", "Immobilier", "Santé & bien-être", "BTP & construction"]
            sector = random.choice(sectors)
            engine.submit(MissionType.HUNT_OPPORTUNITIES, {"sector": sector}, priority=3)
        except Exception as e:
            log.debug(f"Job hunt: {e}")

    def _job_quantum_hunt(self):
        """
        JOB V19.2 — QUANTUM HUNT
        Lance la chasse autonome sur marchés invisibles.
        Toutes les 2h, scanne les marchés oubliés (Polynésie, Afrique francophone),
        besoins ultra-discrets (gouvernements, OIV), opportunités trans-sectorielles,
        niches premium.
        """
        try:
            import asyncio
            from NAYA_CORE.v19_2_supreme_engine import run_autonomous_quantum_hunt

            # Exécuter la chasse quantum dans la boucle async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_autonomous_quantum_hunt())
            loop.close()

            opps = result.get('opportunities_detected', 0)
            value = result.get('total_value_eur', 0)
            priority = len(result.get('outreach_plans', []))

            log.info(f"[SCHEDULER][V19.2] Quantum Hunt: {opps} opportunités invisibles | "
                    f"{value:,.0f} EUR | {priority} prioritaires")
        except Exception as e:
            log.debug(f"Job quantum_hunt: {e}")

    def _job_health(self):
        try:
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            engine = get_autonomous_engine()
            engine.submit(MissionType.MONITOR_HEALTH, {}, priority=2)
        except Exception as e:
            log.debug(f"Job health: {e}")

    def _job_evolution(self):
        try:
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            engine = get_autonomous_engine()
            engine.submit(MissionType.EVOLVE_SYSTEM, {}, priority=7)
        except Exception as e:
            log.debug(f"Job evolution: {e}")

    def _job_memory(self):
        try:
            from NAYA_CORE.memory.distributed_memory import get_memory
            removed = get_memory().clear_old(days=90)
            if removed > 0:
                log.info(f"[SCHEDULER] Memory: {removed} entries removed (>90 days)")
        except Exception as e:
            log.debug(f"Job memory: {e}")

    def _job_portfolio(self):
        try:
            from NAYA_CORE.portfolio_manager import get_portfolio_manager
            pm = get_portfolio_manager()
            report = pm.generate_report()
            log.info(f"[SCHEDULER] Portfolio: {report.get('summary', {})}")
        except Exception as e:
            log.debug(f"Job portfolio: {e}")

    def _job_db_snapshot(self):
        try:
            from PERSISTENCE.database.db_manager import get_db
            db = get_db()
            db.record_kpi("scheduler_snapshot", time.time())
        except Exception as e:
            log.debug(f"Job db_snapshot: {e}")

    def _job_content(self):
        try:
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            import random
            engine = get_autonomous_engine()
            projects = ["P01", "P03", "P05"]
            platforms = ["instagram", "linkedin"]
            engine.submit(MissionType.GENERATE_CONTENT, {
                "project": random.choice(projects),
                "platform": random.choice(platforms),
                "topic": "opportunité business cette semaine",
            }, priority=8)
        except Exception as e:
            log.debug(f"Job content: {e}")

    def _job_performance(self):
        try:
            from NAYA_CORE.autonomous_engine import get_autonomous_engine
            engine = get_autonomous_engine()
            status = engine.get_status()
            stats = status.get("stats", {})
            total = stats.get("missions_total", 0)
            done = stats.get("missions_completed", 0)
            rate = round(done / total * 100, 1) if total > 0 else 0
            log.info(f"[SCHEDULER] Performance: {done}/{total} missions OK ({rate}%)")
        except Exception as e:
            log.debug(f"Job performance: {e}")

    def _job_notion_sync(self):
        try:
            from NAYA_CORE.integrations.notion_integration import NotionIntegration
            notion = NotionIntegration()
            if notion.available:
                result = notion.export_memory(limit=50)
                log.info(f"[SCHEDULER] Notion sync: {result}")
        except Exception as e:
            log.debug(f"Job notion_sync: {e}")

    def _job_predictive(self):
        """Nouveau: PredictiveLayer — anticipe les creux et adapte la chasse."""
        try:
            from EXECUTIVE_ARCHITECTURE.predictive_layer import PredictiveLayer
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            pl = PredictiveLayer()
            engine = get_autonomous_engine()
            status = engine.get_status()
            stats = status.get("stats", {})
            missions_done = stats.get("missions_completed", 0)
            # Simuler historique MRR avec les données de pipeline
            historical = [missions_done * 500.0] if missions_done > 0 else [0.0]
            revenue_pred = pl.predict_revenue(historical, ["sovereign", "hunt"])
            cash_forecast = pl.forecast_cash(revenue_pred.predicted_30d, 200.0, months=3)
            # Si creux prédit → intensifier la chasse
            negative_months = sum(1 for m in cash_forecast if m["status"] == "NEGATIVE")
            if negative_months > 0:
                engine.submit(MissionType.HUNT_OPPORTUNITIES, {"sector": "pme_b2b", "priority": "CRITICAL"}, priority=1)
                log.warning(f"[SCHEDULER] 🔮 Creux prédit dans {negative_months} mois → Chasse intensifiée")
            log.info(f"[SCHEDULER] 🔮 Prédiction MRR 30j: €{revenue_pred.predicted_30d:,.0f} | Cash: {cash_forecast[0]['status'] if cash_forecast else 'N/A'}")
        except Exception as e:
            log.debug(f"Job predictive: {e}")

    def _job_zero_waste(self):
        """Nouveau: ZeroWaste — recycle les opportunités perdues."""
        try:
            from EXECUTIVE_ARCHITECTURE.zero_waste import ZeroWaste
            from NAYA_CORE.autonomous_engine import get_autonomous_engine, MissionType
            zw = ZeroWaste()
            engine = get_autonomous_engine()
            # Récupérer missions échouées récentes
            missions = engine.get_recent_missions(50)
            failed = [m for m in missions if m.get("status") == "failed"]
            for m in failed[:5]:  # Recycler 5 max par cycle
                deal = {
                    "loss_reason": m.get("result", {}).get("error_type", "unknown"),
                    "sector": m.get("payload", {}).get("sector", "unknown"),
                    "mission_id": m.get("id", ""),
                }
                recycled = zw.recycle_lost_deal(deal)
                log.debug(f"[SCHEDULER] ♻️ Recycled: {recycled.get('action', '?')} — reactivation {recycled.get('reactivation_in_days', 30)}j")
            # Monetize by-products
            by_products = zw.monetize_by_products([
                {"id": "content_gen", "data_generated": True, "process_documented": True}
            ])
            if by_products:
                log.info(f"[SCHEDULER] ♻️ {len(by_products)} opportunités sous-produits identifiées")
        except Exception as e:
            log.debug(f"Job zero_waste: {e}")

    def _job_storytelling(self):
        """Nouveau: Storytelling + Publication pour contenu social autonome."""
        try:
            from CHANNEL_INTELLIGENCE.storytelling_engine import StorytellingEngine
            from CHANNEL_INTELLIGENCE.publication_orchestrator import PublicationOrchestrator
            from datetime import datetime
            import random
            se = StorytellingEngine()
            po = PublicationOrchestrator()
            # Générer contenu sur un secteur actif
            sectors = ["pme_b2b", "startup_scaleup", "healthcare_wellness", "artisan_trades"]
            sector = random.choice(sectors)
            post = se.generate_linkedin_post(
                pain=f"les problèmes de trésorerie dans {sector.replace('_', ' ')}",
                solution="notre approche discrète et rapide",
                result="des résultats mesurables en 48H"
            )
            if post:
                plan = po.create_plan(post, ["linkedin", "email"], start=datetime.now(timezone.utc), weeks=2)
                log.info(f"[SCHEDULER] ✍️ Contenu {sector}: {plan.estimated_reach} reach estimé, {plan.estimated_leads} leads potentiels")
        except Exception as e:
            log.debug(f"Job storytelling: {e}")


    def _job_pipeline(self):
        """V8: Avancement automatique des deals dans le pipeline."""
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            engine = get_cash_engine()
            actions = engine.advance_deals()
            if actions:
                log.info(f"[SCHEDULER] 💎 Pipeline: {len(actions)} deals avancés")
        except Exception as e:
            log.debug(f"Job pipeline: {e}")

    def _job_revenue_intel(self):
        """V8: Génère les directives de chasse depuis l'intelligence revenus."""
        try:
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            from NAYA_CORE.money_notifier import get_money_notifier
            intel = get_revenue_intelligence()
            directives = intel.get_hunt_directives()
            # Orienter le sovereign engine vers les meilleurs secteurs
            try:
                from NAYA_CORE.naya_sovereign_engine import get_sovereign
                sov = get_sovereign()
                focus = directives.get("focus_sectors", [])
                for sector in focus[:3]:
                    if not any(s[0] == sector for s in sov._extra_sectors):
                        sov.add_sector(sector, [], 500000)
            except Exception: pass
            log.info(f"[SCHEDULER] 🧠 Intel: top={directives.get('rationale',{}).get('top_sector','?')}")
        except Exception as e:
            log.debug(f"Job revenue_intel: {e}")

    def _job_pipeline_daily(self):
        """V8: Rapport pipeline quotidien sur Telegram."""
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            from NAYA_CORE.money_notifier import get_money_notifier
            engine = get_cash_engine()
            summary = engine.get_pipeline_summary()
            get_money_notifier().alert_pipeline_daily(summary)
            log.info(f"[SCHEDULER] 📊 Pipeline report: {summary.get('active_deals',0)} deals {summary.get('pipeline_total_eur',0):,.0f}€")
        except Exception as e:
            log.debug(f"Job pipeline_daily: {e}")

    def _job_paypal_followup(self):
        """Relance les prospects avec lien PayPal non payé depuis +24H."""
        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            from NAYA_CORE.money_notifier import get_money_notifier
            from datetime import datetime, timedelta
            pt = PipelineTracker(); mn = get_money_notifier()
            threshold = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            count = 0
            for entry in pt.all():
                if (entry.get("status") == "PROPOSAL_SENT" and
                    entry.get("payment_url") and
                    entry.get("last_updated","") < threshold and
                    not entry.get("payment_received")):
                    if mn.available:
                        mn._send(
                            f"\u23f0 <b>PayPal non pay\u00e9 \u2014 relancer ?</b>\n\n"
                            f"\U0001f3e2 {entry.get('company','?')}\n"
                            f"\U0001f4b0 {entry.get('offer_price',0):,.0f}\u20ac\n"
                            f"\U0001f517 {entry.get('payment_url','')}\n\n"
                            f"<i>Envoy\u00e9 +24H \u2014 relancer WhatsApp?</i>"
                        )
                        count += 1
            if count > 0:
                log.info(f"[SCHEDULER] \U0001f4b3 PayPal relance: {count} prospects")
        except Exception as e: log.debug(f"Job paypal_followup: {e}")

    def _job_content_tiktok(self):
        """Script TikTok sur le secteur le plus performant."""
        try:
            from CHANNEL_INTELLIGENCE.storytelling_engine import StorytellingEngine
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            from NAYA_CORE.money_notifier import get_money_notifier
            se = StorytellingEngine(); ri = get_revenue_intelligence(); mn = get_money_notifier()
            dirs = ri.get_hunt_directives()
            sector = dirs.get("rationale",{}).get("top_sector","pme_b2b")
            pain_cat = dirs.get("rationale",{}).get("best_conversion_pain","CASH_TRAPPED")
            pain_map = {"CASH_TRAPPED":"tresorerie bloquee","MARGIN_INVISIBLE_LOSS":"pertes de marges",
                "INVOICE_LEAK":"fuites facturation","UNDERPRICED":"sous-facturation"}
            pain = pain_map.get(pain_cat, pain_cat.replace("_"," "))
            script = se.generate_tiktok_script(pain, "methode NAYA 48H", "ROI x5", sector)
            if mn.available:
                mn._send(
                    f"\U0001f4f1 <b>SCRIPT TIKTOK</b>\n\n"
                    f"Secteur: <b>{sector.replace('_',' ')}</b>\n"
                    f"Douleur: <b>{pain}</b>\n\n"
                    f"<code>{script['script'][:400]}</code>\n\n"
                    f"<i>Filmer + publier sur @nayaservice2025</i>"
                )
            log.info(f"[SCHEDULER] \U0001f4f1 TikTok script: {sector}")
        except Exception as e: log.debug(f"Job content_tiktok: {e}")

    def _job_revenue_learn(self):
        """Enregistre les patterns de succes dans RevenueIntelligence."""
        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            from NAYA_CORE.revenue_intelligence import get_revenue_intelligence
            pt = PipelineTracker(); ri = get_revenue_intelligence()
            for entry in pt.all():
                if entry.get("status") == "CLOSED_WON" and not entry.get("_learned"):
                    ri.record_win(sector=entry.get("sector","unknown"),
                        pain_category=entry.get("pain_category",""),
                        price=float(entry.get("revenue_collected",entry.get("offer_price",0))))
                    pt._pipeline[entry["id"]]["_learned"] = True
                elif entry.get("status") not in ("NEW","ALERTED"):
                    ri.record_detection(sector=entry.get("sector","unknown"),
                        pain_category=entry.get("pain_category",""),
                        price=float(entry.get("offer_price",0)))
            pt._save()
            log.debug("[SCHEDULER] \U0001f4c8 Revenue learn done")
        except Exception as e: log.debug(f"Job revenue_learn: {e}")

        # ── API ────────────────────────────────────────────────────────────────────

    def _job_shopify_sync(self):
        """Synchronise Shopify: produits, commandes, paniers abandonnés."""
        try:
            from NAYA_CORE.integrations.shopify_integration import ShopifyIntegration
            sh = ShopifyIntegration()
            if not sh.available:
                log.debug("[SCHEDULER] Shopify non configuré")
                return
            products = sh.get_products(5)
            orders = sh.get_orders(5)
            prod_count = products.get("count", 0)
            order_count = orders.get("count", 0)
            log.info(f"[SCHEDULER] Shopify: {prod_count} produits | {order_count} commandes recentes")
            # Alerte si nouvelles commandes
            if order_count > 0:
                try:
                    from NAYA_CORE.money_notifier import get_money_notifier
                    mn = get_money_notifier()
                    if mn.available and order_count > 0:
                        total = sum(float(o.get("total_price", 0)) for o in orders.get("orders", []))
                        if total > 0:
                            mn._send(
                                f"\U0001f6d2 <b>SHOPIFY — {order_count} commandes</b>\n"
                                f"Total: <b>{total:.0f}\u20ac</b>\n"
                                f"Shop: {sh.shop_url}"
                            )
                except Exception: pass
        except Exception as e:
            log.debug(f"Job shopify_sync: {e}")

    def _job_cognitive_scan(self):
        """Scan cognitif des 35 prospects existants via pipeline 10 couches."""
        try:
            from NAYA_CORE.cognitive_pipeline import get_cognitive_pipeline
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            cog = get_cognitive_pipeline()
            pt = PipelineTracker()
            upgraded = 0
            for entry in pt.all():
                if entry.get("status") not in ("NEW", "ALERTED"):
                    continue
                signals = [entry.get("pain_category", "").replace("_", " "),
                           entry.get("offer_title", "")[:50]]
                score = cog.score_prospect(
                    entry.get("company", ""),
                    signals,
                    float(entry.get("pain_cost", 30000)),
                    entry.get("sector", "")
                )
                if score.get("tier") == "HOT" and score.get("elite_signals"):
                    upgraded += 1
            log.info(f"[SCHEDULER] Cognitive scan: {upgraded} prospects upgradés HOT")
        except Exception as e:
            log.debug(f"Job cognitive_scan: {e}")

    def get_status(self) -> Dict:
        with self._lock:
            return {
                "running": self._running,
                "cycle": self._cycle,
                "jobs": {
                    name: {
                        "enabled": j.enabled,
                        "description": j.description,
                        "interval_s": j.interval_seconds,
                        "run_count": j.run_count,
                        "error_count": j.error_count,
                        "next_run_in_s": j.next_run_in,
                    }
                    for name, j in self._jobs.items()
                },
            }

    def trigger(self, job_name: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_name)
        if not job:
            return False
        threading.Thread(target=self._run_job, args=(job,), daemon=True).start()
        return True

    def add_job(self, name: str, fn: Callable, interval_seconds: int, description: str = "") -> bool:
        with self._lock:
            self._jobs[name] = ScheduledJob(name=name, fn=fn, interval_seconds=interval_seconds, description=description)
        return True

    def disable_job(self, name: str) -> bool:
        with self._lock:
            if name in self._jobs:
                self._jobs[name].enabled = False
                return True
        return False


# ── Singleton ──────────────────────────────────────────────────────────────────
_scheduler: Optional[NayaScheduler] = None


def get_scheduler() -> NayaScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = NayaScheduler()
    return _scheduler
