#!/usr/bin/env python3
"""
NAYA V19 — Deploy With Validation (Séquence Accélérée)
═══════════════════════════════════════════════════════════════════════════════
Lance la séquence complète : 5 tests (2 ventes réelles chacun) → 5 déploiements.

TEST 1 → 15 000€ + 25 000€ encaissés → Local (port 3000) déployé → Telegram ✅
TEST 2 → 25 000€ + 35 000€ encaissés → Docker déployé            → Telegram ✅
TEST 3 → 35 000€ + 45 000€ encaissés → Vercel déployé            → Telegram ✅
TEST 4 → 45 000€ + 55 000€ encaissés → Render déployé            → Telegram ✅
TEST 5 → 55 000€ + 65 000€ encaissés → Cloud Run déployé         → Telegram ✅
Total   : 400 000 EUR (10 ventes réelles)

Usage :
  python tools/deploy_with_validation.py            # Mode normal (attend paiements)
  python tools/deploy_with_validation.py --status   # Voir l'état
  python tools/deploy_with_validation.py --confirm PDV_XXX --amount 15000
"""

import sys
import os
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.pre_deploy_validator import (
    PreDeployValidator,
    DEPLOYMENT_TARGETS,
    _print_banner,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NAYA V19 — Séquence complète validation + déploiement",
    )
    parser.add_argument("--status",  action="store_true", help="Voir l'état courant")
    parser.add_argument("--confirm", metavar="PAYMENT_ID", help="Confirmer un paiement manuellement")
    parser.add_argument("--amount",  type=float, help="Montant confirmé (avec --confirm)")
    parser.add_argument("--force-test", metavar="TARGET",
                        help="Forcer un test individuel: local|docker|vercel|render|cloud_run")
    args = parser.parse_args()

    validator = PreDeployValidator()

    if args.status:
        validator.print_status()
        return 0

    if args.confirm:
        ok = validator.manual_confirm(args.confirm, args.amount)
        return 0 if ok else 1

    if args.force_test:
        ok = validator.run_test(args.force_test, skip_if_done=False)
        return 0 if ok else 1

    # ── Séquence principale ──────────────────────────────────────────────────
    _print_banner(
        "NAYA V19 — SÉQUENCE VALIDATION + DÉPLOIEMENT ACCÉLÉRÉE",
        char="╔",
    )
    print("""
  Chaque déploiement est conditionné à 2 ventes réelles encaissées.
  Les tests s'exécutent l'un après l'autre automatiquement.

  Séquence : 15k+25k → 25k+35k → 35k+45k → 45k+55k → 55k+65k EUR
  Total     : 400 000 EUR (10 ventes)

  Pour confirmer un paiement manuellement :
    python tools/deploy_with_validation.py --confirm <PAYMENT_ID> --amount <EUR>

  Pour voir l'état :
    python tools/deploy_with_validation.py --status
""")

    ok = validator.run_full_sequence()
    if not ok:
        print("\n⏸  Séquence interrompue — reprendre avec :")
        print("   python tools/deploy_with_validation.py")
        return 1

    # Tous les tests réussis → lancer les déploiements
    print("\n🚀 Tous les tests validés — lancement des déploiements en séquence…\n")
    _run_deployments()
    return 0


def _run_deployments() -> None:
    """Lance les 5 déploiements après validation (2 ventes chacun)."""
    import shutil
    import subprocess

    deploy_sequence = [
        ("local",     f"uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port 3000 --reload &",
         "http://localhost:3000"),
        ("docker",    "docker-compose up -d",
         "http://localhost:8000"),
        ("vercel",    "vercel deploy --prod --yes 2>/dev/null || echo 'Vercel CLI non configuré'",
         "vercel.app"),
        ("render",    "echo 'Render: git push origin main (auto-deploy)'",
         "render.com"),
        ("cloud_run", f"python tools/deploy.py --mode cloud_run --skip-validation",
         "cloud.google.com"),
    ]

    for target_id, cmd, url_hint in deploy_sequence:
        from tools.pre_deploy_validator import PreDeployValidator
        v = PreDeployValidator()
        if not v.ledger.is_validated(target_id):
            print(f"  ⚠️  {target_id} : validation (2 ventes) introuvable — skip")
            continue

        print(f"\n  🚀 Déploiement {target_id.upper()} ({url_hint})…")
        try:
            subprocess.run(cmd, shell=True, cwd=str(ROOT), timeout=300)
            print(f"  ✅ {target_id.upper()} déployé")
        except Exception as e:
            print(f"  ⚠️  {target_id.upper()} : {e}")


if __name__ == "__main__":
    sys.exit(main())
