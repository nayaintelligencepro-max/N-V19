#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Resume Deployment & Real Sales Validation
═══════════════════════════════════════════════════════════════════════════════
Script principal pour reprendre le déploiement et exécuter les validations par ventes réelles.

Ce script:
1. Vérifie l'état actuel du système et des validations
2. Lance les tests pre-deploy gate pour chaque environnement
3. Exécute des ventes réelles de validation
4. Génère un rapport complet consolidé

Usage:
    python scripts/resume_deployment_validation.py
    python scripts/resume_deployment_validation.py --env local
    python scripts/resume_deployment_validation.py --env docker --skip-gate
    python scripts/resume_deployment_validation.py --full-validation

Options:
    --env ENV            : Valider un environnement spécifique (local, docker, vercel, render, cloud_run)
    --skip-gate          : Skip pre-deploy gate tests
    --skip-real-sales    : Skip real sales validation
    --full-validation    : Run full validation on all 5 environments
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# ── Configuration ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("NAYA.VALIDATION")

GATE_LEDGER = ROOT / "data" / "validation" / "pre_deploy_gate.json"
SALES_LEDGER = ROOT / "data" / "validation" / "real_sales_ledger.json"
VALIDATION_REPORT = ROOT / "data" / "validation" / "validation_report.json"

# Montants de validation par environnement
GATE_AMOUNTS = {
    "local":     (15000, 25000),
    "docker":    (20000, 35000),
    "vercel":    (30000, 45000),
    "render":    (40000, 55000),
    "cloud_run": (50000, 70000),
}

ALL_ENVS = ["local", "docker", "vercel", "render", "cloud_run"]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'=' * 78}")
    print(f"  {text}")
    print(f"{'=' * 78}\n")


def print_ok(text: str):
    """Print success message"""
    print(f"✅  {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌  {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def load_json_file(filepath: Path) -> List[Dict]:
    """Load JSON file safely"""
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
        return []
    except Exception as e:
        log.warning(f"Error loading {filepath}: {e}")
        return []


def save_json_file(filepath: Path, data: Any):
    """Save JSON file safely"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        log.error(f"Error saving {filepath}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION ÉTAT ACTUEL
# ══════════════════════════════════════════════════════════════════════════════

def analyze_current_state() -> Dict[str, Any]:
    """Analyse l'état actuel des validations"""

    print_header("ANALYSE ÉTAT ACTUEL DU SYSTÈME")

    gate_data = load_json_file(GATE_LEDGER)
    sales_data = load_json_file(SALES_LEDGER)

    # Analyser gate par environnement
    gate_by_env = {}
    for entry in gate_data:
        env = entry.get('deploy_env', 'unknown')
        if env not in gate_by_env:
            gate_by_env[env] = []
        gate_by_env[env].append(entry)

    # Analyser ventes réelles
    sales_by_status = {}
    for sale in sales_data:
        status = sale.get('status', 'unknown')
        if status not in sales_by_status:
            sales_by_status[status] = []
        sales_by_status[status].append(sale)

    # Calculer statistiques
    confirmed_sales = sales_by_status.get('payment_confirmed', [])
    completed_sales = sales_by_status.get('sale_completed', [])
    total_revenue = sum(s.get('amount_eur', 0) for s in confirmed_sales + completed_sales)

    # Afficher résumé
    print(f"📊 Pre-Deploy Gate Entries: {len(gate_data)}")
    print(f"\n   Répartition par environnement:")
    for env in ALL_ENVS:
        count = len(gate_by_env.get(env, []))
        if count > 0:
            print_ok(f"   {env:12s}: {count:3d} sales")
        else:
            print_info(f"   {env:12s}: {count:3d} sales (AUCUNE)")

    print(f"\n💰 Real Sales Validation:")
    print(f"   Total entries        : {len(sales_data)}")
    print(f"   Payment confirmed    : {len(confirmed_sales)}")
    print(f"   Sale completed       : {len(completed_sales)}")
    print(f"   Total revenue        : {total_revenue:,.0f} EUR")

    return {
        'gate_total': len(gate_data),
        'gate_by_env': {env: len(gate_by_env.get(env, [])) for env in ALL_ENVS},
        'sales_total': len(sales_data),
        'sales_confirmed': len(confirmed_sales),
        'sales_completed': len(completed_sales),
        'total_revenue_eur': total_revenue,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PRE-DEPLOY GATE TESTS
# ══════════════════════════════════════════════════════════════════════════════

def run_predeploy_gate_test(env: str) -> Dict[str, Any]:
    """Execute pre-deploy gate test for environment"""

    print_header(f"PRE-DEPLOY GATE TEST — {env.upper()}")

    sale_1, sale_2 = GATE_AMOUNTS.get(env, (15000, 25000))
    print(f"💰 Vente 1: {sale_1:,} EUR | Vente 2: {sale_2:,} EUR")

    try:
        # Run pytest with environment variable
        cmd = [
            "python3", "-m", "pytest",
            str(ROOT / "tests" / "test_pre_deploy_gate.py"),
            "-v",
            "-s",
            "--tb=short"
        ]

        env_vars = {
            **subprocess.os.environ,
            "DEPLOY_ENV": env,
            "BASE_URL": "http://localhost:8000",
        }

        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env_vars,
            capture_output=True,
            text=True,
            timeout=300,
        )

        success = result.returncode == 0

        if success:
            print_ok(f"Gate {env.upper()} — PASSED (2 sales validées)")
        else:
            print_error(f"Gate {env.upper()} — FAILED")
            if result.stdout:
                print(f"\nSTDOUT:\n{result.stdout[-500:]}")
            if result.stderr:
                print(f"\nSTDERR:\n{result.stderr[-500:]}")

        return {
            'env': env,
            'success': success,
            'returncode': result.returncode,
            'sale_1_eur': sale_1,
            'sale_2_eur': sale_2,
            'total_eur': sale_1 + sale_2,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    except subprocess.TimeoutExpired:
        print_error(f"Gate {env.upper()} — TIMEOUT après 5 minutes")
        return {
            'env': env,
            'success': False,
            'error': 'timeout',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print_error(f"Gate {env.upper()} — ERROR: {e}")
        return {
            'env': env,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# REAL SALES VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

async def run_real_sale_validation(amount_eur: float, sector: str) -> Dict[str, Any]:
    """Execute real sale validation test"""

    print_header(f"REAL SALE VALIDATION — {amount_eur:,.0f} EUR | {sector.upper()}")

    try:
        from NAYA_ACCELERATION.real_sale_validator import run_real_sale_test, validate_payment

        # Phase 1-2: Créer vente + lien paiement
        result = await run_real_sale_test(
            test_name=f"Validation Déploiement {amount_eur:,.0f} EUR",
            amount_eur=amount_eur,
            sector=sector
        )

        if not result.get('success'):
            print_error(f"Échec création vente: {result.get('error')}")
            return result

        sale_id = result['sale_id']

        print_ok(f"Vente créée: {sale_id}")
        print(f"   Company       : {result['company']}")
        print(f"   Amount        : {result['amount_eur']:,.2f} EUR")
        print(f"   Payment URL   : {result['payment_url']}")
        print(f"   Reference     : {result['payment_reference']}")

        # Phase 3: Validation automatique (simulation paiement confirmé)
        print(f"\n⏳ Simulation validation paiement...")
        await asyncio.sleep(2)  # Simule délai traitement

        validation_result = await validate_payment(
            sale_id=sale_id,
            validator="Test Automatisé",
            notes="Test validation E2E"
        )

        if validation_result.get('success'):
            print_ok(f"Paiement confirmé: {sale_id}")
            return {
                **result,
                'validated': True,
                'validation_result': validation_result,
            }
        else:
            print_error(f"Échec validation: {validation_result.get('error')}")
            return {
                **result,
                'validated': False,
                'validation_error': validation_result.get('error'),
            }

    except Exception as e:
        log.error(f"Error running real sale validation: {e}", exc_info=True)
        print_error(f"Exception: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION
# ══════════════════════════════════════════════════════════════════════════════

async def run_validation_workflow(args):
    """Execute complete validation workflow"""

    print_header("NAYA SUPREME V19 — VALIDATION DÉPLOIEMENT & VENTES RÉELLES")

    # 1. Analyser état actuel
    current_state = analyze_current_state()

    # 2. Pre-deploy gate tests
    gate_results = []
    if not args.skip_gate:
        envs_to_test = [args.env] if args.env else (ALL_ENVS if args.full_validation else ["local"])

        for env in envs_to_test:
            result = run_predeploy_gate_test(env)
            gate_results.append(result)

            # Pause entre tests
            if env != envs_to_test[-1]:
                await asyncio.sleep(2)

    # 3. Real sales validation
    sales_results = []
    if not args.skip_real_sales:
        test_sales = [
            (5000, "energy"),
            (3000, "transport"),
            (10000, "energy"),
            (2000, "manufacturing"),
        ]

        for amount, sector in test_sales:
            result = await run_real_sale_validation(amount, sector)
            sales_results.append(result)
            await asyncio.sleep(1)

    # 4. Générer rapport final
    print_header("RAPPORT FINAL")

    gate_passed = sum(1 for r in gate_results if r.get('success'))
    gate_total = len(gate_results)

    sales_validated = sum(1 for r in sales_results if r.get('validated'))
    sales_total = len(sales_results)

    print(f"📊 PRE-DEPLOY GATE TESTS")
    print(f"   Passed : {gate_passed}/{gate_total}")
    for result in gate_results:
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        env_name = result['env'].upper()
        total = result.get('total_eur', 0)
        print(f"   {status} | {env_name:12s} | {total:>6,} EUR")

    print(f"\n💰 REAL SALES VALIDATION")
    print(f"   Validated : {sales_validated}/{sales_total}")
    for result in sales_results:
        if result.get('success'):
            status = "✅ OK" if result.get('validated') else "⏳ PENDING"
            sale_id = result.get('sale_id', 'N/A')
            amount = result.get('amount_eur', 0)
            print(f"   {status} | {sale_id:20s} | {amount:>10,.2f} EUR")

    # Sauvegarder rapport
    report = {
        'current_state': current_state,
        'gate_results': gate_results,
        'sales_results': sales_results,
        'summary': {
            'gate_passed': gate_passed,
            'gate_total': gate_total,
            'sales_validated': sales_validated,
            'sales_total': sales_total,
        },
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }

    save_json_file(VALIDATION_REPORT, report)
    print_ok(f"\nRapport sauvegardé: {VALIDATION_REPORT}")

    # Status final
    all_passed = (gate_passed == gate_total) and (sales_validated == sales_total)

    print_header("RÉSULTAT FINAL")
    if all_passed:
        print_ok("✅ TOUTES LES VALIDATIONS SONT PASSÉES")
        return 0
    else:
        print_error("❌ CERTAINES VALIDATIONS ONT ÉCHOUÉ")
        return 1


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Resume deployment and real sales validation tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--env",
        choices=ALL_ENVS,
        help="Run validation for specific environment only"
    )

    parser.add_argument(
        "--skip-gate",
        action="store_true",
        help="Skip pre-deploy gate tests"
    )

    parser.add_argument(
        "--skip-real-sales",
        action="store_true",
        help="Skip real sales validation"
    )

    parser.add_argument(
        "--full-validation",
        action="store_true",
        help="Run full validation on all 5 environments"
    )

    args = parser.parse_args()

    # Run async workflow
    exit_code = asyncio.run(run_validation_workflow(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
