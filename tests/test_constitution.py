"""Tests for NAYA Constitution - invariants and governance rules."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_invariants_premium_floor():
    from CONSTITUTION.invariants import SystemInvariants
    assert SystemInvariants.get("PREMIUM_FLOOR") == 1000


def test_invariants_non_vendable():
    from CONSTITUTION.invariants import SystemInvariants
    assert SystemInvariants.get("NON_VENDABLE") is True


def test_invariants_transmissible():
    from CONSTITUTION.invariants import SystemInvariants
    assert SystemInvariants.get("TRANSMISSIBLE") is True


def test_invariants_verify_price_above_floor():
    from CONSTITUTION.invariants import SystemInvariants
    assert SystemInvariants.verify_price(5000) is True
    assert SystemInvariants.verify_price(1000) is True


def test_invariants_verify_price_below_floor():
    from CONSTITUTION.invariants import SystemInvariants
    assert SystemInvariants.verify_price(999) is False
    assert SystemInvariants.verify_price(0) is False


def test_invariants_check_all():
    from CONSTITUTION.invariants import SystemInvariants
    result = SystemInvariants.check_all()
    assert result["all_enforced"] is True
    assert result["total"] >= 10


def test_invariants_targets():
    from CONSTITUTION.invariants import SystemInvariants
    targets = SystemInvariants.get_targets()
    assert targets["weekly_eur"] == 60000
    assert targets["monthly_eur"] == 300000


def test_governance_rules_compliant_price():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    result = gov.check_compliance({"price": 5000})
    assert result["compliant"] is True
    assert result["violations"] == []


def test_governance_rules_below_premium():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    result = gov.check_compliance({"price": 500})
    assert result["compliant"] is False
    assert len(result["violations"]) > 0
    assert result["violations"][0]["rule"] == "GOV_001"


def test_governance_rules_stealth_violation():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    result = gov.check_compliance({"exposes_location": True})
    assert result["compliant"] is False


def test_governance_rules_zero_waste_violation():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    result = gov.check_compliance({"is_one_shot": True})
    assert result["compliant"] is False


def test_governance_core_rules_count():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    rules = gov.get_all_rules()
    assert len(rules) >= 12


def test_governance_stats():
    from CONSTITUTION.governance_rules import GovernanceRules
    gov = GovernanceRules()
    stats = gov.get_stats()
    assert stats["total_rules"] >= 12
    assert stats["enforced"] >= 12


def test_leadership_rules_import():
    from CONSTITUTION.leadership_rules import LeadershipRules
    lr = LeadershipRules()
    assert hasattr(lr, "validate")


def test_evolution_constraints_import():
    from CONSTITUTION.evolution_constraints import EvolutionConstraints
    ec = EvolutionConstraints()
    assert hasattr(ec, "validate_evolution")
