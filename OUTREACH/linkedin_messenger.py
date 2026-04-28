"""
NAYA LINKEDIN MESSENGER
Automation LinkedIn outreach - Connection + Messages
Respecte les limites LinkedIn (20-30 connections/jour, 50 messages/jour)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LinkedInMessage:
    """Message LinkedIn"""
    message_id: str
    prospect_name: str
    prospect_linkedin_url: str
    message_type: str  # 'connection_request', 'message', 'inmail'
    message_text: str
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    connection_accepted: bool = False


class LinkedInMessenger:
    """
    Automation LinkedIn pour outreach B2B

    Capacités:
    - Envoi connection requests avec note personnalisée
    - Messages directs aux connections
    - InMail pour non-connections (si Sales Navigator)
    - Respect des limites LinkedIn (anti-ban)
    - Tracking ouvertures et réponses

    Limites LinkedIn:
    - Max 20-30 connection requests/jour
    - Max 50 messages/jour
    - Délai 1-2 min entre actions
    """

    # Limites quotidiennes (sécurité anti-ban)
    MAX_CONNECTIONS_PER_DAY = 25
    MAX_MESSAGES_PER_DAY = 45
    MIN_DELAY_SECONDS = 90  # 1.5 min entre actions

    def __init__(self, linkedin_client=None, sales_navigator_enabled: bool = False):
        """
        Initialise le messenger LinkedIn

        Args:
            linkedin_client: Client API LinkedIn (ou None pour simulation)
            sales_navigator_enabled: True si Sales Navigator disponible (InMail)
        """
        self.linkedin_client = linkedin_client
        self.sales_navigator_enabled = sales_navigator_enabled

        # Compteurs quotidiens
        self.daily_connections_sent = 0
        self.daily_messages_sent = 0
        self.last_action_time: Optional[datetime] = None
        self.reset_date = datetime.now(timezone.utc).date()

        # Messages envoyés (tracking)
        self.sent_messages: Dict[str, LinkedInMessage] = {}

        logger.info(f"LinkedInMessenger initialized (Sales Nav: {sales_navigator_enabled})")

    def _reset_daily_limits_if_needed(self) -> None:
        """Reset les compteurs quotidiens si nouveau jour"""
        today = datetime.now(timezone.utc).date()
        if today > self.reset_date:
            logger.info(f"Resetting daily limits (was: {self.daily_connections_sent} connections, {self.daily_messages_sent} messages)")
            self.daily_connections_sent = 0
            self.daily_messages_sent = 0
            self.reset_date = today

    async def _wait_if_needed(self) -> None:
        """Attend le délai minimal entre actions pour éviter le ban"""
        if self.last_action_time:
            elapsed = (datetime.now(timezone.utc) - self.last_action_time).total_seconds()
            if elapsed < self.MIN_DELAY_SECONDS:
                wait_time = self.MIN_DELAY_SECONDS - elapsed
                logger.debug(f"Waiting {wait_time:.1f}s to respect LinkedIn rate limit")
                await asyncio.sleep(wait_time)

    async def send_connection_request(self,
                                     prospect_name: str,
                                     prospect_linkedin_url: str,
                                     personalized_note: str) -> bool:
        """
        Envoie une demande de connexion LinkedIn avec note personnalisée

        Args:
            prospect_name: Nom du prospect
            prospect_linkedin_url: URL du profil LinkedIn
            personalized_note: Note personnalisée (max 300 caractères)

        Returns:
            True si envoyé avec succès
        """
        self._reset_daily_limits_if_needed()

        # Vérifier limite quotidienne
        if self.daily_connections_sent >= self.MAX_CONNECTIONS_PER_DAY:
            logger.warning(f"Daily connection limit reached ({self.MAX_CONNECTIONS_PER_DAY}), skipping")
            return False

        # Vérifier longueur note
        if len(personalized_note) > 300:
            logger.warning(f"Note too long ({len(personalized_note)} chars), truncating to 300")
            personalized_note = personalized_note[:297] + "..."

        # Attendre si nécessaire
        await self._wait_if_needed()

        logger.info(f"Sending LinkedIn connection request to {prospect_name}")

        try:
            if self.linkedin_client:
                # Envoi réel via API LinkedIn
                success = await self.linkedin_client.send_connection_request(
                    profile_url=prospect_linkedin_url,
                    note=personalized_note
                )
            else:
                # Mode simulation
                logger.warning("LinkedIn client not configured, simulating connection request")
                success = True
                await asyncio.sleep(0.5)  # Simule latence API

            if success:
                # Créer le tracking
                message_id = f"CONN_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{prospect_name.replace(' ', '_')}"
                self.sent_messages[message_id] = LinkedInMessage(
                    message_id=message_id,
                    prospect_name=prospect_name,
                    prospect_linkedin_url=prospect_linkedin_url,
                    message_type='connection_request',
                    message_text=personalized_note,
                    sent_at=datetime.now(timezone.utc)
                )

                # Incrémenter compteurs
                self.daily_connections_sent += 1
                self.last_action_time = datetime.now(timezone.utc)

                logger.info(f"Connection request sent to {prospect_name} ({self.daily_connections_sent}/{self.MAX_CONNECTIONS_PER_DAY} today)")
                return True
            else:
                logger.error(f"Failed to send connection request to {prospect_name}")
                return False

        except Exception as e:
            logger.error(f"Error sending connection request to {prospect_name}: {e}")
            return False

    async def send_message(self,
                         prospect_name: str,
                         message: str,
                         connection_request: bool = False,
                         prospect_linkedin_url: Optional[str] = None) -> bool:
        """
        Envoie un message LinkedIn

        Args:
            prospect_name: Nom du prospect
            message: Texte du message
            connection_request: True si c'est une connection request
            prospect_linkedin_url: URL du profil (requis si connection_request)

        Returns:
            True si envoyé avec succès
        """
        if connection_request:
            if not prospect_linkedin_url:
                logger.error("LinkedIn URL required for connection request")
                return False
            return await self.send_connection_request(prospect_name, prospect_linkedin_url, message)

        self._reset_daily_limits_if_needed()

        # Vérifier limite quotidienne
        if self.daily_messages_sent >= self.MAX_MESSAGES_PER_DAY:
            logger.warning(f"Daily message limit reached ({self.MAX_MESSAGES_PER_DAY}), skipping")
            return False

        # Attendre si nécessaire
        await self._wait_if_needed()

        logger.info(f"Sending LinkedIn message to {prospect_name}")

        try:
            if self.linkedin_client:
                # Envoi réel via API
                success = await self.linkedin_client.send_message(
                    recipient_name=prospect_name,
                    message_text=message
                )
            else:
                # Mode simulation
                logger.warning("LinkedIn client not configured, simulating message send")
                success = True
                await asyncio.sleep(0.5)

            if success:
                # Tracking
                message_id = f"MSG_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{prospect_name.replace(' ', '_')}"
                self.sent_messages[message_id] = LinkedInMessage(
                    message_id=message_id,
                    prospect_name=prospect_name,
                    prospect_linkedin_url=prospect_linkedin_url or '',
                    message_type='message',
                    message_text=message,
                    sent_at=datetime.now(timezone.utc)
                )

                # Incrémenter compteurs
                self.daily_messages_sent += 1
                self.last_action_time = datetime.now(timezone.utc)

                logger.info(f"Message sent to {prospect_name} ({self.daily_messages_sent}/{self.MAX_MESSAGES_PER_DAY} today)")
                return True
            else:
                logger.error(f"Failed to send message to {prospect_name}")
                return False

        except Exception as e:
            logger.error(f"Error sending message to {prospect_name}: {e}")
            return False

    async def send_inmail(self,
                        prospect_name: str,
                        prospect_linkedin_url: str,
                        subject: str,
                        message: str) -> bool:
        """
        Envoie un InMail (Sales Navigator requis)

        Args:
            prospect_name: Nom du prospect
            prospect_linkedin_url: URL du profil
            subject: Sujet de l'InMail
            message: Corps du message

        Returns:
            True si envoyé avec succès
        """
        if not self.sales_navigator_enabled:
            logger.error("Sales Navigator not enabled, cannot send InMail")
            return False

        self._reset_daily_limits_if_needed()

        # InMail compte comme message
        if self.daily_messages_sent >= self.MAX_MESSAGES_PER_DAY:
            logger.warning(f"Daily message limit reached, skipping InMail")
            return False

        await self._wait_if_needed()

        logger.info(f"Sending InMail to {prospect_name}")

        try:
            if self.linkedin_client:
                success = await self.linkedin_client.send_inmail(
                    profile_url=prospect_linkedin_url,
                    subject=subject,
                    message=message
                )
            else:
                logger.warning("LinkedIn client not configured, simulating InMail")
                success = True
                await asyncio.sleep(0.5)

            if success:
                message_id = f"INMAIL_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{prospect_name.replace(' ', '_')}"
                self.sent_messages[message_id] = LinkedInMessage(
                    message_id=message_id,
                    prospect_name=prospect_name,
                    prospect_linkedin_url=prospect_linkedin_url,
                    message_type='inmail',
                    message_text=f"{subject}\n\n{message}",
                    sent_at=datetime.now(timezone.utc)
                )

                self.daily_messages_sent += 1
                self.last_action_time = datetime.now(timezone.utc)

                logger.info(f"InMail sent to {prospect_name}")
                return True
            else:
                logger.error(f"Failed to send InMail to {prospect_name}")
                return False

        except Exception as e:
            logger.error(f"Error sending InMail: {e}")
            return False

    def mark_connection_accepted(self, prospect_name: str) -> bool:
        """Marque une connexion comme acceptée"""
        for msg in self.sent_messages.values():
            if msg.prospect_name == prospect_name and msg.message_type == 'connection_request':
                msg.connection_accepted = True
                logger.info(f"Connection accepted by {prospect_name}")
                return True
        return False

    def mark_message_read(self, message_id: str) -> bool:
        """Marque un message comme lu"""
        if message_id in self.sent_messages:
            self.sent_messages[message_id].read_at = datetime.now(timezone.utc)
            logger.info(f"Message {message_id} marked as read")
            return True
        return False

    def get_remaining_daily_quota(self) -> Dict[str, int]:
        """Retourne le quota restant pour aujourd'hui"""
        self._reset_daily_limits_if_needed()
        return {
            'connections_remaining': self.MAX_CONNECTIONS_PER_DAY - self.daily_connections_sent,
            'messages_remaining': self.MAX_MESSAGES_PER_DAY - self.daily_messages_sent,
            'connections_used': self.daily_connections_sent,
            'messages_used': self.daily_messages_sent
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        total_sent = len(self.sent_messages)
        if total_sent == 0:
            return {'total_messages': 0}

        connection_requests = [m for m in self.sent_messages.values() if m.message_type == 'connection_request']
        accepted = [m for m in connection_requests if m.connection_accepted]

        return {
            'total_messages': total_sent,
            'connection_requests_sent': len(connection_requests),
            'connections_accepted': len(accepted),
            'acceptance_rate': (len(accepted) / len(connection_requests) * 100) if connection_requests else 0,
            'messages_sent': self.daily_messages_sent,
            'daily_quota': self.get_remaining_daily_quota(),
            'sales_navigator_enabled': self.sales_navigator_enabled
        }


__all__ = ['LinkedInMessenger', 'LinkedInMessage']
