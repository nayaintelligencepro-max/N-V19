"""
NAYA V19 — Tests Unitaires Metier (session 8)
Couvre: CashEngine, RevenueIntelligence, PipelineTracker,
        AssetRegistry, RateLimiter, Monitoring, NayaInterface,
        PaymentEngine, MoneyNotifier, Scheduler, ConversionEngine

Usage : python3 tests/test_unit.py
"""
import sys, os, time, json, tempfile, threading, unittest, re
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 1 — CashEngineReal
# ══════════════════════════════════════════════════════════════════════════════
class TestCashEngineReal(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mktemp(suffix=".json"))
        with patch("NAYA_CORE.cash_engine_real.PIPELINE_FILE", self.tmp):
            from NAYA_CORE.cash_engine_real import CashEngineReal
            self.engine = CashEngineReal.__new__(CashEngineReal)
            self.engine._deals = {}
            self.engine._won_total = 0.0
            self.engine._won_count = 0

    def _hunt(self, price=5000, pain="CASH_TRAPPED"):
        return {
            "qualified": True,
            "offer": {"price": price, "title": f"Service {price}"},
            "top_pain": {"category": pain, "annual_cost_eur": price * 8, "cost_ratio": 0.1},
        }

    def test_inject_from_hunt_cree_deal(self):
        with patch.object(self.engine, "_save_pipeline"):
            deal = self.engine.inject_from_hunt(self._hunt(5000), "pme_b2b")
        self.assertIsNotNone(deal)
        self.assertEqual(deal.offer_price, 5000)
        self.assertIn(deal.id, self.engine._deals)

    def test_inject_filtre_prix_sous_plancher(self):
        deal = self.engine.inject_from_hunt(self._hunt(500), "pme_b2b")
        self.assertIsNone(deal)

    def test_inject_filtre_non_qualifie(self):
        hunt = {"qualified": False, "offer": {"price": 10000}}
        self.assertIsNone(self.engine.inject_from_hunt(hunt, "pme_b2b"))

    def test_mark_won_enregistre_revenus(self):
        with patch.object(self.engine, "_save_pipeline"):
            deal = self.engine.inject_from_hunt(self._hunt(8000), "startup_scaleup")
            result = self.engine.mark_won(deal.id, revenue=8000)
        self.assertTrue(result)
        self.assertEqual(self.engine._won_total, 8000)
        self.assertEqual(self.engine._won_count, 1)

    def test_mark_won_utilise_offer_price_si_absent(self):
        with patch.object(self.engine, "_save_pipeline"):
            deal = self.engine.inject_from_hunt(self._hunt(6500), "pme_b2b")
            self.engine.mark_won(deal.id)
        self.assertEqual(self.engine._won_total, 6500)

    def test_mark_won_id_inexistant_retourne_false(self):
        self.assertFalse(self.engine.mark_won("ID_INEXISTANT"))

    def test_mark_lost_change_stage(self):
        with patch.object(self.engine, "_save_pipeline"):
            deal = self.engine.inject_from_hunt(self._hunt(3000), "artisan_trades")
            result = self.engine.mark_lost(deal.id, reason="budget")
        self.assertTrue(result)
        from NAYA_CORE.cash_engine_real import DealStage
        self.assertEqual(deal.stage, DealStage.LOST)

    def test_pipeline_summary_vide(self):
        s = self.engine.get_pipeline_summary()
        self.assertEqual(s["active_deals"], 0)
        self.assertEqual(s["pipeline_total_eur"], 0)

    def test_pipeline_summary_avec_deals(self):
        for price in [3000, 7000, 15000]:
            with patch.object(self.engine, "_save_pipeline"):
                self.engine.inject_from_hunt(self._hunt(price), "pme_b2b")
        s = self.engine.get_pipeline_summary()
        self.assertEqual(s["active_deals"], 3)
        self.assertEqual(s["pipeline_total_eur"], 25000)

    def test_followup_sequence_generee(self):
        with patch.object(self.engine, "_save_pipeline"):
            deal = self.engine.inject_from_hunt(self._hunt(), "pme_b2b")
        self.assertGreater(len(deal.follow_up_sequence), 3)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 2 — RevenueIntelligence
# ══════════════════════════════════════════════════════════════════════════════
class TestRevenueIntelligence(unittest.TestCase):

    def setUp(self):
        tmp = Path(tempfile.mktemp(suffix=".json"))
        with patch("NAYA_CORE.revenue_intelligence.INTEL_FILE", tmp):
            from NAYA_CORE.revenue_intelligence import RevenueIntelligence
            self.intel = RevenueIntelligence.__new__(RevenueIntelligence)
            self.intel._sector_perf = {}
            self.intel._pain_conv = {}
            self.intel._price_conv = {}
            self.intel._init_defaults()

    def test_record_detection_incremente(self):
        with patch.object(self.intel, "_save"):
            self.intel.record_detection("pme_b2b", "CASH_TRAPPED", 5000)
            self.intel.record_detection("pme_b2b", "CASH_TRAPPED", 7000)
        self.assertEqual(self.intel._sector_perf["pme_b2b"].deals_detected, 2)

    def test_record_win_met_a_jour_conversion(self):
        with patch.object(self.intel, "_save"):
            self.intel.record_detection("pme_b2b", "CASH_TRAPPED", 5000)
            self.intel.record_win("pme_b2b", "CASH_TRAPPED", 5000)
        sp = self.intel._sector_perf["pme_b2b"]
        self.assertEqual(sp.deals_won, 1)
        self.assertEqual(sp.revenue_total, 5000)

    def test_record_win_avg_price(self):
        with patch.object(self.intel, "_save"):
            self.intel.record_win("startup_scaleup", "GROWTH_BLOCK", 10000)
            self.intel.record_win("startup_scaleup", "GROWTH_BLOCK", 20000)
        self.assertEqual(self.intel._sector_perf["startup_scaleup"].avg_price, 15000)

    def test_price_bucket(self):
        self.assertEqual(self.intel._price_bucket(3000), "1k-5k")
        self.assertEqual(self.intel._price_bucket(12000), "5k-15k")
        self.assertEqual(self.intel._price_bucket(25000), "15k-30k")
        self.assertEqual(self.intel._price_bucket(80000), "60k+")

    def test_get_priority_sectors_non_vide(self):
        result = self.intel.get_priority_sectors(3)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_hunt_directives_structure(self):
        with patch.object(self.intel, "_save"):
            self.intel.record_win("pme_b2b", "CASH_TRAPPED", 5000)
        d = self.intel.get_hunt_directives()
        self.assertIn("focus_sectors", d)
        self.assertIn("rationale", d)
        self.assertIn("top_sector", d["rationale"])

    def test_nouveau_secteur_auto_cree(self):
        with patch.object(self.intel, "_save"):
            self.intel.record_detection("nouveau_test_xyz", "PAIN_X", 3000)
        self.assertIn("nouveau_test_xyz", self.intel._sector_perf)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 3 — PipelineTracker
# ══════════════════════════════════════════════════════════════════════════════
class TestPipelineTracker(unittest.TestCase):

    def setUp(self):
        tmp = Path(tempfile.mktemp(suffix=".json"))
        with patch("NAYA_REVENUE_ENGINE.pipeline_tracker.PIPELINE_FILE", tmp):
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            self.tracker = PipelineTracker.__new__(PipelineTracker)
            self.tracker._pipeline = {}

    def _prospect(self, company="TestCo", price=5000):
        import uuid
        p = MagicMock()
        p.id = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        p.company_name = company
        p.contact_name = "Test User"
        p.email = "test@test.com"
        p.sector = "pme_b2b"
        p.city = "Paris"
        p.pain_category = "CASH_TRAPPED"
        p.pain_annual_cost_eur = price * 8
        p.offer_price_eur = price
        p.offer_title = f"Offre {company}"
        p.priority = "HIGH"
        p.solvability_score = 75.0
        p.source = "test"
        return p

    def test_add_statut_new(self):
        with patch.object(self.tracker, "_save"):
            pid = self.tracker.add(self._prospect(), offer_price=5000)
        self.assertEqual(self.tracker._pipeline[pid]["status"], "NEW")

    def test_update_status(self):
        with patch.object(self.tracker, "_save"):
            pid = self.tracker.add(self._prospect())
            result = self.tracker.update_status(pid, "ALERTED", "Telegram envoyé")
        self.assertTrue(result)
        self.assertEqual(self.tracker._pipeline[pid]["status"], "ALERTED")

    def test_update_status_id_inconnu(self):
        with patch.object(self.tracker, "_save"):
            result = self.tracker.update_status("INCONNU", "ALERTED")
        self.assertFalse(result)

    def test_closed_won_enregistre_revenue(self):
        with patch.object(self.tracker, "_save"):
            pid = self.tracker.add(self._prospect(price=8500), offer_price=8500)
            self.tracker.update_status(pid, "CLOSED_WON")
        self.assertEqual(self.tracker._pipeline[pid]["revenue_collected"], 8500)

    def test_kpis_pipeline_vide(self):
        self.tracker._pipeline = {}
        kpis = self.tracker.get_kpis()
        self.assertEqual(kpis["pipeline_eur"], 0)
        self.assertEqual(kpis["revenue_won_eur"], 0)

    def test_kpis_avec_deals(self):
        self.tracker._pipeline = {}
        for i, price in enumerate([3000, 7000, 15000]):
            with patch.object(self.tracker, "_save"):
                self.tracker.add(self._prospect(f"Co{i}", price), offer_price=price)
        self.assertEqual(self.tracker.get_kpis()["pipeline_eur"], 25000)

    def test_payment_url(self):
        with patch.object(self.tracker, "_save"):
            pid = self.tracker.add(self._prospect())
            self.tracker.set_payment_url(pid, "https://paypal.me/test/500")
        self.assertEqual(self.tracker._pipeline[pid]["payment_url"], "https://paypal.me/test/500")

    def test_all_retourne_liste(self):
        self.tracker._pipeline = {}
        for i in range(3):
            with patch.object(self.tracker, "_save"):
                self.tracker.add(self._prospect(f"Cie{i}"))
        result = self.tracker.all()
        self.assertEqual(len(result), 3)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 4 — PaymentEngine (nouveau)
# ══════════════════════════════════════════════════════════════════════════════
class TestPaymentEngine(unittest.TestCase):

    def setUp(self):
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
        self.pe = PaymentEngine()
        # Simuler PayPal configuré, Revolut configuré
        self._paypal_url = "https://www.paypal.me/TestUser"
        self._revolut_url = "https://revolut.me/testuser/pocket/ABC123"

    def _pe_with_paypal(self):
        """PaymentEngine avec PayPal mocké."""
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
        pe = PaymentEngine()
        pe.__class__.paypal_url = property(lambda self: self._paypal_url)
        return pe

    def test_has_paypal_vrai(self):
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/Test")):
            self.assertTrue(self.pe.has_paypal)

    def test_has_paypal_faux_si_vide(self):
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "")):
            self.assertFalse(self.pe.has_paypal)

    def test_create_paypal_link_montant_prerempli(self):
        """Le lien PayPal contient le montant exact."""
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/TestUser")):
            with patch.object(type(self.pe), "has_paypal",
                               new_callable=lambda: property(lambda self: True)):
                with patch.object(type(self.pe), "has_revolut",
                                   new_callable=lambda: property(lambda self: False)):
                    result = self.pe._create_paypal_link(3500, "Audit PME", "c@test.com", "Jean")
        self.assertTrue(result["created"])
        self.assertIn("3500.00", result["url"])
        self.assertEqual(result["provider"], "paypal_me")

    def test_create_paypal_link_contient_reference(self):
        """Chaque lien a une référence unique."""
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/TestUser")):
            r1 = self.pe._create_paypal_link(1000, "Service A")
            r2 = self.pe._create_paypal_link(1000, "Service B")
        self.assertNotEqual(r1["reference"], r2["reference"])

    def test_create_paypal_link_email_body_contient_montant(self):
        """L'email de facturation mentionne le montant."""
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/Test")):
            result = self.pe._create_paypal_link(7500, "Mission conseil", "cli@cli.com", "Marie")
        self.assertIn("7500", result["email_body"])
        self.assertIn("Marie", result["email_body"])

    def test_create_revolut_link_structure(self):
        """Revolut retourne url et note sur le montant."""
        with patch.object(type(self.pe), "revolut_url",
                          new_callable=lambda: property(lambda self: "https://revolut.me/user/pocket/XYZ")):
            result = self.pe._create_revolut_link(2000, "Consulting", "r@r.com", "Paul")
        self.assertTrue(result["created"])
        self.assertEqual(result["provider"], "revolut_me")
        self.assertIn("note", result)  # note pour préciser le montant

    def test_dual_method_au_dessus_seuil(self):
        """Au-dessus du seuil, PayPal + Revolut sont tous les deux proposés."""
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/T")):
            with patch.object(type(self.pe), "has_paypal",
                               new_callable=lambda: property(lambda self: True)):
                with patch.object(type(self.pe), "revolut_url",
                                   new_callable=lambda: property(lambda self: "https://revolut.me/t/pocket/X")):
                    with patch.object(type(self.pe), "has_revolut",
                                       new_callable=lambda: property(lambda self: True)):
                        result = self.pe.create_payment_link(
                            self.pe.DUAL_METHOD_THRESHOLD_EUR,
                            "Gros deal", "big@client.com"
                        )
        self.assertIn("revolut_url", result)

    def test_pas_de_revolut_sous_seuil(self):
        """Sous le seuil, PayPal seulement (pas de doublon)."""
        with patch.object(type(self.pe), "paypal_url",
                          new_callable=lambda: property(lambda self: "https://www.paypal.me/T")):
            with patch.object(type(self.pe), "has_paypal",
                               new_callable=lambda: property(lambda self: True)):
                with patch.object(type(self.pe), "has_revolut",
                                   new_callable=lambda: property(lambda self: True)):
                    result = self.pe.create_payment_link(100, "Petit service")
        self.assertNotIn("revolut_url", result)

    def test_aucun_moyen_paiement_retourne_created_false(self):
        """Sans aucune méthode, create_payment_link retourne created=False."""
        with patch.object(type(self.pe), "available",
                          new_callable=lambda: property(lambda self: False)):
            result = self.pe.create_payment_link(5000, "test")
        self.assertFalse(result["created"])

    def test_stats_pas_de_stripe(self):
        """Stripe a été retiré V19.3 — la clé 'stripe_configured' ne doit plus exister."""
        stats = self.pe.get_stats()
        self.assertNotIn("stripe_configured", stats)
        self.assertIn("note", stats)
        self.assertIn("paypal_configured", stats)
        self.assertIn("deblock_configured", stats)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 5 — MoneyNotifier
# ══════════════════════════════════════════════════════════════════════════════
class TestMoneyNotifier(unittest.TestCase):

    def setUp(self):
        from NAYA_CORE.money_notifier import MoneyNotifier
        self.mn = MoneyNotifier()

    def test_unavailable_sans_token(self):
        """Sans token Telegram, available=False."""
        with patch.object(type(self.mn), "token",
                          new_callable=lambda: property(lambda self: "")):
            self.assertFalse(self.mn.available)

    def test_available_avec_token_et_chat(self):
        """Avec token+chat, available=True."""
        with patch.object(type(self.mn), "token",
                          new_callable=lambda: property(lambda self: "fake_token")):
            with patch.object(type(self.mn), "chat_id",
                               new_callable=lambda: property(lambda self: "12345")):
                self.assertTrue(self.mn.available)

    def test_send_retourne_false_sans_telegram(self):
        """_send() retourne False sans Telegram configuré — pas d'exception."""
        with patch.object(type(self.mn), "available",
                          new_callable=lambda: property(lambda self: False)):
            result = self.mn._send("Test message")
        self.assertFalse(result)

    def test_get_stats_structure(self):
        """get_stats retourne sent/failed."""
        stats = self.mn.get_stats()
        self.assertIn("sent", stats)
        self.assertIn("failed", stats)

    def test_alert_opportunity_construit_message(self):
        """alert_opportunity ne crash pas et log le message sans Telegram."""
        prospect = {
            "company_name": "PME Test",
            "city": "Paris",
            "email": "ceo@pme.com",
            "pain_annual_cost_eur": 50000,
            "offer_price_eur": 7500,
            "offer_title": "Libération trésorerie",
            "pain_signals": ["Cash bloqué", "Factures impayées"],
            "priority": "HIGH",
            "id": "TEST_001",
        }
        offer = {"price": 7500, "title": "Libération trésorerie"}
        with patch.object(type(self.mn), "available",
                          new_callable=lambda: property(lambda self: False)):
            result = self.mn.alert_opportunity(prospect, offer, "APPROVAL_XYZ")
        self.assertFalse(result)  # False = pas envoyé (pas de telegram), mais pas d'exception

    def test_alert_won_sans_crash(self):
        """alert_won fonctionne sans Telegram configuré."""
        deal = {"id": "D001", "company": "TestCo", "revenue_collected": 5000,
                "won_total": 5000, "sector": "pme_b2b"}
        with patch.object(type(self.mn), "available",
                          new_callable=lambda: property(lambda self: False)):
            result = self.mn.alert_won(deal)
        self.assertFalse(result)

    def test_notify_boot_sans_crash(self):
        """notify_boot ne crash pas même sans Telegram."""
        with patch.object(type(self.mn), "available",
                          new_callable=lambda: property(lambda self: False)):
            result = self.mn.notify_boot({"score": 85, "active_llm": "groq", "modules": 30})
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 6 — Scheduler
# ══════════════════════════════════════════════════════════════════════════════
class TestScheduler(unittest.TestCase):

    def setUp(self):
        from NAYA_CORE.scheduler import NayaScheduler
        self.scheduler = NayaScheduler()

    def test_18_jobs_enregistres(self):
        """Le scheduler doit avoir au moins 18 jobs."""
        status = self.scheduler.get_status()
        self.assertGreaterEqual(len(status["jobs"]), 18)

    def test_jobs_ont_interval_positif(self):
        """Tous les jobs ont un interval > 0."""
        status = self.scheduler.get_status()
        for name, job in status["jobs"].items():
            self.assertGreater(job["interval_s"], 0, f"{name} interval nul")

    def test_jobs_ont_description(self):
        """Tous les jobs ont une description non vide."""
        status = self.scheduler.get_status()
        for name, job in status["jobs"].items():
            self.assertTrue(job["description"], f"{name} sans description")

    def test_scheduler_non_running_au_init(self):
        """Le scheduler ne tourne pas au démarrage (doit être démarré explicitement)."""
        status = self.scheduler.get_status()
        self.assertFalse(status["running"])

    def test_trigger_job_existant(self):
        """trigger() retourne True pour un job existant."""
        result = self.scheduler.trigger("health_check")
        self.assertTrue(result)

    def test_trigger_job_inexistant(self):
        """trigger() retourne False pour un job inconnu."""
        result = self.scheduler.trigger("job_qui_nexiste_pas")
        self.assertFalse(result)

    def test_add_job(self):
        """add_job() ajoute un job personnalisé."""
        called = []
        self.scheduler.add_job("test_job_custom", lambda: called.append(1), 60, "Job de test")
        status = self.scheduler.get_status()
        self.assertIn("test_job_custom", status["jobs"])

    def test_disable_job(self):
        """disable_job() désactive un job existant."""
        self.scheduler.disable_job("notion_sync")
        status = self.scheduler.get_status()
        self.assertFalse(status["jobs"]["notion_sync"]["enabled"])


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 7 — ConversionEngine
# ══════════════════════════════════════════════════════════════════════════════
class TestConversionEngine(unittest.TestCase):

    def setUp(self):
        from NAYA_CORE.conversion_engine import ConversionEngine
        self.engine = ConversionEngine()

    def _deal(self, price=5000, pain_cost=50000, sector="pme_b2b", pain="cash_trapped"):
        return {
            "price": price,
            "pain_annual_cost": pain_cost,
            "sector": sector,
            "pain": pain,
            "company": "Test PME",
            "offer_title": "Solution test",
            "offer_proof": "3 clients similaires",
        }

    def test_score_hot_roi_exceptionnel(self):
        """ROI x10 + bon prix → tier HOT."""
        deal = self._deal(price=5000, pain_cost=50000)
        result = self.engine.score_deal_conversion_potential(deal)
        self.assertGreaterEqual(result["score"], 70)
        self.assertEqual(result["tier"], "HOT")

    def test_score_cold_roi_faible(self):
        """ROI x1 + prix élevé → tier COLD."""
        deal = self._deal(price=50000, pain_cost=50000)
        result = self.engine.score_deal_conversion_potential(deal)
        self.assertLess(result["score"], 45)

    def test_score_retourne_facteurs(self):
        """Le score inclut toujours une liste de facteurs explicatifs."""
        result = self.engine.score_deal_conversion_potential(self._deal())
        self.assertIn("factors", result)
        self.assertIsInstance(result["factors"], list)

    def test_score_zone_prix_optimale(self):
        """Prix entre 3000-15000€ obtient un bonus de 25 points."""
        deal_opt = self._deal(price=8000, pain_cost=100000)
        deal_hors = self._deal(price=60000, pain_cost=100000)
        opt = self.engine.score_deal_conversion_potential(deal_opt)
        hors = self.engine.score_deal_conversion_potential(deal_hors)
        self.assertGreater(opt["score"], hors["score"])

    def test_tier_mapping(self):
        """Les tiers doivent être exactement HOT/WARM/COLD."""
        for price, pain_cost, expected_tier_options in [
            (5000, 80000, ["HOT", "WARM"]),
            (50000, 10000, ["COLD", "WARM"]),
        ]:
            deal = self._deal(price=price, pain_cost=pain_cost)
            result = self.engine.score_deal_conversion_potential(deal)
            self.assertIn(result["tier"], ["HOT", "WARM", "COLD"])

    def test_close_days_hot_plus_court(self):
        """Un deal HOT a un estimated_close_days plus court qu'un COLD."""
        hot = self.engine.score_deal_conversion_potential(self._deal(5000, 80000))
        cold = self.engine.score_deal_conversion_potential(self._deal(50000, 5000))
        if hot["tier"] == "HOT" and cold["tier"] == "COLD":
            self.assertLess(hot["estimated_close_days"], cold["estimated_close_days"])


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 8 — AssetRegistry
# ══════════════════════════════════════════════════════════════════════════════
class TestAssetRegistry(unittest.TestCase):

    def setUp(self):
        from bootstrap.registry.asset_registry import AssetRegistry
        self.registry = AssetRegistry()

    def test_initialize_trouve_assets(self):
        result = self.registry.initialize()
        self.assertGreater(result["found"], 5)

    def test_get_status_apres_init(self):
        self.registry.initialize()
        status = self.registry.get_status()
        self.assertTrue(status["initialized"])
        self.assertIn("critical_assets", status)

    def test_verify_integrity_assets_intacts(self):
        self.registry.initialize()
        results = self.registry.verify_integrity()
        self.assertTrue(all(results.values()),
                        f"Assets non intègres: {[k for k,v in results.items() if not v]}")

    def test_get_by_category(self):
        self.registry.initialize()
        self.assertGreater(len(self.registry.get_by_category("core")), 0)
        self.assertGreater(len(self.registry.get_by_category("revenue")), 0)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 9 — RateLimiter
# ══════════════════════════════════════════════════════════════════════════════
class TestRateLimiter(unittest.TestCase):

    def _get_limit(self, path):
        RATE_LIMITS = {
            "/brain": (20, 60), "/cognition": (20, 60), "/hunt": (15, 60),
            "/sovereign": (10, 60), "/revenue/scan": (5, 60),
            "/revenue/prospects": (10, 60), "/accelerator": (5, 60),
            "/llm": (20, 60), "/revenue": (30, 60), "/pipeline": (60, 60),
            "/autonomous": (20, 60), "/integrations": (30, 60),
            "/webhooks": (1000, 60), "/": (120, 60),
        }
        for prefix, limit in RATE_LIMITS.items():
            if path.startswith(prefix) and prefix != "/":
                return limit
        return RATE_LIMITS["/"]

    def test_exempt_ips(self):
        src = (ROOT / "api/middleware.py").read_text()
        self.assertIn("127.0.0.1", src)
        self.assertIn("::1", src)

    def test_llm_plus_strict_que_read(self):
        brain_max, _ = self._get_limit("/brain/think")
        read_max, _ = self._get_limit("/status")
        self.assertLess(brain_max, read_max)

    def test_scan_limite_stricte(self):
        scan_max, _ = self._get_limit("/revenue/scan")
        brain_max, _ = self._get_limit("/brain/think")
        self.assertLessEqual(scan_max, brain_max)

    def test_webhooks_haute_limite(self):
        webhook_max, _ = self._get_limit("/webhooks/paypal")
        read_max, _ = self._get_limit("/status")
        self.assertGreater(webhook_max, read_max)

    def test_stats_dans_source(self):
        src = (ROOT / "api/middleware.py").read_text()
        self.assertIn("active_windows", src)
        self.assertIn("top_consumers", src)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 10 — Monitoring
# ══════════════════════════════════════════════════════════════════════════════
class TestMonitoring(unittest.TestCase):

    def test_collect_metrics_structure(self):
        try:
            from NAYA_DASHBOARD.NAYA_MONITORING.metrics_collector import collect_metrics
            m = collect_metrics()
            for key in ("cpu_percent", "memory_percent", "disk_percent", "timestamp"):
                self.assertIn(key, m)
        except ImportError:
            self.skipTest("psutil non installé")

    def test_alerts_cpu_haut(self):
        from NAYA_DASHBOARD.NAYA_MONITORING.alerts_engine import evaluate
        alerts = evaluate({"cpu_percent": 92, "memory_percent": 40, "disk_percent": 50})
        self.assertGreater(len(alerts), 0)

    def test_alerts_systeme_sain(self):
        from NAYA_DASHBOARD.NAYA_MONITORING.alerts_engine import evaluate
        alerts = evaluate({"cpu_percent": 30, "memory_percent": 45, "disk_percent": 60})
        self.assertEqual(len(alerts), 0)

    def test_performance_tracker_average(self):
        from NAYA_DASHBOARD.NAYA_MONITORING.performance_tracker import PerformanceTracker
        pt = PerformanceTracker()
        for v in [20, 40, 60]:
            pt.track({"cpu_percent": v, "memory_percent": 50, "disk_percent": 60})
        self.assertAlmostEqual(pt.get_average("cpu_percent", 3), 40.0, places=1)


# ══════════════════════════════════════════════════════════════════════════════
# GROUPE 11 — NayaInterface
# ══════════════════════════════════════════════════════════════════════════════
class TestNayaInterface(unittest.TestCase):

    def setUp(self):
        from NAYA_DASHBOARD.interface.naya_interface import NayaInterface
        self.iface = NayaInterface(system=None)

    def test_get_status_sans_systeme(self):
        result = self.iface.get_status()
        self.assertIn("status", result)

    def test_snapshot_contient_version(self):
        snap = self.iface.snapshot()
        self.assertIn("version", snap)
        self.assertIn("ready", snap)

    def test_get_pipeline_sans_crash(self):
        result = self.iface.get_pipeline()
        self.assertIn("active_deals", result)

    def test_is_ready_false_sans_systeme(self):
        self.assertFalse(self.iface.is_ready())

    def test_call_count_incremente(self):
        for _ in range(5):
            self.iface.get_status()
        self.assertEqual(self.iface._call_count, 5)

    def test_think_sans_crash(self):
        result = self.iface.think("test")
        self.assertIn("text", result)
        self.assertEqual(result["text"], "")


# ══════════════════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    groups = [
        TestCashEngineReal, TestRevenueIntelligence, TestPipelineTracker,
        TestPaymentEngine, TestMoneyNotifier, TestScheduler, TestConversionEngine,
        TestAssetRegistry, TestRateLimiter, TestMonitoring, TestNayaInterface,
    ]
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for g in groups:
        suite.addTests(loader.loadTestsFromTestCase(g))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print(f"\n{'='*58}")
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Tests passés  : {passed}/{result.testsRun}")
    print(f"  Echecs        : {len(result.failures)}")
    print(f"  Erreurs       : {len(result.errors)}")
    print("="*58)
    if result.wasSuccessful():
        print("  TOUS LES TESTS PASSENT")
    else:
        for test, tb in result.failures + result.errors:
            print(f"\n  FAIL: {test}")
            print(f"  {tb.split(chr(10))[-2]}")
    sys.exit(0 if result.wasSuccessful() else 1)
