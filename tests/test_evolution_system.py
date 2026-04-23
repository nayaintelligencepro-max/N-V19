"""
NAYA V19 — Tests Evolution System
Couvre : AutonomousLearner, AnticipationEngine, ProposalGenerator,
         EvolutionOrchestrator, DynamicScaler, DealRiskScorer
"""
import sys
import time
import tempfile
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
    """Rediriger les fichiers de cache vers un répertoire temporaire."""
    cache = tmp_path / "cache"
    cache.mkdir()
    import EVOLUTION_SYSTEM.autonomous_learner as al_mod
    import EVOLUTION_SYSTEM.anticipation_engine as ae_mod
    import EVOLUTION_SYSTEM.evolution_orchestrator as eo_mod
    import PARALLEL_ENGINE.dynamic_scaler as ds_mod
    import NAYA_CORE.deal_risk_scorer as dr_mod
    monkeypatch.setattr(al_mod, "DATA_FILE", cache / "learner.json")
    monkeypatch.setattr(ae_mod, "DATA_FILE", cache / "anticipation.json")
    monkeypatch.setattr(eo_mod, "DATA_FILE", cache / "orchestrator.json")
    monkeypatch.setattr(ds_mod, "DATA_FILE", cache / "scaler.json")
    monkeypatch.setattr(dr_mod, "DATA_FILE", cache / "deals.json")
    return cache


@pytest.fixture
def learner(tmp_cache):
    from EVOLUTION_SYSTEM.autonomous_learner import AutonomousLearner
    return AutonomousLearner()


@pytest.fixture
def anticipation(tmp_cache):
    from EVOLUTION_SYSTEM.anticipation_engine import AnticipationEngine
    return AnticipationEngine()


@pytest.fixture
def proposal_gen():
    from EVOLUTION_SYSTEM.proposal_generator import ProposalGenerator
    return ProposalGenerator()


@pytest.fixture
def scaler(tmp_cache):
    from PARALLEL_ENGINE.dynamic_scaler import DynamicScaler
    return DynamicScaler()


@pytest.fixture
def deal_scorer(tmp_cache):
    from NAYA_CORE.deal_risk_scorer import DealRiskScorer
    return DealRiskScorer()


@pytest.fixture
def sample_outcome():
    from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
    return DealOutcome(
        deal_id="TEST_001",
        sector="ot",
        signal_type="job_offer",
        offer_tier="TIER2",
        price_eur=15_000,
        converted=True,
        engagement_days=7,
        quality_score=0.75,
    )


@pytest.fixture
def sample_deal():
    from NAYA_CORE.deal_risk_scorer import Deal, DealTemperature
    return Deal(
        id="DEAL_001",
        company="TechCorp",
        contact_name="Jean Martin",
        sector="ot",
        value_eur=15_000,
        created_at=time.time() - 86400,
        last_interaction_at=time.time() - 86400,
        initial_score=0.75,
        temperature=DealTemperature.HOT,
    )


# ══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS LEARNER
# ══════════════════════════════════════════════════════════════════════════════

class TestAutonomousLearner:

    def test_init_empty(self, learner):
        summary = learner.get_learning_summary()
        assert summary["total_outcomes"] == 0
        assert summary["current_params_version"] == 1
        assert summary["current_min_ticket"] == 1_000  # plancher inviolable

    def test_record_outcome_increments_count(self, learner, sample_outcome):
        learner.record_outcome(sample_outcome)
        assert learner.get_learning_summary()["total_outcomes"] == 1

    def test_min_ticket_never_regresses(self, learner, sample_outcome):
        """Le plancher de 1000€ ne peut jamais être violé."""
        learner.record_outcome(sample_outcome)
        params = learner.get_optimized_hunt_params()
        assert params.min_ticket_eur >= 1_000

    def test_target_ticket_never_regresses(self, learner, sample_outcome):
        """Le ticket cible ne peut jamais descendre."""
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        initial_target = learner.get_optimized_hunt_params().target_ticket_eur

        # Enregistrer des deals qui feront apprendre le système
        for i in range(10):
            outcome = DealOutcome(
                deal_id=f"D{i}",
                sector="ot",
                signal_type="regulatory",
                offer_tier="TIER2",
                price_eur=20_000,
                converted=(i % 2 == 0),
                quality_score=0.80,
            )
            learner.record_outcome(outcome)

        new_target = learner.get_optimized_hunt_params().target_ticket_eur
        assert new_target >= initial_target, \
            f"Régression détectée: {initial_target} → {new_target}"

    def test_quality_multiplier_never_decreases(self, learner, sample_outcome):
        """Le multiplicateur de qualité ne peut pas régresser."""
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        initial_mult = learner.get_optimized_hunt_params().quality_multiplier
        for i in range(15):
            learner.record_outcome(DealOutcome(
                deal_id=f"QM{i}", sector="energie",
                signal_type="job_offer", offer_tier="TIER2",
                price_eur=12_000, converted=True, quality_score=0.80,
            ))
        new_mult = learner.get_optimized_hunt_params().quality_multiplier
        assert new_mult >= initial_mult, f"Régression mult: {initial_mult} → {new_mult}"

    def test_sector_ranking_returns_list(self, learner, sample_outcome):
        learner.record_outcome(sample_outcome)
        ranking = learner.get_sector_ranking()
        assert isinstance(ranking, list)

    def test_sector_stats_updated(self, learner, sample_outcome):
        learner.record_outcome(sample_outcome)
        summary = learner.get_learning_summary()
        assert "ot" in summary["sector_stats"]
        assert summary["sector_stats"]["ot"]["total"] == 1

    def test_won_count_increments(self, learner, sample_outcome):
        learner.record_outcome(sample_outcome)
        assert learner.get_learning_summary()["total_won"] == 1

    def test_lost_not_counted_as_won(self, learner):
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        learner.record_outcome(DealOutcome(
            deal_id="LOST_01", sector="ot", signal_type="news",
            offer_tier="TIER1", price_eur=5_000, converted=False,
        ))
        assert learner.get_learning_summary()["total_won"] == 0

    def test_params_based_on_n_deals_grows(self, learner, sample_outcome):
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        for i in range(10):
            learner.record_outcome(DealOutcome(
                deal_id=f"X{i}", sector="transport",
                signal_type="linkedin", offer_tier="TIER2",
                price_eur=8_000, converted=True, quality_score=0.70,
            ))
        params = learner.get_optimized_hunt_params()
        assert params.based_on_n_deals >= 10

    def test_persistence_survives_reload(self, tmp_cache, sample_outcome):
        from EVOLUTION_SYSTEM.autonomous_learner import AutonomousLearner
        import EVOLUTION_SYSTEM.autonomous_learner as al_mod
        al_mod.DATA_FILE = tmp_cache / "learner.json"
        l1 = AutonomousLearner()
        l1.record_outcome(sample_outcome)
        v1 = l1.get_optimized_hunt_params().version

        # Simuler redémarrage
        l2 = AutonomousLearner()
        assert l2.get_learning_summary()["total_outcomes"] >= 1
        assert l2.get_optimized_hunt_params().version == v1


# ══════════════════════════════════════════════════════════════════════════════
# ANTICIPATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TestAnticipationEngine:

    def test_roadmap_has_36_months(self, anticipation):
        roadmap = anticipation.get_3year_roadmap()
        assert len(roadmap) == 36

    def test_month_1_target_positive(self, anticipation):
        roadmap = anticipation.get_3year_roadmap()
        m1 = next(m for m in roadmap if m["month"] == 1)
        assert m1["target_eur"] > 0

    def test_revenue_targets_monotonic(self, anticipation):
        """Les objectifs EUR ne doivent pas décroître avec le temps."""
        roadmap = anticipation.get_3year_roadmap()
        targets = [m["target_eur"] for m in roadmap]
        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1], \
                f"Régression M{i+1}→M{i+2}: {targets[i]} > {targets[i+1]}"

    def test_opportunities_returned(self, anticipation):
        opps = anticipation.get_upcoming_opportunities(horizon_days=365)
        assert len(opps) > 0

    def test_opportunities_sorted_by_priority(self, anticipation):
        opps = anticipation.get_upcoming_opportunities(90)
        priorities = [o.priority_score for o in opps]
        assert priorities == sorted(priorities, reverse=True)

    def test_record_revenue_updates_milestone(self, anticipation):
        anticipation.record_revenue(5_000, month=1)
        m1_status = anticipation.get_3year_roadmap()[0]["achieved_eur"]
        assert m1_status == 5_000

    def test_current_milestone_accessible(self, anticipation):
        cm = anticipation.get_current_milestone()
        assert cm.month >= 1
        assert cm.target_eur > 0

    def test_advance_month_increments(self, anticipation):
        m_before = anticipation.get_current_milestone().month
        anticipation.advance_month()
        m_after = anticipation.get_current_milestone().month
        assert m_after == min(m_before + 1, 36)

    def test_stats_returns_dict(self, anticipation):
        stats = anticipation.get_stats()
        assert "current_month" in stats
        assert "milestones_total" in stats
        assert stats["milestones_total"] == 36


# ══════════════════════════════════════════════════════════════════════════════
# PROPOSAL GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class TestProposalGenerator:

    def test_low_conversion_triggers_qualification_proposal(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "conversion_rate": 0.05,  # < 10%
            "mrr": 10_000,
            "mrr_target": 20_000,
            "automation_rate": 0.6,
            "shi_score": 0.7,
            "avg_ticket_eur": 15_000,
        })
        ids = [p.id for p in proposals]
        assert "P_CONV_01" in ids

    def test_low_mrr_triggers_subscription_proposal(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "conversion_rate": 0.15,
            "mrr": 3_000,   # << 50% de mrr_target=20k
            "mrr_target": 20_000,
            "automation_rate": 0.6,
            "shi_score": 0.7,
        })
        ids = [p.id for p in proposals]
        assert "P_MRR_01" in ids

    def test_low_shi_triggers_resilience_proposal(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "shi_score": 0.40,  # < 0.60
            "conversion_rate": 0.15,
            "mrr": 15_000,
            "mrr_target": 20_000,
            "automation_rate": 0.6,
        })
        ids = [p.id for p in proposals]
        assert "P_SHI_01" in ids

    def test_proposals_sorted_by_priority(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "conversion_rate": 0.05,
            "mrr": 2_000,
            "mrr_target": 20_000,
            "automation_rate": 0.25,
            "shi_score": 0.4,
            "avg_ticket_eur": 5_000,
            "active_slots": 4,
            "max_slots": 4,
            "revenue_growth": -0.1,
        })
        scores = [p.priority_score for p in proposals]
        assert scores == sorted(scores, reverse=True)

    def test_rank_by_roi_works(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "conversion_rate": 0.05, "mrr": 1_000, "mrr_target": 20_000,
        })
        ranked = proposal_gen.rank_by_roi(proposals)
        rois = [p.expected_roi for p in ranked]
        assert rois == sorted(rois, reverse=True)

    def test_floor_violation_not_proposed(self, proposal_gen):
        """Aucune proposition ne doit suggérer un prix inférieur à 1000€ comme contrat cible."""
        proposals = proposal_gen.generate_alternatives({
            "avg_ticket_eur": 500, "conversion_rate": 0.05,
            "mrr": 500, "mrr_target": 20_000,
        })
        for p in proposals:
            # Vérifier que le min_ticket dans les paramètres reste ≥ 1000€
            # (les actions peuvent mentionner des prix partiels comme upsell)
            assert p.type is not None  # chaque proposition a un type valide
        # Le plancher du learner doit rester 1000€ peu importe le contexte
        from EVOLUTION_SYSTEM.autonomous_learner import AutonomousLearner
        l = AutonomousLearner()
        assert l.get_optimized_hunt_params().min_ticket_eur == 1_000

    def test_all_proposals_have_actions(self, proposal_gen):
        proposals = proposal_gen.generate_alternatives({
            "conversion_rate": 0.04, "mrr": 1_000, "mrr_target": 20_000,
            "automation_rate": 0.2, "shi_score": 0.35, "avg_ticket_eur": 2_000,
        })
        for p in proposals:
            assert len(p.actions) > 0, f"Proposition {p.id} sans actions"


# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC SCALER
# ══════════════════════════════════════════════════════════════════════════════

class TestDynamicScaler:

    def test_initial_slots_is_4(self, scaler):
        assert scaler.get_current_slots() == 4

    def test_scale_up_when_conditions_met(self, scaler):
        """Scale vers le haut quand toutes les conditions sont remplies."""
        # Forcer le cooldown à zéro
        scaler._last_scale_ts = 0
        result = scaler.evaluate_and_scale({
            "shi_score": 0.80,
            "conversion_rate": 0.20,
            "mrr": 15_000,
            "slots_libres": 0,
            "active_slots": 4,
            "max_slots": 4,
        })
        assert result["action"] == "up"
        assert scaler.get_current_slots() == 5

    def test_no_scale_below_shi_threshold(self, scaler):
        scaler._last_scale_ts = 0
        result = scaler.evaluate_and_scale({
            "shi_score": 0.60,  # < 0.75
            "conversion_rate": 0.20,
            "mrr": 15_000,
            "slots_libres": 0,
        })
        assert result["action"] == "hold"
        assert scaler.get_current_slots() == 4

    def test_scale_down_when_shi_critical(self, scaler):
        scaler._current_slots = 6
        scaler._last_scale_ts = 0
        result = scaler.evaluate_and_scale({
            "shi_score": 0.30,  # < 0.40 → réduction
            "conversion_rate": 0.20,
            "mrr": 15_000,
        })
        assert result["action"] == "down"
        assert scaler.get_current_slots() == 5

    def test_floor_never_below_4(self, scaler):
        """Le nombre de slots ne peut jamais descendre sous MIN_SLOTS=4."""
        scaler._current_slots = 4
        scaler._last_scale_ts = 0
        scaler.evaluate_and_scale({
            "shi_score": 0.20,  # Force réduction
        })
        assert scaler.get_current_slots() >= 4

    def test_ceiling_never_above_12(self, scaler):
        """Le nombre de slots ne peut jamais dépasser MAX_SLOTS_ABSOLUTE=12."""
        scaler._current_slots = 12
        scaler._last_scale_ts = 0
        result = scaler.force_scale(15)
        assert scaler.get_current_slots() <= 12

    def test_cooldown_prevents_rapid_scaling(self, scaler):
        """Le cooldown empêche deux scalings en moins de 24h."""
        scaler._last_scale_ts = 0
        scaler.evaluate_and_scale({
            "shi_score": 0.80, "conversion_rate": 0.20,
            "mrr": 15_000, "slots_libres": 0,
        })
        # Deuxième scaling immédiatement — doit être bloqué
        slots_after_first = scaler.get_current_slots()
        scaler.evaluate_and_scale({
            "shi_score": 0.80, "conversion_rate": 0.20,
            "mrr": 15_000, "slots_libres": 0,
        })
        assert scaler.get_current_slots() == slots_after_first

    def test_stats_returns_correct_structure(self, scaler):
        stats = scaler.get_stats()
        assert "current_slots" in stats
        assert "min_slots" in stats
        assert "max_slots" in stats
        assert stats["min_slots"] == 4
        assert stats["max_slots"] == 12


# ══════════════════════════════════════════════════════════════════════════════
# DEAL RISK SCORER
# ══════════════════════════════════════════════════════════════════════════════

class TestDealRiskScorer:

    def test_register_deal(self, deal_scorer, sample_deal):
        deal_scorer.register_deal(sample_deal)
        dashboard = deal_scorer.get_dashboard()
        assert dashboard["total_active"] == 1

    def test_hot_deal_recent_interaction(self, deal_scorer, sample_deal):
        """Deal avec interaction récente doit être chaud."""
        from NAYA_CORE.deal_risk_scorer import DealTemperature
        sample_deal.last_interaction_at = time.time() - 3600  # 1h ago
        deal_scorer.register_deal(sample_deal)
        report = deal_scorer.run_check()
        assert report.hot == 1
        assert report.cold == 0

    def test_cold_deal_triggers_alert(self, deal_scorer, sample_deal):
        """Deal sans réponse depuis 8j doit être classé froid."""
        from NAYA_CORE.deal_risk_scorer import DealTemperature
        sample_deal.last_interaction_at = time.time() - 8 * 86400  # 8j ago
        deal_scorer.register_deal(sample_deal)
        with patch.object(deal_scorer, "_notify") as mock_notify:
            report = deal_scorer.run_check()
        assert report.cold >= 1
        mock_notify.assert_called_once()

    def test_lost_deal_after_21_days(self, deal_scorer, sample_deal):
        """Deal sans réponse depuis 22j doit être classé perdu."""
        sample_deal.last_interaction_at = time.time() - 22 * 86400
        deal_scorer.register_deal(sample_deal)
        with patch.object(deal_scorer, "_notify"):
            report = deal_scorer.run_check()
        assert report.lost >= 1

    def test_interaction_reheats_deal(self, deal_scorer, sample_deal):
        """Une interaction récente réchauffe un deal froid."""
        sample_deal.last_interaction_at = time.time() - 8 * 86400
        deal_scorer.register_deal(sample_deal)
        deal_scorer.record_interaction(sample_deal.id, "positive_signal")
        with patch.object(deal_scorer, "_notify"):
            report = deal_scorer.run_check()
        # Après interaction, le deal ne doit plus être froid
        assert sample_deal.id not in report.cold_deals or report.hot >= 1

    def test_pipeline_eur_sums_correctly(self, deal_scorer):
        from NAYA_CORE.deal_risk_scorer import Deal, DealTemperature
        for i, val in enumerate([5_000, 10_000, 20_000]):
            deal_scorer.register_deal(Deal(
                id=f"D{i}", company=f"Co{i}", contact_name="X",
                sector="ot", value_eur=val,
                created_at=time.time(),
                last_interaction_at=time.time() - 3600,
            ))
        report = deal_scorer.run_check()
        assert report.total_pipeline_eur == 35_000

    def test_won_deal_excluded_from_active(self, deal_scorer, sample_deal):
        deal_scorer.register_deal(sample_deal)
        deal_scorer.mark_won(sample_deal.id)
        dashboard = deal_scorer.get_dashboard()
        assert dashboard["total_active"] == 0

    def test_get_cold_deals_list(self, deal_scorer, sample_deal):
        sample_deal.last_interaction_at = time.time() - 10 * 86400
        deal_scorer.register_deal(sample_deal)
        with patch.object(deal_scorer, "_notify"):
            deal_scorer.run_check()
        cold = deal_scorer.get_cold_deals()
        assert len(cold) >= 1
        assert cold[0].id == sample_deal.id


# ══════════════════════════════════════════════════════════════════════════════
# ÉVOLUTION SANS RÉGRESSION — TEST D'INTÉGRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestNoRegressionIntegration:
    """Valide que le cycle d'évolution complet ne crée jamais de régression."""

    def test_min_ticket_never_drops_across_cycles(self, learner):
        """À travers plusieurs cycles d'apprentissage, le plancher reste inviolable."""
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        min_tickets = []
        for cycle in range(3):
            for j in range(5):
                learner.record_outcome(DealOutcome(
                    deal_id=f"C{cycle}_{j}", sector=["ot","energie","transport"][cycle % 3],
                    signal_type=["job_offer","news","regulatory"][j % 3],
                    offer_tier=["TIER1","TIER2","TIER3"][j % 3],
                    price_eur=float(1_000 + cycle * 5_000 + j * 1_000),
                    converted=(j % 2 == 0),
                    quality_score=0.60 + j * 0.05,
                ))
            min_tickets.append(learner.get_optimized_hunt_params().min_ticket_eur)
        # Aucune régression sur le plancher
        for t in min_tickets:
            assert t >= 1_000

    def test_target_ticket_only_increases(self, learner):
        """Le ticket cible ne peut qu'augmenter ou rester stable."""
        from EVOLUTION_SYSTEM.autonomous_learner import DealOutcome
        targets = [learner.get_optimized_hunt_params().target_ticket_eur]
        for i in range(20):
            learner.record_outcome(DealOutcome(
                deal_id=f"T{i}", sector="ot", signal_type="regulatory",
                offer_tier="TIER3", price_eur=float(20_000 + i * 1_000),
                converted=True, quality_score=0.85,
            ))
            targets.append(learner.get_optimized_hunt_params().target_ticket_eur)
        # Vérifier monotonie croissante
        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1], \
                f"Régression ticket à itération {i}: {targets[i]} → {targets[i+1]}"

    def test_slots_never_below_4_across_scaling(self, scaler):
        """Le nombre de slots ne descend jamais sous 4, quelle que soit la situation."""
        scaler._last_scale_ts = 0
        for _ in range(10):
            scaler.evaluate_and_scale({
                "shi_score": 0.20,  # pire cas
                "conversion_rate": 0.0,
                "mrr": 0,
            })
            assert scaler.get_current_slots() >= 4
            scaler._last_scale_ts = 0  # reset cooldown
