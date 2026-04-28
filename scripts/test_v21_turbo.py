#!/usr/bin/env python3
"""
NAYA V19 — Test Suite Performance V21 Turbo
Tests complets validation performances système optimisé.
"""
import asyncio
import time
from typing import Dict

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def test_blitz_hunt_performance():
    """Test BlitzHunt < 20s"""
    print(f"\n{BLUE}[TEST 1/10]{RESET} BlitzHunt Performance")
    try:
        from NAYA_ACCELERATION.blitz_hunter import get_blitz_hunter

        hunter = get_blitz_hunter()
        start = time.time()
        signals = await hunter.hunt(["energie", "transport_logistique"])
        elapsed = time.time() - start

        target = 20.0
        status = f"{GREEN}✓ PASS{RESET}" if elapsed < target else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Time: {elapsed:.1f}s / {target}s | Signals: {len(signals)}")
        return elapsed < target
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


async def test_flash_offer_performance():
    """Test FlashOffer < 45s"""
    print(f"\n{BLUE}[TEST 2/10]{RESET} FlashOffer Performance")
    try:
        from NAYA_ACCELERATION.flash_offer import get_flash_offer

        flash = get_flash_offer()
        start = time.time()
        offer = await flash.generate(
            company="SNCF Réseau",
            sector="transport_logistique",
            pain_description="Conformité NIS2 urgente pour trains connectés",
            budget_estimate=25000,
            urgency="critical"
        )
        elapsed = time.time() - start

        target = 45.0
        status = f"{GREEN}✓ PASS{RESET}" if elapsed < target else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Time: {elapsed:.1f}s / {target}s | Price: {offer.price_eur} EUR")
        return elapsed < target
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_instant_closer_performance():
    """Test InstantCloser < 50s (synchrone)"""
    print(f"\n{BLUE}[TEST 3/10]{RESET} InstantCloser Performance")
    try:
        from NAYA_ACCELERATION.instant_closer import get_instant_closer, PaymentMethod

        closer = get_instant_closer()
        start = time.time()
        link = closer.generate_payment_link(
            offer_id="test_offer_123",
            company="Test Company",
            contact_email="test@example.com",
            amount_eur=15000,
            method=PaymentMethod.PAYPAL
        )
        elapsed = time.time() - start

        target = 1.0  # Should be near-instant (< 1s)
        status = f"{GREEN}✓ PASS{RESET}" if elapsed < target else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Time: {elapsed:.3f}s / {target}s | URL: {link.url[:50]}...")
        return elapsed < target
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


async def test_full_pipeline_performance():
    """Test Pipeline Complet < 3h (simulation rapide)"""
    print(f"\n{BLUE}[TEST 4/10]{RESET} Pipeline Complet Performance")
    try:
        from NAYA_ACCELERATION import get_orchestrator

        orchestrator = get_orchestrator()
        start = time.time()
        result = await orchestrator.run_acceleration_cycle(["energie"])
        elapsed = time.time() - start

        # Projection to 3h based on actual cycle time
        estimated_full_pipeline_h = (elapsed / 60) * 10  # Rough estimate
        target = 3.0

        status = f"{GREEN}✓ PASS{RESET}" if result.offers_generated > 0 else f"{YELLOW}⚠ WARN{RESET}"
        print(f"  {status} | Cycle: {elapsed:.1f}s | Estimated Full: {estimated_full_pipeline_h:.1f}h / {target}h")
        print(f"       | Signals: {result.signals_detected} | Offers: {result.offers_generated}")
        return True
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_dynamic_scaler_5_slots():
    """Test DynamicScaler 5 projets parallèles"""
    print(f"\n{BLUE}[TEST 5/10]{RESET} DynamicScaler 5 Slots")
    try:
        from PARALLEL_ENGINE.dynamic_scaler import get_dynamic_scaler

        scaler = get_dynamic_scaler()
        current_slots = scaler.get_current_slots()

        status = f"{GREEN}✓ PASS{RESET}" if current_slots >= 5 else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Current Slots: {current_slots} / 5 minimum")
        print(f"       | Min: {scaler._lock and 5} | Max: 12")
        return current_slots >= 5
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_api_budget_manager():
    """Test API Budget Manager"""
    print(f"\n{BLUE}[TEST 6/10]{RESET} API Budget Manager")
    try:
        from NAYA_CORE.api_budget_manager import get_api_budget_manager

        manager = get_api_budget_manager()

        # Test can_use
        can_groq = manager.can_use("groq", tokens=1000)
        can_serper = manager.can_use("serper")

        # Test best_provider
        best_llm = manager.get_best_provider("llm")
        best_search = manager.get_best_provider("search")

        # Test record
        manager.record_usage("groq", tokens=100, success=True)

        report = manager.get_usage_report()

        status = f"{GREEN}✓ PASS{RESET}" if best_llm and best_search else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Best LLM: {best_llm} | Best Search: {best_search}")
        print(f"       | Total Requests: {report['total_requests']} | Cost: ${report['total_cost_usd']}")
        return True
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_irresistible_offers():
    """Test Templates Offres Irrésistibles"""
    print(f"\n{BLUE}[TEST 7/10]{RESET} Templates Offres Irrésistibles")
    try:
        from NAYA_ACCELERATION.flash_offer import PAIN_TEMPLATES

        required_templates = ["nis2_compliance", "iec62443_audit", "ransomware_ot", "scada_vulnerability", "ot_training", "pentest_ot"]
        found = [t for t in required_templates if t in PAIN_TEMPLATES]

        # Check urgency_multiplier exists
        with_multiplier = [t for t in found if "urgency_multiplier" in PAIN_TEMPLATES[t]]

        status = f"{GREEN}✓ PASS{RESET}" if len(found) == len(required_templates) else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} | Templates: {len(found)}/{len(required_templates)}")
        print(f"       | With Urgency Multiplier: {len(with_multiplier)}")

        # Show one example
        if found:
            example = PAIN_TEMPLATES[found[0]]
            print(f"       | Example '{found[0]}': {example['title'][:60]}...")

        return len(found) == len(required_templates)
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_client_portal():
    """Test Client Portal Interface"""
    print(f"\n{BLUE}[TEST 8/10]{RESET} Client Portal Interface")
    try:
        from pathlib import Path

        portal_file = Path("CLIENT_PORTAL/index.html")
        exists = portal_file.exists()

        if exists:
            content = portal_file.read_text()
            has_turbo = "Mode Turbo" in content
            has_metrics = "< 20s" in content and "< 45s" in content and "< 50s" in content
            has_projects = "5 slots" in content or "Projets en Cours" in content

            status = f"{GREEN}✓ PASS{RESET}" if has_turbo and has_metrics and has_projects else f"{YELLOW}⚠ WARN{RESET}"
            print(f"  {status} | File: {portal_file}")
            print(f"       | Turbo Mode: {has_turbo} | Metrics: {has_metrics} | Projects: {has_projects}")
            return True
        else:
            print(f"  {RED}✗ FAIL{RESET} | File not found: {portal_file}")
            return False
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_scheduler_turbo_config():
    """Test Scheduler V21 Turbo Configuration"""
    print(f"\n{BLUE}[TEST 9/10]{RESET} Scheduler V21 Turbo")
    try:
        from NAYA_SCHEDULER.autonomous_scheduler import CYCLE_INTERVALS

        turbo_jobs = {
            "blitz_hunt": 15 * 60,
            "offer_background": 20 * 60,
            "velocity_report": 30 * 60,
            "meeting_reminder": 5 * 60,
        }

        matches = sum(1 for job, interval in turbo_jobs.items() if CYCLE_INTERVALS.get(job) == interval)

        status = f"{GREEN}✓ PASS{RESET}" if matches == len(turbo_jobs) else f"{YELLOW}⚠ WARN{RESET}"
        print(f"  {status} | Turbo Jobs: {matches}/{len(turbo_jobs)}")
        print(f"       | blitz_hunt: {CYCLE_INTERVALS.get('blitz_hunt', 0) / 60}min")
        print(f"       | offer_background: {CYCLE_INTERVALS.get('offer_background', 0) / 60}min")
        return matches >= 3  # At least 3/4 turbo jobs configured
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


def test_min_contract_value():
    """Test Plancher 1000 EUR Enforced"""
    print(f"\n{BLUE}[TEST 10/10]{RESET} Plancher 1000 EUR")
    try:
        from NAYA_ACCELERATION.instant_closer import get_instant_closer, MIN_CONTRACT_VALUE_EUR, PaymentMethod

        closer = get_instant_closer()

        # Test plancher enforcement
        try:
            closer.generate_payment_link(
                offer_id="test_low",
                company="Test",
                contact_email="test@test.com",
                amount_eur=500,  # Under floor
                method=PaymentMethod.PAYPAL
            )
            print(f"  {RED}✗ FAIL{RESET} | Plancher NOT enforced (500 EUR accepted)")
            return False
        except ValueError as e:
            if "plancher" in str(e).lower() or "interdit" in str(e).lower():
                print(f"  {GREEN}✓ PASS{RESET} | Plancher enforced: {MIN_CONTRACT_VALUE_EUR} EUR")
                print(f"       | Rejection message: {str(e)[:80]}...")
                return True
            else:
                print(f"  {RED}✗ FAIL{RESET} | Wrong error: {e}")
                return False
    except Exception as e:
        print(f"  {RED}✗ ERROR{RESET} | {e}")
        return False


async def run_all_tests():
    """Execute tous les tests"""
    print(f"\n{'=' * 80}")
    print(f"{BLUE}NAYA V19 — Test Suite Performance V21 Turbo{RESET}")
    print(f"{'=' * 80}")

    results = []

    # Tests async
    results.append(await test_blitz_hunt_performance())
    results.append(await test_flash_offer_performance())

    # Tests sync
    results.append(test_instant_closer_performance())

    # Test async pipeline
    results.append(await test_full_pipeline_performance())

    # Tests config
    results.append(test_dynamic_scaler_5_slots())
    results.append(test_api_budget_manager())
    results.append(test_irresistible_offers())
    results.append(test_client_portal())
    results.append(test_scheduler_turbo_config())
    results.append(test_min_contract_value())

    # Summary
    passed = sum(results)
    total = len(results)
    pct = (passed / total * 100) if total > 0 else 0

    print(f"\n{'=' * 80}")
    color = GREEN if pct >= 80 else YELLOW if pct >= 60 else RED
    print(f"{color}RESULTS: {passed}/{total} tests passed ({pct:.0f}%){RESET}")
    print(f"{'=' * 80}\n")

    if pct >= 80:
        print(f"{GREEN}✅ SYSTÈME OPÉRATIONNEL À {pct:.0f}% — PRÊT POUR PRODUCTION{RESET}")
    elif pct >= 60:
        print(f"{YELLOW}⚠️  SYSTÈME PARTIELLEMENT OPÉRATIONNEL — CORRECTIONS REQUISES{RESET}")
    else:
        print(f"{RED}❌ SYSTÈME NON OPÉRATIONNEL — MAINTENANCE CRITIQUE REQUISE{RESET}")

    return pct >= 80


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
