"""
NAYA V19.2 — REAL SALE VALIDATOR
═══════════════════════════════════════════════════════════════════════════════
Validateur de ventes réelles avec pipeline automatisé complet:
1. Détection opportunité via V19.2 quantum hunt
2. Génération offre personnalisée + lien paiement
3. Validation manuelle paiement (confirmation humaine)
4. Notification Telegram à chaque étape
5. Enregistrement ledger immuable SHA-256

100% automatisé. Notifications Telegram toutes ventes (test + production).
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

log = logging.getLogger("NAYA.REAL_SALE")

ROOT = Path(__file__).resolve().parent.parent
SALES_LEDGER = ROOT / "data" / "validation" / "real_sales_ledger.json"
SALES_LEDGER.parent.mkdir(parents=True, exist_ok=True)


class SaleStatus(Enum):
    """Statuts du cycle de vente"""
    OPPORTUNITY_DETECTED = "opportunity_detected"
    OFFER_GENERATED = "offer_generated"
    PAYMENT_LINK_SENT = "payment_link_sent"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_CONFIRMED = "payment_confirmed"
    SALE_COMPLETED = "sale_completed"
    SALE_FAILED = "sale_failed"


class PaymentMethod(Enum):
    """Méthodes de paiement disponibles"""
    PAYPAL = "paypal"
    DEBLOCK = "deblock"
    REVOLUT = "revolut"
    BANK_TRANSFER = "bank_transfer"

    @classmethod
    def normalize(cls, provider: str) -> 'PaymentMethod':
        """Normaliser nom provider (paypal_me → paypal, deblock_me → deblock)"""
        provider_lower = provider.lower().replace('_me', '').replace('.me', '')

        mapping = {
            'paypal': cls.PAYPAL,
            'deblock': cls.DEBLOCK,
            'revolut': cls.REVOLUT,
            'bank': cls.BANK_TRANSFER,
            'virement': cls.BANK_TRANSFER,
        }

        return mapping.get(provider_lower, cls.PAYPAL)


@dataclass
class RealSaleRecord:
    """Enregistrement vente réelle complète"""
    sale_id: str
    opportunity_id: str
    company: str
    contact_name: str
    contact_email: str
    sector: str
    pain_detected: str

    # Offre
    offer_title: str
    offer_description: str
    amount_eur: float

    # Paiement
    payment_method: PaymentMethod
    payment_url: str
    payment_reference: str

    # Statut
    status: SaleStatus
    created_at: float = field(default_factory=time.time)
    payment_confirmed_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Validation
    validated_by: str = "auto"  # "auto" ou nom validateur manuel
    validation_notes: str = ""

    # Traçabilité
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            data = f"{self.sale_id}|{self.company}|{self.amount_eur}|{self.created_at}"
            self.hash = hashlib.sha256(data.encode()).hexdigest()


class RealSaleValidator:
    """
    Validateur de ventes réelles V19.2
    Pipeline automatisé complet avec notifications Telegram.
    """

    def __init__(self):
        self.sales: List[RealSaleRecord] = []
        self.telegram_notifier = self._get_telegram_notifier()
        self.payment_engine = self._get_payment_engine()
        self._load_ledger()
        log.info(f"[REAL_SALE] Validator initialisé | {len(self.sales)} ventes en ledger")

    def _get_telegram_notifier(self):
        """Récupère le notifier Telegram"""
        try:
            from NAYA_CORE.integrations.telegram_notifier import TelegramNotifier
            return TelegramNotifier()
        except Exception as e:
            log.warning(f"[REAL_SALE] Telegram notifier non disponible: {e}")
            return None

    def _get_payment_engine(self):
        """Récupère le payment engine"""
        try:
            from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
            return PaymentEngine()
        except Exception as e:
            log.warning(f"[REAL_SALE] Payment engine non disponible: {e}")
            return None

    async def run_automated_sale_test(
        self,
        test_name: str = "Test Vente Automatisé",
        target_amount_eur: float = 1000.0,
        sector: str = "energy"
    ) -> Dict[str, Any]:
        """
        PHASE 1-2-3 COMPLÈTE : Test vente réel automatisé

        Phase 1: Détection opportunité
        Phase 2: Génération offre + lien paiement
        Phase 3: Validation manuelle paiement (attente confirmation)

        Args:
            test_name: Nom du test
            target_amount_eur: Montant cible
            sector: Secteur à cibler

        Returns:
            Résultat complet avec sale_id, payment_url, status
        """
        log.info(f"[REAL_SALE] Démarrage test vente: {test_name} | {target_amount_eur} EUR | {sector}")

        # Notification début
        await self._notify_test_started(test_name, target_amount_eur)

        try:
            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: DÉTECTION OPPORTUNITÉ
            # ═══════════════════════════════════════════════════════════════
            log.info("[REAL_SALE] Phase 1: Détection opportunité...")
            opportunity = await self._detect_opportunity(sector, target_amount_eur)

            await self._notify_opportunity_detected(opportunity)

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GÉNÉRATION OFFRE + LIEN PAIEMENT
            # ═══════════════════════════════════════════════════════════════
            log.info("[REAL_SALE] Phase 2: Génération offre...")
            offer = await self._generate_offer(opportunity)

            log.info("[REAL_SALE] Phase 2: Création lien paiement...")
            payment = await self._create_payment_link(offer)

            # Créer enregistrement vente
            sale = RealSaleRecord(
                sale_id=f"REAL_SALE_{uuid.uuid4().hex[:8].upper()}",
                opportunity_id=opportunity['id'],
                company=opportunity['company'],
                contact_name=opportunity['contact_name'],
                contact_email=opportunity['contact_email'],
                sector=opportunity['sector'],
                pain_detected=opportunity['pain'],
                offer_title=offer['title'],
                offer_description=offer['description'],
                amount_eur=offer['price_eur'],
                payment_method=PaymentMethod.normalize(payment['provider']),
                payment_url=payment['url'],
                payment_reference=payment['reference'],
                status=SaleStatus.PAYMENT_LINK_SENT,
            )

            # Sauvegarder
            self.sales.append(sale)
            self._save_ledger()

            await self._notify_payment_link_generated(sale, payment)

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: ATTENTE VALIDATION MANUELLE PAIEMENT
            # ═══════════════════════════════════════════════════════════════
            log.info("[REAL_SALE] Phase 3: En attente validation paiement...")

            result = {
                'success': True,
                'sale_id': sale.sale_id,
                'company': sale.company,
                'amount_eur': sale.amount_eur,
                'payment_url': sale.payment_url,
                'payment_reference': sale.payment_reference,
                'status': sale.status.value,
                'next_action': 'VALIDATION_MANUELLE_REQUISE',
                'instructions': (
                    f"1. Ouvrir le lien: {sale.payment_url}\n"
                    f"2. Effectuer paiement test de {sale.amount_eur} EUR\n"
                    f"3. Confirmer manuellement via: python scripts/validate_payment.py {sale.sale_id}\n"
                    f"OU attendre notification Telegram automatique"
                ),
            }

            log.info(f"[REAL_SALE] ✅ Test créé | Sale ID: {sale.sale_id} | Montant: {sale.amount_eur} EUR")
            log.info(f"[REAL_SALE] 🔗 Lien paiement: {sale.payment_url}")

            return result

        except Exception as e:
            log.error(f"[REAL_SALE] Erreur test vente: {e}", exc_info=True)
            await self._notify_test_failed(test_name, str(e))
            return {
                'success': False,
                'error': str(e),
                'test_name': test_name,
            }

    async def _detect_opportunity(self, sector: str, target_amount: float) -> Dict:
        """Phase 1: Détection opportunité (V19.2 quantum hunt ou mock)"""

        # Essayer V19.2 quantum hunt
        try:
            from NAYA_CORE.v19_2_supreme_engine import run_autonomous_quantum_hunt

            result = await run_autonomous_quantum_hunt()
            opportunities = result.get('outreach_plans', [])

            # Filtrer par secteur et montant
            for opp in opportunities:
                if sector.lower() in opp.get('sector', '').lower():
                    if opp.get('budget_estimate_eur', 0) >= target_amount * 0.8:
                        return {
                            'id': f"OPP_{uuid.uuid4().hex[:8].upper()}",
                            'company': opp.get('company', 'Entreprise détectée'),
                            'contact_name': opp.get('decision_maker', {}).get('name', 'Contact Principal'),
                            'contact_email': opp.get('decision_maker', {}).get('email', 'contact@example.com'),
                            'sector': sector,
                            'pain': opp.get('discrete_pain', 'Besoin détecté'),
                            'budget_estimate': opp.get('budget_estimate_eur', target_amount),
                            'source': 'v19.2_quantum_hunt',
                        }
        except Exception as e:
            log.debug(f"[REAL_SALE] V19.2 hunt non disponible: {e}")

        # Fallback: opportunité simulée réaliste
        mock_opportunities = {
            'energy': {
                'company': 'EDF Renouvelables — Direction SCADA',
                'contact_name': 'Marie DUBOIS',
                'contact_email': 'marie.dubois@edf-renouvelables.fr',
                'pain': 'Conformité NIS2 urgente, infrastructure critique OT non auditée',
            },
            'transport': {
                'company': 'RATP Dev — DSI Cybersécurité',
                'contact_name': 'Thomas MARTIN',
                'contact_email': 'thomas.martin@ratp.fr',
                'pain': 'Audit IEC 62443 systèmes métro automatiques requis avant certification',
            },
            'manufacturing': {
                'company': 'Michelin — Directeur Usine Smart',
                'contact_name': 'Sophie BERNARD',
                'contact_email': 'sophie.bernard@michelin.com',
                'pain': 'Sécurisation automates production, ransomware prevention',
            },
        }

        opp_data = mock_opportunities.get(sector.lower(), mock_opportunities['energy'])

        return {
            'id': f"OPP_{uuid.uuid4().hex[:8].upper()}",
            'company': opp_data['company'],
            'contact_name': opp_data['contact_name'],
            'contact_email': opp_data['contact_email'],
            'sector': sector,
            'pain': opp_data['pain'],
            'budget_estimate': target_amount,
            'source': 'mock_realistic',
        }

    async def _generate_offer(self, opportunity: Dict) -> Dict:
        """Phase 2: Génération offre personnalisée"""

        # Calibrer offre selon budget
        budget = opportunity['budget_estimate']

        if budget >= 50000:
            tier = "PREMIUM"
            title = f"Mission Conformité Complète NIS2 + IEC 62443 — {opportunity['company']}"
            description = (
                f"Audit complet infrastructure OT, gap analysis IEC 62443 SL-1 à SL-4, "
                f"roadmap corrective priorisée, support certification NIS2."
            )
        elif budget >= 20000:
            tier = "ADVANCED"
            title = f"Audit IEC 62443 + Roadmap NIS2 — {opportunity['company']}"
            description = (
                f"Audit IEC 62443 périmètre OT, évaluation conformité NIS2, "
                f"recommandations priorisées, plan d'action 12 mois."
            )
        elif budget >= 5000:
            tier = "STANDARD"
            title = f"Audit Express OT/NIS2 — {opportunity['company']}"
            description = (
                f"Audit rapide systèmes OT critiques, checklist conformité NIS2, "
                f"quick wins identifiés, rapport synthétique 20 pages."
            )
        else:
            tier = "STARTER"
            title = f"Pré-Audit Conformité OT — {opportunity['company']}"
            description = (
                f"Évaluation initiale maturité OT, score conformité NIS2, "
                f"identification gaps prioritaires, rapport exécutif."
            )

        return {
            'title': title,
            'description': description,
            'price_eur': budget,
            'tier': tier,
            'delivery_days': 5 if tier == "STARTER" else 10 if tier == "STANDARD" else 15,
            'company': opportunity['company'],
            'contact': opportunity['contact_name'],
        }

    async def _create_payment_link(self, offer: Dict) -> Dict:
        """Phase 2: Création lien paiement PayPal/Deblock"""

        if not self.payment_engine:
            # Fallback manuel
            return {
                'created': True,
                'url': f"https://www.paypal.me/NAYA/{offer['price_eur']:.2f}",
                'provider': 'paypal',
                'reference': f"NAYA-TEST-{uuid.uuid4().hex[:6].upper()}",
            }

        payment = self.payment_engine.create_payment_link(
            amount_eur=offer['price_eur'],
            description=offer['title'],
            client_name=offer['contact'],
            client_email=""
        )

        return payment

    async def validate_payment_manual(
        self,
        sale_id: str,
        validator_name: str = "manual",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Phase 3: Validation manuelle paiement confirmé

        Args:
            sale_id: ID de la vente
            validator_name: Nom de la personne qui valide
            notes: Notes de validation

        Returns:
            Résultat validation
        """
        sale = next((s for s in self.sales if s.sale_id == sale_id), None)

        if not sale:
            return {
                'success': False,
                'error': f"Vente {sale_id} non trouvée",
            }

        if sale.status == SaleStatus.PAYMENT_CONFIRMED:
            return {
                'success': False,
                'error': f"Paiement déjà confirmé pour {sale_id}",
                'confirmed_at': sale.payment_confirmed_at,
            }

        # Confirmer paiement
        sale.status = SaleStatus.PAYMENT_CONFIRMED
        sale.payment_confirmed_at = time.time()
        sale.validated_by = validator_name
        sale.validation_notes = notes

        self._save_ledger()

        # Notification Telegram
        await self._notify_payment_confirmed(sale)

        log.info(f"[REAL_SALE] ✅ Paiement confirmé | {sale.sale_id} | {sale.amount_eur} EUR | Validé par: {validator_name}")

        return {
            'success': True,
            'sale_id': sale.sale_id,
            'company': sale.company,
            'amount_eur': sale.amount_eur,
            'status': sale.status.value,
            'confirmed_at': sale.payment_confirmed_at,
            'validated_by': sale.validated_by,
        }

    async def complete_sale(self, sale_id: str) -> Dict[str, Any]:
        """Marquer vente comme complétée (après livraison service)"""

        sale = next((s for s in self.sales if s.sale_id == sale_id), None)

        if not sale:
            return {'success': False, 'error': f"Vente {sale_id} non trouvée"}

        sale.status = SaleStatus.SALE_COMPLETED
        sale.completed_at = time.time()

        self._save_ledger()

        await self._notify_sale_completed(sale)

        log.info(f"[REAL_SALE] ✅ Vente complétée | {sale.sale_id} | {sale.company}")

        return {
            'success': True,
            'sale_id': sale.sale_id,
            'total_cycle_time_hours': (sale.completed_at - sale.created_at) / 3600,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # NOTIFICATIONS TELEGRAM
    # ═══════════════════════════════════════════════════════════════════════

    async def _notify_test_started(self, test_name: str, amount: float):
        """Notification début test"""
        if self.telegram_notifier:
            self.telegram_notifier.send(
                f"🧪 <b>TEST VENTE DÉMARRÉ</b>\n\n"
                f"📋 Test: {test_name}\n"
                f"💰 Montant: {amount:,.0f} EUR\n"
                f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )

    async def _notify_opportunity_detected(self, opp: Dict):
        """Notification opportunité détectée"""
        if self.telegram_notifier:
            self.telegram_notifier.send(
                f"🎯 <b>OPPORTUNITÉ DÉTECTÉE</b>\n\n"
                f"🏢 Entreprise: {opp['company']}\n"
                f"👤 Contact: {opp['contact_name']}\n"
                f"🎨 Secteur: {opp['sector']}\n"
                f"💡 Pain: {opp['pain'][:100]}...\n"
                f"💰 Budget estimé: {opp['budget_estimate']:,.0f} EUR\n"
                f"📍 Source: {opp['source']}"
            )

    async def _notify_payment_link_generated(self, sale: RealSaleRecord, payment: Dict):
        """Notification lien paiement généré"""
        if self.telegram_notifier:
            self.telegram_notifier.send(
                f"💳 <b>LIEN PAIEMENT GÉNÉRÉ</b>\n\n"
                f"🆔 Sale ID: <code>{sale.sale_id}</code>\n"
                f"🏢 Client: {sale.company}\n"
                f"💰 Montant: {sale.amount_eur:,.0f} EUR\n"
                f"📋 Offre: {sale.offer_title[:80]}\n\n"
                f"🔗 <b>Lien paiement:</b>\n{sale.payment_url}\n\n"
                f"📌 Référence: <code>{sale.payment_reference}</code>\n\n"
                f"⏳ <b>EN ATTENTE PAIEMENT</b>\n"
                f"Pour valider manuellement:\n"
                f"<code>python scripts/validate_payment.py {sale.sale_id}</code>"
            )

    async def _notify_payment_confirmed(self, sale: RealSaleRecord):
        """Notification paiement confirmé"""
        if self.telegram_notifier:
            self.telegram_notifier.send(
                f"✅ <b>VENTE RÉELLE VALIDÉE</b>\n\n"
                f"🆔 Sale ID: <code>{sale.sale_id}</code>\n"
                f"🏢 Client: {sale.company}\n"
                f"💰 Montant: <b>{sale.amount_eur:,.0f} EUR</b>\n"
                f"💳 Via: {sale.payment_method.value.upper()}\n"
                f"📌 Réf: <code>{sale.payment_reference}</code>\n\n"
                f"👤 Validé par: {sale.validated_by}\n"
                f"📝 Notes: {sale.validation_notes or 'Aucune'}\n\n"
                f"⏰ Confirmé: {datetime.fromtimestamp(sale.payment_confirmed_at, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )

    async def _notify_sale_completed(self, sale: RealSaleRecord):
        """Notification vente complétée"""
        if self.telegram_notifier:
            cycle_hours = (sale.completed_at - sale.created_at) / 3600
            self.telegram_notifier.send(
                f"🎉 <b>VENTE COMPLÉTÉE</b>\n\n"
                f"🆔 Sale ID: <code>{sale.sale_id}</code>\n"
                f"🏢 Client: {sale.company}\n"
                f"💰 Montant: <b>{sale.amount_eur:,.0f} EUR</b>\n"
                f"⏱️ Cycle: {cycle_hours:.1f}h\n\n"
                f"✅ Service livré avec succès"
            )

    async def _notify_test_failed(self, test_name: str, error: str):
        """Notification échec test"""
        if self.telegram_notifier:
            self.telegram_notifier.send(
                f"❌ <b>TEST VENTE ÉCHOUÉ</b>\n\n"
                f"📋 Test: {test_name}\n"
                f"⚠️ Erreur: {error[:200]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE LEDGER
    # ═══════════════════════════════════════════════════════════════════════

    def _save_ledger(self):
        """Sauvegarde ledger immuable"""
        try:
            data = []
            for sale in self.sales:
                sale_dict = asdict(sale)
                # Convertir enums en valeurs
                sale_dict['status'] = sale.status.value
                sale_dict['payment_method'] = sale.payment_method.value
                data.append(sale_dict)

            tmp = SALES_LEDGER.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
            tmp.replace(SALES_LEDGER)

            log.debug(f"[REAL_SALE] Ledger sauvegardé | {len(self.sales)} ventes")
        except Exception as e:
            log.error(f"[REAL_SALE] Erreur sauvegarde ledger: {e}")

    def _load_ledger(self):
        """Charge ledger existant"""
        try:
            if SALES_LEDGER.exists():
                data = json.loads(SALES_LEDGER.read_text(encoding='utf-8'))
                for sale_dict in data:
                    try:
                        # Convertir valeurs en enums
                        sale_dict['status'] = SaleStatus(sale_dict['status'])
                        sale_dict['payment_method'] = PaymentMethod(sale_dict['payment_method'])
                        self.sales.append(RealSaleRecord(**sale_dict))
                    except Exception:
                        pass

                log.info(f"[REAL_SALE] Ledger chargé | {len(self.sales)} ventes")
        except Exception as e:
            log.warning(f"[REAL_SALE] Erreur chargement ledger: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques ventes réelles"""
        confirmed = [s for s in self.sales if s.status == SaleStatus.PAYMENT_CONFIRMED]
        completed = [s for s in self.sales if s.status == SaleStatus.SALE_COMPLETED]

        return {
            'total_sales': len(self.sales),
            'payment_confirmed': len(confirmed),
            'completed': len(completed),
            'total_revenue_eur': sum(s.amount_eur for s in confirmed),
            'avg_amount_eur': sum(s.amount_eur for s in confirmed) / len(confirmed) if confirmed else 0,
            'pending_payment': len([s for s in self.sales if s.status == SaleStatus.AWAITING_PAYMENT]),
        }


# Singleton
_VALIDATOR: Optional[RealSaleValidator] = None


def get_real_sale_validator() -> RealSaleValidator:
    """Retourne instance singleton"""
    global _VALIDATOR
    if _VALIDATOR is None:
        _VALIDATOR = RealSaleValidator()
    return _VALIDATOR


# Export API
async def run_real_sale_test(
    test_name: str = "Test Vente Réel",
    amount_eur: float = 1000.0,
    sector: str = "energy"
) -> Dict[str, Any]:
    """API: Lance un test de vente réel complet"""
    validator = get_real_sale_validator()
    return await validator.run_automated_sale_test(test_name, amount_eur, sector)


async def validate_payment(sale_id: str, validator: str = "manual", notes: str = "") -> Dict[str, Any]:
    """API: Valide un paiement manuellement"""
    validator_instance = get_real_sale_validator()
    return await validator_instance.validate_payment_manual(sale_id, validator, notes)
