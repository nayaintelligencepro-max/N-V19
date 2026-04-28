"""
NAYA SUPREME V19.5 — Tests complets des 15 améliorations
═══════════════════════════════════════════════════════════
Vérifie que tous les modules sont opérationnels et connectés.
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestCloserRoutingBridge(unittest.TestCase):

    def test_receive_conversion(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.closer_routing_bridge import (
            CloserRoutingBridge, ConversionEvent, ConversionSignal, ClosingStrategy,
        )
        bridge = CloserRoutingBridge()
        event = ConversionEvent(
            prospect_id="P-001",
            prospect_name="Jean Dupont",
            company="EnergieCorp",
            email="j.dupont@energiecorp.fr",
            signal=ConversionSignal.MEETING_ACCEPTED,
            reply_text="Oui, je suis disponible pour un échange",
            estimated_value_eur=8000,
            sector="energie",
            services_interested=["audit_iec62443"],
        )
        action = bridge.receive_conversion(event)
        self.assertIsNotNone(action)
        self.assertEqual(action.prospect_id, "P-001")
        self.assertGreaterEqual(action.proposed_amount_eur, 1000)
        self.assertIn("https://", action.payment_link)

    def test_min_contract_enforced(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.closer_routing_bridge import (
            CloserRoutingBridge, ConversionEvent, ConversionSignal,
        )
        bridge = CloserRoutingBridge()
        event = ConversionEvent(
            prospect_id="P-002",
            prospect_name="Test",
            company="TestCo",
            email="test@test.com",
            signal=ConversionSignal.POSITIVE_REPLY,
            reply_text="oui",
            estimated_value_eur=500,
            sector="industrie",
        )
        action = bridge.receive_conversion(event)
        self.assertGreaterEqual(action.proposed_amount_eur, 1000)

    def test_direct_close_strategy(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.closer_routing_bridge import (
            CloserRoutingBridge, ConversionEvent, ConversionSignal, ClosingStrategy,
        )
        bridge = CloserRoutingBridge()
        event = ConversionEvent(
            prospect_id="P-003",
            prospect_name="Marie",
            company="SecureCorp",
            email="m@securecorp.fr",
            signal=ConversionSignal.CONTRACT_REQUESTED,
            reply_text="Envoyez-moi le contrat",
            estimated_value_eur=12000,
            sector="transport",
            services_interested=["audit_nis2"],
        )
        action = bridge.receive_conversion(event)
        self.assertEqual(action.strategy, ClosingStrategy.DIRECT_CLOSE)


class TestPaymentWebhookReceiver(unittest.TestCase):

    def test_process_paypal_webhook(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.payment_webhook_receiver import (
            PaymentWebhookReceiver, PaymentProvider, PaymentStatus,
        )
        receiver = PaymentWebhookReceiver()
        receiver.register_invoice(
            "INV-001", "client@test.com", 5000.0, "audit_iec62443", "REF-001",
        )
        notif = receiver.process_webhook(
            PaymentProvider.PAYPAL,
            {
                "txn_id": "TXN123",
                "mc_gross": "5000.00",
                "mc_currency": "EUR",
                "payer_email": "payer@test.com",
                "first_name": "Jean",
                "last_name": "Test",
                "payment_status": "Completed",
                "custom": "REF-001",
            },
        )
        self.assertEqual(notif.status, PaymentStatus.CONFIRMED)
        self.assertEqual(notif.amount_eur, 5000.0)

    def test_delivery_triggered(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.payment_webhook_receiver import (
            PaymentWebhookReceiver, PaymentProvider,
        )
        receiver = PaymentWebhookReceiver()
        receiver.register_invoice(
            "INV-002", "client@test.com", 8000.0, "audit_nis2", "REF-002",
        )
        receiver.process_webhook(
            PaymentProvider.MANUAL,
            {"id": "M1", "amount": 8000, "email": "c@t.com", "name": "Test", "reference": "REF-002", "confirmed": True},
        )
        self.assertEqual(receiver.stats["total_delivered"], 1)


class TestDeliverabilityMonitor(unittest.TestCase):

    def test_normal_sending(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.deliverability_monitor import (
            DeliverabilityMonitor, EmailEvent, ReputationLevel,
        )
        monitor = DeliverabilityMonitor()
        for i in range(50):
            monitor.record_event(EmailEvent(f"msg-{i}", f"r{i}@test.com", "sent"))
        for i in range(45):
            monitor.record_event(EmailEvent(f"msg-{i}", f"r{i}@test.com", "delivered"))
        for i in range(20):
            monitor.record_event(EmailEvent(f"msg-{i}", f"r{i}@test.com", "opened"))
        self.assertTrue(monitor.can_send())
        rep = monitor.get_reputation()
        self.assertIn(rep, [ReputationLevel.EXCELLENT, ReputationLevel.GOOD])

    def test_pause_on_high_bounce(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.deliverability_monitor import (
            DeliverabilityMonitor, EmailEvent,
        )
        monitor = DeliverabilityMonitor()
        for i in range(100):
            monitor.record_event(EmailEvent(f"msg-{i}", f"r{i}@test.com", "sent"))
        for i in range(9):
            monitor.record_event(EmailEvent(f"msg-{i}", f"r{i}@test.com", "bounce_hard"))
        self.assertFalse(monitor.can_send())


class TestFeedbackLoopConnector(unittest.TestCase):

    def test_record_deal(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.feedback_loop_connector import (
            FeedbackLoopConnector, DealFeedback,
        )
        connector = FeedbackLoopConnector()
        fb = DealFeedback(
            deal_id="D-001",
            result="won",
            sector="energie",
            signal_type="regulatory",
            offer_tier="TIER2",
            proposed_amount_eur=8000,
            final_amount_eur=7500,
            days_to_close=14,
            winning_angle="conformité NIS2",
            channel="email",
        )
        insights = connector.record_deal(fb)
        self.assertIsInstance(insights, list)
        self.assertEqual(connector.sector_stats["energie"]["won"], 1)

    def test_optimized_params(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.feedback_loop_connector import (
            FeedbackLoopConnector, DealFeedback,
        )
        connector = FeedbackLoopConnector()
        for i in range(5):
            connector.record_deal(DealFeedback(
                f"D-{i}", "won", "transport", "news", "TIER1",
                5000, 5000, 10 + i, channel="linkedin",
            ))
        params = connector.get_optimized_params("transport")
        self.assertGreater(params["conversion_rate"], 0)


class TestDailyDigestEngine(unittest.TestCase):

    def test_generate_digest(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.daily_digest_engine import DailyDigestEngine
        engine = DailyDigestEngine()
        engine.start_day()
        engine.record_revenue(5000)
        engine.record_prospect(qualified=True)
        engine.record_email(opened=True)
        engine.record_deal(won=True, value_eur=5000)
        digest = engine.generate_digest()
        self.assertIn("5,000", digest.replace("\u202f", ",").replace(" ", ""))
        self.assertIn("REVENUS", digest)
        self.assertIn("PIPELINE", digest)


class TestSilentProspectReactivator(unittest.TestCase):

    def test_scan_for_reactivation(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.silent_prospect_reactivator import (
            SilentProspectReactivator, SilentProspect, SilenceReason,
        )
        reactivator = SilentProspectReactivator()
        from datetime import timedelta
        old_date = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        prospect = SilentProspect(
            prospect_id="SP-001",
            name="Pierre",
            company="OTSec",
            email="p@otsec.fr",
            sector="industrie",
            last_contact_date=old_date,
            sequence_stage=5,
            total_emails_sent=5,
            total_opens=2,
            estimated_value_eur=6000,
        )
        reactivator.register_silent_prospect(prospect)
        plans = reactivator.scan_for_reactivation()
        self.assertGreaterEqual(len(plans), 1)


class TestSocialProofEngine(unittest.TestCase):

    def test_generate_case_study(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.social_proof_engine import SocialProofEngine
        engine = SocialProofEngine()
        case = engine.generate_case_study(
            "D-001", "energie", "ETI (250-5000)", "audit_iec62443", 3, 23,
        )
        self.assertIsNotNone(case)
        self.assertEqual(case.sector, "energie")
        self.assertGreater(len(case.results), 0)

    def test_format_for_proposal(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.social_proof_engine import SocialProofEngine
        engine = SocialProofEngine()
        engine.generate_case_study("D-002", "transport", "PME", "audit_nis2", 2, 15)
        text = engine.format_for_proposal("transport")
        self.assertIn("transport", text)


class TestMultilingualBridge(unittest.TestCase):

    def test_detect_french(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.multilingual_outreach_bridge import MultilingualOutreachBridge
        bridge = MultilingualOutreachBridge()
        lang = bridge.detect_language("contact@entreprise.fr")
        self.assertEqual(lang, "fr")

    def test_detect_german(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.multilingual_outreach_bridge import MultilingualOutreachBridge
        bridge = MultilingualOutreachBridge()
        lang = bridge.detect_language(country="DE")
        self.assertEqual(lang, "de")

    def test_generate_email(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.multilingual_outreach_bridge import MultilingualOutreachBridge
        bridge = MultilingualOutreachBridge()
        email = bridge.generate_email(
            "Hans Mueller", "hans@siemens.de", "Siemens", "industrie",
            pain_type="iec62443", country="DE",
        )
        self.assertEqual(email.language, "de")
        self.assertIn("IEC 62443", email.body)


class TestClientPortalAPI(unittest.TestCase):

    def test_register_and_authenticate(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.client_portal_api import ClientPortalAPI
        portal = ClientPortalAPI()
        session = portal.register_client("C-001", "TestCorp", "admin@testcorp.com")
        client_id = portal.authenticate(session.token)
        self.assertEqual(client_id, "C-001")

    def test_get_portal_data(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.client_portal_api import ClientPortalAPI
        portal = ClientPortalAPI()
        session = portal.register_client("C-002", "SecureCo", "a@sec.com")
        data = portal.get_portal_data(session.token)
        self.assertIsNotNone(data)
        self.assertIn("projects", data)
        self.assertIn("invoices", data)


class TestContentCalendarEngine(unittest.TestCase):

    def test_generate_content(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.content_calendar_engine import (
            ContentCalendarEngine, ContentFormat,
        )
        engine = ContentCalendarEngine()
        item = engine.generate_content("nis2_compliance", ContentFormat.LINKEDIN_POST, "energie")
        self.assertIsNotNone(item)
        self.assertIn("NIS2", item.title)

    def test_weekly_plan(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.content_calendar_engine import ContentCalendarEngine
        engine = ContentCalendarEngine()
        items = engine.generate_weekly_plan("transport")
        self.assertEqual(len(items), 2)


class TestMaturityScorer(unittest.TestCase):

    def test_ready_now(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.maturity_scorer import (
            MaturityScorer, MaturitySignalInput, BuyingSignal, MaturityLevel,
        )
        scorer = MaturityScorer()
        signals = [
            MaturitySignalInput(BuyingSignal.BUDGET_VOTED, "2024-01-01", 0.9),
            MaturitySignalInput(BuyingSignal.REGULATORY_DEADLINE, "2024-01-01", 0.85),
            MaturitySignalInput(BuyingSignal.SECURITY_INCIDENT, "2024-01-01", 0.95),
            MaturitySignalInput(BuyingSignal.RFP_PUBLISHED, "2024-01-01", 0.9),
        ]
        result = scorer.assess("P-001", signals, has_budget=True)
        self.assertEqual(result.maturity_level, MaturityLevel.READY_NOW)


class TestBackupEngine(unittest.TestCase):

    def test_create_backup(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.backup_engine import BackupEngine
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "data" / "cache").mkdir(parents=True)
            test_file = project / "SYSTEM_IDENTITY.ini"
            test_file.write_text("[system]\nname=NAYA")
            backup_root = project / "backups"
            engine = BackupEngine(backup_root)
            metadata = engine.create_backup(project, "test")
            self.assertGreaterEqual(metadata.files_backed_up, 1)
            self.assertTrue(engine.verify_backup(metadata.backup_id))


class TestLightningPayment(unittest.TestCase):

    def test_create_invoice(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.lightning_payment_complete import LightningPaymentComplete
        lp = LightningPaymentComplete()
        invoice = lp.create_invoice(1000.0, "Audit IEC 62443 — Acompte")
        self.assertIsNotNone(invoice)
        self.assertGreater(invoice.amount_sats, 0)
        self.assertTrue(invoice.payment_request.startswith("lnbc"))

    def test_confirm_payment(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.lightning_payment_complete import LightningPaymentComplete
        lp = LightningPaymentComplete()
        invoice = lp.create_invoice(5000.0, "Audit NIS2")
        success = lp.confirm_payment(invoice.invoice_id)
        self.assertTrue(success)
        self.assertEqual(lp.stats["invoices_paid"], 1)


class TestPipelineConnector(unittest.TestCase):

    def test_health_check(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.pipeline_connector import PipelineConnector
        connector = PipelineConnector()
        health = connector.health_check()
        self.assertEqual(health["health_pct"], 100)
        self.assertTrue(health["all_connected"])

    def test_route_positive_reply(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.pipeline_connector import PipelineConnector
        connector = PipelineConnector()
        targets = connector.on_positive_reply({"prospect_id": "P-001"})
        self.assertIn("closer_routing_bridge", targets)

    def test_full_pipeline_flow(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.pipeline_connector import PipelineConnector
        connector = PipelineConnector()
        targets = connector.on_prospect_detected({"id": "P-100"})
        self.assertGreater(len(targets), 0)
        targets = connector.on_prospect_scored("P-100", 0.85, "HOT")
        self.assertGreater(len(targets), 0)
        targets = connector.on_positive_reply({"prospect_id": "P-100"})
        self.assertIn("closer_routing_bridge", targets)
        targets = connector.on_payment_received({"amount": 5000, "ref": "R-100"})
        self.assertGreater(len(targets), 0)


class TestV20Modules(unittest.TestCase):

    def test_voice_agent(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.v20_modules_completion import VoiceAgentEngine
        engine = VoiceAgentEngine()
        call = engine.schedule_call("P-001", "Jean", "+33612345678")
        self.assertIsNotNone(call)
        engine.complete_call(call.call_id, "meeting_booked", 180, "RDV confirmé")
        self.assertEqual(engine.stats["meetings_booked"], 1)

    def test_digital_twin(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.v20_modules_completion import DigitalTwinEngine
        engine = DigitalTwinEngine()
        profile = engine.create_twin("P-001", "RSSI", "energie", "eti")
        self.assertEqual(profile.persona_type, "rssi_conservative")
        response = engine.simulate_response("P-001", "Bonjour")
        self.assertIn("prediction", response)

    def test_blockchain_proof(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.v20_modules_completion import BlockchainProofOfAudit
        chain = BlockchainProofOfAudit()
        proof = chain.create_proof(
            "AUD-001", "TestCorp", "IEC 62443", 15,
            {"critical": 3, "high": 5, "medium": 7},
        )
        self.assertIsNotNone(proof)
        valid, errors = chain.verify_chain()
        self.assertTrue(valid)

    def test_decision_graph(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.v20_modules_completion import DecisionGraphEngine
        engine = DecisionGraphEngine()
        result = engine.evaluate({
            "sector_match": True,
            "company_size": True,
            "regulation": True,
            "budget": True,
        })
        self.assertIn("CLOSER", result["action"])

    def test_ai_act_compliance(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.v20_modules_completion import AIActComplianceEngine
        engine = AIActComplianceEngine()
        assessment = engine.get_naya_self_assessment()
        self.assertIsNotNone(assessment)
        self.assertIn(assessment.risk_category, ["minimal_risk", "limited_risk", "high_risk"])


class TestE2EPipeline(unittest.TestCase):
    """Test d'intégration End-to-End : simule un prospect traversant tout le pipeline."""

    def test_full_prospect_journey(self):
        from NAYA_IMPROVEMENTS.v19_5_upgrades.pipeline_connector import PipelineConnector
        from NAYA_IMPROVEMENTS.v19_5_upgrades.closer_routing_bridge import (
            CloserRoutingBridge, ConversionEvent, ConversionSignal,
        )
        from NAYA_IMPROVEMENTS.v19_5_upgrades.payment_webhook_receiver import (
            PaymentWebhookReceiver, PaymentProvider,
        )
        from NAYA_IMPROVEMENTS.v19_5_upgrades.feedback_loop_connector import (
            FeedbackLoopConnector, DealFeedback,
        )
        from NAYA_IMPROVEMENTS.v19_5_upgrades.social_proof_engine import SocialProofEngine
        from NAYA_IMPROVEMENTS.v19_5_upgrades.daily_digest_engine import DailyDigestEngine
        from NAYA_IMPROVEMENTS.v19_5_upgrades.deliverability_monitor import (
            DeliverabilityMonitor, EmailEvent,
        )

        connector = PipelineConnector()
        closer = CloserRoutingBridge()
        payments = PaymentWebhookReceiver()
        feedback = FeedbackLoopConnector()
        social = SocialProofEngine()
        digest = DailyDigestEngine()
        deliv = DeliverabilityMonitor()

        # Step 1: Prospect detected
        targets = connector.on_prospect_detected({"id": "E2E-001", "company": "IndustrieX"})
        self.assertGreater(len(targets), 0)

        # Step 2: Prospect scored HOT
        targets = connector.on_prospect_scored("E2E-001", 0.88, "HOT")
        self.assertGreater(len(targets), 0)

        # Step 3: Emails sent (check deliverability)
        for i in range(5):
            deliv.record_event(EmailEvent(f"e2e-{i}", "contact@industriex.com", "sent"))
            deliv.record_event(EmailEvent(f"e2e-{i}", "contact@industriex.com", "delivered"))
        self.assertTrue(deliv.can_send())

        # Step 4: Positive reply → Closer
        conversion = ConversionEvent(
            prospect_id="E2E-001",
            prospect_name="Marc Industriel",
            company="IndustrieX",
            email="m.industriel@industriex.com",
            signal=ConversionSignal.MEETING_ACCEPTED,
            reply_text="Oui, planifions un échange",
            estimated_value_eur=8000,
            sector="industrie",
            services_interested=["audit_iec62443"],
        )
        action = closer.receive_conversion(conversion)
        self.assertGreaterEqual(action.proposed_amount_eur, 1000)

        # Step 5: Payment received
        payments.register_invoice(
            "INV-E2E", "m.industriel@industriex.com", 8000, "audit_iec62443", "REF-E2E",
        )
        notif = payments.process_webhook(
            PaymentProvider.MANUAL,
            {"id": "M-E2E", "amount": 8000, "email": "m@ix.com", "name": "Marc", "reference": "REF-E2E", "confirmed": True},
        )
        self.assertEqual(payments.stats["total_delivered"], 1)

        # Step 6: Feedback recorded
        fb = DealFeedback(
            "D-E2E", "won", "industrie", "regulatory", "TIER2",
            8000, 8000, 7, winning_angle="IEC 62443",
        )
        feedback.record_deal(fb)
        self.assertEqual(feedback.sector_stats["industrie"]["won"], 1)

        # Step 7: Social proof generated
        case = social.generate_case_study("D-E2E", "industrie", "ETI", "audit_iec62443", 3)
        self.assertIsNotNone(case)

        # Step 8: Daily digest
        digest.start_day()
        digest.record_revenue(8000)
        digest.record_deal(won=True, value_eur=8000)
        report = digest.generate_digest()
        self.assertIn("8,000", report.replace("\u202f", ",").replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
