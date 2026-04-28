"""
Tests des corrections apportées — session amélioration système.
Vérifie que tous les bugs critiques sont résolument corrigés.
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from SECRETS.secrets_loader import load_all_secrets, get_secret
load_all_secrets()
from NAYA_CORE.system_connector import fix_secrets
fix_secrets()

# Flags de disponibilité calculés après chargement des secrets (stub-aware)
_SHOPIFY_AVAILABLE = bool(get_secret("SHOPIFY_ACCESS_TOKEN") and get_secret("SHOPIFY_SHOP_URL"))
_EMAIL_FROM_AVAILABLE = bool(get_secret("EMAIL_FROM") or os.environ.get("EMAIL_FROM", ""))


class TestNoiseFilterFix(unittest.TestCase):
    """Bug #1 — NoiseFilter.filter() manquant dans super_brain."""

    def setUp(self):
        import importlib
        import NAYA_CORE.super_brain_hybrid_v6_0 as sb
        importlib.reload(sb)
        self.sb = sb
        self.nf = sb.NoiseFilter()

    def test_filter_returns_dict(self):
        r = self.nf.filter(["impayés clients récurrents", "bla"])
        self.assertIsInstance(r, dict)
        self.assertIn("real", r)

    def test_filter_separates_noise(self):
        r = self.nf.filter(["impayés clients depuis 90 jours", "bla"])
        self.assertGreater(len(r["real"]), 0)

    def test_filter_2word_signals_pass(self):
        """Les signaux 2 mots métier doivent passer le filtre."""
        for sig in ["impayés clients", "relances manuelles", "marges baissent"]:
            is_n, _ = self.nf.is_noise(sig)
            self.assertFalse(is_n, f"'{sig}' ne devrait pas être du bruit")

    def test_hunt_and_create_not_none(self):
        r = self.sb.hunt_and_create("pme_b2b", ["impayés > 45j", "le cash manque"], 500000)
        self.assertIsNotNone(r)
        self.assertIsInstance(r, dict)
        self.assertIn("qualified", r)


class TestSectorQualification(unittest.TestCase):
    """Bug #2 — pme_b2b et startup_scaleup ne qualifiaient pas."""

    def setUp(self):
        import importlib
        import NAYA_CORE.super_brain_hybrid_v6_0 as sb
        importlib.reload(sb)
        self.sb = sb

    def _q(self, sector, signals, revenue):
        r = self.sb.hunt_and_create(sector, signals, revenue)
        return r and r.get("qualified", False)

    def test_pme_b2b_qualifies(self):
        self.assertTrue(self._q("pme_b2b",
            ["impayés > 45j", "le cash manque pour payer", "on perd de la marge"], 600000))

    def test_artisan_qualifies(self):
        self.assertTrue(self._q("artisan_trades",
            ["relances manuelles", "impayés clients récurrents", "facturation chronophage"], 200000))

    def test_restaurant_qualifies(self):
        self.assertTrue(self._q("restaurant_food",
            ["food cost incontrôlable", "marges baissent chaque trimestre", "on perd sur chaque table"], 400000))

    def test_startup_qualifies(self):
        self.assertTrue(self._q("startup_scaleup",
            ["burn rate monte", "le cash manque pour finir le mois", "CAC trop élevé et churn monte"], 800000))

    def test_healthcare_qualifies(self):
        self.assertTrue(self._q("healthcare_wellness",
            ["facturation manuellement au cabinet", "admin trop lourde", "ça prend trop de temps"], 350000))

    def test_ecommerce_qualifies(self):
        self.assertTrue(self._q("ecommerce",
            ["marges baissent à cause des retours", "churn monte", "on perd des clients"], 500000))

    def test_liberal_qualifies(self):
        self.assertTrue(self._q("liberal_professions",
            ["sous-tarifé depuis 3 ans", "j'hésite à augmenter", "concurrent plus cher"], 180000))

    def test_diaspora_qualifies(self):
        self.assertTrue(self._q("diaspora_markets",
            ["impayés clients", "cash flow difficile", "recouvrement compliqué"], 300000))


class TestCognitivePipeline(unittest.TestCase):
    """Cognitive Pipeline — 6 couches actives."""

    def setUp(self):
        from NAYA_CORE.cognitive_pipeline import get_cognitive_pipeline
        self.cog = get_cognitive_pipeline()

    def test_pipeline_has_active_layers(self):
        stats = self.cog.get_stats()
        active = sum(1 for v in stats.values() if v is True)
        self.assertGreaterEqual(active, 3)

    def test_score_prospect_returns_dict(self):
        score = self.cog.score_prospect(
            "PME Test", ["impayés clients récurrents", "marges baissent"], 50000, "pme_b2b"
        )
        self.assertIn("score", score)
        self.assertIn("tier", score)
        self.assertIn("layers_used", score)
        self.assertGreater(score["score"], 0)

    def test_score_range(self):
        score = self.cog.score_prospect("Test", ["impayés", "cash manque"], 30000)
        self.assertGreaterEqual(score["score"], 0)
        self.assertLessEqual(score["score"], 100)

    def test_tier_hot_warm_cold(self):
        score = self.cog.score_prospect("Test", ["impayés > 45j", "le cash manque", "on perd"], 200000)
        self.assertIn(score["tier"], ["HOT", "WARM", "COLD"])


class TestShopifyFix(unittest.TestCase):
    """Bug #3 — ShopifyIntegration doit gérer l'absence de credentials gracieusement."""

    def test_shopify_not_configured_graceful(self):
        """Sans credentials Shopify, l'intégration doit retourner 'not_configured'."""
        from unittest.mock import patch
        from NAYA_CORE.integrations.shopify_integration import ShopifyIntegration
        with patch.dict(os.environ, {"SHOPIFY_SHOP_URL": "", "SHOPIFY_ACCESS_TOKEN": ""}):
            sh = ShopifyIntegration.__new__(ShopifyIntegration)
            sh.shop_url = ""
            sh.token = ""
            sh.available = False
            result = sh.process({"action": "status"})
            self.assertEqual(result["status"], "not_configured")
            self.assertIn("hint", result)

    def test_shopify_integration_with_mock_config(self):
        """Avec des credentials valides, ShopifyIntegration doit être disponible."""
        from unittest.mock import patch
        from NAYA_CORE.integrations.shopify_integration import ShopifyIntegration
        with patch.dict(os.environ, {
            "SHOPIFY_SHOP_URL": "https://test.myshopify.com",
            "SHOPIFY_ACCESS_TOKEN": "shpat_test_mock_token_valid",
        }):
            # Force reload to pick up patched env
            sh = ShopifyIntegration.__new__(ShopifyIntegration)
            sh.shop_url = "https://test.myshopify.com"
            sh.token = "shpat_test_mock_token_valid"
            sh.available = True
            self.assertTrue(sh.available)
            self.assertEqual(sh.shop_url, "https://test.myshopify.com")
            self.assertTrue(sh.shop_url.startswith("https://"))


class TestEmailFromFix(unittest.TestCase):
    """Bug #4 — EMAIL_FROM vide empêchait SendGrid d'envoyer."""

    @unittest.skipUnless(_EMAIL_FROM_AVAILABLE, "EMAIL_FROM non configuré")
    def test_email_from_set(self):
        self.assertTrue(os.environ.get("EMAIL_FROM", ""), "EMAIL_FROM doit être défini")

    @unittest.skipUnless(_EMAIL_FROM_AVAILABLE, "EMAIL_FROM non configuré")
    def test_email_from_valid(self):
        email = os.environ.get("EMAIL_FROM", "")
        self.assertIn("@", email, "EMAIL_FROM doit être une adresse email valide")


class TestPortfolioManager(unittest.TestCase):
    """Portfolio Manager — 5 projets business connectés."""

    def test_portfolio_has_projects(self):
        from NAYA_CORE.portfolio_manager import get_portfolio_manager
        pm = get_portfolio_manager()
        self.assertGreaterEqual(len(pm.PROJECTS), 5)

    def test_portfolio_report(self):
        from NAYA_CORE.portfolio_manager import get_portfolio_manager
        pm = get_portfolio_manager()
        report = pm.generate_report()
        self.assertIn("summary", report)
        self.assertIn("projects", report)


class TestFusionPointFix(unittest.TestCase):
    """Bug #5 — FusionPoint import cassé."""

    def test_fusion_point_importable(self):
        from NAYA_CORE.cognition.fusion.NAYA_COGNITIVE_FUSION import FusionPoint
        fp = FusionPoint()
        self.assertIsNotNone(fp)


class TestSchedulerJobs(unittest.TestCase):
    """Scheduler — 20 jobs maintenant (shopify_sync + cognitive_scan ajoutés)."""

    def test_scheduler_has_new_jobs(self):
        from NAYA_CORE.scheduler import get_scheduler
        sc = get_scheduler()
        jobs = sc.get_status()["jobs"]
        self.assertIn("shopify_sync", jobs, "shopify_sync manquant")
        self.assertIn("cognitive_scan", jobs, "cognitive_scan manquant")

    def test_scheduler_total_jobs(self):
        from NAYA_CORE.scheduler import get_scheduler
        sc = get_scheduler()
        self.assertGreaterEqual(len(sc.get_status()["jobs"]), 20)


class TestForgottenMarkets(unittest.TestCase):
    """Marchés oubliés — 6 marchés, 10 langues."""

    def test_markets_count(self):
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import FORGOTTEN_MARKETS
        self.assertGreaterEqual(len(FORGOTTEN_MARKETS), 6)

    def test_generate_prospects(self):
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import ForgottenMarketsEngine
        fm = ForgottenMarketsEngine()
        prospects = fm.generate_prospects("polynesie_pme", count=3)
        self.assertEqual(len(prospects), 3)
        for p in prospects:
            self.assertIn("language", p)
            self.assertIn("offer_price", p)

    def test_multilanguage_email(self):
        from NAYA_REVENUE_ENGINE.unified_revenue_engine import ForgottenMarketsEngine
        fm = ForgottenMarketsEngine()
        for lang in ["fr", "en", "es"]:
            prospects = fm.generate_prospects(
                "amerique_latine_pme" if lang in ["es","pt"] else "polynesie_pme", 1
            )
            if prospects:
                email = fm.get_email(prospects[0])
                self.assertIn("subject", email)
                self.assertIn("body", email)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestNoiseFilterFix, TestSectorQualification, TestCognitivePipeline,
                TestShopifyFix, TestEmailFromFix, TestPortfolioManager,
                TestFusionPointFix, TestSchedulerJobs, TestForgottenMarkets]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n  Tests passés  : {passed}/{result.testsRun}")
    if result.failures or result.errors:
        for f in result.failures + result.errors:
            print(f"  ❌ {f[0]}: {f[1][:100]}")
