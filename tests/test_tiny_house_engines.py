"""
Tests — Tiny House Engines (Prototype Negotiation + Tester Unit + Full Channel + Asset Recycler)
================================================================================================
Valide tous les nouveaux moteurs liés à la session TINY_HOUSE :
  · PrototypeNegotiationEngine
  · TesterUnitEngine
  · TinyHouseFullChannelManager
  · AssetRecycler
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE.prototype_negotiation_engine import (
    PrototypeNegotiationEngine, ModuleVariant, NegotiationStatus, MODULE_SPECS,
    QUALIFICATION_CRITERIA, TARGET_FACTORIES,
)
from NAYA_PROJECT_ENGINE.business.tester_unit_engine import (
    TesterUnitEngine as _TesterUnitEngine,
    TesterStatus as _TesterStatus,
    PHYSICAL_PROJECTS,
)

# Prevent pytest from trying to collect imported production classes as tests
_TesterUnitEngine.__test__ = False
_TesterStatus.__test__ = False
from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE.full_channel_manager import (
    TinyHouseFullChannelManager, Channel, StoryAngle, OBJECTION_RESPONSES, KNOWN_SUPPLIERS,
)
from NAYA_PROJECT_ENGINE.business.asset_recycler import (
    AssetRecycler, AssetType, AssetStatus,
)


# ═══════════════════════════════════════════════════════════════════════════
# PROTOTYPE NEGOTIATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class TestPrototypeNegotiationEngine:

    def test_init_session_creates_two_units(self):
        engine = PrototypeNegotiationEngine()
        result = engine.init_session()
        assert result["status"] == "initialized"
        assert len(result["units"]) == 2
        variants = list(result["units"].values())
        assert ModuleVariant.ALPHA.value in variants
        assert ModuleVariant.BETA.value in variants

    def test_init_session_idempotent(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        result2 = engine.init_session()
        assert result2["status"] == "already_initialized"

    def test_module_specs_present_for_both_variants(self):
        assert ModuleVariant.ALPHA.value in MODULE_SPECS
        assert ModuleVariant.BETA.value in MODULE_SPECS

    def test_alpha_spec_has_required_rooms(self):
        spec = MODULE_SPECS[ModuleVariant.ALPHA.value]
        rooms = spec["rooms"]
        assert "master_bedroom" in rooms
        assert rooms["master_bedroom"]["ac"] is True
        assert rooms["master_bedroom"]["ensuite_wc"] is True
        assert rooms["master_bedroom"]["ensuite_shower"] is True
        assert "child_bedroom" in rooms
        assert rooms["child_bedroom"]["ac"] is True
        assert "common_wc" in rooms
        assert "living_kitchen" in rooms
        assert rooms["living_kitchen"]["ac"] is True
        assert "laundry" in rooms

    def test_beta_spec_has_mezzanine(self):
        spec = MODULE_SPECS[ModuleVariant.BETA.value]
        assert spec["mezzanine"] is True
        assert spec.get("mezzanine_m2", 0) > 0
        master = spec["rooms"]["master_bedroom"]
        assert master.get("level") == "mezzanine"

    def test_both_modules_20m2(self):
        for variant in (ModuleVariant.ALPHA.value, ModuleVariant.BETA.value):
            assert MODULE_SPECS[variant]["surface_m2"] == 20

    def test_both_modules_have_renewable_energy(self):
        for variant in (ModuleVariant.ALPHA.value, ModuleVariant.BETA.value):
            energy = MODULE_SPECS[variant]["energy"]
            assert energy["off_grid_ready"] is True
            assert energy["solar_kwc"] > 0
            assert energy["battery_kwh"] > 0

    def test_advance_unit_valid_transition(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        status = engine.get_session_status()
        unit_id = status["units"][0]["unit_id"]
        result = engine.advance_unit(unit_id, NegotiationStatus.RFQ_SENT.value, "RFQ envoyée")
        assert result["new_status"] == NegotiationStatus.RFQ_SENT.value

    def test_advance_unit_invalid_status_returns_error(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        status = engine.get_session_status()
        unit_id = status["units"][0]["unit_id"]
        result = engine.advance_unit(unit_id, "invalid_status")
        assert "error" in result

    def test_set_factory(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        result = engine.set_factory(uid, "Factory_A_CN")
        assert result["factory_id"] == "Factory_A_CN"

    def test_set_pricing_floor_enforced(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        result = engine.set_pricing(uid, 500.0)
        assert "error" in result

    def test_set_pricing_valid(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        result = engine.set_pricing(uid, 15000.0, logistics_eur=2500.0)
        assert result["total_cost_eur"] == 17500.0
        assert "vs_target_pct" in result

    def test_assess_unit_score_validation(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        # Must be delivered before assessment can happen properly
        for status in [NegotiationStatus.RFQ_SENT.value,
                       NegotiationStatus.SAMPLES_REQUESTED.value,
                       NegotiationStatus.PROTOTYPE_CONFIRMED.value,
                       NegotiationStatus.LOGISTICS_AGREED.value,
                       NegotiationStatus.IN_PRODUCTION.value,
                       NegotiationStatus.SHIPPED.value,
                       NegotiationStatus.RECEIVED.value]:
            engine.advance_unit(uid, status)
        result = engine.assess_unit(uid, 8.5, "Excellent build quality")
        assert result["passed"] is True
        assert result["assessment_score"] == 8.5

    def test_assess_unit_fail(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        for status in [NegotiationStatus.RFQ_SENT.value,
                       NegotiationStatus.SAMPLES_REQUESTED.value,
                       NegotiationStatus.PROTOTYPE_CONFIRMED.value,
                       NegotiationStatus.LOGISTICS_AGREED.value,
                       NegotiationStatus.IN_PRODUCTION.value,
                       NegotiationStatus.SHIPPED.value,
                       NegotiationStatus.RECEIVED.value]:
            engine.advance_unit(uid, status)
        result = engine.assess_unit(uid, 5.0, "Poor quality")
        assert result["passed"] is False

    def test_get_rfq_brief_structure(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        brief = engine.get_rfq_brief(uid)
        assert "specifications" in brief
        assert "delivery" in brief
        assert "target_price_eur" in brief
        assert "evaluation_criteria" in brief
        assert "external_framing" in brief
        # Must NOT reveal personal ownership
        assert "propriétaire" not in brief.get("purpose", "").lower()
        assert "personal" not in str(brief).lower()

    def test_rfq_mentions_polynesia(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        uid = engine.get_session_status()["units"][0]["unit_id"]
        brief = engine.get_rfq_brief(uid)
        assert "Polynésie" in brief["delivery"]["destination"]

    def test_qualification_checklist_not_empty(self):
        engine = PrototypeNegotiationEngine()
        checklist = engine.get_qualification_checklist()
        assert len(checklist) >= 5

    def test_target_factories_defined(self):
        assert len(TARGET_FACTORIES) >= 3

    def test_get_session_status_before_init(self):
        engine = PrototypeNegotiationEngine()
        result = engine.get_session_status()
        assert "not_initialized" in result.get("status", "")

    def test_get_session_status_after_init(self):
        engine = PrototypeNegotiationEngine()
        engine.init_session()
        status = engine.get_session_status()
        assert status["nb_units"] == 2
        assert "total_cost_eur" in status

    def test_get_module_specs_unknown_variant(self):
        engine = PrototypeNegotiationEngine()
        result = engine.get_module_specs("UNKNOWN")
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# TESTER UNIT ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class TestTesterUnitEngine:

    def test_bootstrap_registers_physical_projects(self):
        engine = _TesterUnitEngine()
        assert engine.is_physical_project("PROJECT_04_TINY_HOUSE")
        assert engine.is_physical_project("PROJECT_03_NAYA_BOTANICA")

    def test_non_physical_project_returns_false(self):
        engine = _TesterUnitEngine()
        assert not engine.is_physical_project("PROJECT_02_GOOGLE_XR")

    def test_register_project(self):
        engine = _TesterUnitEngine()
        result = engine.register_project("PROJECT_NEW_PHYSICAL", "gadget_iot", quantity=2)
        assert result["registered"] is True
        assert engine.is_physical_project("PROJECT_NEW_PHYSICAL")

    def test_request_tester_known_project(self):
        engine = _TesterUnitEngine()
        result = engine.request_tester("PROJECT_04_TINY_HOUSE",
                                       specs_summary="Module 20m² — validation qualité")
        assert result.get("error") is None
        assert "request_id" in result
        assert result["status"] == _TesterStatus.REQUESTED.value
        # Framing must be external / discrete
        assert "propriétaire" not in result.get("external_framing", "").lower()

    def test_request_tester_unknown_project(self):
        engine = _TesterUnitEngine()
        result = engine.request_tester("PROJECT_UNKNOWN")
        assert "error" in result

    def test_update_status_valid_transition(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_04_TINY_HOUSE")
        req_id = r["request_id"]
        result = engine.update_status(req_id, _TesterStatus.NEGOTIATING.value)
        assert result["new_status"] == _TesterStatus.NEGOTIATING.value

    def test_update_status_invalid_transition(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_04_TINY_HOUSE")
        req_id = r["request_id"]
        result = engine.update_status(req_id, _TesterStatus.ASSESSED.value)
        assert "error" in result

    def test_full_happy_path_to_delivery(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_03_NAYA_BOTANICA", quantity=3)
        rid = r["request_id"]
        for status in [_TesterStatus.NEGOTIATING.value, _TesterStatus.CONFIRMED.value,
                       _TesterStatus.PRODUCING.value, _TesterStatus.SHIPPED.value,
                       _TesterStatus.IN_TRANSIT.value, _TesterStatus.DELIVERED.value]:
            engine.update_status(rid, status)
        result = engine.record_assessment(rid, 9.0, "Qualité exceptionnelle")
        assert result["passed"] is True
        assert result["score"] == 9.0

    def test_assessment_fails_below_7(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_04_TINY_HOUSE")
        rid = r["request_id"]
        for status in [_TesterStatus.NEGOTIATING.value, _TesterStatus.CONFIRMED.value,
                       _TesterStatus.PRODUCING.value, _TesterStatus.SHIPPED.value,
                       _TesterStatus.IN_TRANSIT.value, _TesterStatus.DELIVERED.value]:
            engine.update_status(rid, status)
        result = engine.record_assessment(rid, 6.0, "Qualité insuffisante")
        assert result["passed"] is False

    def test_record_assessment_requires_delivered_status(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_04_TINY_HOUSE")
        rid = r["request_id"]
        result = engine.record_assessment(rid, 8.0)
        assert "error" in result

    def test_get_all_requests(self):
        engine = _TesterUnitEngine()
        engine.request_tester("PROJECT_04_TINY_HOUSE")
        engine.request_tester("PROJECT_03_NAYA_BOTANICA")
        stats = engine.get_all_requests()
        assert stats["total_requests"] >= 2

    def test_get_project_requests(self):
        engine = _TesterUnitEngine()
        engine.request_tester("PROJECT_04_TINY_HOUSE", quantity=2)
        result = engine.get_project_requests("PROJECT_04_TINY_HOUSE")
        assert result["total"] >= 1

    def test_enforce_tester_rule_creates_if_none(self):
        engine = _TesterUnitEngine()
        result = engine.enforce_tester_rule("PROJECT_04_TINY_HOUSE")
        assert result["enforced"] is True
        assert result.get("action") in ("auto_created", "already_requested")

    def test_enforce_tester_rule_non_physical(self):
        engine = _TesterUnitEngine()
        result = engine.enforce_tester_rule("PROJECT_02_GOOGLE_XR")
        assert result["enforced"] is False

    def test_get_pending_testers(self):
        engine = _TesterUnitEngine()
        engine.request_tester("PROJECT_04_TINY_HOUSE")
        pending = engine.get_pending_testers()
        assert len(pending) >= 1

    def test_tiny_house_default_quantity_two(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_04_TINY_HOUSE")
        assert r["quantity"] == 2

    def test_botanica_default_quantity_three(self):
        engine = _TesterUnitEngine()
        r = engine.request_tester("PROJECT_03_NAYA_BOTANICA")
        assert r["quantity"] == 3


# ═══════════════════════════════════════════════════════════════════════════
# FULL CHANNEL MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class TestTinyHouseFullChannelManager:

    def test_create_content_returns_pieces(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.create_content(
            pain_signal="Cyclone — familles sans logement",
            channels=[Channel.INSTAGRAM.value, Channel.EMAIL.value],
        )
        assert result["pieces_created"] == 2
        assert len(result["content_ids"]) == 2

    def test_create_content_requires_real_pain_signal(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.create_content(pain_signal="travailleurs saisonniers sans hébergement")
        assert result["pieces_created"] > 0

    def test_publish_content(self):
        mgr = TinyHouseFullChannelManager()
        r = mgr.create_content("test signal", channels=[Channel.LINKEDIN.value])
        cid = r["content_ids"][0]
        pub = mgr.publish_content(cid)
        assert pub["published"] is True

    def test_publish_content_not_found(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.publish_content("CNT-NOTEXIST")
        assert "error" in result

    def test_recycle_content_increments_version(self):
        mgr = TinyHouseFullChannelManager()
        r = mgr.create_content("signal A", channels=[Channel.INSTAGRAM.value])
        cid = r["content_ids"][0]
        recycled = mgr.recycle_content(cid, "signal B", Channel.TIKTOK.value)
        assert recycled["version"] == 2
        assert recycled["original_id"] == cid

    def test_handle_comment_positive_sentiment(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.handle_comment("instagram", "Super module !", "positive", "prospect")
        assert "response" in result
        assert result["action"] == "reply"

    def test_handle_comment_troll_hidden(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.handle_comment("instagram", "C'est nul", "negative", "troll")
        assert result["action"] == "hide"

    def test_handle_objection_prix(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.handle_objection_message("prix_trop_eleve")
        assert "response" in result
        assert "error" not in result

    def test_handle_objection_unknown_returns_known_list(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.handle_objection_message("objection_inexistante")
        assert "error" in result
        assert "known_objections" in result

    def test_evaluate_suppliers_ranked_by_score(self):
        mgr = TinyHouseFullChannelManager()
        ranked = mgr.evaluate_suppliers()
        assert len(ranked) >= 3
        scores = [s["overall_score"] for s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_get_best_supplier(self):
        mgr = TinyHouseFullChannelManager()
        best = mgr.get_best_supplier(min_quality=7.5, max_lead_days=60)
        assert best is not None
        assert "supplier_id" in best

    def test_create_shipment(self):
        mgr = TinyHouseFullChannelManager()
        result = mgr.create_shipment("Chine", units=2, container_type="40HC")
        assert "shipment_id" in result
        assert result["units"] == 2

    def test_update_shipment(self):
        mgr = TinyHouseFullChannelManager()
        s = mgr.create_shipment("Vietnam", units=1)
        result = mgr.update_shipment(s["shipment_id"], status="shipped",
                                     tracking_number="TRK-123456")
        assert "error" not in result

    def test_get_assembly_brief_structure(self):
        mgr = TinyHouseFullChannelManager()
        s = mgr.create_shipment("Chine", units=1)
        brief = mgr.get_assembly_brief(s["shipment_id"])
        assert "assembly_steps" in brief
        assert len(brief["assembly_steps"]) >= 8
        assert "estimated_assembly_days" in brief

    def test_build_credibility_pack(self):
        mgr = TinyHouseFullChannelManager()
        pack = mgr.build_credibility_pack()
        assert "certifications" in pack
        assert "proof_points" in pack
        assert "media_angles" in pack
        assert len(pack["certifications"]) >= 3

    def test_get_stats(self):
        mgr = TinyHouseFullChannelManager()
        mgr.create_content("test pain", channels=[Channel.INSTAGRAM.value])
        stats = mgr.get_stats()
        assert stats["project"] == "PROJECT_04_TINY_HOUSE"
        assert stats["content"]["total_created"] >= 1

    def test_get_content_library_filter_by_channel(self):
        mgr = TinyHouseFullChannelManager()
        mgr.create_content("signal", channels=[Channel.INSTAGRAM.value, Channel.EMAIL.value])
        insta = mgr.get_content_library(channel=Channel.INSTAGRAM.value)
        assert all(c["channel"] == Channel.INSTAGRAM.value for c in insta)

    def test_all_objections_have_responses(self):
        assert len(OBJECTION_RESPONSES) >= 5
        for key, val in OBJECTION_RESPONSES.items():
            assert len(val) > 20, f"Réponse trop courte: {key}"

    def test_story_angles_cover_all_enum_values(self):
        for angle in StoryAngle:
            mgr = TinyHouseFullChannelManager()
            result = mgr.create_content("test", channels=[Channel.INSTAGRAM.value],
                                        angle=angle.value)
            assert result["pieces_created"] >= 1


# ═══════════════════════════════════════════════════════════════════════════
# ASSET RECYCLER
# ═══════════════════════════════════════════════════════════════════════════

class TestAssetRecycler:

    def test_register_asset(self):
        rec = AssetRecycler()
        asset = rec.register(
            asset_type=AssetType.CONTENT_POST.value,
            name="Post Instagram Tiny House",
            content="Votre logement 20m² en 45 jours #tinyhouse",
            project_id="PROJECT_04_TINY_HOUSE",
            sector="habitat",
            channel="instagram",
        )
        assert asset.id.startswith("ASSET-")
        assert asset.version == 1
        assert asset.parent_id is None

    def test_find_by_type(self):
        rec = AssetRecycler()
        rec.register(AssetType.EMAIL_PITCH.value, "Email test", "Corps email", "PROJECT_04_TINY_HOUSE")
        results = rec.find(asset_type=AssetType.EMAIL_PITCH.value)
        assert len(results) >= 1

    def test_find_returns_best_performers_first(self):
        rec = AssetRecycler()
        a1 = rec.register(AssetType.CONTENT_POST.value, "A1", "content1", "PROJECT_04_TINY_HOUSE")
        a2 = rec.register(AssetType.CONTENT_POST.value, "A2", "content2", "PROJECT_04_TINY_HOUSE")
        rec.record_performance(a1.id, 8.0)
        rec.record_performance(a2.id, 5.0)
        results = rec.find(asset_type=AssetType.CONTENT_POST.value)
        assert results[0].id == a1.id

    def test_recycle_creates_v2(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.CONTENT_POST.value, "Post P04",
                         "Module 20m² autonome", "PROJECT_04_TINY_HOUSE", channel="instagram")
        recycled = rec.recycle(a.id, new_project_id="PROJECT_03_NAYA_BOTANICA",
                               new_channel="linkedin")
        assert recycled.version == 2
        assert recycled.parent_id == a.id
        assert recycled.project_id == "PROJECT_03_NAYA_BOTANICA"

    def test_recycle_updates_parent_count(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.STORYTELLING.value, "Story", "Récit pain", "PROJECT_04_TINY_HOUSE")
        rec.recycle(a.id)
        with rec._lock:
            parent = rec._assets[a.id]
        assert parent.recycled_count == 1

    def test_clone_for_project(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.SUPPLIER_BRIEF.value, "Brief fournisseur",
                         "Contenu brief", "PROJECT_04_TINY_HOUSE")
        cloned = rec.clone_for_project(a.id, "PROJECT_03_NAYA_BOTANICA")
        assert cloned.project_id == "PROJECT_03_NAYA_BOTANICA"
        assert f"cloned_to:PROJECT_03_NAYA_BOTANICA" in cloned.tags

    def test_record_performance(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.TEMPLATE.value, "Template", "body", "P04")
        result = rec.record_performance(a.id, 9.0)
        assert "error" not in result
        assert result["new_score"] > 0

    def test_record_performance_out_of_range(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.TEMPLATE.value, "T", "b", "P")
        result = rec.record_performance(a.id, 11.0)
        assert "error" in result

    def test_should_create_new_no_assets(self):
        rec = AssetRecycler()
        decision = rec.should_create_new(AssetType.EMAIL_PITCH.value)
        assert decision["should_create"] is True

    def test_should_create_new_recyclable_exists(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.EMAIL_PITCH.value, "Email", "body", "PROJECT_04_TINY_HOUSE")
        rec.record_performance(a.id, 7.0)
        decision = rec.should_create_new(AssetType.EMAIL_PITCH.value, project_id="PROJECT_04_TINY_HOUSE")
        assert decision["should_create"] is False

    def test_get_best_performers(self):
        rec = AssetRecycler()
        for i in range(5):
            a = rec.register(AssetType.CONTENT_POST.value, f"Post {i}", f"content {i}", "P04")
            rec.record_performance(a.id, float(i + 5))
        top = rec.get_best_performers(asset_type=AssetType.CONTENT_POST.value, top_n=3)
        assert len(top) == 3
        scores = [p["performance_score"] for p in top]
        assert scores == sorted(scores, reverse=True)

    def test_get_stats(self):
        rec = AssetRecycler()
        a = rec.register(AssetType.CONTENT_POST.value, "Post", "body", "P04")
        rec.recycle(a.id, new_project_id="P03")
        stats = rec.get_stats()
        assert stats["total_assets"] >= 2
        assert stats["recycled_assets"] >= 1
        assert "recycle_rate" in stats
        assert "zero_waste_compliance" in stats

    def test_recycle_unknown_asset_raises(self):
        rec = AssetRecycler()
        with pytest.raises(ValueError):
            rec.recycle("ASSET-DOESNOTEXIST")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE CATALOGUE
# ═══════════════════════════════════════════════════════════════════════════

from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE.module_catalogue import (
    ModuleCatalogue, MODULE_LAYOUTS, SOLAR_CONFIGS, ModuleLayout, SolarConfig,
)


class TestModuleCatalogue:

    def test_catalogue_has_six_layouts(self):
        assert len(MODULE_LAYOUTS) == 6
        for code in ("M1", "M2", "M3", "M4", "M5", "M6"):
            assert code in MODULE_LAYOUTS

    def test_all_layouts_have_minimum_programme(self):
        """Every module must have: master bedroom + child bedroom + common wc + kitchen + laundry."""
        for code, m in MODULE_LAYOUTS.items():
            room_names = {r.name.lower() for r in m.rooms}
            assert any("parent" in n or "suite" in n for n in room_names), f"{code}: no master bedroom"
            assert any("enfant" in n for n in room_names), f"{code}: no child bedroom"
            assert any("wc" in n or "douche" in n for n in room_names), f"{code}: no bathroom"
            assert any("salon" in n or "cuisine" in n or "kitchen" in n for n in room_names), f"{code}: no living/kitchen"

    def test_all_layouts_20m2_floor(self):
        for code, m in MODULE_LAYOUTS.items():
            assert m.surface_m2 == 20, f"{code}: floor surface should be 20m²"

    def test_all_layouts_have_ac_in_bedrooms_and_living(self):
        for code, m in MODULE_LAYOUTS.items():
            for r in m.rooms:
                if any(k in r.name.lower() for k in ("parent", "suite", "enfant", "salon", "cuisine")):
                    if r.surface_m2 > 0:
                        assert r.ac, f"{code} — {r.name}: AC manquante"

    def test_master_bedroom_has_ensuite_in_all_layouts(self):
        for code, m in MODULE_LAYOUTS.items():
            ensuite_rooms = [r for r in m.rooms if r.ensuite_wc and r.ensuite_shower]
            assert len(ensuite_rooms) >= 1, f"{code}: master bedroom must have ensuite WC+shower"

    def test_m2_has_mezzanine(self):
        m2 = MODULE_LAYOUTS["M2"]
        assert m2.mezzanine_m2 > 0
        assert m2.levels == 2
        master = next(r for r in m2.rooms if r.ensuite_wc)
        assert master.level == "mezzanine"

    def test_m6_has_solar_roof(self):
        m6 = MODULE_LAYOUTS["M6"]
        assert "BIPV" in m6.roof_type or "solaire" in m6.roof_type.lower()

    def test_four_solar_tiers_defined(self):
        for tier in ("ESSENTIEL", "CONFORT", "PREMIUM", "AUTONOME_TOTAL"):
            assert tier in SOLAR_CONFIGS
            sc = SOLAR_CONFIGS[tier]
            assert sc.solar_panels_kwc > 0
            assert sc.battery_kwh > 0
            assert 0 < sc.self_sufficiency_pct <= 100

    def test_solar_tiers_increasing_capacity(self):
        tiers = ["ESSENTIEL", "CONFORT", "PREMIUM", "AUTONOME_TOTAL"]
        kwc_values = [SOLAR_CONFIGS[t].solar_panels_kwc for t in tiers]
        kwh_values = [SOLAR_CONFIGS[t].battery_kwh for t in tiers]
        assert kwc_values == sorted(kwc_values), "Solar kWc must increase by tier"
        assert kwh_values == sorted(kwh_values), "Battery kWh must increase by tier"

    def test_solar_tiers_increasing_price(self):
        tiers = ["ESSENTIEL", "CONFORT", "PREMIUM", "AUTONOME_TOTAL"]
        prices = [SOLAR_CONFIGS[t].price_eur for t in tiers]
        assert prices == sorted(prices)

    def test_list_all_returns_six_modules(self):
        cat = ModuleCatalogue()
        modules = cat.list_all()
        assert len(modules) == 6

    def test_list_all_includes_pricing(self):
        cat = ModuleCatalogue()
        for m in cat.list_all("CONFORT"):
            assert "pricing" in m
            assert m["pricing"]["total_eur"] >= m["pricing"]["module_base_eur"]
            assert m["pricing"]["solar_system_eur"] == SOLAR_CONFIGS["CONFORT"].price_eur

    def test_list_all_includes_energy(self):
        cat = ModuleCatalogue()
        for m in cat.list_all("PREMIUM"):
            assert "energy" in m
            assert m["energy"]["solar_panels_kwc"] == SOLAR_CONFIGS["PREMIUM"].solar_panels_kwc

    def test_filter_by_levels(self):
        cat = ModuleCatalogue()
        single = cat.filter(levels=1)
        double = cat.filter(levels=2)
        assert all(m["surface"]["levels"] == 1 for m in single)
        assert all(m["surface"]["levels"] == 2 for m in double)
        assert len(single) + len(double) == 6

    def test_filter_by_mezzanine(self):
        cat = ModuleCatalogue()
        with_mez = cat.filter(mezzanine=True)
        without  = cat.filter(mezzanine=False)
        assert all(m["surface"]["mezzanine_m2"] > 0 for m in with_mez)
        assert all(m["surface"]["mezzanine_m2"] == 0 for m in without)

    def test_filter_by_budget(self):
        cat = ModuleCatalogue()
        budget = 25_000
        results = cat.filter(max_budget_eur=budget, solar_tier="ESSENTIEL")
        for m in results:
            assert m["pricing"]["total_eur"] <= budget

    def test_filter_results_sorted_by_price(self):
        cat = ModuleCatalogue()
        results = cat.filter()
        prices = [m["pricing"]["total_eur"] for m in results]
        assert prices == sorted(prices)

    def test_compare_two_modules(self):
        cat = ModuleCatalogue()
        cmp = cat.compare("M1", "M2")
        assert "comparison" in cmp
        assert "delta" in cmp
        assert cmp["comparison"]["module_a"]["code"] == "M1"
        assert cmp["comparison"]["module_b"]["code"] == "M2"
        assert "cheaper" in cmp["delta"]

    def test_compare_unknown_module(self):
        cat = ModuleCatalogue()
        result = cat.compare("M1", "M99")
        assert "error" in result

    def test_select_prototypes_valid(self):
        cat = ModuleCatalogue()
        sel = cat.select_prototypes("M1", "M2", solar_tier_a="CONFORT", solar_tier_b="PREMIUM")
        assert "error" not in sel
        assert len(sel["units"]) == 2
        assert sel["units"][0]["unit"] == "A"
        assert sel["units"][1]["unit"] == "B"
        assert sel["totals"]["grand_total_eur"] > 0
        assert sel["totals"]["grand_total_eur"] >= 1000  # floor

    def test_select_prototypes_unknown_code(self):
        cat = ModuleCatalogue()
        result = cat.select_prototypes("M1", "M99")
        assert "error" in result

    def test_select_prototypes_units_have_floor_plan(self):
        cat = ModuleCatalogue()
        sel = cat.select_prototypes("M1", "M2")
        for unit in sel["units"]:
            assert "floor_plan" in unit
            assert len(unit["floor_plan"]) > 10

    def test_select_prototypes_units_have_solar_config(self):
        cat = ModuleCatalogue()
        sel = cat.select_prototypes("M1", "M2")
        for unit in sel["units"]:
            assert "solar" in unit
            assert unit["solar"]["solar_panels_kwc"] > 0

    def test_recommend_solar_permanent(self):
        cat = ModuleCatalogue()
        r = cat.recommend_solar("M1", usage="permanent")
        assert r["recommended_tier"] == "CONFORT"
        assert "solar_config" in r

    def test_recommend_solar_offgrid(self):
        cat = ModuleCatalogue()
        r = cat.recommend_solar("M6", usage="offgrid")
        assert r["recommended_tier"] == "AUTONOME_TOTAL"

    def test_recommend_solar_unknown_module(self):
        cat = ModuleCatalogue()
        r = cat.recommend_solar("M99")
        assert "error" in r

    def test_get_module_valid(self):
        cat = ModuleCatalogue()
        m = cat.get_module("M1")
        assert m["code"] == "M1"
        assert "rooms" in m
        assert "floor_plan" in m

    def test_get_module_unknown(self):
        cat = ModuleCatalogue()
        result = cat.get_module("M99")
        assert "error" in result
        assert "available_codes" in result

    def test_list_solar_configs(self):
        cat = ModuleCatalogue()
        configs = cat.list_solar_configs()
        assert len(configs) == 4
        assert all("solar_panels_kwc" in c for c in configs)

    def test_get_solar_config_valid(self):
        cat = ModuleCatalogue()
        sc = cat.get_solar_config("PREMIUM")
        assert sc["tier"] == "PREMIUM"
        assert sc["solar_panels_kwc"] == SOLAR_CONFIGS["PREMIUM"].solar_panels_kwc

    def test_get_solar_config_unknown(self):
        cat = ModuleCatalogue()
        result = cat.get_solar_config("NONEXISTENT")
        assert "error" in result

    def test_print_catalogue_contains_all_codes(self):
        cat = ModuleCatalogue()
        txt = cat.print_catalogue()
        for code in ("M1", "M2", "M3", "M4", "M5", "M6"):
            assert code in txt
        for tier in ("ESSENTIEL", "CONFORT", "PREMIUM", "AUTONOME_TOTAL"):
            assert tier in txt

    def test_monthly_energy_cost_autonome_total_is_zero(self):
        cat = ModuleCatalogue()
        sc = cat.get_solar_config("AUTONOME_TOTAL")
        # 100% self-sufficient → monthly cost = 0
        assert sc["monthly_energy_cost_eur"] == 0.0

    def test_all_modules_have_strengths_and_constraints(self):
        cat = ModuleCatalogue()
        for m in cat.list_all():
            assert len(m["strengths"]) >= 2
            assert len(m["constraints"]) >= 1

    def test_all_modules_have_best_for(self):
        cat = ModuleCatalogue()
        for m in cat.list_all():
            assert len(m["best_for"]) > 5
