#!/usr/bin/env python3
"""
NAYA V19.2 — Script Test Vente Réel
═══════════════════════════════════════════════════════════════════════════════
Lance un test de vente réel complet automatisé.

Usage:
    python scripts/run_real_sale_test.py
    python scripts/run_real_sale_test.py --amount 5000 --sector transport
    python scripts/run_real_sale_test.py --amount 15000 --sector energy --test-name "Test Pre-Deploy"

Workflow:
1. Détecte opportunité (V19.2 quantum hunt ou mock)
2. Génère offre personnalisée
3. Crée lien paiement (PayPal/Deblock)
4. Envoie notifications Telegram
5. Attend validation manuelle paiement

Une fois test lancé, utiliser:
    python scripts/validate_payment.py SALE_ID
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


async def main():
    parser = argparse.ArgumentParser(description="Lancer test vente réel automatisé")
    parser.add_argument("--amount", type=float, default=1000.0, help="Montant cible en EUR (défaut: 1000)")
    parser.add_argument("--sector", default="energy", choices=["energy", "transport", "manufacturing"],
                       help="Secteur à cibler")
    parser.add_argument("--test-name", default="Test Vente Réel Automatisé", help="Nom du test")

    args = parser.parse_args()

    from NAYA_ACCELERATION.real_sale_validator import run_real_sale_test

    print(f"\n{'='*70}")
    print(f"NAYA V19.2 — TEST VENTE RÉEL AUTOMATISÉ")
    print(f"{'='*70}")
    print(f"\n📋 Test         : {args.test_name}")
    print(f"💰 Montant cible: {args.amount:,.0f} EUR")
    print(f"🎨 Secteur      : {args.sector.upper()}")
    print(f"\n⏳ Lancement test...\n")

    result = await run_real_sale_test(
        test_name=args.test_name,
        amount_eur=args.amount,
        sector=args.sector
    )

    if result['success']:
        print(f"\n{'='*70}")
        print(f"✅ TEST CRÉÉ AVEC SUCCÈS")
        print(f"{'='*70}")
        print(f"\n🆔 Sale ID       : {result['sale_id']}")
        print(f"🏢 Client        : {result['company']}")
        print(f"💰 Montant       : {result['amount_eur']:,.2f} EUR")
        print(f"📌 Référence     : {result['payment_reference']}")
        print(f"📊 Statut        : {result['status']}")

        print(f"\n{'='*70}")
        print(f"🔗 LIEN PAIEMENT")
        print(f"{'='*70}")
        print(f"\n{result['payment_url']}")

        print(f"\n{'='*70}")
        print(f"📝 PROCHAINES ÉTAPES")
        print(f"{'='*70}")
        print(f"\n{result['instructions']}")

        print(f"\n📱 Notifications Telegram envoyées")
        print(f"💾 Enregistré dans: data/validation/real_sales_ledger.json")

        print(f"\n{'='*70}")
        print(f"⏳ EN ATTENTE VALIDATION PAIEMENT")
        print(f"{'='*70}")
        print(f"\nPour valider après paiement:")
        print(f"  python scripts/validate_payment.py {result['sale_id']}")

    else:
        print(f"\n{'='*70}")
        print(f"❌ ERREUR")
        print(f"{'='*70}")
        print(f"\n{result.get('error', 'Erreur inconnue')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
