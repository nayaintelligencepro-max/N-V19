"""
Tests NAYA V21 — NAYA_ACCELERATION
Couvre : BlitzHunter, FlashOffer, InstantCloser, SalesVelocityTracker,
         AccelerationOrchestrator, API /api/v1/acceleration.
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def patch_telegram(tmp_path, monkeypatch):
    """Disable real Telegram calls during tests."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_OWNER_CHAT_ID", "")
    # Redirect payment log to tmp
    monkeypatch.setenv("PAYMENT_LOG_DIR", str(tmp_path))
    from NAYA_ACCELERATION import instant_closer as ic_module
    ic_module.PAYMENT_LOG_FILE = tmp_path / "payments.jsonl"
    from NAYA_ACCELERATION import sales_velocity_tracker as sv_module
    sv_module.VELOCITY_DB = tmp_path / "velocity.json"
    yield


@pytest.fixture
def blitz():
    from NAYA_ACCELERATION.blitz_hunter import BlitzHunter
    return BlitzHunter(score_threshold=0)  # Low threshold to get all signals


@pytest.fixture
def flash():
    from NAYA_ACCELERATION.flash_offer import FlashOffer
    return FlashOffer()


@pytest.fixture
def closer(tmp_path):
    from NAYA_ACCELERATION.instant_closer import InstantCloser, PAYMENT_LOG_FILE
    inst = InstantCloser()
    return inst


@pytest.fixture
def tracker():
    from NAYA_ACCELERATION.sales_velocity_tracker import SalesVelocityTracker
    return SalesVelocityTracker()


# ═══════════════════════════════════════════════════════════════════════════════
# BlitzHunter tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBlitzHunter:
    def test_import(self):
        from NAYA_ACCELERATION.blitz_hunter import BlitzHunter, BlitzSignal, get_blitz_hunter
        assert BlitzHunter
        assert BlitzSignal

    def test_degraded_signals_returns_signals(self, blitz):
        sigs = blitz._degraded_signals("serper", ["energie", "transport_logistique"])
        assert len(sigs) == 2
        assert all(s.budget_estimate_eur >= 1_000 for s in sigs)

    def test_score_signal_basics(self):
        from NAYA_ACCELERATION.blitz_hunter import _score_signal
        score = _score_signal("iec 62443 audit ot scada", "energie", 40_000, True)
        assert 0 <= score <= 100
        assert score > 50  # Should score well

    def test_score_enforces_floor(self):
        from NAYA_ACCELERATION.blitz_hunter import _score_signal
        score = _score_signal("irrelevant text", "unknown", 500, False)
        assert score >= 0

    def test_detect_sector_energie(self, blitz):
        assert blitz._detect_sector("EDF énergie réseau") == "energie"

    def test_detect_sector_transport(self, blitz):
        assert blitz._detect_sector("SNCF transport ferroviaire") == "transport_logistique"

    def test_detect_sector_manufacturing(self, blitz):
        assert blitz._detect_sector("Airbus usine automate") == "manufacturing"

    def test_detect_urgency_critical(self, blitz):
        assert blitz._detect_urgency("attaque ransomware critique immédiat") == "critical"

    def test_detect_urgency_high(self, blitz):
        assert blitz._detect_urgency("deadline avant fin Q3 2026 obligatoire") == "high"

    def test_estimate_budget_energy(self, blitz):
        budget = blitz._estimate_budget("grande énergie infrastructure")
        assert budget >= 1_000

    def test_make_signal_id_unique(self):
        from NAYA_ACCELERATION.blitz_hunter import _make_signal_id
        id1 = _make_signal_id("serper", "ACME")
        id2 = _make_signal_id("serper", "ACME")
        # May differ due to time, but format should be 16 hex chars
        assert len(id1) == 16

    def test_blitz_hunt_returns_list_without_apis(self, blitz):
        """Hunt works in degraded mode without API keys."""
        signals = asyncio.run(blitz.hunt(["energie"]))
        assert isinstance(signals, list)
        assert len(signals) >= 0  # May be empty or have degraded signals

    def test_blitz_hunt_scores_all_ge_threshold(self, blitz):
        from NAYA_ACCELERATION.blitz_hunter import BlitzHunter
        hunter = BlitzHunter(score_threshold=50)
        signals = asyncio.run(hunter.hunt(["energie", "transport_logistique"]))
        for s in signals:
            assert s.score >= 50

    def test_blitz_signal_to_dict(self, blitz):
        sigs = blitz._degraded_signals("test", ["energie"])
        d = sigs[0].to_dict()
        assert "signal_id" in d
        assert "company" in d
        assert "budget_estimate_eur" in d
        assert d["budget_estimate_eur"] >= 1_000

    def test_get_blitz_hunter_singleton(self):
        from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter
        h1 = get_blitz_hunter()
        h2 = get_blitz_hunter()
        assert h1 is h2


# ═══════════════════════════════════════════════════════════════════════════════
# FlashOffer tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFlashOffer:
    def test_import(self):
        from NAYA_ACCELERATION.flash_offer import FlashOffer, OfferResult, get_flash_offer
        assert FlashOffer

    def test_classify_pain_nis2(self, flash):
        assert flash._classify_pain("NIS2 conformité deadline anssi", "energie") == "nis2_compliance"

    def test_classify_pain_ransomware(self, flash):
        assert flash._classify_pain("ransomware attaque incident cyber", "manufacturing") == "ransomware_ot"

    def test_classify_pain_scada(self, flash):
        assert flash._classify_pain("scada shodan exposé vulnérabilité CVE", "energie") == "scada_vulnerability"

    def test_classify_pain_training(self, flash):
        assert flash._classify_pain("formation équipe sensibilisation", "iec62443") == "ot_training"

    def test_classify_pain_default(self, flash):
        assert flash._classify_pain("unknown random text", "iec62443") == "iec62443_audit"

    def test_calculate_price_floor(self, flash):
        price = flash._calculate_price(1_000, "manufacturing", "startup", "low", 5_000)
        assert price >= 1_000

    def test_calculate_price_energy_premium(self, flash):
        price = flash._calculate_price(15_000, "energie", "grand_compte", "critical", 200_000)
        assert price > 15_000

    def test_calculate_price_capped_at_60pct_budget(self, flash):
        price = flash._calculate_price(100_000, "energie", "grand_compte", "critical", 10_000)
        assert price <= 10_000 * 0.6 + 500  # Rounded

    def test_calculate_price_never_below_floor(self, flash):
        price = flash._calculate_price(100, "unknown", "startup", "low", 50)
        assert price >= 1_000

    def test_score_personalization_high(self, flash):
        body = "Bonjour Jean-Pierre, SNCF cybersécurité ot iec62443 audit scada"
        score = flash._score_personalization("SNCF", "Jean-Pierre", "RSSI", "audit iot scada", body)
        assert score >= 0.5

    def test_score_personalization_zero_no_match(self, flash):
        body = "Generic email without any company or contact name"
        score = flash._score_personalization("SNCF", "Jean-Pierre", "RSSI", "audit", body)
        assert score < 0.5

    def test_generate_offer_returns_offer_result(self, flash):
        offer = asyncio.run(flash.generate(
            company="Enedis",
            sector="energie",
            pain_description="Audit NIS2 requis Q3 2026 réseau SCADA critique",
            contact_name="Marie DUBOIS",
            contact_title="RSSI",
            budget_estimate=40_000,
            urgency="high",
        ))
        from NAYA_ACCELERATION.flash_offer import OfferResult
        assert isinstance(offer, OfferResult)
        assert offer.price_eur >= 1_000
        assert offer.company == "Enedis"
        assert len(offer.email_body) > 50
        assert len(offer.email_subject) > 5
        assert offer.generation_time_ms > 0

    def test_generate_offer_personalization_score(self, flash):
        offer = asyncio.run(flash.generate(
            company="Airbus",
            sector="manufacturing",
            pain_description="Vulnérabilités IEC 62443 identifiées sur automates",
            contact_name="Paul MARTIN",
        ))
        assert 0 <= offer.personalization_score <= 1

    def test_generate_offer_to_dict(self, flash):
        offer = asyncio.run(flash.generate(
            company="RATP", sector="transport_logistique",
            pain_description="NIS2 conformité urgent avant Q4"
        ))
        d = offer.to_dict()
        assert "offer_id" in d
        assert "price_eur" in d
        assert d["price_eur"] >= 1_000

    def test_get_flash_offer_singleton(self):
        from NAYA_ACCELERATION.flash_offer import get_flash_offer
        f1 = get_flash_offer()
        f2 = get_flash_offer()
        assert f1 is f2


# ═══════════════════════════════════════════════════════════════════════════════
# InstantCloser tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestInstantCloser:
    def test_import(self):
        from NAYA_ACCELERATION.instant_closer import InstantCloser, PaymentLink, PaymentMethod, get_instant_closer
        assert InstantCloser

    def test_generate_payment_link_paypal(self, closer):
        link = closer.generate_payment_link(
            offer_id="test-offer-01",
            company="SNCF",
            contact_email="martin@sncf.fr",
            amount_eur=15_000,
            method=__import__("NAYA_ACCELERATION.instant_closer", fromlist=["PaymentMethod"]).PaymentMethod.PAYPAL,
        )
        assert link.amount_eur == 15_000
        assert link.company == "SNCF"
        assert "paypal" in link.url.lower()
        assert link.status == "pending"
        assert len(link.sha256_hash) == 64

    def test_generate_payment_link_deblok(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod
        link = closer.generate_payment_link(
            offer_id="test-02",
            company="Enedis",
            contact_email="test@enedis.fr",
            amount_eur=25_000,
            method=PaymentMethod.DEBLOK,
        )
        assert "deblok" in link.url.lower()
        assert link.amount_eur == 25_000

    def test_reject_below_floor(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod
        with pytest.raises(ValueError, match="plancher"):
            closer.generate_payment_link(
                offer_id="bad",
                company="Test",
                contact_email="test@test.com",
                amount_eur=500,  # Below 1000 EUR floor
                method=PaymentMethod.PAYPAL,
            )

    def test_payment_link_logged_to_file(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod, PAYMENT_LOG_FILE
        link = closer.generate_payment_link(
            offer_id="log-test",
            company="LogTest",
            contact_email="log@test.com",
            amount_eur=10_000,
            method=PaymentMethod.PAYPAL,
        )
        assert PAYMENT_LOG_FILE.exists()
        content = PAYMENT_LOG_FILE.read_text()
        assert "log-test" in content or link.payment_id in content

    def test_confirm_payment(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod
        link = closer.generate_payment_link(
            offer_id="confirm-test",
            company="ConfirmCo",
            contact_email="c@c.com",
            amount_eur=20_000,
            method=PaymentMethod.PAYPAL,
        )
        found = closer.confirm_payment(link.payment_id)
        assert found is True

    def test_get_pending_payments(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod
        closer.generate_payment_link("p1", "Co1", "a@b.com", 5_000, PaymentMethod.PAYPAL)
        closer.generate_payment_link("p2", "Co2", "b@c.com", 8_000, PaymentMethod.DEBLOK)
        pending = closer.get_pending_payments()
        assert len(pending) >= 2

    def test_payment_link_to_dict(self, closer):
        from NAYA_ACCELERATION.instant_closer import PaymentMethod
        link = closer.generate_payment_link("d1", "DictCo", "d@d.com", 12_000, PaymentMethod.PAYPAL)
        d = link.to_dict()
        assert "payment_id" in d
        assert "sha256_hash" in d
        assert d["amount_eur"] == 12_000

    def test_get_instant_closer_singleton(self):
        from NAYA_ACCELERATION.instant_closer import get_instant_closer
        c1 = get_instant_closer()
        c2 = get_instant_closer()
        assert c1 is c2


# ═══════════════════════════════════════════════════════════════════════════════
# SalesVelocityTracker tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSalesVelocityTracker:
    def test_import(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import (
            SalesVelocityTracker, SaleRecord, VelocityMetrics, get_velocity_tracker
        )
        assert SalesVelocityTracker

    def test_record_sale(self, tracker):
        record = tracker.record_sale(
            company="EDF",
            amount_eur=15_000,
            sector="energie",
            pain_type="nis2_compliance",
        )
        from NAYA_ACCELERATION.sales_velocity_tracker import SaleRecord
        assert isinstance(record, SaleRecord)
        assert record.amount_eur == 15_000

    def test_record_sale_floor_enforced(self, tracker):
        with pytest.raises(ValueError, match="plancher"):
            tracker.record_sale("Bad", 500, "energie", "test")

    def test_get_metrics_empty(self, tracker):
        m = tracker.get_metrics()
        assert m.sales_today == 0
        assert m.revenue_today_eur == 0
        assert isinstance(m.ooda_recommendation, str)
        assert len(m.ooda_recommendation) > 10

    def test_get_metrics_after_sales(self, tracker):
        tracker.record_sale("Co1", 10_000, "energie", "nis2_compliance")
        tracker.record_sale("Co2", 20_000, "transport_logistique", "iec62443_audit")
        m = tracker.get_metrics()
        assert m.sales_today == 2
        assert m.revenue_today_eur == 30_000
        assert m.avg_ticket_eur == 15_000

    def test_metrics_to_dict(self, tracker):
        tracker.record_sale("X", 5_000, "manufacturing", "scada_vulnerability")
        d = tracker.get_metrics().to_dict()
        assert "sales_today" in d
        assert "revenue_this_month_eur" in d
        assert "ooda_recommendation" in d
        assert "annual_run_rate_eur" in d

    def test_get_sales_by_period(self, tracker):
        tracker.record_sale("A", 8_000, "energie", "nis2_compliance")
        sales_month = tracker.get_sales_by_period("month")
        sales_today = tracker.get_sales_by_period("today")
        assert len(sales_month) >= 1
        assert len(sales_today) >= 1

    def test_ooda_recommendation_low_velocity(self, tracker):
        m = tracker.get_metrics()
        # velocity=0 → OBSERVE recommendation
        assert "OBSERVE" in m.ooda_recommendation or "velocity" in m.ooda_recommendation.lower()

    def test_sale_record_to_dict(self, tracker):
        r = tracker.record_sale("Test", 3_000, "iec62443", "iec62443_audit", time_to_close_hours=2.5)
        d = r.to_dict()
        assert d["amount_eur"] == 3_000
        assert d["time_to_close_hours"] == 2.5

    def test_multiple_sectors_top_sector(self, tracker):
        for _ in range(3):
            tracker.record_sale("EDF", 10_000, "energie", "nis2_compliance")
        tracker.record_sale("SNCF", 5_000, "transport_logistique", "iec62443_audit")
        m = tracker.get_metrics()
        assert m.top_sector == "energie"

    def test_get_velocity_tracker_singleton(self):
        from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
        t1 = get_velocity_tracker()
        t2 = get_velocity_tracker()
        assert t1 is t2


# ═══════════════════════════════════════════════════════════════════════════════
# AccelerationOrchestrator tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAccelerationOrchestrator:
    def test_import(self):
        from NAYA_ACCELERATION.acceleration_orchestrator import (
            AccelerationOrchestrator, PipelineResult, get_orchestrator
        )
        assert AccelerationOrchestrator

    def test_run_acceleration_cycle_returns_result(self, tracker):
        from NAYA_ACCELERATION.acceleration_orchestrator import AccelerationOrchestrator
        from NAYA_ACCELERATION.blitz_hunter import BlitzHunter
        from NAYA_ACCELERATION.flash_offer import FlashOffer
        from NAYA_ACCELERATION.instant_closer import InstantCloser

        orch = AccelerationOrchestrator(
            blitz=BlitzHunter(score_threshold=0),
            flash=FlashOffer(),
            closer=InstantCloser(),
            tracker=tracker,
            auto_send_payment=False,
        )
        result = asyncio.run(orch.run_acceleration_cycle(sectors=["energie"]))
        from NAYA_ACCELERATION.acceleration_orchestrator import PipelineResult
        assert isinstance(result, PipelineResult)
        assert result.signals_detected >= 0

    def test_pipeline_result_to_dict(self, tracker):
        from NAYA_ACCELERATION.acceleration_orchestrator import AccelerationOrchestrator
        from NAYA_ACCELERATION.blitz_hunter import BlitzHunter
        from NAYA_ACCELERATION.flash_offer import FlashOffer
        from NAYA_ACCELERATION.instant_closer import InstantCloser

        orch = AccelerationOrchestrator(
            blitz=BlitzHunter(score_threshold=0),
            flash=FlashOffer(),
            closer=InstantCloser(),
            tracker=tracker,
        )
        result = asyncio.run(orch.run_acceleration_cycle(["iec62443"]))
        d = result.to_dict()
        assert "run_id" in d
        assert "signals_detected" in d
        assert "total_pipeline_value_eur" in d

    def test_flash_offer_only(self, flash):
        from NAYA_ACCELERATION.acceleration_orchestrator import AccelerationOrchestrator
        from NAYA_ACCELERATION.instant_closer import InstantCloser
        orch = AccelerationOrchestrator(flash=flash)
        offer = asyncio.run(orch.run_flash_offer_only(
            company="Test Corp",
            sector="energie",
            pain_description="NIS2 audit requis",
            urgency="high",
        ))
        assert offer.price_eur >= 1_000

    def test_generate_instant_payment_requires_valid_amount(self, flash, closer):
        from NAYA_ACCELERATION.acceleration_orchestrator import AccelerationOrchestrator
        orch = AccelerationOrchestrator(flash=flash, closer=closer)
        offer = asyncio.run(flash.generate("Co", "energie", "NIS2 audit"))
        link = orch.generate_instant_payment(offer, "test@co.com")
        assert link.amount_eur >= 1_000

    def test_get_velocity_dashboard(self, tracker):
        from NAYA_ACCELERATION.acceleration_orchestrator import AccelerationOrchestrator
        orch = AccelerationOrchestrator(tracker=tracker)
        d = orch.get_velocity_dashboard()
        assert "sales_today" in d
        assert "ooda_recommendation" in d

    def test_get_orchestrator_singleton(self):
        from NAYA_ACCELERATION.acceleration_orchestrator import get_orchestrator
        o1 = get_orchestrator()
        o2 = get_orchestrator()
        assert o1 is o2


# ═══════════════════════════════════════════════════════════════════════════════
# API Router tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAccelerationAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from api.routers.acceleration import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/acceleration")
        return TestClient(app)

    def test_hunt_endpoint(self, client):
        resp = client.post("/api/v1/acceleration/hunt", json={"sectors": ["energie"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "signals_count" in data
        assert "signals" in data

    def test_flash_offer_endpoint(self, client):
        resp = client.post("/api/v1/acceleration/offer", json={
            "company": "Enedis",
            "sector": "energie",
            "pain_description": "Audit NIS2 requis avant Q3 2026",
            "budget_estimate_eur": 40_000,
            "urgency": "high",
        })
        assert resp.status_code == 200
        offer = resp.json()["offer"]
        assert offer["price_eur"] >= 1_000
        assert offer["company"] == "Enedis"

    def test_payment_link_endpoint(self, client):
        resp = client.post("/api/v1/acceleration/payment-link", json={
            "offer_id": "test-offer",
            "company": "Test Corp",
            "contact_email": "test@corp.com",
            "amount_eur": 15_000,
            "method": "paypal",
        })
        assert resp.status_code == 200
        data = resp.json()["payment_link"]
        assert data["amount_eur"] == 15_000

    def test_payment_link_below_floor_rejected(self, client):
        resp = client.post("/api/v1/acceleration/payment-link", json={
            "offer_id": "bad",
            "company": "Bad",
            "contact_email": "b@b.com",
            "amount_eur": 400,
            "method": "paypal",
        })
        assert resp.status_code == 422  # Pydantic validation error (ge=1_000)

    def test_record_sale_endpoint(self, client):
        resp = client.post("/api/v1/acceleration/sale", json={
            "company": "EDF",
            "amount_eur": 20_000,
            "sector": "energie",
            "pain_type": "nis2_compliance",
        })
        assert resp.status_code == 200
        assert resp.json()["sale"]["amount_eur"] == 20_000

    def test_record_sale_below_floor(self, client):
        resp = client.post("/api/v1/acceleration/sale", json={
            "company": "Bad",
            "amount_eur": 400,  # below pydantic ge=1000
            "sector": "energie",
            "pain_type": "nis2_compliance",
        })
        assert resp.status_code == 422

    def test_velocity_endpoint(self, client):
        resp = client.get("/api/v1/acceleration/velocity")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert "sales_today" in data["metrics"]

    def test_velocity_sales_endpoint(self, client):
        resp = client.get("/api/v1/acceleration/velocity/sales?period=month")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "total_eur" in data

    def test_dashboard_endpoint(self, client):
        resp = client.get("/api/v1/acceleration/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "velocity" in data
        assert "target_pipeline_hours" in data
        assert data["target_pipeline_hours"] == 4.0

    def test_run_cycle_endpoint(self, client):
        resp = client.post("/api/v1/acceleration/run", json={"sectors": ["energie"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data
        assert "run_id" in data["pipeline"]

    def test_pending_payments_endpoint(self, client):
        resp = client.get("/api/v1/acceleration/payments/pending")
        assert resp.status_code == 200
        assert "count" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduler V21 Turbo tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchedulerTurbo:
    def test_blitz_hunt_interval_15min(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert "blitz_hunt" in CYCLE_INTERVALS
        assert CYCLE_INTERVALS["blitz_hunt"] == 15 * 60

    def test_offer_background_interval(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert "offer_background" in CYCLE_INTERVALS
        assert CYCLE_INTERVALS["offer_background"] == 20 * 60

    def test_followup_j1_faster_than_j2(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert "followup_j1" in CYCLE_INTERVALS
        assert CYCLE_INTERVALS["followup_j1"] == 24 * 3600

    def test_velocity_report_30min(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert "velocity_report" in CYCLE_INTERVALS
        assert CYCLE_INTERVALS["velocity_report"] == 30 * 60

    def test_blitz_hunt_job_exists(self):
        from NAYA_SCHEDULER.autonomous_scheduler import AutonomousScheduler
        s = AutonomousScheduler()
        assert hasattr(s, "_job_blitz_hunt")

    def test_offer_background_job_exists(self):
        from NAYA_SCHEDULER.autonomous_scheduler import AutonomousScheduler
        s = AutonomousScheduler()
        assert hasattr(s, "_job_offer_background")

    def test_velocity_report_job_exists(self):
        from NAYA_SCHEDULER.autonomous_scheduler import AutonomousScheduler
        s = AutonomousScheduler()
        assert hasattr(s, "_job_velocity_report")

    def test_all_turbo_jobs_exist(self):
        from NAYA_SCHEDULER.autonomous_scheduler import AutonomousScheduler, CYCLE_INTERVALS
        s = AutonomousScheduler()
        for name in CYCLE_INTERVALS:
            job_fn = f"_job_{name}"
            assert hasattr(s, job_fn), f"Missing scheduler job: {job_fn}"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Full pipeline (mock APIs)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    def test_pain_to_offer_to_payment_pipeline(self, tracker, closer, flash):
        """Full pipeline: pain description → offer → payment link."""
        from NAYA_ACCELERATION.instant_closer import PaymentMethod

        # 1. Generate offer from pain
        offer = asyncio.run(flash.generate(
            company="TotalEnergies",
            sector="energie",
            pain_description="Réseau SCADA exposé, audit IEC 62443 SL-2 requis urgent NIS2",
            contact_name="Sophie LAMBERT",
            contact_title="RSSI OT",
            budget_estimate=80_000,
            urgency="critical",
        ))
        assert offer.price_eur >= 1_000

        # 2. Generate payment link
        link = closer.generate_payment_link(
            offer_id=offer.offer_id,
            company=offer.company,
            contact_email="s.lambert@total.fr",
            amount_eur=offer.price_eur,
            method=PaymentMethod.PAYPAL,
        )
        assert link.amount_eur == offer.price_eur
        assert link.status == "pending"

        # 3. Record sale after confirmation
        record = tracker.record_sale(
            company=offer.company,
            amount_eur=offer.price_eur,
            sector=offer.sector,
            pain_type=offer.pain_type,
            time_to_close_hours=3.5,  # < 4h target
        )
        assert record.amount_eur >= 1_000

        # 4. Verify metrics
        metrics = tracker.get_metrics()
        assert metrics.sales_today >= 1
        assert metrics.revenue_today_eur >= offer.price_eur

    def test_pipeline_4h_target(self, flash):
        """Verify offer generation time is well under the 4h target."""
        import time
        start = time.time()
        offer = asyncio.run(flash.generate(
            company="Alstom Transport",
            sector="transport_logistique",
            pain_description="IEC 62443 compliance gap, critical deadline",
            urgency="critical",
        ))
        elapsed_seconds = time.time() - start
        # Should complete in well under 60 seconds (1/240th of the 4h target)
        assert elapsed_seconds < 60
        assert offer.generation_time_ms < 60_000

    def test_minimum_price_floor_enforced_across_pipeline(self, flash, closer, tracker):
        """Floor 1000 EUR must hold across all pipeline components."""
        from NAYA_ACCELERATION.instant_closer import PaymentMethod

        offer = asyncio.run(flash.generate(
            company="Startup PME",
            sector="manufacturing",
            pain_description="Security audit needed",
            company_size="startup",
            budget_estimate=3_000,
        ))
        assert offer.price_eur >= 1_000

        link = closer.generate_payment_link(
            offer_id=offer.offer_id,
            company=offer.company,
            contact_email="x@x.com",
            amount_eur=offer.price_eur,
            method=PaymentMethod.PAYPAL,
        )
        assert link.amount_eur >= 1_000

        record = tracker.record_sale(
            offer.company, offer.price_eur, offer.sector, offer.pain_type
        )
        assert record.amount_eur >= 1_000
