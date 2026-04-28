#!/usr/bin/env python3
"""
NAYA V19.2 — Tests End-to-End Ventes Réelles
═══════════════════════════════════════════════════════════════════════════════
Tests complets du pipeline de vente réelle automatisé:
- Phase 1: Détection opportunité
- Phase 2: Génération offre + lien paiement
- Phase 3: Validation manuelle paiement
- Notifications Telegram toutes étapes

Tous tests utilisent clés API depuis SECRETS/
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from NAYA_ACCELERATION.real_sale_validator import (
    RealSaleValidator,
    get_real_sale_validator,
    run_real_sale_test,
    validate_payment,
    SaleStatus,
    PaymentMethod
)


class TestRealSaleValidatorE2E:
    """Tests end-to-end validateur ventes réelles"""

    @pytest.fixture
    def validator(self):
        """Instance validateur"""
        return RealSaleValidator()

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS PHASE 1: DÉTECTION OPPORTUNITÉ
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_detect_opportunity_energy(self, validator):
        """Test détection opportunité secteur énergie"""
        opp = await validator._detect_opportunity("energy", 15000)

        assert opp is not None
        assert 'id' in opp
        assert 'company' in opp
        assert 'contact_name' in opp
        assert 'contact_email' in opp
        assert opp['sector'] == 'energy'
        assert opp['budget_estimate'] >= 15000 * 0.8
        assert '@' in opp['contact_email']

    @pytest.mark.asyncio
    async def test_detect_opportunity_transport(self, validator):
        """Test détection opportunité secteur transport"""
        opp = await validator._detect_opportunity("transport", 20000)

        assert opp is not None
        assert opp['sector'] == 'transport'
        assert opp['budget_estimate'] >= 16000

    @pytest.mark.asyncio
    async def test_detect_opportunity_manufacturing(self, validator):
        """Test détection opportunité secteur manufacturing"""
        opp = await validator._detect_opportunity("manufacturing", 10000)

        assert opp is not None
        assert opp['sector'] == 'manufacturing'
        assert len(opp['pain']) > 20  # Description pain substantielle

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS PHASE 2: GÉNÉRATION OFFRE
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_generate_offer_starter(self, validator):
        """Test génération offre tier STARTER"""
        opp = {
            'id': 'OPP_TEST',
            'company': 'Test Corp',
            'contact_name': 'John Doe',
            'sector': 'energy',
            'budget_estimate': 3000,
        }

        offer = await validator._generate_offer(opp)

        assert offer['tier'] == 'STARTER'
        assert offer['price_eur'] == 3000
        assert 'Pré-Audit' in offer['title'] or 'STARTER' in offer['tier']
        assert offer['delivery_days'] == 5

    @pytest.mark.asyncio
    async def test_generate_offer_standard(self, validator):
        """Test génération offre tier STANDARD"""
        opp = {
            'id': 'OPP_TEST',
            'company': 'SNCF',
            'contact_name': 'Marie Martin',
            'sector': 'transport',
            'budget_estimate': 15000,
        }

        offer = await validator._generate_offer(opp)

        assert offer['tier'] == 'STANDARD'
        assert offer['price_eur'] == 15000
        assert 'SNCF' in offer['company']

    @pytest.mark.asyncio
    async def test_generate_offer_premium(self, validator):
        """Test génération offre tier PREMIUM"""
        opp = {
            'id': 'OPP_TEST',
            'company': 'EDF',
            'contact_name': 'Sophie Dubois',
            'sector': 'energy',
            'budget_estimate': 75000,
        }

        offer = await validator._generate_offer(opp)

        assert offer['tier'] == 'PREMIUM'
        assert offer['price_eur'] == 75000
        assert offer['delivery_days'] >= 15

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS PHASE 2: CRÉATION LIEN PAIEMENT
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_create_payment_link_paypal(self, validator):
        """Test création lien PayPal.me"""
        offer = {
            'title': 'Audit OT Test',
            'price_eur': 5000,
            'contact': 'Test Client',
        }

        payment = await validator._create_payment_link(offer)

        assert payment['created'] is True
        assert 'url' in payment
        assert 'paypal' in payment['url'].lower() or payment['provider'] == 'paypal'
        assert payment['reference'].startswith('NAYA')
        assert '5000' in payment['url']

    @pytest.mark.asyncio
    async def test_create_payment_link_large_amount(self, validator):
        """Test création lien paiement montant élevé"""
        offer = {
            'title': 'Mission Conformité Complète',
            'price_eur': 50000,
            'contact': 'Big Client',
        }

        payment = await validator._create_payment_link(offer)

        assert payment['created'] is True
        assert '50000' in payment['url']

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS PHASE 1-2-3 COMPLÈTE
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_full_sale_cycle_1000_eur(self, validator):
        """Test cycle complet vente 1000 EUR (STARTER)"""
        result = await validator.run_automated_sale_test(
            test_name="Test E2E 1000 EUR",
            target_amount_eur=1000,
            sector="energy"
        )

        assert result['success'] is True
        assert 'sale_id' in result
        assert result['amount_eur'] >= 1000
        assert 'payment_url' in result
        assert 'payment_reference' in result
        assert result['status'] == SaleStatus.PAYMENT_LINK_SENT.value

        # Vérifier enregistrement
        sale = next((s for s in validator.sales if s.sale_id == result['sale_id']), None)
        assert sale is not None
        assert sale.amount_eur >= 1000
        assert sale.status == SaleStatus.PAYMENT_LINK_SENT

    @pytest.mark.asyncio
    async def test_full_sale_cycle_15000_eur(self, validator):
        """Test cycle complet vente 15000 EUR (STANDARD)"""
        result = await validator.run_automated_sale_test(
            test_name="Test E2E 15000 EUR",
            target_amount_eur=15000,
            sector="transport"
        )

        assert result['success'] is True
        assert result['amount_eur'] >= 15000

        sale = next((s for s in validator.sales if s.sale_id == result['sale_id']), None)
        assert sale is not None
        assert sale.company is not None
        assert len(sale.offer_title) > 20

    @pytest.mark.asyncio
    async def test_full_sale_cycle_50000_eur(self, validator):
        """Test cycle complet vente 50000 EUR (PREMIUM)"""
        result = await validator.run_automated_sale_test(
            test_name="Test E2E 50000 EUR",
            target_amount_eur=50000,
            sector="energy"
        )

        assert result['success'] is True
        assert result['amount_eur'] >= 50000

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS PHASE 3: VALIDATION PAIEMENT
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_validate_payment_manual(self, validator):
        """Test validation manuelle paiement"""
        # Créer vente test
        sale_result = await validator.run_automated_sale_test(
            test_name="Test Validation Paiement",
            target_amount_eur=5000,
            sector="energy"
        )

        sale_id = sale_result['sale_id']

        # Valider paiement
        validation = await validator.validate_payment_manual(
            sale_id=sale_id,
            validator_name="Test Automatisé",
            notes="Test validation E2E"
        )

        assert validation['success'] is True
        assert validation['sale_id'] == sale_id
        assert validation['validated_by'] == "Test Automatisé"

        # Vérifier statut mis à jour
        sale = next((s for s in validator.sales if s.sale_id == sale_id), None)
        assert sale.status == SaleStatus.PAYMENT_CONFIRMED
        assert sale.payment_confirmed_at is not None

    @pytest.mark.asyncio
    async def test_validate_payment_already_confirmed(self, validator):
        """Test validation paiement déjà confirmé"""
        # Créer et valider vente
        sale_result = await validator.run_automated_sale_test(
            test_name="Test Double Validation",
            target_amount_eur=3000,
            sector="transport"
        )

        sale_id = sale_result['sale_id']

        # Première validation
        await validator.validate_payment_manual(sale_id, "Validator1")

        # Deuxième validation (doit échouer)
        validation2 = await validator.validate_payment_manual(sale_id, "Validator2")

        assert validation2['success'] is False
        assert 'déjà confirmé' in validation2['error']

    @pytest.mark.asyncio
    async def test_validate_payment_unknown_sale(self, validator):
        """Test validation paiement vente inexistante"""
        validation = await validator.validate_payment_manual(
            sale_id="SALE_NONEXISTENT_12345",
            validator_name="Test"
        )

        assert validation['success'] is False
        assert 'non trouvée' in validation['error']

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS COMPLÉTION VENTE
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_complete_sale(self, validator):
        """Test complétion vente (service livré)"""
        # Créer et valider vente
        sale_result = await validator.run_automated_sale_test(
            test_name="Test Complétion",
            target_amount_eur=10000,
            sector="energy"
        )

        sale_id = sale_result['sale_id']

        # Valider paiement
        await validator.validate_payment_manual(sale_id, "Test")

        # Compléter vente
        completion = await validator.complete_sale(sale_id)

        assert completion['success'] is True
        assert completion['total_cycle_time_hours'] >= 0

        # Vérifier statut
        sale = next((s for s in validator.sales if s.sale_id == sale_id), None)
        assert sale.status == SaleStatus.SALE_COMPLETED
        assert sale.completed_at is not None

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS LEDGER & PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_ledger_persistence(self, validator):
        """Test persistence ledger immuable"""
        initial_count = len(validator.sales)

        # Créer vente
        await validator.run_automated_sale_test(
            test_name="Test Ledger",
            target_amount_eur=2000,
            sector="manufacturing"
        )

        assert len(validator.sales) == initial_count + 1

        # Vérifier fichier ledger créé/mis à jour
        ledger_file = Path(ROOT) / "data" / "validation" / "real_sales_ledger.json"
        assert ledger_file.exists()

        # Vérifier contenu
        data = json.loads(ledger_file.read_text())
        assert len(data) >= 1
        assert all('hash' in sale for sale in data)

    @pytest.mark.asyncio
    async def test_get_stats(self, validator):
        """Test statistiques ventes"""
        stats = validator.get_stats()

        assert 'total_sales' in stats
        assert 'payment_confirmed' in stats
        assert 'completed' in stats
        assert 'total_revenue_eur' in stats
        assert stats['total_sales'] >= 0

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS NOTIFICATIONS TELEGRAM
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_telegram_notifications_enabled(self, validator):
        """Test notifications Telegram activées"""
        # Si Telegram configuré (TELEGRAM_BOT_TOKEN dans SECRETS)
        if validator.telegram_notifier:
            assert validator.telegram_notifier is not None
            stats = validator.telegram_notifier.stats()
            assert 'sent' in stats
            assert 'failed' in stats

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS API GLOBALES
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_api_run_real_sale_test(self):
        """Test API globale run_real_sale_test"""
        result = await run_real_sale_test(
            test_name="Test API Globale",
            amount_eur=7500,
            sector="energy"
        )

        assert result['success'] is True
        assert result['amount_eur'] >= 7500

    @pytest.mark.asyncio
    async def test_api_validate_payment(self):
        """Test API globale validate_payment"""
        # Créer vente
        sale_result = await run_real_sale_test(
            test_name="Test API Validation",
            amount_eur=3500,
            sector="transport"
        )

        sale_id = sale_result['sale_id']

        # Valider via API
        validation = await validate_payment(
            sale_id=sale_id,
            validator="API Test",
            notes="Test API validation"
        )

        assert validation['success'] is True
        assert validation['validated_by'] == "API Test"

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test instance singleton validator"""
        v1 = get_real_sale_validator()
        v2 = get_real_sale_validator()

        assert v1 is v2  # Même instance


# ═══════════════════════════════════════════════════════════════════════════
# TESTS INTÉGRATION PAIEMENT
# ═══════════════════════════════════════════════════════════════════════════

class TestPaymentIntegration:
    """Tests intégration moteur paiement"""

    @pytest.mark.asyncio
    async def test_payment_engine_available(self):
        """Test payment engine disponible"""
        validator = RealSaleValidator()

        if validator.payment_engine:
            assert validator.payment_engine.available
            assert validator.payment_engine.has_paypal or validator.payment_engine.has_deblock

    @pytest.mark.asyncio
    async def test_payment_methods_from_secrets(self):
        """Test méthodes paiement chargées depuis SECRETS"""
        validator = RealSaleValidator()

        if validator.payment_engine:
            # Vérifier au moins une méthode configurée
            has_method = (
                validator.payment_engine.has_paypal or
                validator.payment_engine.has_deblock or
                validator.payment_engine.has_revolut
            )
            assert has_method, "Aucune méthode paiement configurée dans SECRETS/keys/"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
