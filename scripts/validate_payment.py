#!/usr/bin/env python3
"""
NAYA V19.2 — Script Validation Paiement Manuel
═══════════════════════════════════════════════════════════════════════════════
Script pour valider manuellement un paiement après réception réelle.

Usage:
    python scripts/validate_payment.py SALE_ID
    python scripts/validate_payment.py SALE_ID --validator="Jean Dupont" --notes="Paiement vérifié PayPal"

Workflow:
1. Lire sale_id depuis ledger
2. Demander confirmation utilisateur
3. Marquer paiement comme confirmé
4. Envoyer notification Telegram
5. Mettre à jour ledger immuable
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


async def main():
    parser = argparse.ArgumentParser(description="Valider paiement vente réelle")
    parser.add_argument("sale_id", help="ID de la vente à valider (ex: REAL_SALE_ABC12345)")
    parser.add_argument("--validator", default="manual", help="Nom du validateur")
    parser.add_argument("--notes", default="", help="Notes de validation")
    parser.add_argument("--auto", action="store_true", help="Mode automatique sans confirmation")

    args = parser.parse_args()

    from NAYA_ACCELERATION.real_sale_validator import get_real_sale_validator

    validator = get_real_sale_validator()

    # Trouver la vente
    sale = next((s for s in validator.sales if s.sale_id == args.sale_id), None)

    if not sale:
        print(f"❌ Vente {args.sale_id} non trouvée")
        print(f"\nVentes disponibles ({len(validator.sales)}):")
        for s in validator.sales[-10:]:  # Dernières 10
            print(f"  - {s.sale_id} | {s.company} | {s.amount_eur:,.0f} EUR | {s.status.value}")
        sys.exit(1)

    # Afficher détails
    print(f"\n{'='*70}")
    print(f"VALIDATION PAIEMENT — VENTE RÉELLE")
    print(f"{'='*70}")
    print(f"\n🆔 Sale ID       : {sale.sale_id}")
    print(f"🏢 Client        : {sale.company}")
    print(f"👤 Contact       : {sale.contact_name}")
    print(f"💰 Montant       : {sale.amount_eur:,.2f} EUR")
    print(f"💳 Méthode       : {sale.payment_method.value.upper()}")
    print(f"🔗 Lien paiement : {sale.payment_url}")
    print(f"📌 Référence     : {sale.payment_reference}")
    print(f"📋 Statut actuel : {sale.status.value}")

    if sale.status.value == "payment_confirmed":
        print(f"\n⚠️  Paiement déjà confirmé !")
        print(f"   Confirmé le: {sale.payment_confirmed_at}")
        print(f"   Par: {sale.validated_by}")
        sys.exit(0)

    # Confirmation
    if not args.auto:
        print(f"\n{'='*70}")
        confirm = input("\n✅ Confirmer que le paiement a été REÇU ? (oui/non): ").strip().lower()
        if confirm not in ('oui', 'yes', 'y', 'o'):
            print("❌ Validation annulée")
            sys.exit(0)

    # Valider
    print(f"\n⏳ Validation en cours...")
    result = await validator.validate_payment_manual(
        sale_id=args.sale_id,
        validator_name=args.validator,
        notes=args.notes
    )

    if result['success']:
        print(f"\n{'='*70}")
        print(f"✅ PAIEMENT CONFIRMÉ")
        print(f"{'='*70}")
        print(f"\n🆔 Sale ID   : {result['sale_id']}")
        print(f"🏢 Client    : {result['company']}")
        print(f"💰 Montant   : {result['amount_eur']:,.2f} EUR")
        print(f"👤 Validé par: {result['validated_by']}")
        print(f"📅 Confirmé  : {result['confirmed_at']}")
        print(f"\n📱 Notification Telegram envoyée")
        print(f"💾 Ledger mis à jour: data/validation/real_sales_ledger.json")
    else:
        print(f"\n❌ Erreur: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
