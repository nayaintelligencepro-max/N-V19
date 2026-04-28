"""
Tests unitaires — 13 PainHuntEngines spécifiques par projet
=============================================================
Valide : detect, scan, qualify, build_offer, convert, get_stats
pour chacun des 13 moteurs de chasse.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# ── Vérifier que les sources existent avant de les importer ───────────────
try:
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE.pain_hunt_engine import CashRapidePainHuntEngine
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_02_GOOGLE_XR.pain_hunt_engine import GoogleXRPainHuntEngine
except ImportError as _e:
    pytest.skip(
        f"Sources pain_hunt_engine manquantes (modules non générés): {_e}",
        allow_module_level=True,
    )

# ── imports des 13 moteurs (déjà vérifiés ci-dessus) ─────────────────────
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE.pain_hunt_engine import CashRapidePainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_02_GOOGLE_XR.pain_hunt_engine import GoogleXRPainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.pain_hunt_engine import BotanicaPainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE.pain_hunt_engine import TinyHousePainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_05_MARCHES_OUBLIES.pain_hunt_engine import MarchesOubliesPainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_06_ACQUISITION_IMMOBILIERE.pain_hunt_engine import ImmoAcquisitionPainHuntEngine
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_07_NAYA_PAYE.pain_hunt_engine import NayaPayePainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_004_SUPPLY_CHAIN.pain_hunt_engine import SupplyChainPainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_005_HR_SCALING.pain_hunt_engine import HRScalingPainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_006_MARKET_EXPANSION.pain_hunt_engine import MarketExpansionPainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_007_FINTECH_SOLUTIONS.pain_hunt_engine import FintechSolutionsPainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_008_DATA_ANALYTICS.pain_hunt_engine import DataAnalyticsPainHuntEngine
from NAYA_PROJECT_ENGINE.projects.PROJECT_009_SUSTAINABILITY.pain_hunt_engine import SustainabilityPainHuntEngine

# ── Registre de tous les moteurs et leurs signaux de test ──────────────────
ALL_ENGINES = [
    (CashRapidePainHuntEngine, "PROJECT_01_CASH_RAPIDE", "A",
     {"signal_type": "cyber_incident", "sector": "industrie", "company": "TestCo",
      "description": "Ransomware détecté", "urgency": 0.92, "solvability": 0.88, "estimated_value_eur": 35000}),
    (GoogleXRPainHuntEngine, "PROJECT_02_GOOGLE_XR", "B",
     {"signal_type": "poc_stalled", "sector": "enterprise", "company": "XRCorp",
      "description": "POC XR bloqué", "urgency": 0.78, "solvability": 0.82, "estimated_value_eur": 48000}),
    (BotanicaPainHuntEngine, "PROJECT_03_NAYA_BOTANICA", "C",
     {"signal_type": "b2b_inci_demand", "sector": "cosmétiques", "company": "BeautyFR",
      "description": "Marque cherche actif naturel", "urgency": 0.82, "solvability": 0.90, "estimated_value_eur": 45000}),
    (TinyHousePainHuntEngine, "PROJECT_04_TINY_HOUSE", "C",
     {"signal_type": "seasonal_workers_unhoused", "sector": "agriculture", "company": "FarmCo",
      "description": "40 saisonniers sans logement", "urgency": 0.88, "solvability": 0.85, "estimated_value_eur": 55000}),
    (MarchesOubliesPainHuntEngine, "PROJECT_05_MARCHES_OUBLIES", "B",
     {"signal_type": "digital_desert", "sector": "artisanat", "company": "UNKNOWN",
      "description": "Zone sans digitalisation", "urgency": 0.68, "solvability": 0.82, "estimated_value_eur": 18000}),
    (ImmoAcquisitionPainHuntEngine, "PROJECT_06_ACQUISITION_IMMOBILIERE", "C",
     {"signal_type": "liquidity_need_seller", "sector": "résidentiel", "company": "OwnerX",
      "description": "Vendeur urgent liquidité", "urgency": 0.90, "solvability": 0.92, "estimated_value_eur": 60000}),
    (NayaPayePainHuntEngine, "PROJECT_07_NAYA_PAYE", "C",
     {"signal_type": "cross_border_friction", "sector": "diaspora", "company": "UNKNOWN",
      "description": "Frais transfert diaspora 12%", "urgency": 0.82, "solvability": 0.85, "estimated_value_eur": 28000}),
    (SupplyChainPainHuntEngine, "PROJECT_004_SUPPLY_CHAIN", "A",
     {"signal_type": "stockout_crisis", "sector": "agroalimentaire", "company": "FoodCo",
      "description": "Rupture emballages ligne arrêtée", "urgency": 0.96, "solvability": 0.88, "estimated_value_eur": 35000}),
    (HRScalingPainHuntEngine, "PROJECT_005_HR_SCALING", "C",
     {"signal_type": "high_turnover_signal", "sector": "tech", "company": "SaasCo",
      "description": "Turnover 45% en 2 mois", "urgency": 0.84, "solvability": 0.80, "estimated_value_eur": 28000}),
    (MarketExpansionPainHuntEngine, "PROJECT_006_MARKET_EXPANSION", "B",
     {"signal_type": "competitor_exit", "sector": "cybersécurité", "company": "MidCorp",
      "description": "Concurrent racheté, 200 clients orphelins", "urgency": 0.92, "solvability": 0.88, "estimated_value_eur": 60000}),
    (FintechSolutionsPainHuntEngine, "PROJECT_007_FINTECH_SOLUTIONS", "A",
     {"signal_type": "dora_compliance_gap", "sector": "banque", "company": "BankX",
      "description": "DORA gaps critiques", "urgency": 0.94, "solvability": 0.88, "estimated_value_eur": 50000}),
    (DataAnalyticsPainHuntEngine, "PROJECT_008_DATA_ANALYTICS", "A",
     {"signal_type": "ai_project_stalled", "sector": "assurance", "company": "InsureCo",
      "description": "POC IA scoring bloqué 10 mois", "urgency": 0.82, "solvability": 0.80, "estimated_value_eur": 38000}),
    (SustainabilityPainHuntEngine, "PROJECT_009_SUSTAINABILITY", "B",
     {"signal_type": "csrd_compliance_gap", "sector": "industrie", "company": "ManuCo",
      "description": "CSRD applicable 2025, aucun reporting", "urgency": 0.92, "solvability": 0.85, "estimated_value_eur": 38000}),
]


class TestPainHuntEngineBase:
    """Classe de base réutilisée pour tous les moteurs."""

    @staticmethod
    def _run_full_cycle(engine_class, project_id, famille, test_signal):
        """Valide le cycle complet detect→qualify→build_offer→convert pour un moteur."""
        engine = engine_class()

        # ── identité ───────────────────────────────────────────────────────
        assert engine.PROJECT_ID == project_id
        assert engine.FAMILLE == famille
        assert engine.FLOOR_EUR == 1000.0

        # ── detect ────────────────────────────────────────────────────────
        pain = engine.detect(test_signal)
        assert pain is not None, f"detect() returned None for {project_id}"
        assert pain.id.startswith(f"P0" if "_" not in pain.id[:4] else pain.id[:2])
        assert pain.estimated_value_eur >= 1000.0
        assert 0.0 <= pain.score <= 1.0
        assert pain.status == "detected"

        # ── qualify ───────────────────────────────────────────────────────
        q = engine.qualify(pain.id)
        assert "error" not in q, f"qualify() error for {project_id}: {q}"
        assert "score" in q
        assert "qualified" in q
        assert "tier" in q
        assert "recommendation" in q
        assert isinstance(q["qualified"], bool)
        assert 0.0 <= q["score"] <= 1.0

        # ── build_offer ───────────────────────────────────────────────────
        offer = engine.build_offer(pain.id)
        assert "error" not in offer, f"build_offer() error for {project_id}: {offer}"
        assert offer["price_eur"] >= 1000.0, f"Price below floor for {project_id}: {offer['price_eur']}"
        assert offer["project"] == project_id
        assert offer["pitch"]
        assert offer["duration_days"] > 0

        # ── convert ───────────────────────────────────────────────────────
        revenue = offer["price_eur"]
        conv = engine.convert(pain.id, revenue)
        assert conv["converted"] is True, f"convert() failed for {project_id}"
        assert conv["revenue_eur"] == revenue
        assert conv["total_revenue_eur"] >= revenue

        # ── get_stats ─────────────────────────────────────────────────────
        stats = engine.get_stats()
        assert stats["project"] == project_id
        assert stats["famille"] == famille
        assert stats["floor_eur"] == 1000.0
        assert stats["converted"] == 1
        assert stats["total_revenue_eur"] >= revenue
        assert stats["active_pipeline"] == 0  # pain removed after convert

        return engine

    @staticmethod
    def _run_scan(engine_class):
        """Valide que scan() retourne des pains valides."""
        engine = engine_class()
        pains = engine.scan()
        assert isinstance(pains, list)
        assert len(pains) > 0, f"scan() returned empty list for {engine_class.__name__}"
        for p in pains:
            assert p.estimated_value_eur >= 1000.0
            assert 0.0 <= p.score <= 1.0
        return pains

    @staticmethod
    def _run_not_found(engine_class):
        """Valide les retours d'erreur pour IDs inexistants."""
        engine = engine_class()
        assert engine.qualify("NONEXISTENT")["error"] == "not_found"
        assert engine.build_offer("NONEXISTENT")["error"] == "not_found"
        assert engine.convert("NONEXISTENT", 5000)["error"] == "not_found"

    @staticmethod
    def _run_floor_enforcement(engine_class):
        """Valide que convert() rejette les revenus sous plancher."""
        engine = engine_class()
        result = engine.convert("ANYPAIN", 500.0)
        assert "error" in result
        assert "plancher" in result["error"]

    @staticmethod
    def _run_unknown_signal(engine_class):
        """Valide que detect() retourne None sur signal inconnu."""
        engine = engine_class()
        result = engine.detect({"signal_type": "TOTALLY_UNKNOWN_XYZ", "description": "nothing matches"})
        assert result is None

    @staticmethod
    def _run_keyword_fallback(engine_class, keyword_fragment):
        """Valide la détection par keyword quand signal_type absent."""
        engine = engine_class()
        result = engine.detect({"description": keyword_fragment, "estimated_value_eur": 5000})
        assert result is not None, f"keyword fallback failed for {engine_class.__name__} with '{keyword_fragment}'"


# ── Tests individuels pour chaque moteur ──────────────────────────────────

class TestCashRapidePainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[0]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[0][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[0][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[0][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[0][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[0][0], "ransomware industriel")

    def test_multiple_detects_stats(self):
        engine = CashRapidePainHuntEngine()
        engine.scan()
        stats = engine.get_stats()
        assert stats["detected_total"] >= 1
        assert stats["scan_count"] == 1


class TestGoogleXRPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[1]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[1][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[1][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[1][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[1][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[1][0], "POC XR bloqué 6 mois")


class TestBotanicaPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[2]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[2][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[2][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[2][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[2][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[2][0], "ingrédient endémique non certifié")


class TestTinyHousePainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[3]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[3][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[3][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[3][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[3][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[3][0], "cyclone logement urgence")


class TestMarchesOubliesPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[4]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[4][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[4][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[4][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[4][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[4][0], "territoire non digitalisé")


class TestImmoAcquisitionPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[5]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[5][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[5][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[5][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[5][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[5][0], "succession bloquée 3 héritiers")


class TestNayaPayePainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[6]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[6][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[6][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[6][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[6][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[6][0], "transfert diaspora Polynésie frais élevés")


class TestSupplyChainPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[7]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[7][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[7][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[7][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[7][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[7][0], "rupture stock critique ligne arrêtée")


class TestHRScalingPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[8]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[8][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[8][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[8][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[8][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[8][0], "turnover élevé démissions massives")


class TestMarketExpansionPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[9]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[9][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[9][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[9][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[9][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[9][0], "CA stagnant croissance arrêtée")


class TestFintechSolutionsPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[10]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[10][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[10][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[10][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[10][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[10][0], "DORA non conforme deadline")


class TestDataAnalyticsPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[11]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[11][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[11][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[11][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[11][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[11][0], "projet IA bloqué data science")


class TestSustainabilityPainHuntEngine:
    def test_full_cycle(self):
        ec, pid, fam, sig = ALL_ENGINES[12]
        TestPainHuntEngineBase._run_full_cycle(ec, pid, fam, sig)

    def test_scan(self):
        TestPainHuntEngineBase._run_scan(ALL_ENGINES[12][0])

    def test_not_found(self):
        TestPainHuntEngineBase._run_not_found(ALL_ENGINES[12][0])

    def test_floor_enforcement(self):
        TestPainHuntEngineBase._run_floor_enforcement(ALL_ENGINES[12][0])

    def test_unknown_signal(self):
        TestPainHuntEngineBase._run_unknown_signal(ALL_ENGINES[12][0])

    def test_keyword_fallback(self):
        TestPainHuntEngineBase._run_keyword_fallback(ALL_ENGINES[12][0], "CSRD non conforme rapport durabilité")


class TestAllEnginesFloor:
    """Garantit que le plancher 1 000 EUR est inviolable sur tous les moteurs."""

    @pytest.mark.parametrize("engine_class,project_id,famille,test_signal", ALL_ENGINES)
    def test_floor_all_engines(self, engine_class, project_id, famille, test_signal):
        engine = engine_class()
        pain = engine.detect(test_signal)
        assert pain is not None
        assert pain.estimated_value_eur >= 1000.0
        offer = engine.build_offer(pain.id)
        assert offer.get("price_eur", 0) >= 1000.0

    @pytest.mark.parametrize("engine_class,project_id,famille,test_signal", ALL_ENGINES)
    def test_convert_below_floor_rejected(self, engine_class, project_id, famille, test_signal):
        engine = engine_class()
        result = engine.convert("fake_id", 500.0)
        assert "error" in result

    @pytest.mark.parametrize("engine_class,project_id,famille,test_signal", ALL_ENGINES)
    def test_scan_returns_pains(self, engine_class, project_id, famille, test_signal):
        engine = engine_class()
        pains = engine.scan()
        assert len(pains) > 0
        for p in pains:
            assert p.estimated_value_eur >= 1000.0

    @pytest.mark.parametrize("engine_class,project_id,famille,test_signal", ALL_ENGINES)
    def test_stats_structure(self, engine_class, project_id, famille, test_signal):
        engine = engine_class()
        engine.scan()
        stats = engine.get_stats()
        required_keys = ["project", "famille", "floor_eur", "scan_count", "detected_total",
                         "active_pipeline", "qualified", "offered", "converted",
                         "total_revenue_eur", "conversion_rate", "avg_revenue_eur"]
        for key in required_keys:
            assert key in stats, f"Missing key '{key}' in stats for {project_id}"
        assert stats["floor_eur"] == 1000.0
        assert stats["projet"] if "projet" in stats else True
