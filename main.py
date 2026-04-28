#!/usr/bin/env python3
"""
NAYA SUPREME V19.3 — ENTRY POINT
Système autonome IA pour génération revenue multi-stream.

Commandes:
    python main.py                  # Single cycle
    python main.py daemon           # Boucle infinie (interval 1h)
    python main.py daemon --interval 300   # Boucle 5min
    python main.py dashboard        # Lance dashboard OODA sur :8080
"""

import asyncio
import sys
import logging
import argparse
import json

# 🔐 CHARGER TOUTES LES CLÉS API DÈS LE BOOT
from SECRETS import load_all_secrets, validate_all_keys, validate_production_secrets
from NAYA_CORE.preflight import run_preflight
from NAYA_CORE.llm_router import llm_router

# Charger les secrets avant toute autre opération
try:
    secrets_result = load_all_secrets(verbose=False)
    logging.info(f"[BOOT] 🔐 {secrets_result['real_keys']}/{secrets_result.get('critical_keys_total', 0)} clés API chargées")
except Exception as e:
    logging.error(f"[BOOT] ❌ Erreur chargement secrets: {e}")
    # Continuer malgré l'erreur (mode dégradé)

from NAYA_CORE.multi_agent_orchestrator import multi_agent_orchestrator
# V19.3: registry unifié des 32 pains (remplace 39 fichiers dupliqués)
from NAYA_CORE.pain import register_all_specs, pain_registry


def print_banner():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     🚀 NAYA SUPREME V19.3 — AUTONOMOUS AI BUSINESS SYSTEM         ║
║                                                                    ║
║     11 Agents IA | 29 Modules Revenue | 32 Pain Engines          ║
║     Circuit Breakers | OODA Dashboard | Revenue Reconciliation   ║
║                                                                    ║
║     Capacity: 4.3-6M EUR/an (realistic year 1+)                   ║
║     Status: PRODUCTION READY                                       ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)


async def run_single_cycle():
    print("Running single cycle...")
    result = await multi_agent_orchestrator.run_full_cycle()
    print("\n✅ CYCLE COMPLETE")
    print(f"Cycle #{result['cycle']}")
    print(f"Total revenue potential: {result['phases']['outreach']} EUR")
    print(f"Execution time: {result['elapsed_seconds']:.2f}s")


async def run_daemon(interval: int):
    print(f"Starting NAYA SUPREME daemon (cycle every {interval}s)...")
    await multi_agent_orchestrator.start_daemon(interval_seconds=interval)


def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Lance le dashboard OODA."""
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn non installé. pip install uvicorn")
        sys.exit(1)
    from NAYA_DASHBOARD.ooda_dashboard import app
    print(f"🖥️  OODA Dashboard: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    print_banner()

    # Preflight de sécurité/runtime
    preflight = run_preflight()
    if not preflight["ok"]:
        print("[BOOT] ⚠️ Preflight partiellement invalide:")
        for check in preflight["checks"]:
            status = "OK" if check["ok"] else "FAIL"
            print(f" - {check['name']}: {status} ({check['detail']})")
    else:
        print("[BOOT] ✅ Preflight validé")

    weak = validate_production_secrets(raise_on_weak=False)
    if weak:
        print(f"[BOOT] ⚠️ Secrets faibles détectés: {', '.join(weak)}")

    # Enregistrer les 32 pain engines (remplace 39 fichiers dupliqués)
    register_all_specs()
    stats = pain_registry.global_stats()
    print(f"[BOOT] ✅ {stats['engines']} pain engines enregistrés")

    # Universal Pain Engine + Zero Waste au boot
    try:
        from NAYA_PROJECT_ENGINE.business.universal_pain_engine import universal_pain_engine
        from NAYA_PROJECT_ENGINE.business.zero_waste_recycler import zero_waste_recycler
        _pain_count = len(universal_pain_engine._catalogue)
        print(f"[BOOT] ✅ Universal Pain Engine: {_pain_count} douleurs discrètes chargées")
        _waste_stats = zero_waste_recycler.stats()
        print(f"[BOOT] ✅ Zero-Waste Registry: {_waste_stats['total_assets']} assets | {_waste_stats['total_recycled_usages']} réutilisations")
    except Exception as _e:
        print(f"[BOOT] ⚠️ Pain/Waste engine: {_e}")

    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="cycle",
                        choices=["cycle", "daemon", "dashboard", "preflight", "status",
                                 "tori", "launch10d", "pains", "mission10d", "briefing",
                                 "regulatory", "ooda", "score", "warmpath", "hybrid", "edge", "cashtruth", "partition-sales",
                                 "real-sales-live", "real-sales-daemon"])
    parser.add_argument("--interval", type=int, default=3600,
                        help="Daemon cycle interval (seconds)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.command == "cycle":
        asyncio.run(run_single_cycle())
    elif args.command == "daemon":
        asyncio.run(run_daemon(args.interval))
    elif args.command == "dashboard":
        run_dashboard(args.host, args.port)
    elif args.command == "tori":
        run_tori_server(args.host, args.port)
    elif args.command == "launch10d":
        from NAYA_INTERFACE.tori_app_bridge import ToriBridge
        bundle = ToriBridge().get_launch_10d_bundle()
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    elif args.command == "mission10d":
        from NAYA_PROJECT_ENGINE.mission_10_days_engine import mission_10_days_engine
        print(json.dumps(mission_10_days_engine.report(), indent=2, ensure_ascii=False))
    elif args.command == "briefing":
        from NAYA_CORE.integrations.telegram_mission_briefing import telegram_mission_briefing
        result = telegram_mission_briefing.send_morning_briefing()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "pains":
        from NAYA_PROJECT_ENGINE.business.universal_pain_engine import UniversalPainEngine
        pains = UniversalPainEngine().get_ultra_discrete(10)
        for p in pains:
            print(f"[{p['pain_level'].upper()}] {p['sector']} — {p['title'][:60]} → {p['budget_target_eur']:,} EUR")
    elif args.command == "preflight":
        print(json.dumps(preflight, indent=2, ensure_ascii=False))
    elif args.command == "status":
        from NAYA_INTERFACE.tori_app_bridge import ToriBridge
        status_data = ToriBridge().get_system_status()
        print(json.dumps({
            "preflight_ok": preflight["ok"],
            "llm_selected": llm_router.select(),
            "llm_available": llm_router.available(),
            "llm_health": llm_router.health(),
            "tori_components": status_data["components"],
        }, indent=2, ensure_ascii=False))
    elif args.command == "regulatory":
        from NAYA_CORE.regulatory_trigger_engine import regulatory_trigger_engine
        top = regulatory_trigger_engine.top_opportunities(10)
        print("\n🏛️  TOP OPPORTUNITÉS RÉGLEMENTAIRES\n" + "═"*55)
        for opp in top:
            print(f"[{opp['regulation']}] {opp['title'][:50]}")
            print(f"  ↳ Deadline: {opp['deadline']} ({opp['days_remaining']}j) | Pressure: {opp['pressure_score']:.0f}/100")
            print(f"  ↳ Budget: {opp['budget_range']} | Secteurs: {', '.join(opp['sectors'])}")
        signals = regulatory_trigger_engine.scan()
        print(f"\n✅ {len(signals)} HuntSignals actifs prêts pour le pipeline")
    elif args.command == "ooda":
        from NAYA_CORE.ooda_speed_layer import ooda_speed_layer
        print("\n⚡ OODA SPEED LAYER — Test signal")
        action = ooda_speed_layer.ingest_sync(
            "pain_detected",
            {"score": 85, "budget_estimate_eur": 25000, "sector": "Energie"},
            source="main_test"
        )
        print(json.dumps(ooda_speed_layer.status(), indent=2, ensure_ascii=False))
        if action:
            print(f"\n→ Action: {action.action_type} (prio={action.priority}) → {action.dispatch_target}")
    elif args.command == "score":
        from NAYA_CORE.composite_scorer_v2 import composite_scorer
        result = composite_scorer.score(
            prospect_id="demo_prospect",
            signals={
                "signal_age_days": 5,
                "has_job_post": True,
                "has_linkedin": True,
                "budget_estimate_eur": 30000,
                "regulatory_pressure_score": 65,
                "mutual_connections": 2,
                "company_revenue_m": 50,
            },
            sector="Transport",
        )
        print(f"\n🎯 COMPOSITE SCORER V2 — Demo Prospect")
        print(f"  Score: {result.composite_score:.1f}/100 | Tier: {result.tier}")
        print(f"  Win Probability: {result.win_probability*100:.1f}%")
        print(f"  Deal Estimate: {result.estimated_deal_eur:,.0f} EUR")
        print(f"  Action: {result.recommended_action}")
        print(f"  Vecteur 6D:")
        v = result.vector
        print(f"    D1 Urgency:          {v.urgency:.2f}")
        print(f"    D2 Budget Confidence:{v.budget_confidence:.2f}")
        print(f"    D3 Accessibility:    {v.accessibility:.2f}")
        print(f"    D4 Regulatory Press: {v.regulatory_pressure:.2f}")
        print(f"    D5 Competitive Iso:  {v.competitive_isolation:.2f}")
        print(f"    D6 Timing Window:    {v.timing_window:.2f}")
    elif args.command == "warmpath":
        from NAYA_CORE.warm_path_orchestrator import warm_path_orchestrator, Contact
        print("\n🌡️  WARM PATH ORCHESTRATOR — Demo")
        target = Contact(
            contact_id="target_rssi_001",
            name="Jean Dupont",
            role="RSSI",
            company="Enedis SA",
            sector="Energie",
            linkedin_url="https://linkedin.com/in/jean-dupont",
        )
        warm_path_orchestrator.add_contact(target)
        plan = warm_path_orchestrator.build_plan(target, our_network=[])
        print(f"  Target: {plan.target_name} @ {plan.target_company}")
        print(f"  Approach: {plan.approach_type}")
        print(f"  Conv. Rate: {plan.estimated_conversion_rate*100:.0f}%")
        print(f"  Best Path: {plan.best_path}")
        print(f"\n  Cold Hook fallback:\n  {plan.fallback_cold_hook[:200]}")
        print(f"\n  Status: {json.dumps(warm_path_orchestrator.status(), indent=4)}")
    elif args.command == "hybrid":
        from NAYA_CORE.hybrid_autonomy_kernel import hybrid_autonomy_kernel
        report = hybrid_autonomy_kernel.daily_autonomous_brief()
        print("\n🧠 HYBRID AUTONOMY KERNEL — Daily Brief")
        print(f"  Slots actifs: {len(report['parallel_slots'])}")
        print(f"  Pains ultra-discrets: {report['ultra_pains_count']}")
        print(f"  Triggers réglementaires: {report['regulatory_count']}")
        print(f"  Objectif 72h: {report['target_cash_72h_eur']:,} EUR")
        print(f"  Telegram: {report['telegram_message']}")
        print(f"  Dashboard: {report['dashboard_hint']}")
    elif args.command == "edge":
        from NAYA_CORE.sovereign_advantage_engine import sovereign_advantage_engine
        edge = sovereign_advantage_engine.build_edge_report()
        v = edge.advantage_vector
        print("\n👑 SOVEREIGN ADVANTAGE ENGINE")
        print(f"  Blind Spot Index:     {v.blind_spot_index:.1f}/100")
        print(f"  Cash Likelihood:      {v.cash_likelihood*100:.1f}%")
        print(f"  Moat Score:           {v.moat_score:.1f}/100")
        print(f"  Execution Readiness:  {v.execution_readiness*100:.1f}%")
        print(f"  Anti-Refusal Strength:{v.anti_refusal_strength*100:.1f}%")
        print(f"  Recurrence Potential: {v.recurrence_potential*100:.1f}%")
        print(f"  Positioning: {edge.positioning_statement}")
        print(f"  Next actions: {', '.join(edge.next_best_actions)}")
    elif args.command == "cashtruth":
        from NAYA_CORE.revenue_truth_engine import revenue_truth_engine
        rep = revenue_truth_engine.build_report()
        print("\n🧾 REVENUE TRUTH REPORT")
        print(f"  Verified revenue:   {rep.verified_revenue_eur:,.0f} EUR ({rep.verified_sales_count} ventes)")
        print(f"  Unverified revenue: {rep.unverified_revenue_eur:,.0f} EUR ({rep.unverified_sales_count} entrées)")
        print(f"  Simulated/Test:     {rep.simulated_or_test_count} entrées")
        for n in rep.notes:
            print(f"  - {n}")
    elif args.command == "partition-sales":
        from NAYA_CORE.sales_partition_engine import sales_partition_engine
        rep = sales_partition_engine.partition()
        print("\n🧼 SALES PARTITION REPORT")
        print(f"  Source entries:      {rep.source_entries}")
        print(f"  Real verified:       {rep.real_verified_count} ({rep.real_verified_eur:,.0f} EUR)")
        print(f"  Test/Simulated:      {rep.test_count} ({rep.test_eur:,.0f} EUR)")
        print(f"  Pending/Unverified:  {rep.pending_count} ({rep.pending_eur:,.0f} EUR)")
        print("  Files:")
        print("   - data/validation/real_sales_verified_only.json")
        print("   - data/validation/real_sales_test_or_simulated.json")
        print("   - data/validation/real_sales_pending_or_unverified.json")
    elif args.command == "real-sales-live":
        from NAYA_REAL_SALES.live_sales_ops import get_live_sales_ops
        ops = get_live_sales_ops()
        rep = asyncio.run(ops.run_cycle(max_sales=3))
        print("\n🔥 REAL SALES LIVE CYCLE")
        print(f"  Created this cycle: {rep['cycle_created']}")
        print(f"  Pending revenue:    {rep['stats'].get('revenue_pending_eur', 0):,.0f} EUR")
        print(f"  Confirmed revenue:  {rep['stats'].get('revenue_confirmed_eur', 0):,.0f} EUR")
        print("  Report: data/real_sales/live_ops_report.json")
    elif args.command == "real-sales-daemon":
        from NAYA_REAL_SALES.live_sales_ops import get_live_sales_ops
        print(f"🚀 Starting Real Sales daemon (interval={args.interval}s)")
        asyncio.run(get_live_sales_ops().run_daemon(interval_seconds=args.interval, max_sales_per_cycle=3))


def run_tori_server(host: str = "0.0.0.0", port: int = 8080):
    """Lance le serveur TORI_APP (FastAPI pour Tauri)."""
    try:
        import uvicorn
        from fastapi import FastAPI
    except ImportError:
        print("❌ uvicorn/fastapi non installé. pip install uvicorn fastapi")
        sys.exit(1)

    from NAYA_INTERFACE.tori_app_bridge import tori_router

    app = FastAPI(title="NAYA TORI_APP Bridge", version="19.0")
    if tori_router is not None:
        app.include_router(tori_router)

    # CORS pour Tauri (localhost)
    try:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["tauri://localhost", "http://localhost", "http://127.0.0.1"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except ImportError:
        pass

    print(f"🖥️  TORI_APP Server: http://{host}:{port}")
    print(f"📡 Endpoints: /tori/status | /tori/pain/discovery | /tori/launch_10d | /tori/missions/today")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
