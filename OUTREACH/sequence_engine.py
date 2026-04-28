"""
NAYA SEQUENCE ENGINE
Moteur de séquences multi-touch 7 touches sur 21 jours
Touch 1-7: J0/J2/J5/J8/J12/J16/J21
Canaux: Email, LinkedIn, WhatsApp, Video
"""

import asyncio
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TouchChannel(Enum):
    """Canaux de communication disponibles"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    VIDEO = "video"
    SMS = "sms"


class TouchStatus(Enum):
    """Status d'une touche"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TouchPoint:
    """Représente un point de contact dans la séquence"""
    touch_number: int  # 1-7
    day_offset: int  # J+0, J+2, J+5, etc.
    channel: TouchChannel
    message_template_id: str
    subject_template: Optional[str] = None
    personalization_required: bool = True

    # Métadonnées
    status: TouchStatus = TouchStatus.PENDING
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Contenu généré
    generated_subject: Optional[str] = None
    generated_body: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire"""
        return {
            'touch_number': self.touch_number,
            'day_offset': self.day_offset,
            'channel': self.channel.value,
            'message_template_id': self.message_template_id,
            'subject_template': self.subject_template,
            'personalization_required': self.personalization_required,
            'status': self.status.value,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'error_message': self.error_message
        }


@dataclass
class Sequence:
    """Séquence complète pour un prospect"""
    sequence_id: str
    prospect_id: str
    prospect_name: str
    prospect_email: str
    prospect_company: str
    prospect_sector: str

    # Configuration
    touches: List[TouchPoint] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused: bool = False

    # Métriques
    total_touches: int = 0
    touches_sent: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0

    # Contexte prospect
    prospect_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire"""
        return {
            'sequence_id': self.sequence_id,
            'prospect_id': self.prospect_id,
            'prospect_name': self.prospect_name,
            'prospect_email': self.prospect_email,
            'prospect_company': self.prospect_company,
            'prospect_sector': self.prospect_sector,
            'touches': [t.to_dict() for t in self.touches],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'paused': self.paused,
            'total_touches': self.total_touches,
            'touches_sent': self.touches_sent,
            'opens': self.opens,
            'clicks': self.clicks,
            'replies': self.replies,
            'prospect_context': self.prospect_context
        }


class SequenceEngine:
    """
    Moteur de séquences multi-touch autonome

    Séquence standard 7 touches sur 21 jours:
    - Touch 1 (J0): Email personnalisé accroche signal détecté
    - Touch 2 (J2): LinkedIn connection + message court
    - Touch 3 (J5): Email 2 angle valeur (cas anonymisé)
    - Touch 4 (J8): LinkedIn message question ouverte
    - Touch 5 (J12): Email 3 objection anticipée + preuve sociale
    - Touch 6 (J16): Video message 60s (Loom automatisé)
    - Touch 7 (J21): Email final fermeture bienveillante

    Gestion automatique:
    - Réponse positive → meeting_booker.py
    - Réponse négative → CloserAgent
    - Silence total → ZeroWasteEngine recycle le contenu
    """

    DEFAULT_SEQUENCE_TEMPLATE = [
        TouchPoint(1, 0, TouchChannel.EMAIL, "email_touch1_signal", "🎯 {signal_detected} — {company_name}", True),
        TouchPoint(2, 2, TouchChannel.LINKEDIN, "linkedin_touch2_connect", None, True),
        TouchPoint(3, 5, TouchChannel.EMAIL, "email_touch3_value", "📊 Comment {competitor} a réduit ses incidents OT de 78%", True),
        TouchPoint(4, 8, TouchChannel.LINKEDIN, "linkedin_touch4_question", None, True),
        TouchPoint(5, 12, TouchChannel.EMAIL, "email_touch5_objection", "❓ Pourquoi {company_name} n'a pas encore audité son OT ?", True),
        TouchPoint(6, 16, TouchChannel.VIDEO, "video_touch6_loom", "🎥 Message vidéo personnalisé — 60s", True),
        TouchPoint(7, 21, TouchChannel.EMAIL, "email_touch7_final", "✋ Dernière tentative — {prospect_name}", True)
    ]

    def __init__(self,
                 email_sender=None,
                 linkedin_messenger=None,
                 whatsapp_agent=None,
                 video_generator=None,
                 personalizer=None):
        """
        Initialise le moteur de séquences

        Args:
            email_sender: Service d'envoi email (SendGrid, Gmail, etc.)
            linkedin_messenger: Service LinkedIn automation
            whatsapp_agent: Service WhatsApp Business
            video_generator: Service génération vidéos (Loom API)
            personalizer: Service de personnalisation IA
        """
        self.email_sender = email_sender
        self.linkedin_messenger = linkedin_messenger
        self.whatsapp_agent = whatsapp_agent
        self.video_generator = video_generator
        self.personalizer = personalizer

        # Séquences actives en mémoire
        self.active_sequences: Dict[str, Sequence] = {}

        # Métriques globales
        self.total_sequences_created = 0
        self.total_sequences_completed = 0
        self.total_touches_sent = 0
        self.total_replies_received = 0

        logger.info("SequenceEngine initialized")

    def create_sequence(self,
                       prospect_id: str,
                       prospect_data: Dict[str, Any],
                       custom_template: Optional[List[TouchPoint]] = None) -> Sequence:
        """
        Crée une nouvelle séquence pour un prospect

        Args:
            prospect_id: ID unique du prospect
            prospect_data: Données du prospect (name, email, company, sector, context)
            custom_template: Template personnalisé (sinon DEFAULT_SEQUENCE_TEMPLATE)

        Returns:
            Sequence créée et prête à démarrer
        """
        # Générer sequence_id unique
        sequence_id = self._generate_sequence_id(prospect_id)

        # Créer les touches depuis le template
        touches = custom_template or [
            TouchPoint(
                touch_number=tp.touch_number,
                day_offset=tp.day_offset,
                channel=tp.channel,
                message_template_id=tp.message_template_id,
                subject_template=tp.subject_template,
                personalization_required=tp.personalization_required
            ) for tp in self.DEFAULT_SEQUENCE_TEMPLATE
        ]

        # Créer la séquence
        sequence = Sequence(
            sequence_id=sequence_id,
            prospect_id=prospect_id,
            prospect_name=prospect_data.get('name', 'Prospect'),
            prospect_email=prospect_data.get('email', ''),
            prospect_company=prospect_data.get('company', ''),
            prospect_sector=prospect_data.get('sector', ''),
            touches=touches,
            total_touches=len(touches),
            prospect_context=prospect_data.get('context', {})
        )

        # Stocker en mémoire
        self.active_sequences[sequence_id] = sequence
        self.total_sequences_created += 1

        logger.info(f"Sequence created: {sequence_id} for prospect {prospect_id} ({prospect_data.get('company')})")

        return sequence

    async def start_sequence(self, sequence_id: str) -> bool:
        """
        Démarre une séquence (envoie immédiatement Touch 1 et planifie les suivantes)

        Args:
            sequence_id: ID de la séquence à démarrer

        Returns:
            True si démarrage réussi, False sinon
        """
        if sequence_id not in self.active_sequences:
            logger.error(f"Sequence {sequence_id} not found")
            return False

        sequence = self.active_sequences[sequence_id]

        if sequence.started_at:
            logger.warning(f"Sequence {sequence_id} already started")
            return False

        # Marquer comme démarrée
        sequence.started_at = datetime.now(timezone.utc)

        logger.info(f"Starting sequence {sequence_id} for {sequence.prospect_name} ({sequence.prospect_company})")

        try:
            # Envoyer immédiatement Touch 1 (J+0)
            touch1 = sequence.touches[0]
            success = await self._send_touch(sequence, touch1)

            if success:
                # Planifier les touches suivantes
                await self._schedule_remaining_touches(sequence)
                logger.info(f"Sequence {sequence_id} started successfully - Touch 1 sent, remaining touches scheduled")
                return True
            else:
                logger.error(f"Failed to send Touch 1 for sequence {sequence_id}")
                return False

        except Exception as e:
            logger.error(f"Error starting sequence {sequence_id}: {e}")
            return False

    async def _send_touch(self, sequence: Sequence, touch: TouchPoint) -> bool:
        """
        Envoie une touche spécifique

        Args:
            sequence: Séquence parente
            touch: TouchPoint à envoyer

        Returns:
            True si envoi réussi, False sinon
        """
        logger.info(f"Sending touch {touch.touch_number} ({touch.channel.value}) for sequence {sequence.sequence_id}")

        try:
            # Personnalisation du message si requise
            if touch.personalization_required and self.personalizer:
                personalized = await self.personalizer.personalize(
                    template_id=touch.message_template_id,
                    prospect_data={
                        'name': sequence.prospect_name,
                        'email': sequence.prospect_email,
                        'company': sequence.prospect_company,
                        'sector': sequence.prospect_sector,
                        'context': sequence.prospect_context
                    },
                    touch_number=touch.touch_number
                )
                touch.generated_subject = personalized.get('subject')
                touch.generated_body = personalized.get('body')
            else:
                # Template statique sans personnalisation
                touch.generated_subject = touch.subject_template
                touch.generated_body = f"[Template {touch.message_template_id}]"

            # Envoi selon le canal
            success = False

            if touch.channel == TouchChannel.EMAIL:
                if self.email_sender:
                    success = await self.email_sender.send(
                        to_email=sequence.prospect_email,
                        subject=touch.generated_subject,
                        body=touch.generated_body,
                        tracking_id=f"{sequence.sequence_id}_T{touch.touch_number}"
                    )
                else:
                    logger.warning("Email sender not configured, simulating send")
                    success = True  # Mode simulation

            elif touch.channel == TouchChannel.LINKEDIN:
                if self.linkedin_messenger:
                    success = await self.linkedin_messenger.send_message(
                        prospect_name=sequence.prospect_name,
                        message=touch.generated_body,
                        connection_request=(touch.touch_number == 2)
                    )
                else:
                    logger.warning("LinkedIn messenger not configured, simulating send")
                    success = True

            elif touch.channel == TouchChannel.WHATSAPP:
                if self.whatsapp_agent:
                    success = await self.whatsapp_agent.send_message(
                        phone_number=sequence.prospect_context.get('phone'),
                        message=touch.generated_body
                    )
                else:
                    logger.warning("WhatsApp agent not configured, simulating send")
                    success = True

            elif touch.channel == TouchChannel.VIDEO:
                if self.video_generator:
                    video_url = await self.video_generator.create_personalized_video(
                        prospect_name=sequence.prospect_name,
                        company=sequence.prospect_company
                    )
                    success = video_url is not None
                else:
                    logger.warning("Video generator not configured, simulating send")
                    success = True

            # Mettre à jour le statut
            if success:
                touch.status = TouchStatus.SENT
                touch.sent_at = datetime.now(timezone.utc)
                sequence.touches_sent += 1
                self.total_touches_sent += 1
                logger.info(f"Touch {touch.touch_number} sent successfully for {sequence.prospect_name}")
            else:
                touch.status = TouchStatus.FAILED
                touch.error_message = "Send failed"
                logger.error(f"Failed to send touch {touch.touch_number} for {sequence.prospect_name}")

            return success

        except Exception as e:
            logger.error(f"Error sending touch {touch.touch_number}: {e}")
            touch.status = TouchStatus.FAILED
            touch.error_message = str(e)
            return False

    async def _schedule_remaining_touches(self, sequence: Sequence) -> None:
        """
        Planifie les touches 2-7 selon les day_offset

        Args:
            sequence: Séquence dont les touches doivent être planifiées
        """
        now = datetime.now(timezone.utc)

        for touch in sequence.touches[1:]:  # Skip touch 1 (déjà envoyée)
            scheduled_time = now + timedelta(days=touch.day_offset)
            touch.scheduled_at = scheduled_time
            touch.status = TouchStatus.SCHEDULED
            logger.info(f"Touch {touch.touch_number} scheduled for {scheduled_time.isoformat()} (J+{touch.day_offset})")

    async def process_scheduled_touches(self) -> int:
        """
        Traite toutes les touches planifiées dont l'heure est arrivée

        Returns:
            Nombre de touches envoyées
        """
        now = datetime.now(timezone.utc)
        sent_count = 0

        for sequence in self.active_sequences.values():
            if sequence.paused or sequence.completed_at:
                continue

            for touch in sequence.touches:
                if (touch.status == TouchStatus.SCHEDULED and
                    touch.scheduled_at and
                    touch.scheduled_at <= now):

                    success = await self._send_touch(sequence, touch)
                    if success:
                        sent_count += 1

                    # Si c'était la dernière touche, marquer séquence complète
                    if touch.touch_number == len(sequence.touches):
                        sequence.completed_at = datetime.now(timezone.utc)
                        self.total_sequences_completed += 1
                        logger.info(f"Sequence {sequence.sequence_id} completed!")

        if sent_count > 0:
            logger.info(f"Processed {sent_count} scheduled touches")

        return sent_count

    async def handle_reply(self, sequence_id: str, reply_text: str, reply_channel: TouchChannel) -> Dict[str, Any]:
        """
        Gère une réponse d'un prospect

        Args:
            sequence_id: ID de la séquence
            reply_text: Texte de la réponse
            reply_channel: Canal de réponse (email, linkedin, etc.)

        Returns:
            Analyse de la réponse et action recommandée
        """
        if sequence_id not in self.active_sequences:
            logger.error(f"Sequence {sequence_id} not found for reply handling")
            return {'error': 'Sequence not found'}

        sequence = self.active_sequences[sequence_id]
        sequence.replies += 1
        self.total_replies_received += 1

        logger.info(f"Reply received for sequence {sequence_id} from {sequence.prospect_name}")

        # Analyser le sentiment de la réponse
        sentiment = self._analyze_reply_sentiment(reply_text)

        result = {
            'sequence_id': sequence_id,
            'prospect_name': sequence.prospect_name,
            'reply_text': reply_text,
            'reply_channel': reply_channel.value,
            'sentiment': sentiment,
            'action': None
        }

        if sentiment == 'positive':
            # Réponse positive → déclencher meeting booking
            result['action'] = 'book_meeting'
            result['message'] = f"Positive reply from {sequence.prospect_name} - trigger meeting booking"
            # Pause la séquence
            sequence.paused = True
            logger.info(f"Sequence {sequence_id} paused - positive reply received")

        elif sentiment == 'negative':
            # Réponse négative → passer au CloserAgent pour gestion d'objection
            result['action'] = 'handle_objection'
            result['message'] = f"Negative reply from {sequence.prospect_name} - send to CloserAgent"
            sequence.paused = True

        else:
            # Réponse neutre → continuer la séquence
            result['action'] = 'continue_sequence'
            result['message'] = f"Neutral reply from {sequence.prospect_name} - continue sequence"

        return result

    def _analyze_reply_sentiment(self, reply_text: str) -> str:
        """
        Analyse basique du sentiment de réponse

        Args:
            reply_text: Texte de la réponse

        Returns:
            'positive', 'negative', ou 'neutral'
        """
        reply_lower = reply_text.lower()

        # Mots-clés positifs
        positive_keywords = ['intéressé', 'interested', 'oui', 'yes', 'ok', 'rendez-vous', 'meeting',
                           'discuter', 'discuss', 'appel', 'call', 'quand', 'when']

        # Mots-clés négatifs
        negative_keywords = ['non', 'no', 'pas intéressé', 'not interested', 'stop', 'unsubscribe',
                           'jamais', 'never', 'déjà', 'already']

        positive_score = sum(1 for kw in positive_keywords if kw in reply_lower)
        negative_score = sum(1 for kw in negative_keywords if kw in reply_lower)

        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'

    def pause_sequence(self, sequence_id: str) -> bool:
        """Pause une séquence"""
        if sequence_id in self.active_sequences:
            self.active_sequences[sequence_id].paused = True
            logger.info(f"Sequence {sequence_id} paused")
            return True
        return False

    def resume_sequence(self, sequence_id: str) -> bool:
        """Reprend une séquence en pause"""
        if sequence_id in self.active_sequences:
            self.active_sequences[sequence_id].paused = False
            logger.info(f"Sequence {sequence_id} resumed")
            return True
        return False

    def stop_sequence(self, sequence_id: str) -> bool:
        """Arrête définitivement une séquence"""
        if sequence_id in self.active_sequences:
            sequence = self.active_sequences[sequence_id]
            sequence.paused = True
            sequence.completed_at = datetime.now(timezone.utc)
            logger.info(f"Sequence {sequence_id} stopped")
            return True
        return False

    def get_sequence_status(self, sequence_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le statut complet d'une séquence"""
        if sequence_id in self.active_sequences:
            return self.active_sequences[sequence_id].to_dict()
        return None

    def get_all_active_sequences(self) -> List[Dict[str, Any]]:
        """Retourne toutes les séquences actives"""
        return [seq.to_dict() for seq in self.active_sequences.values()
                if not seq.completed_at and not seq.paused]

    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques globales du moteur"""
        active_count = len([s for s in self.active_sequences.values()
                          if not s.completed_at and not s.paused])
        paused_count = len([s for s in self.active_sequences.values()
                          if s.paused and not s.completed_at])

        return {
            'total_sequences_created': self.total_sequences_created,
            'total_sequences_completed': self.total_sequences_completed,
            'sequences_active': active_count,
            'sequences_paused': paused_count,
            'total_touches_sent': self.total_touches_sent,
            'total_replies_received': self.total_replies_received,
            'reply_rate': (self.total_replies_received / self.total_touches_sent * 100)
                         if self.total_touches_sent > 0 else 0.0
        }

    def _generate_sequence_id(self, prospect_id: str) -> str:
        """Génère un ID unique pour une séquence"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{prospect_id}_{timestamp}"
        return f"SEQ_{hashlib.sha256(data.encode()).hexdigest()[:12].upper()}"


__all__ = ['SequenceEngine', 'TouchPoint', 'Sequence', 'TouchChannel', 'TouchStatus']
