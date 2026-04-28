"""Tests for the 10 NAYA SUPREME unique improvements."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── AM1: Auto-Diagnostic Engine ─────────────────────────────────

def test_diagnostic_engine_creates():
    from NAYA_IMPROVEMENTS.auto_diagnostic_engine import get_diagnostic_engine
    engine = get_diagnostic_engine()
    assert engine is not None


def test_diagnostic_engine_runs():
    from NAYA_IMPROVEMENTS.auto_diagnostic_engine import get_diagnostic_engine
    engine = get_diagnostic_engine()
    result = engine.run_full_diagnostic()
    assert result.overall_score >= 0
    assert result.overall_score <= 100
    assert result.overall_status in ("healthy", "degraded", "critical")
    assert len(result.modules) > 0


def test_diagnostic_engine_trend():
    from NAYA_IMPROVEMENTS.auto_diagnostic_engine import get_diagnostic_engine
    engine = get_diagnostic_engine()
    engine.run_full_diagnostic()
    trend = engine.get_trend()
    assert "trend" in trend
    assert "scores" in trend


# ── AM2: Revenue Forecaster ─────────────────────────────────────

def test_forecaster_creates():
    from NAYA_IMPROVEMENTS.revenue_forecaster import get_revenue_forecaster
    f = get_revenue_forecaster()
    assert f is not None


def test_forecaster_default_pipeline():
    from NAYA_IMPROVEMENTS.revenue_forecaster import get_revenue_forecaster
    f = get_revenue_forecaster()
    result = f.forecast()
    assert result.monte_carlo_p10 >= 0
    assert result.monte_carlo_p50 >= result.monte_carlo_p10
    assert result.monte_carlo_p90 >= result.monte_carlo_p50
    assert len(result.scenarios) == 3
    labels = [s.label for s in result.scenarios]
    assert "pessimiste" in labels
    assert "realiste" in labels
    assert "optimiste" in labels


def test_forecaster_custom_pipeline():
    from NAYA_IMPROVEMENTS.revenue_forecaster import get_revenue_forecaster
    f = get_revenue_forecaster()
    pipeline = [
        {"amount": 10000, "stage": "negotiation", "company": "Test Corp"},
        {"amount": 5000, "stage": "contract", "company": "Test Ltd"},
    ]
    result = f.forecast(pipeline=pipeline)
    assert result.pipeline_value == 15000
    assert result.weighted_pipeline > 0


def test_forecaster_insights():
    from NAYA_IMPROVEMENTS.revenue_forecaster import get_revenue_forecaster
    f = get_revenue_forecaster()
    result = f.forecast(pipeline=[])
    assert any("Pipeline vide" in i for i in result.insights)


# ── AM3: Smart Retry Engine ─────────────────────────────────────

def test_smart_retry_creates():
    from NAYA_IMPROVEMENTS.smart_retry_engine import get_smart_retry
    engine = get_smart_retry()
    assert engine is not None


def test_smart_retry_success():
    from NAYA_IMPROVEMENTS.smart_retry_engine import SmartRetryEngine
    engine = SmartRetryEngine()
    result = engine.execute_with_retry("test_service", lambda: "OK")
    assert result.success is True
    assert result.result == "OK"
    assert result.attempts == 1


def test_smart_retry_with_failures():
    from NAYA_IMPROVEMENTS.smart_retry_engine import SmartRetryEngine
    engine = SmartRetryEngine()
    call_count = [0]
    def flaky():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError("temporary failure")
        return "recovered"
    result = engine.execute_with_retry("flaky_service", flaky, max_retries=3, base_delay=0.01)
    assert result.success is True
    assert result.attempts == 3


def test_smart_retry_circuit_breaker():
    from NAYA_IMPROVEMENTS.smart_retry_engine import SmartRetryEngine, CircuitState
    engine = SmartRetryEngine()
    # Trigger circuit breaker
    for _ in range(6):
        engine.execute_with_retry(
            "bad_service", lambda: (_ for _ in ()).throw(Exception("fail")),
            max_retries=0, base_delay=0.01
        )
    status = engine.get_circuit_status("bad_service")
    assert status["state"] == "open"


def test_smart_retry_fallback():
    from NAYA_IMPROVEMENTS.smart_retry_engine import SmartRetryEngine
    engine = SmartRetryEngine()
    result = engine.execute_with_retry(
        "fail_service",
        lambda: (_ for _ in ()).throw(Exception("always fails")),
        max_retries=1,
        base_delay=0.01,
        fallback=lambda: "fallback_value"
    )
    assert result.success is True
    assert result.result == "fallback_value"


# ── AM4: Prospect Deduplicator ──────────────────────────────────

def test_deduplicator_creates():
    from NAYA_IMPROVEMENTS.prospect_deduplicator import get_deduplicator
    d = get_deduplicator()
    assert d is not None


def test_deduplicator_finds_email_duplicates():
    from NAYA_IMPROVEMENTS.prospect_deduplicator import ProspectDeduplicator
    d = ProspectDeduplicator()
    prospects = [
        {"id": "1", "email": "ceo@example.com", "company": "Example Corp"},
        {"id": "2", "email": "ceo@example.com", "company": "Example Corporation"},
        {"id": "3", "email": "cto@other.com", "company": "Other Corp"},
    ]
    result = d.find_duplicates(prospects)
    assert result.duplicates_found == 1
    assert result.unique_prospects == 2


def test_deduplicator_no_duplicates():
    from NAYA_IMPROVEMENTS.prospect_deduplicator import ProspectDeduplicator
    d = ProspectDeduplicator()
    prospects = [
        {"id": "1", "email": "a@a.com", "company": "A"},
        {"id": "2", "email": "b@b.com", "company": "B"},
    ]
    result = d.find_duplicates(prospects)
    assert result.duplicates_found == 0


# ── AM5: Offer A/B Optimizer ────────────────────────────────────

def test_ab_optimizer_creates():
    from NAYA_IMPROVEMENTS.offer_ab_optimizer import get_ab_optimizer
    opt = get_ab_optimizer()
    assert opt is not None


def test_ab_optimizer_assigns_variant():
    from NAYA_IMPROVEMENTS.offer_ab_optimizer import OfferABOptimizer
    opt = OfferABOptimizer()
    result = opt.get_variant_for_prospect("energy", "P001")
    assert "variant" in result
    assert "template" in result
    assert "source" in result


def test_ab_optimizer_records_events():
    from NAYA_IMPROVEMENTS.offer_ab_optimizer import OfferABOptimizer
    opt = OfferABOptimizer()
    opt.record_event("energy", "control", "sent")
    opt.record_event("energy", "control", "replied")
    results = opt.get_experiment_results("energy")
    assert results["sector"] == "energy"
    assert "control" in results["variants"]


# ── AM6: Deal Temperature Alerts ────────────────────────────────

def test_deal_temperature_creates():
    from NAYA_IMPROVEMENTS.deal_temperature_alerts import get_deal_temperature
    dt = get_deal_temperature()
    assert dt is not None


def test_deal_temperature_hot_deal():
    from NAYA_IMPROVEMENTS.deal_temperature_alerts import DealTemperatureAlerts
    dt = DealTemperatureAlerts()
    dt.register_deal("D1", "Hot Corp", 5000, "negotiation")
    dt.record_activity("D1", "email_replied")
    dt.record_activity("D1", "meeting")
    alerts = dt.check_temperatures()
    # Active deal should not generate cooling alerts
    dashboard = dt.get_dashboard()
    assert dashboard["total_deals"] == 1


def test_deal_temperature_cold_deal():
    from NAYA_IMPROVEMENTS.deal_temperature_alerts import DealTemperatureAlerts, DealState
    dt = DealTemperatureAlerts()
    dt.register_deal("D2", "Cold Corp", 8000)
    # Simulate old last_activity
    dt._deals["D2"].last_activity = time.time() - 86400 * 20  # 20 days ago
    alerts = dt.check_temperatures()
    assert len(alerts) > 0
    assert alerts[0].company == "Cold Corp"


# ── AM7: Competitive Moat Scorer ────────────────────────────────

def test_moat_scorer_creates():
    from NAYA_IMPROVEMENTS.competitive_moat_scorer import get_moat_scorer
    ms = get_moat_scorer()
    assert ms is not None


def test_moat_scorer_energy_sector():
    from NAYA_IMPROVEMENTS.competitive_moat_scorer import CompetitiveMoatScorer
    ms = CompetitiveMoatScorer()
    score = ms.score_prospect("P1", "Energy Corp", "energy_utilities", urgency="high")
    assert score.overall_score > 0
    assert score.moat_level in ("wide", "narrow", "none")
    assert score.pricing_recommendation >= 1000  # Premium floor
    assert len(score.key_advantages) > 0


def test_moat_scorer_pricing_above_floor():
    from NAYA_IMPROVEMENTS.competitive_moat_scorer import CompetitiveMoatScorer
    ms = CompetitiveMoatScorer()
    score = ms.score_prospect("P2", "Small Corp", "healthcare", urgency="low")
    assert score.pricing_recommendation >= 1000  # NAYA premium floor


# ── AM8: Auto-Escalation Engine ─────────────────────────────────

def test_escalation_creates():
    from NAYA_IMPROVEMENTS.auto_escalation_engine import get_escalation_engine
    engine = get_escalation_engine()
    assert engine is not None


def test_escalation_high_value_deal():
    from NAYA_IMPROVEMENTS.auto_escalation_engine import AutoEscalationEngine
    engine = AutoEscalationEngine()
    tickets = engine.evaluate("D1", "Big Corp", 25000, {"stage": "negotiation"})
    assert len(tickets) > 0
    levels = [t.level.value for t in tickets]
    assert "urgent" in levels  # > 20k = urgent


def test_escalation_contract_ready():
    from NAYA_IMPROVEMENTS.auto_escalation_engine import AutoEscalationEngine
    engine = AutoEscalationEngine()
    tickets = engine.evaluate("D2", "Ready Corp", 5000, {"stage": "contract"})
    assert any(t.level.value == "critical" for t in tickets)


def test_escalation_resolve():
    from NAYA_IMPROVEMENTS.auto_escalation_engine import AutoEscalationEngine
    engine = AutoEscalationEngine()
    tickets = engine.evaluate("D3", "Test", 30000)
    assert len(tickets) > 0
    resolved = engine.resolve(tickets[0].ticket_id, "Handled manually")
    assert resolved is True


# ── AM9: Revenue Reconciliation ─────────────────────────────────

def test_reconciliation_creates():
    from NAYA_IMPROVEMENTS.revenue_reconciliation import get_reconciliation_engine
    engine = get_reconciliation_engine()
    assert engine is not None


def test_reconciliation_matching():
    from NAYA_IMPROVEMENTS.revenue_reconciliation import RevenueReconciliationEngine
    engine = RevenueReconciliationEngine()
    engine.register_deal("D1", "Corp A", 5000, "won")
    engine.register_payment("P1", "D1", 5000)
    report = engine.reconcile()
    assert report.total_revenue_expected == 5000
    assert report.health_score >= 90


def test_reconciliation_missing_payment():
    from NAYA_IMPROVEMENTS.revenue_reconciliation import RevenueReconciliationEngine
    engine = RevenueReconciliationEngine()
    engine.register_deal("D2", "Corp B", 10000, "won", closed_at=time.time() - 86400 * 15)
    report = engine.reconcile()
    assert len(report.discrepancies) > 0
    assert any(d.discrepancy_type.value == "deal_without_payment" for d in report.discrepancies)


# ── AM10: System Heartbeat Monitor ──────────────────────────────

def test_heartbeat_creates():
    from NAYA_IMPROVEMENTS.system_heartbeat_monitor import get_heartbeat_monitor
    hb = get_heartbeat_monitor()
    assert hb is not None


def test_heartbeat_alive():
    from NAYA_IMPROVEMENTS.system_heartbeat_monitor import SystemHeartbeatMonitor
    hb = SystemHeartbeatMonitor()
    hb.register_module("test_module")
    hb.beat("test_module")
    statuses = hb.check_all()
    assert statuses["test_module"] == "alive"


def test_heartbeat_dead_module():
    from NAYA_IMPROVEMENTS.system_heartbeat_monitor import SystemHeartbeatMonitor
    hb = SystemHeartbeatMonitor()
    hb.register_module("dead_module", max_silence_seconds=0.1)
    hb._modules["dead_module"].last_beat = time.time() - 100  # Simulate old beat
    statuses = hb.check_all()
    assert statuses["dead_module"] == "dead"


def test_heartbeat_dashboard():
    from NAYA_IMPROVEMENTS.system_heartbeat_monitor import SystemHeartbeatMonitor
    hb = SystemHeartbeatMonitor()
    hb.register_module("mod_a")
    hb.register_module("mod_b")
    hb.beat("mod_a")
    hb.beat("mod_b")
    dashboard = hb.get_dashboard()
    assert dashboard["summary"]["total_modules"] == 2
    assert dashboard["summary"]["alive"] == 2
