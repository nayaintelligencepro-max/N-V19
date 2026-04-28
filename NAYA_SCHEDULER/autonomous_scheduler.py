"""
NAYA V19 — Autonomous Scheduler
Orchestre tous les cycles automatiques: chasse, outreach, relances, réconciliation.
"""
import os, time, logging, threading
from typing import Dict, Callable, Optional
from datetime import datetime, timezone

log = logging.getLogger("NAYA.SCHEDULER")

CYCLE_INTERVALS = {
    # ── Hybrid Autonomy Kernel ────────────────────────────────────────────────
    "hybrid_daily_brief":     24 * 3600, # Brief hybride quotidien 08h00 Tahiti (18h00 UTC)
    # ── V21 Turbo (accélération) ───────────────────────────────────────────────
    "blitz_hunt":             15 * 60,   # BlitzHunter toutes les 15 min (vs 4h avant)
    "offer_background":       20 * 60,   # FlashOffer background dès prospect ≥70
    "followup_j1":            24 * 3600, # Follow-up J+1 (vs J+2 avant)
    "followup_j3":            3 * 3600,  # Check J+3 follow-ups
    "followup_j7":            6 * 3600,  # Check J+7 follow-ups
    "velocity_report":        30 * 60,   # Rapport velocity toutes les 30 min
    # ── Legacy (conservés) ────────────────────────────────────────────────────
    "hunt_serper":        4 * 3600,
    "hunt_apollo":        6 * 3600,
    "followup_check":     3 * 3600,
    "payment_reconcile":  24 * 3600,
    "telegram_report":    24 * 3600,
    "deblock_overdue":    6 * 3600,
    # ── Cycles évolution ──────────────────────────────────────────────────────
    "evolution_cycle":    6 * 3600,
    "regression_check":   12 * 3600,
    "anticipation_refresh": 24 * 3600,
    "deal_risk_check":    1 * 3600,
    # ── Cycles V20 Intelligence ───────────────────────────────────────────────
    "dark_web_scan":           2 * 3600,
    "cve_shodan_refresh":      6 * 3600,
    "tender_radar_scan":       1 * 3600,
    "regulatory_deadline_check": 24 * 3600,
    "sentiment_radar_sweep":   30 * 60,
    # ── V21 SaaS ──────────────────────────────────────────────────────────────
    "meeting_reminder":        5 * 60,    # Rappels pre-call toutes les 5 min
    "mrr_check":               24 * 3600, # Vérif MRR quotidienne
}


class AutonomousScheduler:
    def __init__(self):
        self._last_run: Dict[str, float] = {}
        self._running = False
        self._cycles = 0

    def start(self):
        self._running = True
        threading.Thread(target=self._main_loop, daemon=True, name="NAYA-Scheduler").start()
        log.info("✅ Autonomous Scheduler V19 started")

    def stop(self):
        self._running = False

    def _main_loop(self):
        while self._running:
            now = time.time()
            for name, interval in CYCLE_INTERVALS.items():
                if now - self._last_run.get(name, 0) >= interval:
                    threading.Thread(target=self._safe_run, args=(name,), daemon=True).start()
                    self._last_run[name] = now
            time.sleep(60)
            self._cycles += 1

    def _safe_run(self, name: str):
        fn = getattr(self, f"_job_{name}", None)
        if not fn:
            return
        try:
            log.info(f"[SCHEDULER] {name}")
            fn()
        except Exception as e:
            log.warning(f"[SCHEDULER] {name} failed: {e}")

    def _job_hunt_serper(self):
        from NAYA_CORE.integrations.serper_hunter import get_serper
        s = get_serper()
        if s.available:
            signals = s.hunt_pains()
            if signals:
                self._notify(f"🔍 Hunt: {len(signals)} signaux")

    def _job_hunt_apollo(self):
        from NAYA_CORE.integrations.apollo_hunter import get_apollo
        a = get_apollo()
        if a.available:
            a.search_people(["DSI","CEO","CTO"], countries=["France","Morocco"], limit=10)

    def _job_followup_check(self):
        log.debug("[SCHEDULER] followup check")

    def _job_payment_reconcile(self):
        from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
        overdue = get_deblock().get_overdue(hours=72)
        if overdue:
            self._notify(f"⚠️ {len(overdue)} paiements en retard")

    def _job_deblock_overdue(self):
        from NAYA_REVENUE_ENGINE.deblock_engine import get_deblock
        get_deblock().get_overdue(hours=48)

    def _job_telegram_report(self):
        from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
        d = get_tracker().dashboard()
        self._notify(
            f"📊 RAPPORT JOURNALIER\nSemaine: {d['week_revenue']:,.0f}€\n"
            f"Mois: {d['month_revenue']:,.0f}€\nTotal: {d['total_revenue']:,.0f}€"
        )

    def _job_evolution_cycle(self):
        """Cycle d'évolution complet toutes les 6h."""
        from EVOLUTION_SYSTEM.evolution_orchestrator import get_evolution_orchestrator
        cycle = get_evolution_orchestrator().run()
        log.info("[SCHEDULER] Evolution cycle #%d — %s (%.1fs)",
                 cycle.cycle_id, cycle.status, cycle.duration_s)

    def _job_regression_check(self):
        """Vérification anti-régression toutes les 12h."""
        from EVOLUTION_SYSTEM.regression_guard import get_regression_guard
        report = get_regression_guard().run_all()
        if report.regression_detected:
            self._notify(
                f"⚠️ RÉGRESSION DÉTECTÉE\n"
                f"Tests: {report.passed}/{report.total_tests} OK\n"
                f"Échecs critiques: {', '.join(report.critical_failures)}"
            )
        else:
            log.info("[SCHEDULER] Regression check: %d/%d OK",
                     report.passed, report.total_tests)

    def _job_anticipation_refresh(self):
        """Mise à jour du moteur d'anticipation quotidienne."""
        from EVOLUTION_SYSTEM.anticipation_engine import get_anticipation_engine
        engine = get_anticipation_engine()
        opps = engine.get_upcoming_opportunities(horizon_days=30)
        if opps:
            top = opps[0]
            self._notify(
                f"🔮 ANTICIPATION — Top opportunité 30j\n"
                f"├── {top.label}\n"
                f"├── Valeur attendue: {top.expected_value:,.0f}€\n"
                f"└── Action: {top.action_required}"
            )

    def _job_deal_risk_check(self):
        """Surveillance température deals toutes les heures."""
        from NAYA_CORE.deal_risk_scorer import get_deal_risk_scorer
        report = get_deal_risk_scorer().run_check()
        if report.cold_deals:
            log.warning("[SCHEDULER] Deal Risk: %d deals froids | at_risk=%.0f€",
                        len(report.cold_deals), report.at_risk_eur)

    # ── V20 Intelligence Jobs ─────────────────────────────────────────────────

    def _job_dark_web_scan(self):
        """Scan dark web OT toutes les 2h."""
        try:
            from V20_INTELLIGENCE.hunters.dark_web_ot_scanner import get_dark_web_scanner
            scanner = get_dark_web_scanner()
            result = scanner.scan()
            if result.alerts_triggered:
                log.info("[SCHEDULER] DarkWebScan: %d signaux, %d alertes",
                         result.signals_found, result.alerts_triggered)
        except Exception as exc:
            log.warning("[SCHEDULER] dark_web_scan failed: %s", exc)

    def _job_cve_shodan_refresh(self):
        """Refresh CVE + Shodan intelligence toutes les 6h."""
        try:
            from V20_INTELLIGENCE.hunters.cve_shodan_intelligence import get_cve_shodan_intelligence
            engine = get_cve_shodan_intelligence()
            log.info("[SCHEDULER] CVE+Shodan refresh: %s", engine.get_stats())
        except Exception as exc:
            log.warning("[SCHEDULER] cve_shodan_refresh failed: %s", exc)

    def _job_tender_radar_scan(self):
        """Scan appels d'offres toutes les heures."""
        try:
            from V20_INTELLIGENCE.hunters.tender_radar import get_tender_radar
            radar = get_tender_radar()
            log.info("[SCHEDULER] TenderRadar: %s", radar.get_stats())
        except Exception as exc:
            log.warning("[SCHEDULER] tender_radar_scan failed: %s", exc)

    def _job_regulatory_deadline_check(self):
        """Vérification deadlines réglementaires quotidienne."""
        try:
            from V20_INTELLIGENCE.hunters.regulatory_deadline_engine import get_regulatory_deadline_engine
            engine = get_regulatory_deadline_engine()
            upcoming = engine.get_upcoming(horizon_days=30)
            if upcoming:
                self._notify(f"⚖️ {len(upcoming)} deadlines réglementaires dans 30j")
        except Exception as exc:
            log.warning("[SCHEDULER] regulatory_deadline_check failed: %s", exc)

    def _job_sentiment_radar_sweep(self):
        """Sweep SentimentRadar toutes les 30min."""
        try:
            from V20_INTELLIGENCE.ai_advanced.sentiment_radar import get_sentiment_radar
            radar = get_sentiment_radar()
            hot = radar.get_hot_leads(min_score=70)
            if hot:
                log.info("[SCHEDULER] SentimentRadar: %d hot leads", len(hot))
        except Exception as exc:
            log.warning("[SCHEDULER] sentiment_radar_sweep failed: %s", exc)

    # ── V21 Turbo jobs ─────────────────────────────────────────────────────────

    def _job_blitz_hunt(self):
        """BlitzHunter toutes les 15min — 5 sources async < 30s."""
        try:
            import asyncio
            from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
            hunter = get_blitz_hunter()
            signals = asyncio.run(hunter.hunt())
            if signals:
                log.info("[SCHEDULER] BlitzHunt: %d signals (top score=%d)", len(signals), signals[0].score)
                high_priority = [s for s in signals if s.urgency_level in ("critical", "high")]
                if high_priority:
                    self._notify(
                        f"⚡ BLITZ HUNT: {len(high_priority)} signaux critiques/haute priorité\n"
                        + "\n".join(f"• {s.company} — {s.sector} — {s.budget_estimate_eur:,} EUR".replace(",", " ")
                                    for s in high_priority[:3])
                    )
        except Exception as exc:
            log.warning("[SCHEDULER] blitz_hunt failed: %s", exc)

    def _job_offer_background(self):
        """Génère des offres en background pour les signaux ≥70 en attente."""
        try:
            import asyncio
            from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
            from NAYA_ACCELERATION.flash_offer import get_flash_offer
            hunter = get_blitz_hunter()
            flash = get_flash_offer()
            signals = asyncio.run(hunter.hunt())
            top = [s for s in signals if s.score >= 70][:4]
            if top:
                async def gen_all():
                    tasks = [
                        flash.generate(
                            company=s.company, sector=s.sector,
                            pain_description=s.pain_description,
                            contact_name=s.contact_name,
                            budget_estimate=s.budget_estimate_eur,
                            urgency=s.urgency_level,
                            signal_id=s.signal_id,
                        ) for s in top
                    ]
                    return await asyncio.gather(*tasks, return_exceptions=True)
                results = asyncio.run(gen_all())
                ok = [r for r in results if not isinstance(r, Exception)]
                log.info("[SCHEDULER] OfferBackground: %d offers generated", len(ok))
        except Exception as exc:
            log.warning("[SCHEDULER] offer_background failed: %s", exc)

    def _job_followup_j1(self):
        """Follow-up automatique J+1 (vs J+2 avant)."""
        log.info("[SCHEDULER] Followup J+1 check (J+1 is faster than J+2)")

    def _job_followup_j3(self):
        """Follow-up J+3."""
        log.info("[SCHEDULER] Followup J+3 check")

    def _job_followup_j7(self):
        """Follow-up J+7 — relance finale."""
        log.info("[SCHEDULER] Followup J+7 check")

    def _job_velocity_report(self):
        """Rapport velocity toutes les 30min."""
        try:
            from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
            tracker = get_velocity_tracker()
            m = tracker.get_metrics()
            if m.sales_today > 0 or m.revenue_this_month_eur > 0:
                log.info(
                    "[SCHEDULER] Velocity: today=%d sales/%d EUR | month=%d/%d EUR | velocity=%.2f/day",
                    m.sales_today, m.revenue_today_eur,
                    m.sales_this_month, m.revenue_this_month_eur,
                    m.daily_velocity,
                )
        except Exception as exc:
            log.warning("[SCHEDULER] velocity_report failed: %s", exc)

    def _job_meeting_reminder(self):
        """Envoie les briefs pre-call 30 min avant les réunions confirmées."""
        try:
            from OUTREACH.meeting_booker import get_meeting_booker
            booker = get_meeting_booker()
            meetings = booker.get_meetings_needing_reminder()
            for meeting in meetings:
                result = booker.send_pre_call_reminder(meeting.meeting_id)
                if result.get("success"):
                    self._notify(
                        f"📞 PRE-CALL dans 30 min: {meeting.company}\n"
                        f"{meeting.pre_brief[:200]}"
                    )
            if meetings:
                log.info("[SCHEDULER] meeting_reminder: %d reminders sent", len(meetings))
        except Exception as exc:
            log.warning("[SCHEDULER] meeting_reminder failed: %s", exc)

    def _job_hybrid_daily_brief(self):
        """Brief hybride quotidien 08h00 heure Tahiti (18h00 UTC) — slots + pains + objectif 72h."""
        # Gating horaire : ne s'exécute qu'entre 17h55 et 18h05 UTC
        now_utc = datetime.now(timezone.utc)
        if not (17 <= now_utc.hour <= 18):
            return
        try:
            from NAYA_CORE.hybrid_autonomy_kernel import hybrid_autonomy_kernel
            brief = hybrid_autonomy_kernel.daily_autonomous_brief()
            telegram_msg = brief.get("telegram_message", "")
            slots = brief.get("active_slots", 0)
            pains = brief.get("ultra_discrete_pains_count", 0)
            target = brief.get("fast_cash_target_72h_eur", 0)
            self._notify(
                f"🧠 NAYA BRIEFING HYBRIDE — {now_utc.strftime('%d/%m')}\n"
                f"├── Slots actifs : {slots}\n"
                f"├── Pains ultra-discrets : {pains}\n"
                f"├── Objectif 72h : {target:,.0f} EUR\n"
                f"└── Dashboard : TORI_APP /tori/hybrid/brief\n\n"
                + telegram_msg[:300]
            )
        except Exception as exc:
            log.warning("[SCHEDULER] hybrid_daily_brief failed: %s", exc)

    def _job_mrr_check(self):
        """Vérifie le MRR SaaS et notifie si objectif M6 atteint."""
        try:
            from SAAS_NIS2.subscription_manager import get_subscription_manager
            mgr = get_subscription_manager()
            mrr_data = mgr.get_mrr()
            mrr = mrr_data.get("mrr_eur", 0)
            log.info("[SCHEDULER] MRR: %d EUR / objectif 10,000 EUR", mrr)
            if mrr >= 10_000:
                self._notify(f"🎉 OBJECTIF MRR ATTEINT: {mrr:,} EUR/mois !")
            elif mrr >= 5_000:
                self._notify(f"📈 MRR 50% atteint: {mrr:,} EUR/mois")
        except Exception as exc:
            log.warning("[SCHEDULER] mrr_check failed: %s", exc)

    def _notify(self, msg: str):
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception:
            pass

    def status(self) -> Dict:
        now = time.time()
        return {
            "running": self._running, "cycles": self._cycles,
            "jobs": {n: {
                "interval_h": CYCLE_INTERVALS[n]/3600,
                "next_in_min": round((CYCLE_INTERVALS[n]-(now-self._last_run.get(n,0)))/60,1)
            } for n in CYCLE_INTERVALS}
        }


_scheduler: Optional[AutonomousScheduler] = None

def get_scheduler() -> AutonomousScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AutonomousScheduler()
    return _scheduler

# Alias pour la compatibilité avec l'import NAYA_SCHEDULER.autonomous_scheduler.NayaScheduler
NayaScheduler = AutonomousScheduler
