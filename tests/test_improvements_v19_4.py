"""
Tests pour les améliorations NAYA Supreme V19.4.
Couvre les 6 GAP resolus + 8 améliorations revenus + 10 améliorations qualité.
"""

import pytest


class TestPredictiveLeadScorer:
    def test_score_prospect(self):
        from NAYA_IMPROVEMENTS.predictive_lead_scorer import (
            PredictiveLeadScorer, ProspectFeatures,
        )
        scorer = PredictiveLeadScorer()
        features = ProspectFeatures(
            company_revenue_eur=50_000_000,
            has_ot_infrastructure=True,
            regulatory_pressure_score=80,
            budget_estimate_eur=25000,
            decision_maker_identified=True,
        )
        result = scorer.score("test_001", features)
        assert 0 <= result.conversion_probability <= 1
        assert result.tier in ("HOT", "WARM", "COLD", "DISCARD")
        assert result.recommended_action

    def test_batch_score(self):
        from NAYA_IMPROVEMENTS.predictive_lead_scorer import (
            PredictiveLeadScorer, ProspectFeatures,
        )
        scorer = PredictiveLeadScorer()
        prospects = {
            "p1": ProspectFeatures(has_ot_infrastructure=True, regulatory_pressure_score=90),
            "p2": ProspectFeatures(has_ot_infrastructure=False, regulatory_pressure_score=10),
        }
        results = scorer.batch_score(prospects)
        assert len(results) == 2
        assert results[0].conversion_probability >= results[1].conversion_probability


class TestNurturingContentEngine:
    def test_generate_sequence(self):
        from NAYA_IMPROVEMENTS.nurturing_content_engine import (
            NurturingContentEngine, PipelineStage,
        )
        engine = NurturingContentEngine()
        seq = engine.generate_sequence(
            "prospect_001", "energie", PipelineStage.AWARENESS,
            "Jean Dupont", "EDF",
        )
        assert seq.total_touches >= 1
        assert len(seq.contents) > 0
        assert seq.estimated_conversion_boost > 0


class TestTimezoneAwareScheduler:
    def test_schedule_action(self):
        from NAYA_IMPROVEMENTS.timezone_aware_scheduler import TimezoneAwareScheduler
        scheduler = TimezoneAwareScheduler()
        action = scheduler.schedule("p001", "email_first_touch", "Europe/Paris")
        assert action.prospect_id == "p001"
        assert action.timezone_name == "Europe/Paris"
        assert action.confidence_score > 0


class TestSemanticResponseAnalyzer:
    def test_analyze_interested(self):
        from NAYA_IMPROVEMENTS.semantic_response_analyzer import SemanticResponseAnalyzer
        analyzer = SemanticResponseAnalyzer()
        result = analyzer.analyze("p001", "Oui ça m'intéresse, pouvez-vous m'en dire plus ?")
        assert result.interest_score > 0.5
        assert result.primary_intent.value == "interested"

    def test_analyze_objection(self):
        from NAYA_IMPROVEMENTS.semantic_response_analyzer import SemanticResponseAnalyzer
        analyzer = SemanticResponseAnalyzer()
        result = analyzer.analyze("p002", "C'est trop cher pour notre budget actuel")
        assert len(result.objections) > 0


class TestRegulatoryWatchdog:
    def test_scan(self):
        from NAYA_IMPROVEMENTS.regulatory_watchdog import RegulatoryWatchdog
        watchdog = RegulatoryWatchdog()
        alerts = watchdog.scan()
        assert len(alerts) > 0
        assert alerts[0].regulation  # first alert should have regulation name

    def test_top_opportunities(self):
        from NAYA_IMPROVEMENTS.regulatory_watchdog import RegulatoryWatchdog
        watchdog = RegulatoryWatchdog()
        top = watchdog.top_opportunities(3)
        assert len(top) == 3


class TestUnifiedKPIDashboard:
    def test_snapshot(self):
        from NAYA_IMPROVEMENTS.unified_kpi_dashboard import UnifiedKPIDashboard
        dashboard = UnifiedKPIDashboard()
        snap = dashboard.snapshot()
        assert snap.timestamp
        assert snap.overall_score >= 0

    def test_executive_summary(self):
        from NAYA_IMPROVEMENTS.unified_kpi_dashboard import UnifiedKPIDashboard
        dashboard = UnifiedKPIDashboard()
        summary = dashboard.get_executive_summary()
        assert "score_global" in summary


class TestRevenueAutopilot:
    def test_register_and_advance(self):
        from NAYA_IMPROVEMENTS.revenue_autopilot import RevenueAutopilot
        autopilot = RevenueAutopilot()
        deal = autopilot.register_deal("p001", "EDF", 10000)
        assert deal.stage.value == "detected"
        autopilot.advance_deal(deal.deal_id)
        updated = autopilot._deals[deal.deal_id]
        assert updated.stage.value == "qualified"

    def test_run_cycle(self):
        from NAYA_IMPROVEMENTS.revenue_autopilot import RevenueAutopilot
        autopilot = RevenueAutopilot()
        autopilot.register_deal("p001", "Total", 15000, confidence=0.8)
        result = autopilot.run_cycle()
        assert result["deals_advanced"] >= 1


class TestInstantProposalGenerator:
    def test_generate_proposal(self):
        from NAYA_IMPROVEMENTS.instant_proposal_generator import InstantProposalGenerator
        gen = InstantProposalGenerator()
        proposal = gen.generate(
            "Jean Dupont", "EDF", "energie",
            "Non-conformité NIS2", 15000,
        )
        assert proposal.total_price_eur >= 1000
        assert len(proposal.sections) >= 2


class TestMultiChannelOptimizer:
    def test_optimize(self):
        from NAYA_IMPROVEMENTS.multi_channel_revenue_optimizer import MultiChannelRevenueOptimizer
        opt = MultiChannelRevenueOptimizer()
        allocations = opt.optimize()
        assert len(allocations) > 0
        total_pct = sum(a.budget_pct for a in allocations)
        assert abs(total_pct - 100) < 1


class TestSmartPricing:
    def test_calculate_price(self):
        from NAYA_IMPROVEMENTS.smart_pricing_engine import SmartPricingEngine
        engine = SmartPricingEngine()
        result = engine.calculate_price(
            "audit_nis2", 12000,
            company_revenue_eur=100_000_000,
            sector="energie",
            urgency="immediate",
        )
        assert result.adjusted_price_eur >= 1000
        assert result.confidence > 0


class TestUpsellEngine:
    def test_analyze_client(self):
        from NAYA_IMPROVEMENTS.upsell_cross_sell_engine import UpsellCrossSellEngine
        engine = UpsellCrossSellEngine()
        opps = engine.analyze_client("client_001", ["security_assessment"])
        assert len(opps) > 0


class TestRecurringRevenue:
    def test_create_subscription(self):
        from NAYA_IMPROVEMENTS.recurring_revenue_manager import RecurringRevenueManager
        manager = RecurringRevenueManager()
        sub = manager.create_subscription("client_001", "professional")
        assert sub.mrr_eur == 1500
        assert sub.status == "active"


class TestPaymentAcceleration:
    def test_create_invoice(self):
        from NAYA_IMPROVEMENTS.payment_acceleration_engine import PaymentAccelerationEngine
        engine = PaymentAccelerationEngine()
        invoice = engine.create_invoice("client_001", 8000)
        assert invoice.amount_eur == 8000
        assert invoice.status == "pending"


class TestMarketExpansion:
    def test_top_markets(self):
        from NAYA_IMPROVEMENTS.market_expansion_engine import MarketExpansionEngine
        engine = MarketExpansionEngine()
        markets = engine.top_markets(3)
        assert len(markets) == 3

    def test_quick_wins(self):
        from NAYA_IMPROVEMENTS.market_expansion_engine import MarketExpansionEngine
        engine = MarketExpansionEngine()
        wins = engine.quick_wins()
        assert all(w.time_to_revenue_months <= 2 for w in wins)


class TestHealthCheckSuite:
    def test_run_all(self):
        from NAYA_IMPROVEMENTS.production_quality.health_check_suite import HealthCheckSuite
        suite = HealthCheckSuite()
        results = suite.run_all()
        assert results["overall_status"] in ("healthy", "degraded", "unhealthy")
        assert len(results["checks"]) > 0


class TestCircuitBreakerV2:
    def test_normal_operation(self):
        from NAYA_IMPROVEMENTS.production_quality.circuit_breaker_v2 import CircuitBreakerV2
        cb = CircuitBreakerV2("test", failure_threshold=3)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_opens_on_failures(self):
        from NAYA_IMPROVEMENTS.production_quality.circuit_breaker_v2 import (
            CircuitBreakerV2, CircuitBreakerOpenError,
        )
        cb = CircuitBreakerV2("test_fail", failure_threshold=2, recovery_timeout_seconds=999)

        def failing_fn():
            raise ValueError("boom")

        for _ in range(2):
            try:
                cb.call(failing_fn)
            except ValueError:
                pass

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: 1)


class TestRateLimiter:
    def test_allows_within_limit(self):
        from NAYA_IMPROVEMENTS.production_quality.rate_limiter import (
            TokenBucketRateLimiter, RateLimitConfig,
        )
        limiter = TokenBucketRateLimiter(RateLimitConfig("test", 5, 60))
        for _ in range(5):
            assert limiter.allow() is True
        assert limiter.allow() is False


class TestDataValidator:
    def test_validate_email(self):
        from NAYA_IMPROVEMENTS.production_quality.data_validator import DataValidator
        v = DataValidator()
        assert v.validate_email("test@example.com").valid is True
        assert v.validate_email("invalid").valid is False

    def test_validate_amount(self):
        from NAYA_IMPROVEMENTS.production_quality.data_validator import DataValidator
        v = DataValidator()
        assert v.validate_amount(5000).valid is True
        assert v.validate_amount(500).valid is False  # Under 1000 EUR floor


class TestDeploymentGate:
    def test_evaluate(self):
        from NAYA_IMPROVEMENTS.production_quality.deployment_gate import DeploymentGate
        gate = DeploymentGate()
        decision = gate.evaluate()
        assert decision.overall_score >= 0
        assert isinstance(decision.allowed, bool)


class TestExistenceContract:
    @staticmethod
    def _load_contract():
        import importlib.util
        import importlib.machinery
        import sys
        loader = importlib.machinery.SourceFileLoader(
            "contrat", "contrat d'existence de NAYA par sa creatrice.txt"
        )
        spec = importlib.util.spec_from_loader("contrat", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["contrat"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_contract_loads(self):
        mod = self._load_contract()
        contract = mod.ExistenceContract()
        assert contract.version == "19.4"
        assert contract.creator.name == "MAMA Stéphanie"
        assert contract.mission.minimum_contract_eur == 1000

    def test_contract_understand(self):
        mod = self._load_contract()
        contract = mod.ExistenceContract()
        text = contract.understand()
        assert "NAYA SUPREME" in text
        assert "MAMA" in text

    def test_action_validation(self):
        mod = self._load_contract()
        contract = mod.ExistenceContract()
        allowed, msg = contract.is_action_allowed("send_offer", {"amount": 5000})
        assert allowed is True
        allowed, msg = contract.is_action_allowed("send_offer", {"amount": 500})
        assert allowed is False
        allowed, msg = contract.is_action_allowed("spam_everyone")
        assert allowed is False
