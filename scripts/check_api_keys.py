#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Vérification des clés API
Script de diagnostic pour valider que toutes les clés sont chargées
Usage:
    python scripts/check_api_keys.py           # Rapport standard
    python scripts/check_api_keys.py -d        # Rapport diagnostic complet
    python scripts/check_api_keys.py -v        # Validation stricte (exit 1 si erreur)
    python scripts/check_api_keys.py --fix     # Tenter de réparer les clés manquantes
"""

import sys
import os
from pathlib import Path

# Ajouter la racine au path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from SECRETS.secrets_loader import (
    load_all_secrets,
    validate_all_keys,
    print_diagnostic_report,
    get_status,
)


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🔐 NAYA V19 — Vérification des clés API"
    )
    parser.add_argument(
        "-d", "--diagnostic",
        action="store_true",
        help="Afficher rapport diagnostic complet"
    )
    parser.add_argument(
        "-v", "--validate",
        action="store_true",
        help="Validation stricte (exit 1 si clés manquantes)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Tenter de réparer les clés manquantes"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format"
    )

    args = parser.parse_args()

    # Mode diagnostic complet
    if args.diagnostic:
        print_diagnostic_report()
        return 0

    # Mode validation stricte
    if args.validate:
        try:
            report = validate_all_keys(strict=True)
            print(f"✅ VALIDATION RÉUSSIE: {report['loaded_critical']}/{report['total_critical']} clés critiques")
            return 0
        except RuntimeError as e:
            print(str(e))
            return 1

    # Mode fix
    if args.fix:
        print("🔧 MODE RÉPARATION (expérimental)")
        print("Tentative de chargement depuis tous les fichiers disponibles...")
        result = load_all_secrets(verbose=True)
        print(f"\n✅ {result['loaded']} variables chargées")
        print(f"   {result['real_keys']}/{result.get('critical_keys_total', 0)} clés critiques")
        return 0

    # Mode JSON
    if args.json:
        import json
        report = validate_all_keys(strict=False)
        print(json.dumps(report, indent=2))
        return 0

    # Mode standard
    print("="*70)
    print("🔐 NAYA V19 — Vérification des Clés API")
    print("="*70)

    result = load_all_secrets(verbose=True)
    st = get_status()

    print(f"\n📊 RÉSUMÉ:")
    print(f"   • Variables chargées: {result['loaded']}")
    print(f"   • Clés critiques: {result['real_keys']}/{result.get('critical_keys_total', 0)}")
    print(f"   • LLM actif: {st['active_llm'].upper()}")
    print(f"   • Score global: {st['score']}")

    # Clés manquantes
    missing = result.get('missing_keys', [])
    if missing:
        print(f"\n⚠️  CLÉS MANQUANTES ({len(missing)}):")
        for key in missing[:10]:
            print(f"    ❌ {key}")
        if len(missing) > 10:
            print(f"    ... et {len(missing) - 10} autres")
        print(f"\n💡 Utiliser -d pour diagnostic complet")
        print(f"💡 Utiliser --fix pour tenter réparation")
        return 1

    print("\n✅ Toutes les clés critiques sont chargées")
    return 0


if __name__ == "__main__":
    sys.exit(main())
