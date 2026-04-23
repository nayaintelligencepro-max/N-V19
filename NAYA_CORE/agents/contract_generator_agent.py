"""
NAYA CORE — AGENT 8 — CONTRACT GENERATOR
Génération automatique de contrats PDF signables + facturation
Templates: prestation, abonnement SaaS, NDA, lettre de mission
Intégration paiement: Deblok.me + PayPal.me + log immuable SHA-256
"""

import asyncio
import logging
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


# Plancher minimum absolu NAYA SUPREME (INVIOLABLE)
MIN_CONTRACT_VALUE_EUR = 1000


@dataclass
class ContractData:
    """Données d'un contrat"""
    contract_id: str
    contract_type: str  # 'prestation', 'saas_subscription', 'nda', 'mission_letter'
    client_name: str
    client_company: str
    client_email: str
    client_address: str

    # Financier
    total_amount_eur: Decimal
    payment_terms: str  # '30_days', '50_50', 'monthly'
    currency: str = "EUR"

    # Détails prestation
    service_description: str = ""
    deliverables: List[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = None
    signed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Fichiers générés
    contract_pdf_path: Optional[str] = None
    invoice_pdf_path: Optional[str] = None
    payment_link: Optional[str] = None

    # Hash immuable (SHA-256)
    contract_hash: Optional[str] = None

    def __post_init__(self):
        if self.deliverables is None:
            self.deliverables = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class ContractGeneratorAgent:
    """
    Agent 8 — Générateur de contrats automatiques

    Capacités:
    - Génération contrats PDF depuis templates
    - Facturation automatique
    - Links de paiement (Deblok.me + PayPal.me)
    - Log immuable SHA-256 pour audit
    - Validation plancher 1000 EUR

    Templates disponibles:
    - Contrat de prestation (one-shot)
    - Contrat abonnement SaaS (récurrent)
    - NDA (confidentiel standard)
    - Lettre de mission (cadrage projet)
    """

    # Templates de contrats (simplifiés pour démo)
    CONTRACT_TEMPLATES = {
        'prestation': {
            'title': 'CONTRAT DE PRESTATION DE SERVICES',
            'sections': [
                'ENTRE LES SOUSSIGNÉS',
                'OBJET DE LA MISSION',
                'DURÉE ET DÉLAIS',
                'RÉMUNÉRATION',
                'CONDITIONS DE PAIEMENT',
                'OBLIGATIONS DES PARTIES',
                'RÉSILIATION',
                'CONFIDENTIALITÉ',
                'PROPRIÉTÉ INTELLECTUELLE',
                'DROIT APPLICABLE'
            ]
        },
        'saas_subscription': {
            'title': 'CONTRAT D\'ABONNEMENT SAAS',
            'sections': [
                'DESCRIPTION DU SERVICE',
                'DURÉE ET RENOUVELLEMENT',
                'TARIFICATION',
                'MODALITÉS DE PAIEMENT',
                'SUPPORT ET MAINTENANCE',
                'DONNÉES ET CONFIDENTIALITÉ',
                'RÉSILIATION',
                'RESPONSABILITÉS'
            ]
        },
        'nda': {
            'title': 'ACCORD DE CONFIDENTIALITÉ (NDA)',
            'sections': [
                'DÉFINITIONS',
                'INFORMATIONS CONFIDENTIELLES',
                'OBLIGATIONS DE CONFIDENTIALITÉ',
                'EXCEPTIONS',
                'DURÉE',
                'RESTITUTION',
                'SANCTIONS'
            ]
        },
        'mission_letter': {
            'title': 'LETTRE DE MISSION',
            'sections': [
                'CONTEXTE',
                'OBJECTIFS',
                'PÉRIMÈTRE',
                'LIVRABLES',
                'PLANNING',
                'CONDITIONS COMMERCIALES',
                'RESSOURCES',
                'MODALITÉS DE COLLABORATION'
            ]
        }
    }

    def __init__(self,
                 pdf_generator=None,
                 payment_processor=None,
                 audit_logger=None,
                 data_dir: str = "./data/contracts"):
        """
        Initialise le Contract Generator Agent

        Args:
            pdf_generator: Générateur PDF (reportlab/weasyprint)
            payment_processor: Processeur de paiement (Deblock + PayPal — Polynésie)
            audit_logger: Logger immuable SHA-256
            data_dir: Répertoire de stockage des contrats
        """
        self.pdf_generator = pdf_generator
        self.payment_processor = payment_processor
        self.audit_logger = audit_logger
        self.data_dir = data_dir

        # Créer le répertoire si nécessaire
        os.makedirs(data_dir, exist_ok=True)

        # Contracts générés
        self.generated_contracts: Dict[str, ContractData] = {}

        # Métriques
        self.total_contracts_generated = 0
        self.total_contracts_signed = 0
        self.total_amount_contracted_eur = Decimal('0')
        self.total_amount_paid_eur = Decimal('0')

        logger.info(f"ContractGeneratorAgent initialized (data_dir: {data_dir})")

    async def generate_contract(self,
                               client_data: Dict[str, Any],
                               offer_data: Dict[str, Any]) -> ContractData:
        """
        Génère un contrat complet (PDF + facture + payment link)

        Args:
            client_data: Données client (name, company, email, address)
            offer_data: Données offre (type, amount, services, deliverables)

        Returns:
            ContractData avec tous les fichiers générés
        """
        logger.info(f"Generating contract for {client_data.get('company')} - {offer_data.get('amount_eur')} EUR")

        # 1. VALIDATION PLANCHER 1000 EUR (RÈGLE ABSOLUE)
        amount_eur = Decimal(str(offer_data.get('amount_eur', 0)))
        if amount_eur < MIN_CONTRACT_VALUE_EUR:
            error_msg = f"VIOLATION PLANCHER: Montant {amount_eur} EUR < minimum {MIN_CONTRACT_VALUE_EUR} EUR"
            logger.error(error_msg)
            if self.audit_logger:
                await self.audit_logger.log_critical(error_msg, context={'client': client_data, 'offer': offer_data})
            raise ValueError(error_msg)

        # 2. Créer le ContractData
        contract_id = self._generate_contract_id(client_data.get('company', 'CLIENT'))

        contract = ContractData(
            contract_id=contract_id,
            contract_type=offer_data.get('type', 'prestation'),
            client_name=client_data.get('name', ''),
            client_company=client_data.get('company', ''),
            client_email=client_data.get('email', ''),
            client_address=client_data.get('address', ''),
            total_amount_eur=amount_eur,
            payment_terms=offer_data.get('payment_terms', '30_days'),
            service_description=offer_data.get('service_description', ''),
            deliverables=offer_data.get('deliverables', []),
            start_date=offer_data.get('start_date'),
            end_date=offer_data.get('end_date')
        )

        # 3. Générer le PDF du contrat
        contract.contract_pdf_path = await self._generate_contract_pdf(contract)

        # 4. Générer la facture
        contract.invoice_pdf_path = await self._generate_invoice_pdf(contract)

        # 5. Créer le payment link (Deblok.me ou PayPal.me)
        contract.payment_link = await self._create_payment_link(contract)

        # 6. Calculer le hash immuable
        contract.contract_hash = self._calculate_contract_hash(contract)

        # 7. Log immuable dans l'audit logger
        if self.audit_logger:
            await self.audit_logger.log_contract_generation(contract.to_dict())

        # 8. Stocker
        self.generated_contracts[contract_id] = contract
        self.total_contracts_generated += 1
        self.total_amount_contracted_eur += amount_eur

        logger.info(f"Contract generated: {contract_id} - {amount_eur} EUR - Hash: {contract.contract_hash[:16]}...")

        return contract

    async def _generate_contract_pdf(self, contract: ContractData) -> str:
        """Génère le PDF du contrat"""
        pdf_filename = f"{contract.contract_id}_contract.pdf"
        pdf_path = os.path.join(self.data_dir, pdf_filename)

        if self.pdf_generator:
            # Génération réelle via reportlab/weasyprint
            template = self.CONTRACT_TEMPLATES.get(contract.contract_type)

            content = {
                'title': template['title'] if template else 'CONTRAT',
                'contract_id': contract.contract_id,
                'date': contract.created_at.strftime('%d/%m/%Y'),
                'client_company': contract.client_company,
                'client_name': contract.client_name,
                'client_address': contract.client_address,
                'provider': 'NAYA SUPREME - Stéphanie MAMA',
                'provider_address': 'Polynésie française',
                'service_description': contract.service_description,
                'deliverables': contract.deliverables,
                'amount': f"{contract.total_amount_eur} EUR",
                'payment_terms': contract.payment_terms,
                'start_date': contract.start_date.strftime('%d/%m/%Y') if contract.start_date else 'À définir',
                'end_date': contract.end_date.strftime('%d/%m/%Y') if contract.end_date else 'À définir'
            }

            await self.pdf_generator.generate(
                template_name=contract.contract_type,
                output_path=pdf_path,
                content=content
            )
        else:
            # Mode simulation: créer un fichier texte
            logger.warning("PDF generator not configured, creating text placeholder")
            with open(pdf_path.replace('.pdf', '.txt'), 'w') as f:
                f.write(f"CONTRACT {contract.contract_id}\n")
                f.write(f"Client: {contract.client_company}\n")
                f.write(f"Amount: {contract.total_amount_eur} EUR\n")
                f.write(f"Type: {contract.contract_type}\n")
                f.write(f"Created: {contract.created_at.isoformat()}\n")
            pdf_path = pdf_path.replace('.pdf', '.txt')

        logger.info(f"Contract PDF generated: {pdf_path}")
        return pdf_path

    async def _generate_invoice_pdf(self, contract: ContractData) -> str:
        """Génère la facture PDF"""
        invoice_filename = f"{contract.contract_id}_invoice.pdf"
        invoice_path = os.path.join(self.data_dir, invoice_filename)

        if self.pdf_generator:
            content = {
                'invoice_id': f"INV-{contract.contract_id}",
                'date': contract.created_at.strftime('%d/%m/%Y'),
                'due_date': (contract.created_at + timedelta(days=30)).strftime('%d/%m/%Y'),
                'client_company': contract.client_company,
                'client_name': contract.client_name,
                'client_address': contract.client_address,
                'provider': 'NAYA SUPREME',
                'description': contract.service_description,
                'amount_ht': float(contract.total_amount_eur / Decimal('1.20')),  # Estimation HT
                'tva': float(contract.total_amount_eur / Decimal('1.20') * Decimal('0.20')),
                'amount_ttc': float(contract.total_amount_eur),
                'payment_link': contract.payment_link or 'À générer'
            }

            await self.pdf_generator.generate(
                template_name='invoice',
                output_path=invoice_path,
                content=content
            )
        else:
            # Simulation
            logger.warning("PDF generator not configured, creating invoice placeholder")
            with open(invoice_path.replace('.pdf', '.txt'), 'w') as f:
                f.write(f"INVOICE {contract.contract_id}\n")
                f.write(f"Client: {contract.client_company}\n")
                f.write(f"Amount TTC: {contract.total_amount_eur} EUR\n")
                f.write(f"Due: {(contract.created_at + timedelta(days=30)).strftime('%d/%m/%Y')}\n")
            invoice_path = invoice_path.replace('.pdf', '.txt')

        logger.info(f"Invoice PDF generated: {invoice_path}")
        return invoice_path

    async def _create_payment_link(self, contract: ContractData) -> str:
        """Crée le lien de paiement (Deblok.me ou PayPal.me)"""

        if self.payment_processor:
            # Génération réelle via API
            payment_link = await self.payment_processor.create_payment_link(
                amount_eur=float(contract.total_amount_eur),
                description=f"Contrat {contract.contract_id} - {contract.client_company}",
                client_email=contract.client_email,
                contract_id=contract.contract_id
            )
        else:
            # Simulation: générer un lien factice
            # En Polynésie française, Deblok.me est préféré, puis PayPal.me
            if float(contract.total_amount_eur) >= 5000:
                # Grands montants → Deblok.me (support local)
                payment_link = f"https://deblok.me/pay/{contract.contract_id}?amount={contract.total_amount_eur}"
            else:
                # Petits montants → PayPal.me
                payment_link = f"https://paypal.me/nayasupreme/{contract.total_amount_eur}EUR"

            logger.warning(f"Payment processor not configured, generated simulation link: {payment_link}")

        return payment_link

    def _calculate_contract_hash(self, contract: ContractData) -> str:
        """Calcule le hash SHA-256 immuable du contrat"""
        # Données critiques pour le hash
        hash_data = {
            'contract_id': contract.contract_id,
            'client_company': contract.client_company,
            'client_email': contract.client_email,
            'amount_eur': str(contract.total_amount_eur),
            'created_at': contract.created_at.isoformat(),
            'service_description': contract.service_description
        }

        # Serialization JSON déterministe
        json_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)

        # SHA-256
        contract_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

        return contract_hash

    async def mark_contract_signed(self, contract_id: str) -> bool:
        """Marque un contrat comme signé"""
        if contract_id not in self.generated_contracts:
            logger.error(f"Contract {contract_id} not found")
            return False

        contract = self.generated_contracts[contract_id]
        contract.signed_at = datetime.now(timezone.utc)
        self.total_contracts_signed += 1

        logger.info(f"Contract {contract_id} marked as SIGNED")

        # Log immuable
        if self.audit_logger:
            await self.audit_logger.log_contract_signature(contract_id, contract.contract_hash)

        return True

    async def mark_contract_paid(self, contract_id: str) -> bool:
        """Marque un contrat comme payé"""
        if contract_id not in self.generated_contracts:
            logger.error(f"Contract {contract_id} not found")
            return False

        contract = self.generated_contracts[contract_id]
        contract.paid_at = datetime.now(timezone.utc)
        self.total_amount_paid_eur += contract.total_amount_eur

        logger.info(f"Contract {contract_id} marked as PAID - {contract.total_amount_eur} EUR")

        # Log immuable
        if self.audit_logger:
            await self.audit_logger.log_payment_received(
                contract_id,
                float(contract.total_amount_eur),
                contract.contract_hash
            )

        return True

    def get_contract(self, contract_id: str) -> Optional[ContractData]:
        """Récupère un contrat"""
        return self.generated_contracts.get(contract_id)

    def get_all_contracts(self, status: str = None) -> List[ContractData]:
        """
        Récupère tous les contrats

        Args:
            status: Filtre par statut ('signed', 'paid', 'pending')
        """
        contracts = list(self.generated_contracts.values())

        if status == 'signed':
            return [c for c in contracts if c.signed_at is not None]
        elif status == 'paid':
            return [c for c in contracts if c.paid_at is not None]
        elif status == 'pending':
            return [c for c in contracts if c.signed_at is None]
        else:
            return contracts

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'agent"""
        pending = len([c for c in self.generated_contracts.values() if c.signed_at is None])
        signed = self.total_contracts_signed
        paid = len([c for c in self.generated_contracts.values() if c.paid_at is not None])

        return {
            'total_contracts_generated': self.total_contracts_generated,
            'contracts_pending': pending,
            'contracts_signed': signed,
            'contracts_paid': paid,
            'total_contracted_eur': float(self.total_amount_contracted_eur),
            'total_paid_eur': float(self.total_amount_paid_eur),
            'collection_rate': (float(self.total_amount_paid_eur) / float(self.total_amount_contracted_eur) * 100)
                              if self.total_amount_contracted_eur > 0 else 0
        }

    def _generate_contract_id(self, company_name: str) -> str:
        """Génère un ID unique de contrat"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        company_slug = company_name.replace(' ', '_')[:20].upper()
        random_suffix = hashlib.sha256(f"{company_name}{timestamp}".encode()).hexdigest()[:6].upper()
        return f"CTR_{company_slug}_{timestamp}_{random_suffix}"


    # ------------------------------------------------------------------
    # V19.3 — Cycle unifié pour le multi_agent_orchestrator
    # ------------------------------------------------------------------
    async def run_cycle(self, signed_deals: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cycle contrat appelé par multi_agent_orchestrator.

        Pour chaque deal signé, génère :
        - Contrat PDF (ou placeholder texte si generator non configuré)
        - Facture PDF
        - Lien de paiement (PayPal.me / Deblock.me)
        """
        signed_deals = signed_deals or []
        generated = 0
        errors = 0
        payment_links: List[str] = []

        for deal in signed_deals:
            try:
                contract = await self.generate_contract(
                    client_data=deal.get('client', {}),
                    contract_type=deal.get('contract_type', 'service'),
                    service_details=deal.get('service', {}),
                    amount_eur=float(deal.get('amount_eur', 1000)),
                )
                generated += 1
                if contract and contract.payment_link:
                    payment_links.append(contract.payment_link)
            except Exception as exc:
                errors += 1
                logger.warning(f"[contract_generator] generate failed: {exc}")

        return {
            'total_generated': generated,
            'total_amount_contracted_eur': float(self.total_amount_contracted_eur),
            'total_contracts_signed': self.total_contracts_signed,
            'total_amount_paid_eur': float(self.total_amount_paid_eur),
            'payment_links': payment_links,
            'errors': errors,
        }


# ---------------------------------------------------------------------------
# Singleton partagé
# ---------------------------------------------------------------------------
def _build_contract_generator_agent() -> "ContractGeneratorAgent":
    """Construit l'instance avec les vraies dépendances (payment_engine réel)."""
    payment_processor = None
    pdf_generator = None
    audit_logger = None

    try:
        # Payment engine réel : PayPal.me + Deblock.me uniquement (Polynésie).
        from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine

        class _PaymentProcessorAdapter:
            """Adapter interne pour matcher l'interface attendue par ContractGenerator."""

            def __init__(self) -> None:
                self._engine = PaymentEngine()

            async def create_payment_link(self, amount_eur: float, description: str,
                                          client_email: str = "", contract_id: str = "",
                                          **_: Any) -> str:
                result = self._engine.create_payment_link(
                    amount_eur=amount_eur,
                    description=description,
                    client_email=client_email,
                )
                if not result.get('created'):
                    return ""
                return result.get('primary_url', '') or result.get('paypal_url', '')

        payment_processor = _PaymentProcessorAdapter()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[contract_generator] payment engine unavailable: {exc}")

    try:
        # PDF generator réel si reportlab installé
        import reportlab  # noqa: F401
        from NAYA_CORE.agents._pdf_generator import PdfGeneratorReal
        pdf_generator = PdfGeneratorReal()
    except Exception:
        pdf_generator = None  # placeholder texte utilisé en fallback

    try:
        from NAYA_CORE.notifier import get_notifier
        audit_logger = get_notifier()
    except Exception:
        pass

    return ContractGeneratorAgent(
        pdf_generator=pdf_generator,
        payment_processor=payment_processor,
        audit_logger=audit_logger,
    )


contract_generator_agent = _build_contract_generator_agent()


__all__ = [
    'ContractGeneratorAgent',
    'ContractData',
    'MIN_CONTRACT_VALUE_EUR',
    'contract_generator_agent',
]
