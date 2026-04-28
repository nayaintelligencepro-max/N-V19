"""
NAYA WHATSAPP AGENT
WhatsApp Business API integration pour outreach B2B
Messages personnalisés, templates approuvés, tracking delivery
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessage:
    """Message WhatsApp"""
    message_id: str
    phone_number: str
    prospect_name: str
    message_text: str
    template_name: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    failed: bool = False
    error_message: Optional[str] = None


class WhatsAppAgent:
    """
    Agent WhatsApp Business pour outreach B2B

    Capacités:
    - Envoi messages via WhatsApp Business API
    - Templates pré-approuvés (requis par WhatsApp)
    - Personnalisation avec variables
    - Tracking delivery, read, reply
    - Respect limites API WhatsApp

    Note: WhatsApp Business API requiert:
    - Templates approuvés par Meta
    - Opt-in du destinataire (RGPD)
    - Business account vérifié
    """

    # Templates approuvés WhatsApp (exemples)
    APPROVED_TEMPLATES = {
        'initial_contact_ot_security': {
            'name': 'initial_contact_ot_security',
            'language': 'fr',
            'body': 'Bonjour {{1}}, je me permets de vous contacter concernant la sécurité OT de {{2}}. Seriez-vous disponible pour un échange rapide ?',
            'variables': ['prospect_name', 'company_name']
        },
        'followup_audit_offer': {
            'name': 'followup_audit_offer',
            'language': 'fr',
            'body': 'Bonjour {{1}}, suite à mon email concernant l\'audit IEC 62443 pour {{2}}, avez-vous pu y jeter un œil ?',
            'variables': ['prospect_name', 'company_name']
        },
        'meeting_confirmation': {
            'name': 'meeting_confirmation',
            'language': 'fr',
            'body': 'Bonjour {{1}}, merci pour votre intérêt ! Notre rendez-vous est confirmé pour le {{2}} à {{3}}. À très bientôt !',
            'variables': ['prospect_name', 'date', 'time']
        }
    }

    def __init__(self, whatsapp_api_client=None, business_phone_number: Optional[str] = None):
        """
        Initialise l'agent WhatsApp

        Args:
            whatsapp_api_client: Client API WhatsApp Business
            business_phone_number: Numéro de téléphone business (format: +33...)
        """
        self.api_client = whatsapp_api_client
        self.business_phone_number = business_phone_number

        # Messages envoyés (tracking)
        self.sent_messages: Dict[str, WhatsAppMessage] = {}

        # Compteurs
        self.total_sent = 0
        self.total_delivered = 0
        self.total_read = 0
        self.total_replied = 0
        self.total_failed = 0

        logger.info(f"WhatsAppAgent initialized (business number: {business_phone_number})")

    async def send_message(self,
                         phone_number: str,
                         message: str,
                         prospect_name: str = "Prospect",
                         template_name: Optional[str] = None,
                         template_variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Envoie un message WhatsApp

        Args:
            phone_number: Numéro destinataire (format international +33...)
            message: Texte du message (si pas de template)
            prospect_name: Nom du prospect
            template_name: Nom du template approuvé (optionnel)
            template_variables: Variables pour le template

        Returns:
            True si envoyé avec succès
        """
        # Valider le format du numéro
        if not phone_number.startswith('+'):
            logger.error(f"Invalid phone number format: {phone_number} (must start with +)")
            return False

        logger.info(f"Sending WhatsApp message to {prospect_name} ({phone_number})")

        try:
            message_text = message
            used_template = template_name

            # Si template spécifié, utiliser le template approuvé
            if template_name:
                template = self.APPROVED_TEMPLATES.get(template_name)
                if not template:
                    logger.error(f"Template {template_name} not found in approved templates")
                    return False

                # Remplacer les variables dans le template
                if template_variables:
                    message_text = template['body']
                    for i, var_name in enumerate(template['variables'], 1):
                        var_value = template_variables.get(var_name, f'{{{{var_{i}}}}}')
                        message_text = message_text.replace(f'{{{{{i}}}}}', var_value)

            # Envoi via API WhatsApp Business
            if self.api_client:
                if template_name:
                    # Envoi avec template
                    response = await self.api_client.send_template_message(
                        to=phone_number,
                        template_name=template_name,
                        language='fr',
                        variables=list(template_variables.values()) if template_variables else []
                    )
                else:
                    # Envoi message libre (nécessite session active)
                    response = await self.api_client.send_text_message(
                        to=phone_number,
                        message=message_text
                    )

                message_id = response.get('message_id', f"WHATSAPP_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
                success = response.get('success', False)

            else:
                # Mode simulation
                logger.warning("WhatsApp API client not configured, simulating message send")
                message_id = f"WHATSAPP_SIM_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                success = True
                await asyncio.sleep(0.3)

            if success:
                # Créer le tracking
                self.sent_messages[message_id] = WhatsAppMessage(
                    message_id=message_id,
                    phone_number=phone_number,
                    prospect_name=prospect_name,
                    message_text=message_text,
                    template_name=used_template,
                    sent_at=datetime.now(timezone.utc)
                )

                self.total_sent += 1
                logger.info(f"WhatsApp message sent to {prospect_name} (ID: {message_id})")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message to {prospect_name}")
                self.total_failed += 1
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {prospect_name}: {e}")
            self.total_failed += 1

            # Créer entrée d'échec pour tracking
            failed_msg_id = f"FAILED_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            self.sent_messages[failed_msg_id] = WhatsAppMessage(
                message_id=failed_msg_id,
                phone_number=phone_number,
                prospect_name=prospect_name,
                message_text=message,
                sent_at=datetime.now(timezone.utc),
                failed=True,
                error_message=str(e)
            )

            return False

    async def send_template_message(self,
                                   phone_number: str,
                                   prospect_name: str,
                                   template_name: str,
                                   **kwargs) -> bool:
        """
        Envoie un message via template approuvé

        Args:
            phone_number: Numéro destinataire
            prospect_name: Nom du prospect
            template_name: Nom du template
            **kwargs: Variables du template

        Returns:
            True si envoyé avec succès
        """
        return await self.send_message(
            phone_number=phone_number,
            message="",  # Le message sera généré depuis le template
            prospect_name=prospect_name,
            template_name=template_name,
            template_variables=kwargs
        )

    def handle_webhook_update(self, webhook_data: Dict[str, Any]) -> None:
        """
        Gère les webhooks WhatsApp (delivery, read, reply)

        Args:
            webhook_data: Données du webhook WhatsApp
        """
        try:
            message_id = webhook_data.get('message_id')
            status = webhook_data.get('status')  # 'delivered', 'read', 'failed'

            if not message_id or message_id not in self.sent_messages:
                logger.warning(f"Webhook for unknown message: {message_id}")
                return

            message = self.sent_messages[message_id]

            if status == 'delivered':
                message.delivered_at = datetime.now(timezone.utc)
                self.total_delivered += 1
                logger.info(f"Message {message_id} delivered to {message.prospect_name}")

            elif status == 'read':
                message.read_at = datetime.now(timezone.utc)
                self.total_read += 1
                logger.info(f"Message {message_id} read by {message.prospect_name}")

            elif status == 'failed':
                message.failed = True
                message.error_message = webhook_data.get('error', 'Unknown error')
                self.total_failed += 1
                logger.error(f"Message {message_id} failed: {message.error_message}")

        except Exception as e:
            logger.error(f"Error handling webhook update: {e}")

    def handle_incoming_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère un message entrant (réponse du prospect)

        Args:
            webhook_data: Données du webhook

        Returns:
            Analyse de la réponse
        """
        try:
            phone_number = webhook_data.get('from')
            message_text = webhook_data.get('message', {}).get('text', '')

            # Trouver le prospect correspondant
            prospect_message = None
            for msg in self.sent_messages.values():
                if msg.phone_number == phone_number:
                    prospect_message = msg
                    break

            if prospect_message:
                prospect_message.replied_at = datetime.now(timezone.utc)
                self.total_replied += 1

                logger.info(f"Reply received from {prospect_message.prospect_name}: {message_text[:50]}...")

                return {
                    'prospect_name': prospect_message.prospect_name,
                    'phone_number': phone_number,
                    'message': message_text,
                    'original_message_id': prospect_message.message_id,
                    'action': 'forward_to_reply_handler'
                }
            else:
                logger.warning(f"Incoming message from unknown number: {phone_number}")
                return {
                    'phone_number': phone_number,
                    'message': message_text,
                    'action': 'unknown_sender'
                }

        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
            return {'error': str(e)}

    def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le statut d'un message"""
        if message_id not in self.sent_messages:
            return None

        msg = self.sent_messages[message_id]
        return {
            'message_id': msg.message_id,
            'prospect_name': msg.prospect_name,
            'phone_number': msg.phone_number,
            'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
            'delivered': msg.delivered_at is not None,
            'read': msg.read_at is not None,
            'replied': msg.replied_at is not None,
            'failed': msg.failed,
            'error': msg.error_message
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        delivery_rate = (self.total_delivered / self.total_sent * 100) if self.total_sent > 0 else 0
        read_rate = (self.total_read / self.total_delivered * 100) if self.total_delivered > 0 else 0
        reply_rate = (self.total_replied / self.total_read * 100) if self.total_read > 0 else 0

        return {
            'total_sent': self.total_sent,
            'total_delivered': self.total_delivered,
            'total_read': self.total_read,
            'total_replied': self.total_replied,
            'total_failed': self.total_failed,
            'delivery_rate': round(delivery_rate, 2),
            'read_rate': round(read_rate, 2),
            'reply_rate': round(reply_rate, 2),
            'templates_available': len(self.APPROVED_TEMPLATES),
            'business_phone': self.business_phone_number
        }


__all__ = ['WhatsAppAgent', 'WhatsAppMessage']
