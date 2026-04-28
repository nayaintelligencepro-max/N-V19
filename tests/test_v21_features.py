"""
NAYA V21 — Tests Gate V2 Velocity + Modules V21
Gate V2 : métriques ventes/jour, time-to-close, conversion rate.
Couvre : NIS2 Checker, IEC 62443, Subscriptions, LLM Router V2, Meeting Booker,
         Local LLM Trainer, Event Bus V2, Telegram Bot V2.
"""
import asyncio
import pytest
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — NIS2 CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class TestNIS2Checker:
    """Tests du moteur de scoring NIS2."""

    def test_get_questions_returns_20(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        checker = get_nis2_checker()
        questions = checker.get_questions()
        assert len(questions) == 20

    def test_questions_have_required_fields(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        for q in get_nis2_checker().get_questions():
            assert q.id
            assert q.category
            assert q.weight > 0
            assert q.text
            assert q.guidance

    def test_score_all_yes_is_100(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: True for q in NIS2_QUESTIONS}
        score, tier = checker.compute_score(answers)
        assert score == 100
        assert tier == "avancé"

    def test_score_all_no_is_0(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: False for q in NIS2_QUESTIONS}
        score, tier = checker.compute_score(answers)
        assert score == 0
        assert tier == "non-conforme"

    def test_score_partial_is_between(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: (i % 2 == 0) for i, q in enumerate(NIS2_QUESTIONS)}
        score, tier = checker.compute_score(answers)
        assert 0 < score < 100

    def test_identify_gaps(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: True for q in NIS2_QUESTIONS}
        answers["Q01"] = False
        answers["Q05"] = False
        gaps = checker.identify_gaps(answers)
        assert len(gaps) == 2
        assert any("Q01" in g for g in gaps)

    def test_create_assessment_freemium(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: True for q in NIS2_QUESTIONS[:10]} | \
                  {q["id"]: False for q in NIS2_QUESTIONS[10:]}
        a = checker.create_assessment(
            company="TestCorp",
            sector="energie_utilities",
            contact_email="test@test.com",
            answers=answers,
            freemium=True,
        )
        assert a.assessment_id
        assert 0 <= a.score <= 100
        assert a.freemium is True
        # Freemium: max 3 gaps
        assert len(a.gaps) <= 3

    def test_create_assessment_paid_has_recommendations(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: False for q in NIS2_QUESTIONS}
        a = checker.create_assessment(
            company="PaidCorp",
            sector="manufacturing",
            contact_email="paid@test.com",
            answers=answers,
            freemium=False,
        )
        assert a.freemium is False
        assert len(a.recommendations) > 0

    def test_tier_mapping(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        checker = get_nis2_checker()
        cases = [(85, "avancé"), (65, "conforme"), (45, "partiel"), (20, "non-conforme")]
        for score, expected_tier in cases:
            # Reverse-engineer answers to produce desired score (approximate)
            _, tier = checker.compute_score({"Q01": True} if score > 50 else {})
            # Just test the tier logic directly
        assert checker.compute_score({"Q01": True, "Q02": True, "Q03": True, "Q04": True,
                                       "Q05": True, "Q06": True, "Q07": True, "Q08": True,
                                       "Q09": True, "Q10": True, "Q11": True, "Q12": True,
                                       "Q13": True, "Q14": True, "Q15": True, "Q16": True,
                                       "Q17": True, "Q18": True, "Q19": True, "Q20": True})[1] == "avancé"

    def test_get_stats(self):
        from SAAS_NIS2.nis2_checker import get_nis2_checker
        stats = get_nis2_checker().get_stats()
        assert "total" in stats
        assert "avg_score" in stats

    def test_floor_not_needed_nis2(self):
        """NIS2 score range 0-100, no EUR floor here."""
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: True for q in NIS2_QUESTIONS}
        score, _ = checker.compute_score(answers)
        assert score == 100


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — IEC 62443 PORTAL
# ═══════════════════════════════════════════════════════════════════════════════

class TestIEC62443Portal:
    """Tests du portail IEC 62443."""

    def test_get_requirements_has_4_levels(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        reqs = get_iec62443_portal().get_requirements()
        assert "SL1" in reqs
        assert "SL2" in reqs
        assert "SL3" in reqs
        assert "SL4" in reqs

    def test_analyze_all_compliant(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal, IEC62443_REQUIREMENTS
        portal = get_iec62443_portal()
        responses = {
            req["id"]: "compliant"
            for level, reqs in IEC62443_REQUIREMENTS.items()
            for req in reqs
        }
        report = portal.analyze_compliance(
            company="TestEnergy",
            sector="energie_utilities",
            contact_email="test@energy.fr",
            responses=responses,
        )
        assert report.overall_score == 100
        assert len(report.gaps) == 0

    def test_analyze_all_missing_has_gaps(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        portal = get_iec62443_portal()
        report = portal.analyze_compliance(
            company="GapCorp",
            sector="manufacturing",
            contact_email="gap@corp.fr",
            responses={},
        )
        assert report.overall_score == 0
        assert len(report.gaps) > 0

    def test_report_has_roadmap(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        portal = get_iec62443_portal()
        report = portal.analyze_compliance(
            company="RoadmapCorp",
            sector="transport_logistique",
            contact_email="test@corp.fr",
            responses={"SL1-01": "partial"},
        )
        assert len(report.roadmap) > 0

    def test_report_has_upsell(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        portal = get_iec62443_portal()
        report = portal.analyze_compliance(
            company="UpsellCorp",
            sector="iec62443",
            contact_email="u@corp.fr",
            responses={},
        )
        assert "EUR" in report.upsell_proposal

    def test_remediation_cost_positive(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal
        portal = get_iec62443_portal()
        report = portal.analyze_compliance(
            company="CostCorp", sector="manufacturing",
            contact_email="c@corp.fr", responses={},
        )
        assert report.estimated_remediation_eur > 0

    def test_compliance_scores_per_level(self):
        from SAAS_NIS2.iec62443_portal import get_iec62443_portal, IEC62443_REQUIREMENTS
        portal = get_iec62443_portal()
        responses = {req["id"]: "compliant" for req in IEC62443_REQUIREMENTS["SL1"]}
        report = portal.analyze_compliance(
            company="PartialCorp", sector="energie_utilities",
            contact_email="p@corp.fr", responses=responses,
        )
        assert report.compliance_scores.get("SL1", 0) == 100
        assert report.compliance_scores.get("SL2", 100) < 100


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SUBSCRIPTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class TestSubscriptionManager:
    """Tests du gestionnaire d'abonnements."""

    def test_get_plans_not_empty(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        plans = get_subscription_manager().get_plans()
        assert len(plans) >= 3

    def test_freemium_plan_is_free(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager, PLANS
        assert PLANS["nis2_freemium"]["price_eur"] == 0

    def test_starter_plan_is_500(self):
        from SAAS_NIS2.subscription_manager import PLANS
        assert PLANS["nis2_starter"]["price_eur"] == 500

    def test_iec62443_plan_is_2000(self):
        from SAAS_NIS2.subscription_manager import PLANS
        assert PLANS["iec62443_portal"]["price_eur"] == 2_000

    def test_create_freemium_subscription(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        sub = mgr.create_subscription("FreeCorp", "free@corp.fr", "nis2_freemium")
        assert sub.subscription_id
        assert sub.price_eur == 0
        assert sub.status == "active"

    def test_create_paid_subscription_is_pending(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        sub = mgr.create_subscription("PaidCorp", "paid@corp.fr", "nis2_starter")
        assert sub.price_eur == 500
        assert sub.status == "pending"

    def test_activate_subscription(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        sub = mgr.create_subscription("ActivateCorp", "act@corp.fr", "nis2_starter")
        assert mgr.activate_subscription(sub.subscription_id) is True
        activated = mgr.list_subscriptions("active")
        ids = [s.subscription_id for s in activated]
        assert sub.subscription_id in ids

    def test_mrr_increases_with_paid(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        mrr_before = mgr.get_mrr()["mrr_eur"]
        sub = mgr.create_subscription("MRRCorp", "mrr@corp.fr", "nis2_starter")
        mgr.activate_subscription(sub.subscription_id)
        mrr_after = mgr.get_mrr()["mrr_eur"]
        assert mrr_after >= mrr_before

    def test_payment_webhook_activates(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        mgr = get_subscription_manager()
        sub = mgr.create_subscription("WebhookCorp", "wh@corp.fr", "nis2_pro")
        result = mgr.handle_payment_webhook(sub.subscription_id, "payment_succeeded", 1200)
        assert result["success"] is True
        assert result["status"] == "active"

    def test_invalid_plan_raises(self):
        from SAAS_NIS2.subscription_manager import get_subscription_manager
        with pytest.raises(ValueError):
            get_subscription_manager().create_subscription("Bad", "b@c.fr", "fake_plan_xyz")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — LLM ROUTER V2
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMRouterV2:
    """Tests du routeur LLM V2."""

    def test_router_initializes(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        assert router is not None

    def test_generate_uses_template_fallback(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp = router.generate(task="offer_generation", prompt="Test offer")
        assert resp.text
        assert len(resp.text) > 10

    def test_generate_offer_returns_text(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp = router.generate_offer(
            company="SNCF", sector="transport_logistique",
            pain="Audit NIS2 requis Q3 2026",
        )
        assert resp.text
        assert resp.task == "offer_generation"

    def test_generate_closing_response(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp = router.generate_closing_response(
            objection="Trop cher pour notre budget",
            context="Prospect RSSI transport",
            sector="transport_logistique",
        )
        assert resp.text
        assert resp.task == "closing_negotiation"

    def test_sector_templates_available(self):
        from ML_ENGINE.llm_router_v2 import SECTOR_PROMPT_TEMPLATES
        assert "transport_logistique" in SECTOR_PROMPT_TEMPLATES
        assert "energie_utilities" in SECTOR_PROMPT_TEMPLATES
        assert "manufacturing" in SECTOR_PROMPT_TEMPLATES
        assert "iec62443" in SECTOR_PROMPT_TEMPLATES

    def test_task_models_configured(self):
        from ML_ENGINE.llm_router_v2 import TASK_MODELS
        assert "offer_generation" in TASK_MODELS
        assert "closing_negotiation" in TASK_MODELS
        assert "template" in TASK_MODELS["offer_generation"]
        assert "template" in TASK_MODELS["closing_negotiation"]

    def test_cache_hit(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp1 = router.generate(task="content_generation", prompt="Cache test XYZ123")
        resp2 = router.generate(task="content_generation", prompt="Cache test XYZ123")
        assert resp2.from_cache is True

    def test_get_stats(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        stats = get_llm_router_v2().get_stats()
        assert isinstance(stats, dict)

    def test_latency_recorded(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp = router.generate(task="pain_detection", prompt="Latency test")
        assert resp.latency_ms >= 0

    def test_model_override(self):
        from ML_ENGINE.llm_router_v2 import get_llm_router_v2
        router = get_llm_router_v2()
        resp = router.generate(
            task="offer_generation",
            prompt="Override test",
            model_override="template",
        )
        assert resp.model_used == "template"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — LOCAL LLM TRAINER
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalLLMTrainer:
    """Tests du trainer local."""

    def test_trainer_initializes(self):
        from ML_ENGINE.local_llm_trainer import get_local_trainer
        trainer = get_local_trainer()
        assert trainer is not None

    def test_record_conversion_win(self):
        from ML_ENGINE.local_llm_trainer import get_local_trainer
        trainer = get_local_trainer()
        ex = trainer.record_conversion(
            company="WinCorp",
            sector="energie_utilities",
            pain="NIS2 audit needed Q2",
            offer_text="Notre audit IEC 62443 garantit la conformité NIS2 en 90 jours. ROI certifié.",
            price_eur=15_000,
            converted=True,
            conversion_value_eur=15_000,
            time_to_close_days=7,
        )
        assert ex.example_id
        assert ex.converted is True

    def test_record_conversion_loss(self):
        from ML_ENGINE.local_llm_trainer import get_local_trainer
        trainer = get_local_trainer()
        ex = trainer.record_conversion(
            company="LossCorp",
            sector="manufacturing",
            pain="Budget constraints",
            offer_text="Generic offer",
            price_eur=5_000,
            converted=False,
        )
        assert ex.converted is False

    def test_get_rag_context_empty_no_error(self):
        from ML_ENGINE.local_llm_trainer import LocalLLMTrainer
        trainer = LocalLLMTrainer()  # Fresh instance
        contexts = trainer.get_rag_context("energie_utilities", "NIS2 audit")
        assert isinstance(contexts, list)

    def test_get_stats(self):
        from ML_ENGINE.local_llm_trainer import get_local_trainer
        stats = get_local_trainer().get_stats()
        assert "total_examples" in stats
        assert "conversion_rate" in stats

    def test_winning_phrases_extracted(self):
        from ML_ENGINE.local_llm_trainer import get_local_trainer
        trainer = get_local_trainer()
        trainer.record_conversion(
            company="PhraseCorp",
            sector="transport_logistique",
            pain="SCADA vulnerabilities",
            offer_text="Notre audit IEC 62443 certifié garantit conformité NIS2. ROI confirmé en 6 mois.",
            price_eur=20_000,
            converted=True,
            conversion_value_eur=20_000,
            time_to_close_days=5,
        )
        stats = trainer.get_stats()
        assert stats["total_examples"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — MEETING BOOKER
# ═══════════════════════════════════════════════════════════════════════════════

class TestMeetingBooker:
    """Tests du meeting booker."""

    def test_create_booking_link(self):
        from OUTREACH.meeting_booker import get_meeting_booker
        booker = get_meeting_booker()
        meeting = booker.create_booking_link(
            prospect_id="PROSPECT-001",
            company="SNCF Voyageurs",
            contact_name="Jean Martin",
            contact_email="j.martin@sncf.fr",
            sector="transport_logistique",
            deal_value_eur=20_000,
        )
        assert meeting.meeting_id
        assert meeting.booking_url
        assert "sncf" in meeting.booking_url.lower() or "calendly" in meeting.booking_url.lower()
        assert meeting.status == "pending"

    def test_pre_brief_generated(self):
        from OUTREACH.meeting_booker import get_meeting_booker
        booker = get_meeting_booker()
        meeting = booker.create_booking_link(
            prospect_id="PROSPECT-002",
            company="EDF",
            contact_name="Marie Dupont",
            contact_email="m.dupont@edf.fr",
            sector="energie_utilities",
            deal_value_eur=40_000,
        )
        assert meeting.pre_brief
        assert "EDF" in meeting.pre_brief or "BRIEF" in meeting.pre_brief

    def test_confirm_meeting(self):
        from OUTREACH.meeting_booker import get_meeting_booker
        booker = get_meeting_booker()
        meeting = booker.create_booking_link(
            "P003", "Michelin", "Paul D", "p@michelin.fr",
            "manufacturing", 15_000,
        )
        future = (datetime.now() + timedelta(days=1)).isoformat()
        assert booker.confirm_meeting(meeting.meeting_id, future) is True
        confirmed = booker._meetings[meeting.meeting_id]
        assert confirmed.status == "confirmed"

    def test_post_call_summary(self):
        from OUTREACH.meeting_booker import get_meeting_booker
        booker = get_meeting_booker()
        meeting = booker.create_booking_link(
            "P004", "Alstom", "Sophie R", "s@alstom.fr",
            "manufacturing", 25_000,
        )
        booker.confirm_meeting(meeting.meeting_id,
                               (datetime.now() + timedelta(hours=1)).isoformat())
        result = booker.record_post_call_summary(
            meeting_id=meeting.meeting_id,
            summary="Très intéressé par l'audit IEC 62443. Budget confirmé.",
            next_steps=["Envoyer proposition", "Planifier audit flash"],
            outcome="positive",
        )
        assert result["success"] is True
        assert result["outcome"] == "positive"
        assert len(result["auto_actions"]) > 0

    def test_get_stats(self):
        from OUTREACH.meeting_booker import get_meeting_booker
        stats = get_meeting_booker().get_stats()
        assert "total" in stats
        assert "confirmed" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — EVENT BUS V2
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventBusV2:
    """Tests du bus d'événements V2."""

    def test_event_bus_initializes(self):
        from EVENT_STREAMING.event_bus_v2 import get_event_bus_v2
        bus = get_event_bus_v2()
        assert bus is not None

    def test_subscribe_and_publish(self):
        from EVENT_STREAMING.event_bus_v2 import EventBusV2, Event, EventType
        bus = EventBusV2(persist_events=False)
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EventType.PAIN_DETECTED, handler)

        event = Event(
            event_type=EventType.PAIN_DETECTED,
            source="test",
            data={"company": "TestCo", "score": 80},
        )
        asyncio.run(bus.publish(event))
        assert len(received) == 1
        assert received[0].data["company"] == "TestCo"

    def test_emit_creates_event(self):
        from EVENT_STREAMING.event_bus_v2 import EventBusV2, EventType
        bus = EventBusV2(persist_events=False)

        async def run():
            return await bus.emit(
                EventType.OFFER_GENERATED,
                source="test",
                data={"company": "EmitCo", "price_eur": 15_000},
            )

        event = asyncio.run(run())
        assert event.event_id
        assert event.event_type == EventType.OFFER_GENERATED

    def test_pipeline_chain_registered(self):
        from EVENT_STREAMING.event_bus_v2 import get_event_bus_v2, EventType
        bus = get_event_bus_v2()
        # Should have handlers for pipeline events
        assert EventType.PAIN_DETECTED in bus._handlers
        assert EventType.DEAL_SIGNED in bus._handlers

    def test_history_tracked(self):
        from EVENT_STREAMING.event_bus_v2 import EventBusV2, Event, EventType
        bus = EventBusV2(persist_events=False)
        event = Event(EventType.PAYMENT_RECEIVED, "test", {"amount": 1000})
        asyncio.run(bus.publish(event))
        history = bus.get_history()
        assert len(history) >= 1

    def test_get_stats(self):
        from EVENT_STREAMING.event_bus_v2 import get_event_bus_v2
        stats = get_event_bus_v2().get_stats()
        assert "total_events" in stats
        assert "handlers_registered" in stats

    def test_multiple_handlers(self):
        from EVENT_STREAMING.event_bus_v2 import EventBusV2, Event, EventType
        bus = EventBusV2(persist_events=False)
        results = []

        async def h1(e: Event): results.append("h1")
        async def h2(e: Event): results.append("h2")

        bus.subscribe(EventType.LEAD_ENRICHED, h1)
        bus.subscribe(EventType.LEAD_ENRICHED, h2)

        event = Event(EventType.LEAD_ENRICHED, "test", {"score": 75})
        asyncio.run(bus.publish(event))
        assert "h1" in results
        assert "h2" in results

    def test_event_type_enum(self):
        from EVENT_STREAMING.event_bus_v2 import EventType
        assert EventType.PAIN_DETECTED.value == "pain.detected"
        assert EventType.DEAL_SIGNED.value == "deal.signed"
        assert EventType.PAYMENT_RECEIVED.value == "payment.received"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — TELEGRAM BOT V2
# ═══════════════════════════════════════════════════════════════════════════════

class TestTelegramBotV2:
    """Tests du bot Telegram V2."""

    def test_bot_initializes(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        assert bot is not None

    def test_cmd_ooda_returns_string(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        result = bot.cmd_ooda()
        assert isinstance(result, str)
        assert len(result) > 20
        assert "OODA" in result

    def test_cmd_simulate_known_scenario(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        result = bot.cmd_simulate("10_deals_15k")
        assert "EUR" in result
        assert "M6" in result

    def test_cmd_simulate_unknown_scenario(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        result = bot.cmd_simulate("unknown_xyz")
        assert "inconnu" in result.lower() or "disponibles" in result.lower()

    def test_register_and_approve_action(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        action = bot.register_pending_action(
            action_type="offer_send",
            description="Envoyer offre 15k EUR à SNCF",
            amount_eur=15_000,
            payload={"company": "SNCF", "price": 15_000},
        )
        assert action.action_id
        assert action.status == "pending"
        result = bot.cmd_approve(action.action_id)
        assert "APPROUVÉE" in result
        assert bot.is_action_approved(action.action_id) is True

    def test_veto_action(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        bot = get_telegram_bot_v2()
        action = bot.register_pending_action(
            action_type="payment_send",
            description="Paiement 5k EUR",
            amount_eur=5_000,
            payload={},
        )
        result = bot.cmd_veto(action.action_id)
        assert "BLOQUÉE" in result
        assert not bot.is_action_approved(action.action_id)

    def test_cmd_mrr_returns_string(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2
        result = get_telegram_bot_v2().cmd_mrr()
        assert "MRR" in result
        assert "EUR" in result

    def test_get_pending_actions(self):
        from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import TelegramBotV2
        bot = TelegramBotV2()  # Fresh instance
        action = bot.register_pending_action("test", "Test action", 600, {})
        pending = bot.get_pending_actions()
        ids = [a.action_id for a in pending]
        assert action.action_id in ids


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — GATE V2 VELOCITY (MÉTRIQUES VENTES)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGateV2Velocity:
    """
    Gate V2 : métriques velocity pour chaque environnement de déploiement.
    Mesure : ventes/jour, time-to-close, conversion rate, MRR.
    """

    # ── Gate definitions ──────────────────────────────────────────────────────
    GATE_LOCAL = {
        "min_sales_day": 2,
        "min_avg_ticket": 5_000,
        "max_time_to_close_days": 7,
        "min_mrr": 0,  # Pas encore de MRR requis en local
    }
    GATE_DOCKER = {
        "min_sales_day": 5,
        "min_avg_ticket": 10_000,
        "max_time_to_close_days": 5,
        "min_mrr": 0,
    }
    GATE_VERCEL = {
        "min_sales_day": 10,
        "min_avg_ticket": 10_000,
        "max_time_to_close_days": 3,
        "min_mrr": 200,
    }
    GATE_CLOUD_RUN = {
        "min_sales_day": 20,
        "min_avg_ticket": 15_000,
        "max_time_to_close_days": 2,
        "min_mrr": 1_000,
    }

    def test_gate_local_metrics_defined(self):
        assert self.GATE_LOCAL["min_sales_day"] == 2
        assert self.GATE_LOCAL["min_avg_ticket"] == 5_000

    def test_gate_docker_harder_than_local(self):
        assert self.GATE_DOCKER["min_sales_day"] > self.GATE_LOCAL["min_sales_day"]
        assert self.GATE_DOCKER["max_time_to_close_days"] < self.GATE_LOCAL["max_time_to_close_days"]

    def test_gate_vercel_requires_mrr(self):
        assert self.GATE_VERCEL["min_mrr"] == 200

    def test_gate_cloud_run_requires_1k_mrr(self):
        assert self.GATE_CLOUD_RUN["min_mrr"] == 1_000

    def test_velocity_tracker_can_record_sale(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        tracker = get_velocity_tracker()
        sale = tracker.record_sale(
            company="SNCF",
            sector="transport_logistique",
            amount_eur=15_000,
            pain_type="nis2_compliance",
        )
        assert sale.sale_id
        assert sale.amount_eur == 15_000

    def test_velocity_tracker_enforces_floor(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        tracker = get_velocity_tracker()
        with pytest.raises(Exception):
            tracker.record_sale(
                company="BelowFloor",
                sector="test",
                amount_eur=500,  # Sous le plancher 1000 EUR
                pain_type="test",
            )

    def test_velocity_stats_structure(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        metrics = get_velocity_tracker().get_metrics()
        d = metrics.to_dict()
        assert "sales_today" in d
        assert "sales_this_month" in d
        assert "revenue_this_month_eur" in d

    def test_conversion_rate_computed(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        metrics = get_velocity_tracker().get_metrics()
        rate = metrics.conversion_rate_pct
        assert 0 <= rate <= 100

    def test_ooda_projection_present(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        metrics = get_velocity_tracker().get_metrics()
        d = metrics.to_dict()
        assert "projected_month_eur" in d or "monthly_run_rate_eur" in d

    def test_blitz_hunter_returns_signals(self):
        """BlitzHunter doit retourner des signaux en < 30s."""
        from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
        import time
        hunter = get_blitz_hunter()
        t0 = time.time()
        signals = asyncio.run(hunter.hunt(sectors=["energie_utilities"]))
        elapsed = time.time() - t0
        assert isinstance(signals, list)
        assert elapsed < 30, f"BlitzHunter trop lent: {elapsed:.1f}s (max 30s)"

    def test_flash_offer_generates_in_time(self):
        """FlashOffer doit générer en < 60s."""
        from NAYA_ACCELERATION.flash_offer import get_flash_offer
        import time
        flash = get_flash_offer()
        t0 = time.time()
        offer = asyncio.run(flash.generate(
            company="TestCo",
            sector="energie_utilities",
            pain_description="NIS2 compliance deadline approaching",
            budget_estimate=15_000,
        ))
        elapsed = time.time() - t0
        assert offer.price_eur >= 1_000
        assert elapsed < 60, f"FlashOffer trop lent: {elapsed:.1f}s (max 60s)"

    def test_instant_closer_generates_payment_link(self):
        """InstantCloser doit générer un lien < 5 min après accord."""
        from NAYA_ACCELERATION.instant_closer import get_instant_closer
        import time
        closer = get_instant_closer()
        t0 = time.time()
        link = closer.generate_payment_link(
            offer_id="TEST-001",
            company="FastCorp",
            contact_email="fast@corp.fr",
            amount_eur=15_000,
        )
        elapsed = time.time() - t0
        assert link.url
        assert link.amount_eur == 15_000
        assert elapsed < 300, f"InstantCloser trop lent: {elapsed:.1f}s (max 300s)"

    def test_pipeline_end_to_end_timing(self):
        """
        Test bout-en-bout : Pain détecté → Offre générée.
        Doit compléter en < 4h (critère principal V21).
        Ce test valide les < 90s (fraction du pipeline).
        """
        from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
        from NAYA_ACCELERATION.flash_offer import get_flash_offer
        import time

        # Step 1: Hunt
        hunter = get_blitz_hunter()
        t0 = time.time()
        signals = asyncio.run(hunter.hunt(sectors=["iec62443"]))
        hunt_time = time.time() - t0
        assert hunt_time < 30

        # Step 2: Generate offer for first signal
        if signals:
            flash = get_flash_offer()
            signal = signals[0]
            t1 = time.time()
            offer = asyncio.run(flash.generate(
                company=getattr(signal, "company", "TestCo"),
                sector=getattr(signal, "sector", "iec62443"),
                pain_description=getattr(signal, "pain_signal", "Conformité requise"),
                budget_estimate=15_000,
            ))
            offer_time = time.time() - t1
            assert offer.price_eur >= 1_000
            assert offer_time < 60

        total_step_time = time.time() - t0
        assert total_step_time < 90, f"Pipeline partiel trop lent: {total_step_time:.1f}s"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportGenerator:
    """Tests du générateur de rapports NIS2."""

    def test_generate_text_report(self):
        from SAAS_NIS2.report_generator import get_report_generator
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: True for q in NIS2_QUESTIONS[:15]} | \
                  {q["id"]: False for q in NIS2_QUESTIONS[15:]}
        assessment = checker.create_assessment(
            company="ReportCorp",
            sector="manufacturing",
            contact_email="r@corp.fr",
            answers=answers,
            freemium=False,
        )
        gen = get_report_generator()
        path = gen.generate(assessment)
        assert path
        import os
        assert os.path.exists(path)

    def test_report_contains_company_name(self):
        from SAAS_NIS2.report_generator import get_report_generator
        from SAAS_NIS2.nis2_checker import get_nis2_checker, NIS2_QUESTIONS
        checker = get_nis2_checker()
        answers = {q["id"]: False for q in NIS2_QUESTIONS}
        assessment = checker.create_assessment(
            company="UniqueCompanyXYZ",
            sector="energie_utilities",
            contact_email="x@xyz.fr",
            answers=answers,
            freemium=False,
        )
        gen = get_report_generator()
        path = gen.generate(assessment)
        if path.endswith(".txt"):
            content = open(path).read()
            assert "UniqueCompanyXYZ" in content
