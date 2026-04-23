"""
NAYA V20 — Tests V20 Intelligence Modules
Couvre : 25 modules (5 hunters + 5 ai_advanced + 5 architecture + 5 verticals + 5 future_tech)
"""
import sys
import time
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    """Redirect all V20 DATA_FILE paths to tmp_path."""
    cache = tmp_path / "cache"
    cache.mkdir()
    vs_dir = tmp_path / "vector_store"
    vs_dir.mkdir()

    import V20_INTELLIGENCE.ai_advanced.local_llm_trainer as llt_mod
    import V20_INTELLIGENCE.ai_advanced.decision_graph_engine as dge_mod
    import V20_INTELLIGENCE.ai_advanced.sentiment_radar as sr_mod
    import V20_INTELLIGENCE.ai_advanced.voice_agent_engine as vae_mod
    import V20_INTELLIGENCE.ai_advanced.annual_report_parser as arp_mod
    import V20_INTELLIGENCE.architecture.federated_learner as fl_mod
    import V20_INTELLIGENCE.architecture.digital_twin_engine as dte_mod
    import V20_INTELLIGENCE.architecture.zkp_audit_engine as zkp_mod
    import V20_INTELLIGENCE.architecture.quantum_safe_advisor as qsa_mod
    import V20_INTELLIGENCE.architecture.sovereign_vector_store as svs_mod
    import V20_INTELLIGENCE.verticals.ai_act_compliance_engine as aace_mod
    import V20_INTELLIGENCE.verticals.africa_ot_vertical as afr_mod
    import V20_INTELLIGENCE.verticals.supply_chain_risk_scorer as scrs_mod
    import V20_INTELLIGENCE.verticals.insurance_advisory_engine as iae_mod
    import V20_INTELLIGENCE.verticals.space_satellite_ot_security as ssos_mod
    import V20_INTELLIGENCE.future_tech.agentic_orchestrator as ao_mod
    import V20_INTELLIGENCE.future_tech.ambient_iot_intelligence as aii_mod
    import V20_INTELLIGENCE.future_tech.neuromorphic_scorer as ns_mod
    import V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit as bpa_mod
    import V20_INTELLIGENCE.future_tech.ar_ot_assessment as ara_mod

    monkeypatch.setattr(llt_mod, "DATA_FILE", cache / "local_llm_trainer.json")
    monkeypatch.setattr(dge_mod, "DATA_FILE", cache / "decision_graph_engine.json")
    monkeypatch.setattr(sr_mod, "DATA_FILE", cache / "sentiment_radar.json")
    monkeypatch.setattr(vae_mod, "DATA_FILE", cache / "voice_agent_engine.json")
    monkeypatch.setattr(arp_mod, "DATA_FILE", cache / "annual_report_parser.json")
    monkeypatch.setattr(fl_mod, "DATA_FILE", cache / "federated_learner.json")
    monkeypatch.setattr(dte_mod, "DATA_FILE", cache / "digital_twin_engine.json")
    monkeypatch.setattr(zkp_mod, "DATA_FILE", cache / "zkp_audit_engine.json")
    monkeypatch.setattr(qsa_mod, "DATA_FILE", cache / "quantum_safe_advisor.json")
    monkeypatch.setattr(svs_mod, "_STORE_DIR", vs_dir)
    monkeypatch.setattr(aace_mod, "DATA_FILE", cache / "ai_act_compliance_engine.json")
    monkeypatch.setattr(afr_mod, "DATA_FILE", cache / "africa_ot_vertical.json")
    monkeypatch.setattr(scrs_mod, "DATA_FILE", cache / "supply_chain_risk_scorer.json")
    monkeypatch.setattr(iae_mod, "DATA_FILE", cache / "insurance_advisory_engine.json")
    monkeypatch.setattr(ssos_mod, "DATA_FILE", cache / "space_satellite_ot_security.json")
    monkeypatch.setattr(ao_mod, "DATA_FILE", cache / "agentic_orchestrator.json")
    monkeypatch.setattr(aii_mod, "DATA_FILE", cache / "ambient_iot_intelligence.json")
    monkeypatch.setattr(ns_mod, "DATA_FILE", cache / "neuromorphic_scorer.json")
    monkeypatch.setattr(bpa_mod, "DATA_FILE", cache / "blockchain_proof_of_audit.json")
    monkeypatch.setattr(ara_mod, "DATA_FILE", cache / "ar_ot_assessment.json")

    return cache


# ══════════════════════════════════════════════════════════════════════════════
# GROUP 2 — AI ADVANCED
# ══════════════════════════════════════════════════════════════════════════════

class TestLocalLLMTrainer:

    def test_add_training_sample_returns_id(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.local_llm_trainer import LocalLLMTrainer
        trainer = LocalLLMTrainer()
        sample_id = trainer.add_training_sample("contract", "Contrat OT 15k€", "won", "energie")
        assert isinstance(sample_id, str)
        assert len(sample_id) > 0

    def test_get_training_dataset_filtered(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.local_llm_trainer import LocalLLMTrainer
        trainer = LocalLLMTrainer()
        trainer.add_training_sample("contract", "Contrat A", "won", "energie")
        trainer.add_training_sample("email", "Email B", "replied", "transport")
        contracts = trainer.get_training_dataset(sample_type="contract")
        assert len(contracts) == 1
        assert contracts[0]["sample_type"] == "contract"

    def test_compute_training_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.local_llm_trainer import LocalLLMTrainer
        trainer = LocalLLMTrainer()
        trainer.add_training_sample("contract", "Content A", "won", "energie")
        trainer.add_training_sample("email", "Content B", "replied", "transport")
        stats = trainer.compute_training_stats()
        assert "total" in stats
        assert "by_type" in stats
        assert "by_sector" in stats
        assert stats["total"] == 2

    def test_export_jsonl_writes_lines(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.local_llm_trainer import LocalLLMTrainer
        trainer = LocalLLMTrainer()
        trainer.add_training_sample("offer", "Offre test", "accepted", "industrie")
        out_path = str(tmp_cache / "export.jsonl")
        count = trainer.export_jsonl(out_path)
        assert count == 1
        with open(out_path) as f:
            line = json.loads(f.readline())
        assert "sample_type" in line

    def test_get_stats_returns_dict(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.local_llm_trainer import LocalLLMTrainer
        stats = LocalLLMTrainer().get_stats()
        assert isinstance(stats, dict)
        assert "total_samples" in stats


class TestDecisionGraphEngine:

    def test_add_person_returns_id(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.decision_graph_engine import DecisionGraphEngine
        engine = DecisionGraphEngine()
        pid = engine.add_person("P1", "Alice Dupont", "RSSI", "EDF", "energie")
        assert pid == "P1"

    def test_add_connection_requires_both_persons(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.decision_graph_engine import DecisionGraphEngine
        engine = DecisionGraphEngine()
        engine.add_person("P1", "Alice", "RSSI", "EDF", "energie")
        result = engine.add_connection("P1", "P2_nonexistent")
        assert result is False

    def test_find_bridges_correct_count(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.decision_graph_engine import DecisionGraphEngine
        engine = DecisionGraphEngine()
        engine.add_person("P1", "Alice", "RSSI", "EDF", "energie")
        for i in range(4):
            engine.add_person(f"P{i+10}", f"Person{i}", "CTO", f"Company{i}", "transport")
            engine.add_connection("P1", f"P{i+10}")
        bridges = engine.find_bridges(min_connections=3)
        assert len(bridges) >= 1
        assert bridges[0]["person_id"] == "P1"

    def test_get_intro_path_same_company(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.decision_graph_engine import DecisionGraphEngine
        engine = DecisionGraphEngine()
        engine.add_person("P1", "Alice", "RSSI", "EDF", "energie")
        engine.add_person("P2", "Bob", "CTO", "TotalEnergies", "energie")
        engine.add_connection("P1", "P2")
        path = engine.get_intro_path("P1", "TotalEnergies")
        assert isinstance(path, list)
        assert len(path) >= 1

    def test_get_stats_returns_dict(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.decision_graph_engine import DecisionGraphEngine
        stats = DecisionGraphEngine().get_stats()
        assert "total_persons" in stats
        assert "total_connections" in stats


class TestSentimentRadar:

    def test_ingest_post_high_distress(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.sentiment_radar import SentimentRadar
        radar = SentimentRadar()
        signal = radar.ingest_post(
            "P001", "Jean RSSI", "RSSI", "Acme Corp",
            "Nuit blanche suite à ransomware sur nos SCADA !",
            "linkedin", datetime.now(timezone.utc).isoformat()
        )
        assert signal is not None
        assert signal.distress_score > 0
        assert len(signal.hot_keywords) > 0

    def test_ingest_duplicate_returns_none(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.sentiment_radar import SentimentRadar
        radar = SentimentRadar()
        ts = datetime.now(timezone.utc).isoformat()
        radar.ingest_post("P002", "Marie", "DSI", "Corp", "incident critique", "twitter", ts)
        result = radar.ingest_post("P002", "Marie", "DSI", "Corp", "incident critique", "twitter", ts)
        assert result is None

    def test_get_hot_leads_threshold(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.sentiment_radar import SentimentRadar
        radar = SentimentRadar()
        radar.ingest_post("P003", "X", "RSSI", "BigCo",
                          "ransomware attaque production arrêtée urgence NIS2",
                          "linkedin", datetime.now(timezone.utc).isoformat())
        hot = radar.get_hot_leads(min_score=70)
        assert isinstance(hot, list)

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.sentiment_radar import SentimentRadar
        stats = SentimentRadar().get_stats()
        assert "total_posts" in stats
        assert "hot_leads" in stats


class TestVoiceAgentEngine:

    def test_create_call_script_fields(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.voice_agent_engine import VoiceAgentEngine
        engine = VoiceAgentEngine()
        script = engine.create_call_script("Jean Martin", "Schneider", "energie",
                                           "audit NIS2 manquant", "Pack Audit Express 15k€")
        assert script.prospect_name == "Jean Martin"
        assert script.company == "Schneider"
        assert len(script.qualification_questions) == 3
        assert isinstance(script.objection_responses, dict)

    def test_log_call_attempt(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.voice_agent_engine import VoiceAgentEngine
        engine = VoiceAgentEngine()
        script = engine.create_call_script("Alice", "ABB", "transport", "pain", "offer")
        log_id = engine.log_call_attempt(script.script_id, "voicemail", 45)
        assert isinstance(log_id, str)

    def test_get_best_call_times_default(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.voice_agent_engine import VoiceAgentEngine
        engine = VoiceAgentEngine()
        result = engine.get_best_call_times("energie")
        assert "best_day" in result
        assert "best_hour" in result

    def test_get_stats_returns_dict(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.voice_agent_engine import VoiceAgentEngine
        stats = VoiceAgentEngine().get_stats()
        assert "total_scripts" in stats
        assert "total_calls" in stats


class TestAnnualReportParser:

    SAMPLE_TEXT = """
    Directeur de la Sécurité des Systèmes d'Information: Marc Dupont
    Budget cybersécurité 2023: 2 M€ alloués à la sécurité OT et SCADA.
    Incident majeur détecté en mars 2023 sur les systèmes SCADA.
    Ambitions OT: digitalisation industrie 4.0 et déploiement ICS.
    CTO: Pierre Lambert nommé en janvier 2023.
    """

    def test_ingest_report_extracts_fields(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.annual_report_parser import AnnualReportParser
        parser = AnnualReportParser()
        report = parser.ingest_report("TotalEnergies", 2023, "energie", self.SAMPLE_TEXT)
        assert report.company == "TotalEnergies"
        assert report.year == 2023
        assert report.investment_score >= 0

    def test_ingest_report_detects_ot_ambitions(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.annual_report_parser import AnnualReportParser
        parser = AnnualReportParser()
        report = parser.ingest_report("Michelin", 2022, "industrie", self.SAMPLE_TEXT)
        assert len(report.ot_ambitions) > 0

    def test_get_high_value_companies_filter(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.annual_report_parser import AnnualReportParser
        parser = AnnualReportParser()
        parser.ingest_report("BigCo", 2023, "energie", self.SAMPLE_TEXT)
        high_value = parser.get_high_value_companies(min_cyber_budget=100_000)
        assert isinstance(high_value, list)

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.ai_advanced.annual_report_parser import AnnualReportParser
        stats = AnnualReportParser().get_stats()
        assert "total_reports" in stats


# ══════════════════════════════════════════════════════════════════════════════
# GROUP 3 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════

class TestSovereignVectorStore:

    def test_upsert_and_search(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.sovereign_vector_store import SovereignVectorStore
        store = SovereignVectorStore()
        store.upsert("test_col", "doc1", [1.0, 0.0, 0.0], {"sector": "energie"})
        store.upsert("test_col", "doc2", [0.0, 1.0, 0.0], {"sector": "transport"})
        results = store.search("test_col", [1.0, 0.0, 0.0], top_k=2)
        assert len(results) >= 1
        assert results[0]["doc_id"] == "doc1"
        assert results[0]["score"] > 0.9

    def test_cosine_similarity_identical(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.sovereign_vector_store import SovereignVectorStore
        store = SovereignVectorStore()
        store.upsert("col", "d1", [1.0, 1.0, 1.0], {})
        results = store.search("col", [1.0, 1.0, 1.0], top_k=1)
        assert abs(results[0]["score"] - 1.0) < 1e-6

    def test_delete_removes_doc(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.sovereign_vector_store import SovereignVectorStore
        store = SovereignVectorStore()
        store.upsert("col2", "d1", [1.0, 0.0], {"x": 1})
        deleted = store.delete("col2", "d1")
        assert deleted is True
        results = store.search("col2", [1.0, 0.0], top_k=5)
        assert len(results) == 0

    def test_filter_metadata_works(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.sovereign_vector_store import SovereignVectorStore
        store = SovereignVectorStore()
        store.upsert("col3", "d1", [1.0, 0.0], {"sector": "energie"})
        store.upsert("col3", "d2", [0.9, 0.1], {"sector": "transport"})
        results = store.search("col3", [1.0, 0.0], top_k=5, filter_metadata={"sector": "energie"})
        assert all(r["metadata"]["sector"] == "energie" for r in results)

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.sovereign_vector_store import SovereignVectorStore
        stats = SovereignVectorStore().get_stats()
        assert "collections" in stats
        assert "total_docs" in stats


class TestFederatedLearner:

    def test_record_outcome_returns_id(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.federated_learner import FederatedLearner
        learner = FederatedLearner()
        oid = learner.record_outcome("deal_won", {"sector": "energie", "tier": "TIER2"},
                                     "success", 15000.0)
        assert isinstance(oid, str)

    def test_predict_probability_range(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.federated_learner import FederatedLearner
        learner = FederatedLearner()
        for _ in range(5):
            learner.record_outcome("deal_won", {"sector": "energie"}, "success", 15000.0)
        for _ in range(3):
            learner.record_outcome("deal_won", {"sector": "transport"}, "failure", 0.0)
        prob = learner.predict_success_probability("deal_won", {"sector": "energie"})
        assert 0.0 <= prob <= 1.0

    def test_no_data_returns_half(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.federated_learner import FederatedLearner
        learner = FederatedLearner()
        prob = learner.predict_success_probability("deal_won", {"sector": "unknown_sector"})
        assert prob == 0.5

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.federated_learner import FederatedLearner
        stats = FederatedLearner().get_stats()
        assert "total_outcomes" in stats
        assert "model_version" in stats


class TestDigitalTwinEngine:

    def test_create_twin_returns_twin(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.digital_twin_engine import DigitalTwinEngine
        engine = DigitalTwinEngine()
        twin = engine.create_twin("P001", "EDF", "Jean Martin", "RSSI", "energie")
        assert twin.prospect_id == "P001"
        assert twin.company == "EDF"

    def test_update_behavior_updates_response_rate(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.digital_twin_engine import DigitalTwinEngine
        engine = DigitalTwinEngine()
        engine.create_twin("P002", "TotalEnergies", "Alice", "DSI", "energie")
        engine.update_behavior("P002", "email_sent", "email", True, "positive")
        engine.update_behavior("P002", "email_sent", "email", False, "neutral")
        twin = engine.get_twin("P002")
        assert twin.response_rate == 0.5

    def test_get_optimal_contact_window_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.digital_twin_engine import DigitalTwinEngine
        engine = DigitalTwinEngine()
        engine.create_twin("P003", "SNCF", "Bob", "CTO", "transport")
        window = engine.get_optimal_contact_window("P003")
        assert "day" in window
        assert "channel" in window
        assert "confidence" in window

    def test_get_twin_nonexistent_returns_none(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.digital_twin_engine import DigitalTwinEngine
        engine = DigitalTwinEngine()
        assert engine.get_twin("nonexistent_id") is None

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.digital_twin_engine import DigitalTwinEngine
        stats = DigitalTwinEngine().get_stats()
        assert "total_twins" in stats


class TestZKPAuditEngine:

    def test_create_commitment_fields(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.zkp_audit_engine import ZKPAuditEngine
        engine = ZKPAuditEngine()
        commitment = engine.create_audit_commitment(
            "COMP_001", {"level": 2, "zones": 5, "score": 78}
        )
        assert commitment.company_id == "COMP_001"
        assert len(commitment.data_hash) == 64
        assert len(commitment.merkle_root) == 64

    def test_generate_and_verify_proof(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.zkp_audit_engine import ZKPAuditEngine
        engine = ZKPAuditEngine()
        commitment = engine.create_audit_commitment("COMP_002", {"data": "audit"})
        proof = engine.generate_proof(commitment.commitment_id, "compliant_level_2")
        assert engine.verify_proof(proof) is True

    def test_tampered_proof_fails_verification(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.zkp_audit_engine import ZKPAuditEngine, ZKProof
        engine = ZKPAuditEngine()
        commitment = engine.create_audit_commitment("COMP_003", {"data": "real"})
        proof = engine.generate_proof(commitment.commitment_id, "compliant_level_3")
        tampered = ZKProof(
            proof_id=proof.proof_id,
            commitment_id=proof.commitment_id,
            claim=proof.claim,
            challenge_hash=proof.challenge_hash,
            response_hash="000000tampered",
            verified=proof.verified,
            created_at=proof.created_at,
        )
        assert engine.verify_proof(tampered) is False

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.zkp_audit_engine import ZKPAuditEngine
        stats = ZKPAuditEngine().get_stats()
        assert "total_commitments" in stats
        assert "total_proofs" in stats


class TestQuantumSafeAdvisor:

    def test_assess_crypto_posture_rsa(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.quantum_safe_advisor import QuantumSafeAdvisor
        advisor = QuantumSafeAdvisor()
        assessment = advisor.assess_crypto_posture(
            "Airbus", "aeronautique",
            [{"algorithm": "RSA"}, {"algorithm": "ECDSA"}]
        )
        assert "RSA" in assessment.vulnerable_algorithms
        assert "ECDSA" in assessment.vulnerable_algorithms
        assert assessment.quantum_risk_score > 0

    def test_generate_roadmap_phases(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.quantum_safe_advisor import QuantumSafeAdvisor
        advisor = QuantumSafeAdvisor()
        assessment = advisor.assess_crypto_posture("Test Co", "industrie", [{"algorithm": "DH"}])
        roadmap = advisor.generate_migration_roadmap(assessment.assessment_id)
        assert len(roadmap.phases) >= 3
        assert roadmap.total_effort_days > 0
        assert roadmap.estimated_cost_eur > 0

    def test_get_pqc_algorithms(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.quantum_safe_advisor import QuantumSafeAdvisor
        algorithms = QuantumSafeAdvisor().get_pqc_algorithms()
        assert len(algorithms) >= 4
        names = [a["name"] for a in algorithms]
        assert "CRYSTALS-Kyber" in names

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.architecture.quantum_safe_advisor import QuantumSafeAdvisor
        stats = QuantumSafeAdvisor().get_stats()
        assert "total_assessments" in stats


# ══════════════════════════════════════════════════════════════════════════════
# GROUP 4 — VERTICALS
# ══════════════════════════════════════════════════════════════════════════════

class TestAIActComplianceEngine:

    def test_high_risk_transport_sector(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import AIActComplianceEngine
        engine = AIActComplianceEngine()
        assessment = engine.assess_ai_system(
            "SNCF", "TrafficAI", "traffic_management",
            "transport", ["predictive_routing"]
        )
        assert assessment.risk_category == "HIGH"
        assert len(assessment.applicable_obligations) > 0
        assert assessment.compliance_gap_score > 0

    def test_unacceptable_risk_category(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import AIActComplianceEngine
        engine = AIActComplianceEngine()
        assessment = engine.assess_ai_system(
            "BadCo", "ScoringAI", "social_scoring",
            "government", ["social_scoring"]
        )
        assert assessment.risk_category == "UNACCEPTABLE"

    def test_minimal_risk_category(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import AIActComplianceEngine
        engine = AIActComplianceEngine()
        assessment = engine.assess_ai_system(
            "SmallCo", "SpamFilter", "spam_detection",
            "retail", ["email_filter"]
        )
        assert assessment.risk_category == "MINIMAL"

    def test_get_upcoming_deadlines(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import AIActComplianceEngine
        deadlines = AIActComplianceEngine().get_upcoming_deadlines()
        assert len(deadlines) >= 3

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.ai_act_compliance_engine import AIActComplianceEngine
        stats = AIActComplianceEngine().get_stats()
        assert "total_assessments" in stats


class TestAfricaOTVertical:

    def test_qualify_prospect_developing(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.africa_ot_vertical import AfricaOTVertical
        vertical = AfricaOTVertical()
        prospect = vertical.qualify_prospect(
            "Gabon Oil Corp", "Gabon", "oil_gas", 500, True, True
        )
        assert prospect.ot_maturity_level == "DEVELOPING"
        assert prospect.estimated_budget_eur > 0
        assert prospect.priority_score >= 40

    def test_qualify_prospect_nascent(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.africa_ot_vertical import AfricaOTVertical
        vertical = AfricaOTVertical()
        prospect = vertical.qualify_prospect(
            "Small Factory", "Sénégal", "agro_food", 50, False, False
        )
        assert prospect.ot_maturity_level == "NASCENT"

    def test_get_target_countries_count(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.africa_ot_vertical import AfricaOTVertical
        countries = AfricaOTVertical().get_target_countries()
        assert len(countries) >= 6
        codes = [c["code"] for c in countries]
        assert "SN" in codes
        assert "MA" in codes

    def test_generate_localized_pitch(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.africa_ot_vertical import AfricaOTVertical
        vertical = AfricaOTVertical()
        prospect = vertical.qualify_prospect("Mining Co", "Côte d'Ivoire", "mining", 200, True, False)
        pitch = vertical.generate_localized_pitch(prospect.prospect_id, language="fr")
        assert isinstance(pitch, str)
        assert len(pitch) > 10

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.africa_ot_vertical import AfricaOTVertical
        stats = AfricaOTVertical().get_stats()
        assert "total_prospects" in stats


class TestSupplyChainRiskScorer:

    def test_register_supplier_creates_profile(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.supply_chain_risk_scorer import SupplyChainRiskScorer
        scorer = SupplyChainRiskScorer()
        profile = scorer.register_supplier(
            "S001", "TechCorp", "France", "cybersecurite", 200,
            ["ISO27001", "IEC62443"], known_vulnerabilities=0
        )
        assert profile.supplier_id == "S001"
        assert profile.cyber_risk_score >= 0
        assert profile.risk_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    def test_score_supplier_iso27001_reduces_risk(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.supply_chain_risk_scorer import SupplyChainRiskScorer
        scorer = SupplyChainRiskScorer()
        good = scorer.register_supplier("S002", "Good Co", "France", "it", 500, ["ISO27001", "IEC62443"])
        bad = scorer.register_supplier("S003", "Bad Co", "Unknown", "it", 10, [], known_vulnerabilities=5)
        assert good.cyber_risk_score < bad.cyber_risk_score

    def test_assess_supply_chain_report(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.supply_chain_risk_scorer import SupplyChainRiskScorer
        scorer = SupplyChainRiskScorer()
        scorer.register_supplier("S010", "VendorA", "France", "it", 100, ["ISO27001"])
        scorer.register_supplier("S011", "VendorB", "Russia", "it", 5, [], known_vulnerabilities=10)
        report = scorer.assess_supply_chain("MyCo", ["S010", "S011"])
        assert report.total_suppliers == 2
        assert report.overall_chain_score >= 0

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.supply_chain_risk_scorer import SupplyChainRiskScorer
        stats = SupplyChainRiskScorer().get_stats()
        assert "total_suppliers" in stats
        assert "avg_risk_score" in stats


class TestInsuranceAdvisoryEngine:

    def test_assess_insurability_high_score(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.insurance_advisory_engine import InsuranceAdvisoryEngine
        engine = InsuranceAdvisoryEngine()
        assessment = engine.assess_insurability(
            "Safe Corp", "energie", 10_000_000, True, 10, ["ISO27001", "IEC62443"]
        )
        assert assessment.insurability_score > 50
        assert len(assessment.recommended_insurers) > 0
        assert assessment.estimated_premium_eur > 0

    def test_recent_incident_reduces_score(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.insurance_advisory_engine import InsuranceAdvisoryEngine
        engine = InsuranceAdvisoryEngine()
        good = engine.assess_insurability("Good Co", "transport", 5_000_000, True, 10, [])
        bad = engine.assess_insurability("Bad Co", "transport", 5_000_000, False, 1, [])
        assert good.insurability_score > bad.insurability_score

    def test_calculate_commission_12_percent(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.insurance_advisory_engine import InsuranceAdvisoryEngine
        engine = InsuranceAdvisoryEngine()
        commission = engine.calculate_commission(15_000.0)
        assert abs(commission - 1_800.0) < 0.01

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.insurance_advisory_engine import InsuranceAdvisoryEngine
        stats = InsuranceAdvisoryEngine().get_stats()
        assert "total_assessments" in stats


class TestSpaceSatelliteOTSecurity:

    def test_assess_satellite_link_fields(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.space_satellite_ot_security import SpaceSatelliteOTSecurity
        service = SpaceSatelliteOTSecurity()
        assessment = service.assess_satellite_link(
            "PowerGrid", "Starlink", "LEO",
            ["SCADA-controller", "HMI-station"], "none"
        )
        assert assessment.company == "PowerGrid"
        assert assessment.attack_surface_score > 0
        assert len(assessment.critical_vulnerabilities) > 0
        assert assessment.estimated_hardening_eur > 0

    def test_no_encryption_adds_vulnerability(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.space_satellite_ot_security import SpaceSatelliteOTSecurity
        service = SpaceSatelliteOTSecurity()
        a1 = service.assess_satellite_link("Co1", "Starlink", "LEO", [], "AES256")
        a2 = service.assess_satellite_link("Co2", "Starlink", "LEO", [], "none")
        assert len(a2.critical_vulnerabilities) >= len(a1.critical_vulnerabilities)

    def test_get_known_vulnerabilities_starlink(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.space_satellite_ot_security import SpaceSatelliteOTSecurity
        vulns = SpaceSatelliteOTSecurity().get_known_vulnerabilities("Starlink")
        assert len(vulns) > 0
        assert "vulnerability" in vulns[0]

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.verticals.space_satellite_ot_security import SpaceSatelliteOTSecurity
        stats = SpaceSatelliteOTSecurity().get_stats()
        assert "total_assessments" in stats


# ══════════════════════════════════════════════════════════════════════════════
# GROUP 5 — FUTURE TECH
# ══════════════════════════════════════════════════════════════════════════════

class TestAgenticOrchestrator:

    def test_register_agent(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.agentic_orchestrator import AgenticOrchestrator
        orch = AgenticOrchestrator()
        result = orch.register_agent("A1", "PainHunter", ["hunting", "scoring"])
        assert result is True

    def test_submit_task_assigned(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.agentic_orchestrator import AgenticOrchestrator
        orch = AgenticOrchestrator()
        orch.register_agent("A2", "Researcher", ["enrichment"])
        task_id = orch.submit_task("T001", "enrich_prospect",
                                   {"company": "EDF"}, priority=8,
                                   required_capabilities=["enrichment"])
        status = orch.get_task_status(task_id)
        assert status["status"] in ("ASSIGNED", "PENDING")

    def test_get_delegation_chain(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.agentic_orchestrator import AgenticOrchestrator
        orch = AgenticOrchestrator()
        orch.register_agent("A3", "Writer", ["writing"])
        orch.submit_task("T002", "write_offer", {"prospect": "Airbus"})
        chain = orch.get_delegation_chain("T002")
        assert isinstance(chain, list)
        assert len(chain) >= 1

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.agentic_orchestrator import AgenticOrchestrator
        stats = AgenticOrchestrator().get_stats()
        assert "total_agents" in stats
        assert "total_tasks" in stats


class TestAmbientIoTIntelligence:

    def test_normal_reading_returns_none(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ambient_iot_intelligence import AmbientIoTIntelligence
        iot = AmbientIoTIntelligence()
        result = iot.ingest_sensor_event(
            "DEV001", "temperature_sensor", "PlantA", "industrie",
            "temperature", 45.0, 80.0, "°C"
        )
        assert result is None

    def test_anomaly_detected_above_threshold(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ambient_iot_intelligence import AmbientIoTIntelligence
        iot = AmbientIoTIntelligence()
        anomaly = iot.ingest_sensor_event(
            "DEV002", "pressure_sensor", "PlantB", "industrie",
            "pressure", 200.0, 100.0, "bar"
        )
        assert anomaly is not None
        assert anomaly.deviation_pct == 100.0
        assert anomaly.severity in ("CRITICAL", "HIGH", "MEDIUM")

    def test_get_active_anomalies_filter(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ambient_iot_intelligence import AmbientIoTIntelligence
        iot = AmbientIoTIntelligence()
        iot.ingest_sensor_event("D1", "sensor", "CompanyX", "industrie",
                                "voltage", 500.0, 200.0, "V")
        iot.ingest_sensor_event("D2", "sensor", "CompanyY", "energie",
                                "voltage", 500.0, 200.0, "V")
        x_anomalies = iot.get_active_anomalies(company="CompanyX")
        assert all(a.company == "CompanyX" for a in x_anomalies)

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ambient_iot_intelligence import AmbientIoTIntelligence
        stats = AmbientIoTIntelligence().get_stats()
        assert "total_anomalies" in stats
        assert "critical_count" in stats


class TestNeuromorphicScorer:

    def test_record_and_score(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.neuromorphic_scorer import NeuromorphicScorer
        scorer = NeuromorphicScorer()
        now = datetime.now(timezone.utc).isoformat()
        scorer.record_event("LEAD001", "reply", now, 1.0)
        scorer.record_event("LEAD001", "meeting_request", now, 1.0)
        score = scorer.compute_temporal_score("LEAD001")
        assert score > 0
        assert score <= 100

    def test_score_decays_over_time(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.neuromorphic_scorer import NeuromorphicScorer
        scorer = NeuromorphicScorer()
        old_ts = "2020-01-01T00:00:00+00:00"
        now_ts = datetime.now(timezone.utc).isoformat()
        scorer.record_event("LEAD002", "reply", old_ts)
        scorer.record_event("LEAD003", "reply", now_ts)
        old_score = scorer.compute_temporal_score("LEAD002")
        new_score = scorer.compute_temporal_score("LEAD003")
        assert new_score > old_score

    def test_empty_lead_score_zero(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.neuromorphic_scorer import NeuromorphicScorer
        assert NeuromorphicScorer().compute_temporal_score("NONEXISTENT") == 0.0

    def test_get_top_leads(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.neuromorphic_scorer import NeuromorphicScorer
        scorer = NeuromorphicScorer()
        now_ts = datetime.now(timezone.utc).isoformat()
        scorer.record_event("L1", "meeting_request", now_ts)
        scorer.record_event("L2", "email_open", now_ts)
        top = scorer.get_top_leads(top_n=2)
        assert len(top) == 2
        assert top[0]["score"] >= top[1]["score"]

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.neuromorphic_scorer import NeuromorphicScorer
        stats = NeuromorphicScorer().get_stats()
        assert "total_leads" in stats
        assert "total_spikes" in stats


class TestBlockchainProofOfAudit:

    def test_register_audit_returns_proof(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import BlockchainProofOfAudit
        chain = BlockchainProofOfAudit()
        proof = chain.register_audit(
            "AUDIT001", "TotalEnergies", "IEC62443",
            "NAYA SUPREME", "Zones 1-4", "Conforme SL-2"
        )
        assert proof.audit_id == "AUDIT001"
        assert proof.company == "TotalEnergies"
        assert len(proof.content_hash) == 64
        assert len(proof.tx_hash) == 64
        assert proof.is_verified is True

    def test_verify_proof_valid(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import BlockchainProofOfAudit
        chain = BlockchainProofOfAudit()
        proof = chain.register_audit("AUDIT002", "EDF", "NIS2", "NAYA", "All systems", "Gap 15%")
        result = chain.verify_proof(proof.proof_id)
        assert result["verified"] is True
        assert "tx_hash" in result

    def test_get_proof_by_company(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import BlockchainProofOfAudit
        chain = BlockchainProofOfAudit()
        chain.register_audit("A1", "Airbus", "IEC62443", "NAYA", "scope", "ok")
        chain.register_audit("A2", "Airbus", "NIS2", "NAYA", "scope2", "ok")
        chain.register_audit("A3", "Other Co", "NIS2", "NAYA", "scope3", "ok")
        proofs = chain.get_proof_by_company("Airbus")
        assert len(proofs) == 2

    def test_export_certificate_text(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import BlockchainProofOfAudit
        chain = BlockchainProofOfAudit()
        proof = chain.register_audit("A4", "Renault", "IEC62443", "NAYA", "s", "r")
        cert = chain.export_certificate(proof.proof_id)
        assert isinstance(cert, str)
        assert "Renault" in cert

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.blockchain_proof_of_audit import BlockchainProofOfAudit
        stats = BlockchainProofOfAudit().get_stats()
        assert "total_proofs" in stats
        assert "verified_proofs" in stats


class TestAROTAssessment:

    def test_create_session(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ar_ot_assessment import AROTAssessment
        engine = AROTAssessment()
        session = engine.create_session("SES001", "Michelin", "Usine Clermont", "Tech Dumont")
        assert session.session_id == "SES001"
        assert session.status == "ACTIVE"

    def test_ingest_ar_frame_detects_equipment(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ar_ot_assessment import AROTAssessment
        engine = AROTAssessment()
        engine.create_session("SES002", "Airbus", "Hangar 5", "Marie")
        detections = engine.ingest_ar_frame("SES002", {
            "equipment_labels": ["Siemens S7-1500 PLC", "Schneider Modicon M340"],
            "location": "Zone A"
        })
        assert len(detections) > 0
        assert detections[0].vendor in ("Siemens", "Schneider")

    def test_finalize_session_returns_report(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ar_ot_assessment import AROTAssessment
        engine = AROTAssessment()
        engine.create_session("SES003", "Renault", "Usine Flins", "Pierre")
        engine.ingest_ar_frame("SES003", {
            "equipment_labels": ["Rockwell CompactLogix controller"],
            "location": "Line 1"
        })
        report = engine.finalize_session("SES003")
        assert report.session_id == "SES003"
        assert report.equipment_count >= 1
        assert report.risk_score >= 0

    def test_get_stats_structure(self, tmp_cache):
        from V20_INTELLIGENCE.future_tech.ar_ot_assessment import AROTAssessment
        stats = AROTAssessment().get_stats()
        assert "total_sessions" in stats
        assert "completed_sessions" in stats


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER — V20 JOBS REGISTERED
# ══════════════════════════════════════════════════════════════════════════════

class TestSchedulerV20Jobs:

    def test_v20_jobs_in_cycle_intervals(self):
        """All 5 V20 jobs are registered in CYCLE_INTERVALS."""
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        expected = [
            "dark_web_scan", "cve_shodan_refresh", "tender_radar_scan",
            "regulatory_deadline_check", "sentiment_radar_sweep"
        ]
        for job in expected:
            assert job in CYCLE_INTERVALS, f"Missing job: {job}"

    def test_dark_web_scan_interval_2h(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert CYCLE_INTERVALS["dark_web_scan"] == 2 * 3600

    def test_sentiment_radar_30min(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert CYCLE_INTERVALS["sentiment_radar_sweep"] == 30 * 60

    def test_regulatory_deadline_check_24h(self):
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS
        assert CYCLE_INTERVALS["regulatory_deadline_check"] == 24 * 3600

    def test_scheduler_has_job_methods(self):
        """All V20 job methods exist on AutonomousScheduler."""
        from NAYA_SCHEDULER.autonomous_scheduler import AutonomousScheduler
        scheduler = AutonomousScheduler()
        for job in ["dark_web_scan", "cve_shodan_refresh", "tender_radar_scan",
                    "regulatory_deadline_check", "sentiment_radar_sweep"]:
            assert hasattr(scheduler, f"_job_{job}"), f"Missing method _job_{job}"
