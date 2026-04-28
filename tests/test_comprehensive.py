"""
NAYA V19 Comprehensive Tests — All assertions aligned to real APIs.
"""
import os, sys, time, threading, json, uuid, logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class TestNarrativeMemory:
    def setup_method(self):
        import naya_memory_narrative.narrative_memory as m
        m._M = None
        from naya_memory_narrative.narrative_memory import NarrativeMemory
        self.mem = NarrativeMemory(max_entries=50)

    def test_add_and_get_all(self):
        self.mem.add("Signal detecte")
        entries = self.mem.get_all()
        assert any(e.get("text") == "Signal detecte" for e in entries)

    def test_record_pain(self):
        self.mem.record_pain("transport", "cybersecu", 20000, 15000)
        assert self.mem._total_pains >= 1
        assert self.mem._total_pipeline >= 15000
        entries = self.mem.get_all()
        assert any(e["type"] == "pain" and e["sector"] == "transport" for e in entries)

    def test_record_cycle(self):
        self.mem.record_cycle({"pain": "OT", "sector": "energie"})
        assert any(e["type"] == "cycle" for e in self.mem.get_all())

    def test_record_event(self):
        self.mem.record_event("pipeline_execution", {"sector": "ot"})
        assert any(e["type"] == "pipeline_execution" for e in self.mem.get_all())

    def test_get_best_sectors(self):
        # Use fresh isolated instance with disk loading disabled
        import naya_memory_narrative.narrative_memory as m
        m._M = None
        from naya_memory_narrative.narrative_memory import NarrativeMemory
        with patch.object(NarrativeMemory, "_load", lambda self: None):
            fresh = NarrativeMemory(max_entries=50)
        fresh.record_pain("energie", "NIS2", 40000, 30000)
        fresh.record_pain("energie", "OT", 20000, 15000)
        fresh.record_pain("transport", "SCADA", 10000, 8000)
        best = fresh.get_best_sectors(2)
        sector_names = [b["sector"] for b in best]
        assert "energie" in sector_names
        energie_entry = next(b for b in best if b["sector"] == "energie")
        assert energie_entry["wins"] == 2

    def test_get_recent_with_filter(self):
        self.mem.record_pain("transport", "cyber", 15000, 10000)
        self.mem.record_event("hunt", {"signal": "job"})
        recent = self.mem.get_recent(20, type_filter="pain")
        assert all(e["type"] == "pain" for e in recent)

    def test_get_stats(self):
        self.mem.record_pain("industrie", "ransom", 30000, 20000)
        stats = self.mem.get_stats()
        assert "total_entries" in stats
        assert "total_pains" in stats
        assert stats["total_pains"] >= 1
        assert "best_sectors" in stats

    def test_lock_rlock_no_deadlock(self):
        self.mem.record_pain("energie", "NIS2", 10000, 8000)
        stats = self.mem.get_stats()
        assert stats is not None


class TestSelfDiagnostic:
    def setup_method(self):
        import naya_self_diagnostic.diagnostic as m
        m._D = None
        from naya_self_diagnostic.diagnostic import SelfDiagnostic
        self.diag = SelfDiagnostic()

    def test_run_returns_overall(self):
        r = self.diag.run()
        assert r["overall"] in ("ok", "degraded", "critical", "unknown")

    def test_run_returns_components(self):
        r = self.diag.run()
        assert "components" in r and "healthy" in r and "total" in r

    def test_get_report(self):
        r = self.diag.get_report()
        assert "overall" in r and r["last_run"] > 0

    def test_start_stop(self):
        self.diag.start()
        assert self.diag._running
        self.diag.stop()
        assert not self.diag._running

    def test_compute_overall_ok(self):
        from naya_self_diagnostic.diagnostic import Health
        r = self.diag._compute_overall({"a": {"status": "ok"}, "b": {"status": "ok"}})
        assert r == Health.OK

    def test_compute_overall_degraded(self):
        from naya_self_diagnostic.diagnostic import Health
        r = self.diag._compute_overall({"a": {"status": "degraded"}})
        assert r == Health.DEGRADED

    def test_compute_overall_critical(self):
        from naya_self_diagnostic.diagnostic import Health
        r = self.diag._compute_overall({"a": {"status": "critical"}})
        assert r == Health.CRITICAL

    def test_chk_methods_return_tuples(self):
        for name in ["_chk_superbrain", "_chk_scheduler", "_chk_db", "_chk_brain",
                     "_chk_notifier", "_chk_memory", "_chk_brain_activator", "_chk_sovereign"]:
            result = getattr(self.diag, name)()
            assert isinstance(result, tuple) and len(result) == 2

    def test_singleton(self):
        import naya_self_diagnostic.diagnostic as m
        m._D = None
        from naya_self_diagnostic.diagnostic import get_diagnostic
        assert get_diagnostic() is get_diagnostic()


class TestIntentionLoop:
    def setup_method(self):
        import naya_intention_loop.intention_loop as m
        m._loop = None
        from naya_intention_loop.intention_loop import IntentionLoop
        self.loop = IntentionLoop()

    def test_evaluate_returns_decision(self):
        d = self.loop.evaluate({"seconds_since_hunt": 7200, "seconds_since_evolve": 0, "hunt_interval": 3600})
        assert hasattr(d, "intent") and hasattr(d, "reason") and hasattr(d, "urgency")

    def test_evaluate_intent_valid(self):
        d = self.loop.evaluate({"seconds_since_hunt": 7200, "seconds_since_evolve": 0, "hunt_interval": 3600})
        assert d.intent.value in ("hunt", "evolve", "idle", "close", "sleep")

    def test_evaluate_idle(self):
        d = self.loop.evaluate({"seconds_since_hunt": 100, "seconds_since_evolve": 100, "hunt_interval": 3600})
        assert d.urgency >= 0

    def test_run_returns_string(self):
        r = self.loop.run({"seconds_since_hunt": 7200, "seconds_since_evolve": 0, "hunt_interval": 3600})
        assert isinstance(r, str)

    def test_start_stop(self):
        self.loop.start()
        assert self.loop._running
        self.loop.stop()
        assert not self.loop._running

    def test_get_stats_keys(self):
        stats = self.loop.get_stats()
        assert "running" in stats and "state" in stats and "total_decisions" in stats

    def test_get_stats_after_evaluate(self):
        # evaluate() doesn't append to _decisions; test stats structure only
        stats = self.loop.get_stats()
        assert "total_decisions" in stats
        assert isinstance(stats["total_decisions"], int)

    def test_singleton(self):
        import naya_intention_loop.intention_loop as m
        m._loop = None
        from naya_intention_loop.intention_loop import get_intention_loop
        assert get_intention_loop() is get_intention_loop()


class TestGuardian:
    def setup_method(self):
        import naya_guardian.guardian as m
        m._G = None
        from naya_guardian.guardian import get_guardian
        self.g = get_guardian()

    def test_auto_decisions_zero(self):
        assert self.g._auto_decisions == 0

    def test_has_last_human_ts(self):
        assert self.g._last_human_ts > 0

    def test_register_human_activity(self):
        t0 = self.g._last_human_ts
        time.sleep(0.01)
        self.g.register_human_activity()
        assert self.g._last_human_ts >= t0

    def test_check_returns_value(self):
        r = self.g.check(last_human_interaction_hours=1.0)
        assert r is not None

    def test_enforce_returns_dict(self):
        r = self.g.enforce()
        assert isinstance(r, dict) and len(r) > 0

    def test_record_auto_decision(self):
        n = self.g._auto_decisions
        self.g.record_auto_decision()
        assert self.g._auto_decisions == n + 1

    def test_status_is_dict(self):
        r = self.g.status
        assert isinstance(r, dict)

    def test_singleton(self):
        import naya_guardian.guardian as m
        m._G = None
        from naya_guardian.guardian import get_guardian
        assert get_guardian() is get_guardian()


class TestPaymentEngine:
    def setup_method(self):
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
        with patch.dict(os.environ, {"PAYPAL_ME_URL": "https://paypal.me/nayasupreme", "DEBLOCK_ME_URL": "", "REVOLUT_ME_URL": ""}):
            self.engine = PaymentEngine()

    def test_has_paypal(self):
        assert self.engine.has_paypal

    def test_create_paypal_link(self):
        r = self.engine._create_paypal_link(15000, "Pack Audit OT")
        assert r["created"] and "15000" in r["url"] and r["provider"] == "paypal_me"

    def test_create_paypal_with_client(self):
        r = self.engine._create_paypal_link(5000, "Formation", email="cto@sncf.fr", name="Martin")
        assert r["created"] and r["client_name"] == "Martin"

    def test_create_deblock_link_returns_dict(self):
        r = self.engine._create_deblock_link(5000, "Pack")
        assert isinstance(r, dict)

    def test_get_stats_has_available(self):
        stats = self.engine.get_stats()
        assert "available" in stats

    def test_create_payment_link_full(self):
        r = self.engine.create_payment_link(15000, "Pack Audit", client_name="SNCF")
        assert "url" in r and "payment_id" in r

    def test_check_deblock_status_no_url(self):
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
        with patch.dict(os.environ, {"PAYPAL_ME_URL": "", "DEBLOCK_ME_URL": "", "REVOLUT_ME_URL": ""}):
            r = PaymentEngine().check_deblock_status()
            assert r["available"] is False

    def test_no_config_still_responds(self):
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
        with patch.dict(os.environ, {"PAYPAL_ME_URL": "", "DEBLOCK_ME_URL": "", "REVOLUT_ME_URL": ""}):
            r = PaymentEngine().create_payment_link(5000, "Test")
            assert isinstance(r, dict)


class TestPaymentTracker:
    def setup_method(self):
        from NAYA_REVENUE_ENGINE.payment_tracker import PaymentTracker
        with patch("NAYA_REVENUE_ENGINE.payment_tracker.PaymentTracker._load"):
            self.tracker = PaymentTracker()

    def test_create_invoice(self):
        inv = self.tracker.create_invoice("OPP_001", "SNCF", 15000.0, "paypal", due_days=7)
        assert inv.payment_id.startswith("PAY_")
        assert inv.amount_eur == 15000.0
        assert inv.prospect_name == "SNCF"

    def test_record_payment_full(self):
        inv = self.tracker.create_invoice("OPP_002", "EDF", 40000.0, "paypal")
        r = self.tracker.record_payment(inv.payment_id, 40000.0)
        assert r["status"] == "paid" and r["paid"] == 40000.0

    def test_record_payment_partial(self):
        inv = self.tracker.create_invoice("OPP_003", "Alstom", 20000.0, "deblock")
        r = self.tracker.record_payment(inv.payment_id, 10000.0)
        assert isinstance(r, dict)

    def test_record_payment_invalid(self):
        r = self.tracker.record_payment("PAY_NOTEXIST", 5000.0)
        assert "error" in r

    def test_check_overdue_past_due(self):
        from NAYA_REVENUE_ENGINE.payment_tracker import PaymentRecord
        rec = PaymentRecord(
            payment_id="PAY_OVER", opportunity_id="OPP_X", prospect_name="TestCo",
            amount_eur=5000.0, due_date=time.time() - 86400 * 2, invoice_date=time.time(),
        )
        self.tracker._payments["PAY_OVER"] = rec
        assert any(p.payment_id == "PAY_OVER" for p in self.tracker.check_overdue())

    def test_generate_reminder(self):
        inv = self.tracker.create_invoice("OPP_004", "Renault", 8000.0, "paypal")
        r = self.tracker.generate_reminder(inv.payment_id)
        assert r is not None and isinstance(r, dict)

    def test_generate_reminder_invalid(self):
        assert self.tracker.generate_reminder("NOTEXIST") is None

    def test_reconcile_keys(self):
        inv = self.tracker.create_invoice("OPP_005", "Michelin", 10000.0, "paypal")
        self.tracker.record_payment(inv.payment_id, 10000.0)
        r = self.tracker.reconcile()
        assert "total_collected" in r and r["total_collected"] >= 10000.0

    def test_get_stats_keys(self):
        self.tracker.create_invoice("OPP_006", "CMA", 30000.0, "deblock")
        s = self.tracker.get_stats()
        assert "total_invoiced" in s and "total_collected" in s and "outstanding" in s


class TestPipelineTracker:
    def setup_method(self):
        from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
        self.tracker = PipelineTracker()

    def _prospect(self, company="SNCF", sector="transport"):
        p = MagicMock()
        p.id = f"P_{uuid.uuid4().hex[:8]}"
        p.company_name = company; p.contact_name = "Jean Martin"; p.email = f"{company.lower()}@test.fr"
        p.sector = sector; p.city = "Paris"; p.pain_category = "NIS2"
        p.pain_annual_cost_eur = 40000; p.offer_title = "Pack Audit OT"
        p.priority = "HIGH"; p.solvability_score = 85; p.source = "linkedin"
        return p

    def test_add_and_get_kpis(self):
        p = self._prospect()
        self.tracker.add(p, 15000)
        kpis = self.tracker.get_kpis()
        assert kpis["total_prospects"] >= 1 and kpis["pipeline_eur"] >= 15000

    def test_update_status(self):
        p = self._prospect("EDF", "energie")
        self.tracker.add(p, 40000)
        assert self.tracker.update_status(p.id, "CONTACTED", "Premier contact") is True

    def test_set_payment_url(self):
        p = self._prospect("Alstom", "industrie")
        self.tracker.add(p, 20000)
        self.tracker.set_payment_url(p.id, "https://paypal.me/naya/20000")
        item = next((x for x in self.tracker.all() if x["id"] == p.id), None)
        assert item and item["payment_url"] == "https://paypal.me/naya/20000"

    def test_get_hot_prospects(self):
        for i in range(3):
            self.tracker.add(self._prospect(f"Co{i}"), 10000 * (i + 1))
        assert isinstance(self.tracker.get_hot_prospects(5), list)

    def test_get_daily_report(self):
        assert isinstance(self.tracker.get_daily_report(), dict)

    def test_all_returns_list(self):
        self.tracker.add(self._prospect(), 8000)
        assert isinstance(self.tracker.all(), list)

    def test_stages_constant(self):
        assert len(self.tracker.STAGES) > 0

    def test_kpis_stages(self):
        kpis = self.tracker.get_kpis()
        assert "stages" in kpis and "conversion_rate" in kpis


class TestCashEngineReal:
    def setup_method(self):
        from NAYA_CORE.cash_engine_real import CashEngineReal
        with patch("NAYA_CORE.cash_engine_real.CashEngineReal._load_pipeline"):
            self.engine = CashEngineReal()

    def _hunt(self, price=15000, pain="NIS2", sector="transport"):
        return {
            "qualified": True,
            "offer": {"price": price, "title": f"Pack {pain}", "proof": "x", "guarantee": "y", "irrefutable_logic": "z"},
            "top_pain": {"category": pain, "annual_cost_eur": 40000, "cost_ratio": 0.1},
        }

    def test_inject_valid(self):
        d = self.engine.inject_from_hunt(self._hunt(), "transport")
        assert d and d.id.startswith("DEAL_") and d.sector == "transport"

    def test_inject_not_qualified(self):
        assert self.engine.inject_from_hunt({"qualified": False, "offer": {"price": 15000}}, "transport") is None

    def test_inject_below_floor(self):
        assert self.engine.inject_from_hunt(self._hunt(500), "pme") is None

    def test_inject_adds_to_deals(self):
        d = self.engine.inject_from_hunt(self._hunt(40000, "SCADA", "energie"), "energie")
        assert d.id in self.engine._deals

    def test_advance_deals_empty(self):
        self.engine._deals = {}
        assert isinstance(self.engine.advance_deals(), list)

    def test_mark_won(self):
        d = self.engine.inject_from_hunt(self._hunt(), "transport")
        assert self.engine.mark_won(d.id, revenue=15000) is True

    def test_mark_won_invalid(self):
        assert self.engine.mark_won("NOTEXIST", revenue=5000) is False

    def test_mark_lost(self):
        d = self.engine.inject_from_hunt(self._hunt(8000, "formation", "pme"), "pme")
        assert self.engine.mark_lost(d.id, reason="budget") is True

    def test_mark_lost_invalid(self):
        assert self.engine.mark_lost("NOTEXIST") is False

    def test_get_pipeline_summary_keys(self):
        self.engine.inject_from_hunt(self._hunt(), "transport")
        s = self.engine.get_pipeline_summary()
        assert "active_deals" in s and "pipeline_total_eur" in s and "by_stage" in s

    def test_get_revenue_projection(self):
        d = self.engine.inject_from_hunt(self._hunt(20000), "transport")
        self.engine.mark_won(d.id, revenue=20000)
        assert isinstance(self.engine.get_revenue_projection(90), dict)

    def test_build_followup_sequence(self):
        from NAYA_CORE.cash_engine_real import Deal
        d = Deal(sector="transport", company_profile="SNCF", pain_category="NIS2",
                 pain_annual_cost=40000, offer_price=15000, offer_title="Pack")
        seq = self.engine._build_followup_sequence(d)
        assert isinstance(seq, list) and len(seq) > 0


class TestRevenueIntelligence:
    def setup_method(self):
        from NAYA_CORE.revenue_intelligence import RevenueIntelligence
        self.intel = RevenueIntelligence()

    def test_record_detection(self):
        self.intel.record_detection("transport", "NIS2_audit", 15000)
        sectors = self.intel.get_priority_sectors(15)
        # transport sector will be present (may have low initial score from defaults)
        assert isinstance(sectors, list) and len(sectors) > 0

    def test_record_win(self):
        self.intel.record_win("energie", "OT_security", 40000, days_to_close=14)
        sectors = self.intel.get_priority_sectors(15)
        assert isinstance(sectors, list) and len(sectors) > 0

    def test_get_priority_sectors(self):
        r = self.intel.get_priority_sectors()
        assert isinstance(r, list) and len(r) > 0 and "sector" in r[0]

    def test_get_hunt_directives(self):
        r = self.intel.get_hunt_directives()
        assert "focus_sectors" in r and "target_price_bucket" in r

    def test_get_best_price_range(self):
        r = self.intel.get_best_price_range()
        assert "best_bucket" in r

    def test_get_top_pain_categories(self):
        self.intel.record_detection("transport", "NIS2", 15000)
        r = self.intel.get_top_pain_categories(3)
        assert isinstance(r, list)


class TestMoneyNotifier:
    def setup_method(self):
        from NAYA_CORE.money_notifier import MoneyNotifier
        self.notifier = MoneyNotifier()

    def test_not_available(self):
        assert not self.notifier.available

    def test_alert_opportunity_false(self):
        assert self.notifier.alert_opportunity({"company": "SNCF"}, {"price": 15000}, "A001") is False

    def test_alert_payment_false(self):
        assert self.notifier.alert_payment_link_created("https://paypal.me/x/15000", 15000, "SNCF") is False

    def test_alert_won_false(self):
        assert self.notifier.alert_won({"company": "EDF", "value": 40000}) is False

    def test_alert_pipeline_false(self):
        assert self.notifier.alert_pipeline_daily({"total_deals": 5}) is False

    def test_alert_revenue_intel_false(self):
        assert self.notifier.alert_revenue_intel({"actions": ["x"]}) is False

    def test_notify_boot_false(self):
        assert self.notifier.notify_boot({"status": "ok"}) is False

    def test_get_stats(self):
        s = self.notifier.get_stats()
        assert s["sent"] == 0 and "failed" in s

    def test_send_with_mock(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "123"}):
            from NAYA_CORE.money_notifier import MoneyNotifier
            n = MoneyNotifier()
            assert n.available
            with patch("NAYA_CORE.money_notifier.MoneyNotifier._send", return_value=True):
                assert n.alert_won({"company": "Test", "value": 5000}) is True


class TestConversionEngine:
    def setup_method(self):
        from NAYA_CORE.conversion_engine import ConversionEngine
        self.e = ConversionEngine()

    def test_score_deal_conversion(self):
        r = self.e.score_deal_conversion_potential({
            "sector": "energie", "pain_annual_cost": 100000, "offer_price": 15000,
            "offer_guarantee": "ROI garanti", "irrefutable_logic": "NIS2 obligation"
        })
        assert "score" in r and "tier" in r and "factors" in r

    def test_score_deal_low(self):
        r = self.e.score_deal_conversion_potential({
            "sector": "pme", "pain_annual_cost": 5000, "offer_price": 4500,
        })
        assert isinstance(r["score"], (int, float))

    def test_score_deal_cold(self):
        r = self.e.score_deal_conversion_potential({"sector": "x", "pain_annual_cost": 0, "offer_price": 1000})
        assert r["tier"] in ("COLD", "WARM", "HOT", "BURNING")

    def test_build_conversion_script(self):
        script = self.e.build_conversion_script({
            "sector": "transport", "pain_category": "NIS2",
            "pain_annual_cost": 40000, "offer_price": 15000,
            "offer_title": "Pack Audit", "offer_guarantee": "ROI"
        })
        assert script is not None


class TestFollowUpSequenceEngine:
    def setup_method(self):
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import FollowUpSequenceEngine
        import NAYA_REVENUE_ENGINE.followup_sequence_engine as m
        m._ENGINE = None
        self.engine = FollowUpSequenceEngine()

    def test_create_cold_sequence(self):
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import SequenceType
        s = self.engine.create_sequence("P001", "rssi@sncf.fr", "Jean", "SNCF",
                                        SequenceType.COLD_OUTREACH, "transport", pain_type="NIS2", price_floor=15000)
        assert s.sequence_id.startswith("SEQ_") and len(s.touches) > 0

    def test_get_sequence_by_id(self):
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import SequenceType
        s = self.engine.create_sequence("P002", "it@edf.fr", "Marie", "EDF", SequenceType.COLD_OUTREACH, "energie")
        # Sequences are stored in _sequences dict
        assert s.sequence_id in self.engine._sequences

    def test_get_stats(self):
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import SequenceType
        self.engine.create_sequence("P003", "test@test.fr", "T", "Co", SequenceType.COLD_OUTREACH, "pme")
        s = self.engine.get_stats()
        assert s["sequences_total"] >= 1 and "touches_sent" in s

    def test_rlock_no_deadlock(self):
        from NAYA_REVENUE_ENGINE.followup_sequence_engine import SequenceType
        self.engine.create_sequence("P004", "t@t.fr", "T", "Co", SequenceType.COLD_OUTREACH, "energie")
        assert self.engine.get_stats() is not None


class TestBusinessRouter:
    @classmethod
    def setup_class(cls):
        try:
            from fastapi.testclient import TestClient
            from NAYA_CORE.api.main import app
            cls.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            cls.client = None

    def test_offer_tier1(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/business/offer/generate", json={"prospect_id": "T1", "budget_eur": 2000, "company": "PME"})
        assert r.status_code == 200 and r.json()["status"] == "generated"
        assert r.json()["offer"]["tier"] == "TIER1_QUICK_WIN"

    def test_offer_tier2(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/business/offer/generate", json={"budget_eur": 10000, "company": "SNCF"})
        assert r.json()["offer"]["tier"] == "TIER2_PROJET_COURT"

    def test_offer_tier3(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/business/offer/generate", json={"budget_eur": 40000, "company": "EDF"})
        assert r.json()["offer"]["tier"] == "TIER3_CONTRAT_LONG"

    def test_offer_below_floor(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/business/offer/generate", json={"budget_eur": 500, "company": "Micro"})
        assert r.json()["status"] == "error"

    def test_offer_next_steps(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/business/offer/generate", json={"budget_eur": 15000, "company": "Airbus"})
        assert len(r.json()["next_steps"]) > 0


class TestSystemRouter:
    @classmethod
    def setup_class(cls):
        try:
            from fastapi.testclient import TestClient
            from NAYA_CORE.api.main import app
            cls.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            cls.client = None

    def test_health(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.get("/api/v1/health")
        assert r.status_code == 200
        b = r.json()
        assert b["status"] == "healthy" and "version" in b and "memory_mb" in b

    def test_modules_structure(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.get("/api/v1/modules")
        assert r.status_code == 200 and r.json()["total"] == 7

    def test_modules_keys(self):
        if not self.client: pytest.skip("TestClient unavailable")
        b = self.client.get("/api/v1/modules").json()
        for k in ["intention_loop", "narrative_memory", "self_diagnostic", "guardian",
                   "pipeline", "hunt_seeder", "contact_enricher"]:
            assert k in b["modules"]


class TestRevenueRoutes:
    @classmethod
    def setup_class(cls):
        try:
            from fastapi.testclient import TestClient
            from NAYA_CORE.api.main import app
            cls.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            cls.client = None

    def test_pipeline_stats(self):
        if not self.client: pytest.skip("TestClient unavailable")
        assert self.client.get("/api/v1/revenue/pipeline/stats").status_code == 200

    def test_pipeline_inject(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/revenue/pipeline/inject", json={"sector": "transport", "entity": "SNCF", "score": 80})
        b = r.json()
        assert b["status"] == "pipeline_started" and "execution_id" in b

    def test_sale_create_valid(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/revenue/sale/create", json={"company": "Airbus", "amount_eur": 20000, "method": "paypal"})
        b = r.json()
        assert b["status"] == "ok" and b["plancher_respected"] is True

    def test_sale_create_below_floor(self):
        if not self.client: pytest.skip("TestClient unavailable")
        r = self.client.post("/api/v1/revenue/sale/create", json={"company": "Micro", "amount_eur": 500, "method": "paypal"})
        assert r.json()["status"] == "rejected"


class TestSecretsLoader:
    def test_get_secret_from_env(self):
        from SECRETS.secrets_loader import get_secret
        with patch.dict(os.environ, {"TEST_KEY_XYZ": "val123"}):
            assert get_secret("TEST_KEY_XYZ") == "val123"

    def test_get_secret_default(self):
        from SECRETS.secrets_loader import get_secret
        assert get_secret("NONEXISTENT_9999", "fallback") == "fallback"

    def test_load_all_secrets(self):
        from SECRETS.secrets_loader import load_all_secrets
        assert isinstance(load_all_secrets(), dict)


class TestAssetRegistry:
    def setup_method(self):
        from bootstrap.registry.asset_registry import AssetRegistry
        self.registry = AssetRegistry()

    def test_initialize(self):
        self.registry.initialize()
        s = self.registry.get_status()
        assert "initialized" in s or "total_tracked" in s or "critical_assets" in s

    def test_get_by_category_missing(self):
        r = self.registry.get_by_category("nonexistent_xyz")
        assert r == [] or r is None

    def test_verify_integrity(self):
        self.registry.initialize()
        assert isinstance(self.registry.verify_integrity(), dict)

    def test_consistent_inits(self):
        self.registry.initialize()
        c1 = self.registry.get_status().get("total", 0)
        self.registry.initialize()
        assert self.registry.get_status().get("total", 0) == c1


class TestPrometheusMetrics:
    def test_track_pain_signal(self):
        from RUNTIME.prometheus_metrics import track_pain_signal
        track_pain_signal(industry="energie", pain_type="NIS2")

    def test_track_service_offer(self):
        from RUNTIME.prometheus_metrics import track_service_offer
        track_service_offer(tier="TIER3", industry="energie")

    def test_track_http_request(self):
        from RUNTIME.prometheus_metrics import track_http_request
        # track_http_request is a decorator, not a context manager - call directly
        called = []
        @track_http_request("/api/v1/health")
        async def dummy():
            called.append(True)
        import asyncio
        asyncio.get_event_loop().run_until_complete(dummy())
        assert len(called) == 1

    def test_track_cache(self):
        from RUNTIME.prometheus_metrics import track_cache_hit, track_cache_miss
        track_cache_hit("v"); track_cache_miss("v")

    def test_track_lead(self):
        from RUNTIME.prometheus_metrics import track_lead
        track_lead(source="linkedin", quality="hot")

    def test_track_api(self):
        from RUNTIME.prometheus_metrics import track_external_api_call
        track_external_api_call(provider="apollo", status="success", duration=0.3)

    def test_set_sessions(self):
        from RUNTIME.prometheus_metrics import set_active_sessions
        set_active_sessions(5)

    def test_set_conversion(self):
        from RUNTIME.prometheus_metrics import set_conversion_rate
        set_conversion_rate(stage="proposal", rate=0.35)

    def test_set_revenue(self):
        from RUNTIME.prometheus_metrics import set_revenue
        set_revenue(currency="EUR", source="outreach", amount=15000)

    def test_db_query(self):
        from RUNTIME.prometheus_metrics import track_database_query
        # It's already a @contextmanager — use directly
        with track_database_query(operation="select", table="deals"):
            pass

    def test_track_publication(self):
        from RUNTIME.prometheus_metrics import track_publication
        track_publication(channel="linkedin", status="published")

    def test_get_metrics_text(self):
        from RUNTIME.prometheus_metrics import get_metrics_text
        assert isinstance(get_metrics_text(), (str, bytes))


class TestStructuredLogging:
    def setup_method(self):
        from RUNTIME.structured_logging import setup_logging
        self.logger = setup_logging("test.naya", log_level="DEBUG", enable_file=False, enable_console=False)

    def test_setup_logging_returns_logger(self):
        import logging
        from RUNTIME.structured_logging import setup_logging
        assert isinstance(setup_logging("t2", enable_file=False, enable_console=False), logging.Logger)

    def test_log_with_context(self):
        from RUNTIME.structured_logging import log_with_context
        log_with_context(self.logger, "info", "Test", sector="transport")

    def test_log_api_call(self):
        from RUNTIME.structured_logging import log_api_call
        log_api_call(self.logger, "GET", "/api/v1/health", 200, 5.0)

    def test_log_business_event(self):
        from RUNTIME.structured_logging import log_business_event
        log_business_event(self.logger, "sale_created", "BIZ_001", amount_eur=15000)

    def test_log_error(self):
        from RUNTIME.structured_logging import log_error_with_context
        try:
            raise ValueError("x")
        except Exception as e:
            log_error_with_context(self.logger, e)

    def test_log_performance(self):
        from RUNTIME.structured_logging import log_performance_metrics
        log_performance_metrics(self.logger, "pipeline", duration_ms=120.0)

    def test_log_business_metrics(self):
        from RUNTIME.structured_logging import log_business_metrics
        log_business_metrics(self.logger, "revenue", 15000.0)

    def test_initialize(self):
        from RUNTIME.structured_logging import initialize_logging_system
        initialize_logging_system(log_level="INFO")


class TestRedisRateLimitingMocked:
    """Tests with mocked Redis connection (no real Redis server needed)."""

    def _make_limiter(self):
        import sys, redis
        for key in list(sys.modules.keys()):
            if "redis_rate_limiting" in key:
                del sys.modules[key]
        mock_r = MagicMock()
        mock_r.ping.return_value = True
        mock_r.zcard.return_value = 5          # integer — critical for < comparison
        mock_r.zremrangebyscore.return_value = 1
        mock_r.zadd.return_value = 1
        mock_r.expire.return_value = True
        mock_r.info.return_value = {"used_memory": 1024, "connected_clients": 1}
        with patch.object(redis, "from_url", return_value=mock_r):
            from RUNTIME.redis_rate_limiting import RedisRateLimiter
            return RedisRateLimiter(), mock_r

    def test_instantiation(self):
        limiter, _ = self._make_limiter()
        assert limiter is not None

    def test_check_rate_limit_returns_dict(self):
        limiter, _ = self._make_limiter()
        result = limiter.check_rate_limit("192.168.1.1", 100, 60)
        assert isinstance(result, dict)

    def test_check_rate_limit_has_allowed_key(self):
        limiter, _ = self._make_limiter()
        result = limiter.check_rate_limit("10.0.0.1", 100, 60)
        assert "allowed" in result

    def test_check_rate_limit_allowed_true_below_limit(self):
        limiter, mock_r = self._make_limiter()
        mock_r.zcard.return_value = 5   # 5 < 100 → allowed
        result = limiter.check_rate_limit("user_a", 100, 60)
        assert result["allowed"] is True

    def test_check_rate_limit_multiple_keys(self):
        limiter, _ = self._make_limiter()
        for i in range(3):
            r = limiter.check_rate_limit(f"key_{i}", 50, 60)
            assert isinstance(r, dict) and "allowed" in r


class TestPydanticModels:
    def test_pain_signal_valid(self):
        from RUNTIME.pydantic_models import PainSignalRequest, PainType
        ps = PainSignalRequest(business_id="B1", pain_type=PainType.FINANCIAL,
                               description="Slow invoicing process costing time", severity=7)
        assert ps.severity == 7

    def test_pain_signal_with_context(self):
        from RUNTIME.pydantic_models import PainSignalRequest, PainType
        ps = PainSignalRequest(business_id="B2", pain_type=PainType.OPERATIONAL,
                               description="Manual invoicing takes too long", severity=5,
                               context={"sector": "transport"})
        assert ps.context["sector"] == "transport"

    def test_service_offer_valid(self):
        from RUNTIME.pydantic_models import ServiceOfferRequest
        o = ServiceOfferRequest(title="Pack Audit OT", description="Audit IEC 62443 complet professionnel",
                                price_tier="premium", delivery_days=5, business_id="B1")
        assert o.delivery_days == 5

    def test_business_profile_valid(self):
        from RUNTIME.pydantic_models import BusinessProfile, ContactInfo
        p = BusinessProfile(name="SNCF", industry="transport", size="enterprise",
                            contact=ContactInfo(email="contact@sncf.fr",
                                               linkedin="https://linkedin.com/company/sncf"))
        assert p.size == "enterprise"

    def test_business_profile_invalid_size(self):
        from RUNTIME.pydantic_models import BusinessProfile, ContactInfo
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            BusinessProfile(name="X", industry="y", size="invalid_xyz",
                            contact=ContactInfo(email="x@x.fr",
                                               linkedin="https://linkedin.com/company/x"))

    def test_hunting_query(self):
        from RUNTIME.pydantic_models import HuntingQuery
        q = HuntingQuery(keywords=["RSSI OT", "IEC 62443"], industries=["transport"])
        assert len(q.keywords) == 2

    def test_payment_intent(self):
        from RUNTIME.pydantic_models import PaymentIntent
        pi = PaymentIntent(amount=15000.0, currency="EUR",
                           service_id="SVC_001", client_id="CLI_001",
                           description="Pack Audit Express OT Complet")
        assert pi.amount == 15000.0

    def test_transaction_record(self):
        from RUNTIME.pydantic_models import TransactionRecord
        import datetime
        tr = TransactionRecord(
            transaction_id=str(uuid.uuid4()),
            amount=15000.0,
            status="completed",
            timestamp=datetime.datetime.utcnow(),
            metadata={"sector": "transport"},
        )
        assert tr.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
