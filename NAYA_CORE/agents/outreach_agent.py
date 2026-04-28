"""
NAYA CORE — AGENT 4 — OUTREACH AGENT
Orchestration complète des séquences multi-touch automatisées
7 touches sur 21 jours (J0, J2, J5, J8, J12, J16, J21)
Canaux: Email (SendGrid), LinkedIn, WhatsApp Business, Video
Réponse positive → meeting_booker | Réponse négative → closer_agent | Silence → ZeroWasteEngine
"""

import asyncio
import logging
import hashlib
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

logger = logging.getLogger(__name__)


# Plancher minimum absolu NAYA SUPREME (INVIOLABLE)
MIN_CONTRACT_VALUE_EUR = 1000


class SequenceStatus(Enum):
    """Status d'une séquence outreach"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    POSITIVE_REPLY = "positive_reply"
    NEGATIVE_REPLY = "negative_reply"


class OutreachChannel(Enum):
    """Canaux d'outreach disponibles"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    VIDEO = "video"
    SMS = "sms"
    TELEGRAM = "telegram"


@dataclass
class ProspectOutreach:
    """Données d'un prospect en outreach"""
    prospect_id: str
    sequence_id: str

    # Identité prospect
    name: str
    email: str
    company: str
    sector: str
    decision_maker_title: str

    # Contexte
    pain_description: str
    budget_estimate_eur: Decimal
    pain_signals: List[str] = field(default_factory=list)

    # Offre associée
    offer_title: str = ""
    offer_price_eur: Decimal = Decimal('0')
    offer_description: str = ""

    # LinkedIn / WhatsApp
    linkedin_profile: Optional[str] = None
    phone_number: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: SequenceStatus = SequenceStatus.PENDING

    # Séquence
    current_touch: int = 0
    touches_sent: int = 0
    last_touch_at: Optional[datetime] = None
    next_touch_at: Optional[datetime] = None

    # Engagement
    emails_opened: int = 0
    emails_clicked: int = 0
    replies_received: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire"""
        return {
            'prospect_id': self.prospect_id,
            'sequence_id': self.sequence_id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'sector': self.sector,
            'decision_maker_title': self.decision_maker_title,
            'pain_description': self.pain_description,
            'budget_estimate_eur': float(self.budget_estimate_eur),
            'pain_signals': self.pain_signals,
            'offer_title': self.offer_title,
            'offer_price_eur': float(self.offer_price_eur),
            'offer_description': self.offer_description,
            'linkedin_profile': self.linkedin_profile,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'current_touch': self.current_touch,
            'touches_sent': self.touches_sent,
            'last_touch_at': self.last_touch_at.isoformat() if self.last_touch_at else None,
            'next_touch_at': self.next_touch_at.isoformat() if self.next_touch_at else None,
            'emails_opened': self.emails_opened,
            'emails_clicked': self.emails_clicked,
            'replies_received': self.replies_received
        }


class OutreachAgent:
    """
    Agent 4 — Outreach Orchestrator

    Capacités:
    - Orchestration séquences 7 touches (J0, J2, J5, J8, J12, J16, J21)
    - Multi-canal: Email, LinkedIn, WhatsApp, Video
    - Personnalisation IA niveau individuel
    - Tracking engagement (opens, clicks, replies)
    - Routing intelligent réponses (positive → meeting_booker, négative → closer_agent)
    - Intégration ZeroWasteEngine pour silence total
    - Validation plancher 1000 EUR sur toutes les offres

    Séquence obligatoire:
    - Touch 1 (J0): Email personnalisé accroche signal détecté
    - Touch 2 (J2): LinkedIn connection + message court
    - Touch 3 (J5): Email 2 angle valeur (cas anonymisé)
    - Touch 4 (J8): LinkedIn message question ouverte
    - Touch 5 (J12): Email 3 objection anticipée + preuve sociale
    - Touch 6 (J16): Video message 60s (Loom automatisé)
    - Touch 7 (J21): Email final fermeture bienveillante
    """

    # Séquence standard 7 touches (jours de décalage depuis J0)
    SEQUENCE_DAYS = [0, 2, 5, 8, 12, 16, 21]

    # Canaux par touche
    SEQUENCE_CHANNELS = [
        OutreachChannel.EMAIL,      # Touch 1
        OutreachChannel.LINKEDIN,   # Touch 2
        OutreachChannel.EMAIL,      # Touch 3
        OutreachChannel.LINKEDIN,   # Touch 4
        OutreachChannel.EMAIL,      # Touch 5
        OutreachChannel.VIDEO,      # Touch 6
        OutreachChannel.EMAIL       # Touch 7
    ]

    def __init__(self,
                 sequence_engine=None,
                 email_personalizer=None,
                 reply_handler=None,
                 meeting_booker=None,
                 closer_agent=None,
                 linkedin_messenger=None,
                 whatsapp_agent=None,
                 video_generator=None,
                 zero_waste_engine=None,
                 telegram_notifier=None,
                 persistence_manager=None):
        """
        Initialise l'Outreach Agent

        Args:
            sequence_engine: Moteur séquences (OUTREACH/sequence_engine.py)
            email_personalizer: Personnalisateur emails IA (OUTREACH/email_personalizer.py)
            reply_handler: Gestionnaire réponses (OUTREACH/reply_handler.py)
            meeting_booker: Service booking RDV (OUTREACH/meeting_booker.py)
            closer_agent: Agent closing (agents/closer_advanced.py)
            linkedin_messenger: Service LinkedIn (OUTREACH/linkedin_messenger.py)
            whatsapp_agent: Service WhatsApp (OUTREACH/whatsapp_agent.py)
            video_generator: Générateur vidéos Loom
            zero_waste_engine: Moteur recyclage contenu
            telegram_notifier: Notifications Telegram
            persistence_manager: Persistance données
        """
        self.sequence_engine = sequence_engine
        self.email_personalizer = email_personalizer
        self.reply_handler = reply_handler
        self.meeting_booker = meeting_booker
        self.closer_agent = closer_agent
        self.linkedin_messenger = linkedin_messenger
        self.whatsapp_agent = whatsapp_agent
        self.video_generator = video_generator
        self.zero_waste_engine = zero_waste_engine
        self.telegram_notifier = telegram_notifier
        self.persistence_manager = persistence_manager

        # Prospects en outreach actifs
        self.active_prospects: Dict[str, ProspectOutreach] = {}

        # Métriques globales
        self.total_sequences_started = 0
        self.total_sequences_completed = 0
        self.total_touches_sent = 0
        self.total_replies_received = 0
        self.total_meetings_booked = 0
        self.total_positive_replies = 0
        self.total_negative_replies = 0

        logger.info("OutreachAgent initialized")

    async def start_outreach_sequence(self,
                                     prospect_data: Dict[str, Any],
                                     offer_data: Dict[str, Any]) -> ProspectOutreach:
        """
        Démarre une séquence outreach complète pour un prospect

        Args:
            prospect_data: Données du prospect (id, name, email, company, sector, pain_description, etc.)
            offer_data: Données de l'offre (title, price_eur, description, deliverables)

        Returns:
            ProspectOutreach créé et séquence démarrée
        """
        logger.info(f"Starting outreach sequence for {prospect_data.get('company')} - {offer_data.get('price_eur')} EUR")

        # 1. VALIDATION PLANCHER 1000 EUR (RÈGLE ABSOLUE)
        offer_price = Decimal(str(offer_data.get('price_eur', 0)))
        if offer_price < MIN_CONTRACT_VALUE_EUR:
            error_msg = f"VIOLATION PLANCHER: Prix offre {offer_price} EUR < minimum {MIN_CONTRACT_VALUE_EUR} EUR"
            logger.error(error_msg)
            if self.telegram_notifier:
                await self.telegram_notifier.send(f"⚠️ {error_msg}")
            raise ValueError(error_msg)

        # 2. Créer ProspectOutreach
        prospect_id = prospect_data.get('id', self._generate_prospect_id(prospect_data.get('email', '')))
        sequence_id = self._generate_sequence_id(prospect_id)

        prospect_outreach = ProspectOutreach(
            prospect_id=prospect_id,
            sequence_id=sequence_id,
            name=prospect_data.get('name', ''),
            email=prospect_data.get('email', ''),
            company=prospect_data.get('company', ''),
            sector=prospect_data.get('sector', ''),
            decision_maker_title=prospect_data.get('decision_maker_title', 'Décideur'),
            pain_description=prospect_data.get('pain_description', ''),
            budget_estimate_eur=Decimal(str(prospect_data.get('budget_estimate_eur', 0))),
            pain_signals=prospect_data.get('pain_signals', []),
            offer_title=offer_data.get('title', ''),
            offer_price_eur=offer_price,
            offer_description=offer_data.get('description', ''),
            linkedin_profile=prospect_data.get('linkedin_profile'),
            phone_number=prospect_data.get('phone_number'),
            status=SequenceStatus.PENDING
        )

        # 3. Enregistrer en mémoire
        self.active_prospects[prospect_id] = prospect_outreach

        # 4. Créer la séquence dans le SequenceEngine si disponible
        if self.sequence_engine:
            sequence_data = {
                'name': prospect_outreach.name,
                'email': prospect_outreach.email,
                'company': prospect_outreach.company,
                'sector': prospect_outreach.sector,
                'context': {
                    'pain_description': prospect_outreach.pain_description,
                    'pain_signals': prospect_outreach.pain_signals,
                    'offer_title': prospect_outreach.offer_title,
                    'offer_price_eur': float(prospect_outreach.offer_price_eur),
                    'decision_maker_title': prospect_outreach.decision_maker_title,
                    'budget_estimate_eur': float(prospect_outreach.budget_estimate_eur)
                }
            }

            sequence = self.sequence_engine.create_sequence(
                prospect_id=prospect_id,
                prospect_data=sequence_data
            )

            # Démarrer la séquence (envoie Touch 1 immédiatement)
            started = await self.sequence_engine.start_sequence(sequence_id)

            if started:
                prospect_outreach.status = SequenceStatus.ACTIVE
                prospect_outreach.current_touch = 1
                prospect_outreach.touches_sent = 1
                prospect_outreach.last_touch_at = datetime.now(timezone.utc)
                prospect_outreach.next_touch_at = datetime.now(timezone.utc) + timedelta(days=self.SEQUENCE_DAYS[1])
                self.total_sequences_started += 1
                self.total_touches_sent += 1
                logger.info(f"Sequence {sequence_id} started for {prospect_outreach.company}")
            else:
                logger.error(f"Failed to start sequence {sequence_id}")

        else:
            # Mode simulation sans SequenceEngine
            logger.warning("SequenceEngine not configured, simulating sequence start")
            prospect_outreach.status = SequenceStatus.ACTIVE
            prospect_outreach.current_touch = 1
            prospect_outreach.touches_sent = 1
            prospect_outreach.last_touch_at = datetime.now(timezone.utc)
            prospect_outreach.next_touch_at = datetime.now(timezone.utc) + timedelta(days=self.SEQUENCE_DAYS[1])
            self.total_sequences_started += 1
            self.total_touches_sent += 1

        # 5. Notification Telegram si configuré
        if self.telegram_notifier:
            await self._notify_sequence_started(prospect_outreach)

        # 6. Persister si disponible
        if self.persistence_manager:
            await self.persistence_manager.save_prospect_outreach(prospect_id, prospect_outreach.to_dict())

        logger.info(f"Outreach sequence started: {sequence_id} for {prospect_outreach.company} - {offer_price} EUR")

        return prospect_outreach

    async def process_scheduled_touches(self) -> int:
        """
        Traite toutes les touches planifiées dont l'heure est arrivée

        Appelé automatiquement par le scheduler toutes les 30 minutes

        Returns:
            Nombre de touches envoyées
        """
        if self.sequence_engine:
            # Utiliser le SequenceEngine pour traiter les touches
            sent_count = await self.sequence_engine.process_scheduled_touches()
            self.total_touches_sent += sent_count
            return sent_count
        else:
            # Mode simulation
            now = datetime.now(timezone.utc)
            sent_count = 0

            for prospect in self.active_prospects.values():
                if prospect.status != SequenceStatus.ACTIVE:
                    continue

                if prospect.next_touch_at and prospect.next_touch_at <= now:
                    # Envoyer la prochaine touche
                    success = await self._send_next_touch_simulated(prospect)
                    if success:
                        sent_count += 1

            return sent_count

    async def handle_reply(self,
                          prospect_id: str,
                          reply_text: str,
                          reply_channel: str = 'email') -> Dict[str, Any]:
        """
        Gère une réponse d'un prospect

        Args:
            prospect_id: ID du prospect
            reply_text: Texte de la réponse
            reply_channel: Canal de réponse ('email', 'linkedin', 'whatsapp')

        Returns:
            Résultat du traitement (action, sentiment, etc.)
        """
        if prospect_id not in self.active_prospects:
            logger.error(f"Prospect {prospect_id} not found in active prospects")
            return {'error': 'Prospect not found'}

        prospect = self.active_prospects[prospect_id]
        prospect.replies_received += 1
        self.total_replies_received += 1

        logger.info(f"Reply received from {prospect.name} ({prospect.company}): {reply_text[:100]}...")

        # 1. Analyser la réponse avec ReplyHandler si disponible
        if self.reply_handler:
            reply_analysis = await self.reply_handler.analyze_reply(
                prospect_id=prospect_id,
                prospect_name=prospect.name,
                prospect_email=prospect.email,
                reply_text=reply_text,
                reply_channel=reply_channel
            )

            reply_type = reply_analysis.get('reply_type')
            reply_action = reply_analysis.get('reply_action')
        else:
            # Analyse simple basée sur mots-clés
            reply_type, reply_action = self._analyze_reply_simple(reply_text)

        result = {
            'prospect_id': prospect_id,
            'prospect_name': prospect.name,
            'company': prospect.company,
            'reply_text': reply_text,
            'reply_channel': reply_channel,
            'reply_type': reply_type,
            'reply_action': reply_action,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # 2. Router selon le type de réponse

        if reply_action == 'book_meeting':
            # Réponse positive → meeting_booker
            logger.info(f"Positive reply from {prospect.name} - booking meeting")
            prospect.status = SequenceStatus.POSITIVE_REPLY
            self.total_positive_replies += 1

            # Pause la séquence
            if self.sequence_engine:
                self.sequence_engine.pause_sequence(prospect.sequence_id)

            # Déclencher le meeting booker si disponible
            if self.meeting_booker:
                meeting = self.meeting_booker.create_booking_link(
                    prospect_id=prospect_id,
                    company=prospect.company,
                    contact_name=prospect.name,
                    contact_email=prospect.email,
                    sector=prospect.sector,
                    deal_value_eur=int(prospect.offer_price_eur),
                    prospect_context=prospect.pain_description
                )
                result['meeting'] = {
                    'meeting_id': meeting.meeting_id,
                    'booking_url': meeting.booking_url,
                    'status': meeting.status
                }
                self.total_meetings_booked += 1
                logger.info(f"Meeting created: {meeting.meeting_id} - {meeting.booking_url}")

            # Notification Telegram
            if self.telegram_notifier:
                await self.telegram_notifier.send(
                    f"🎉 RÉPONSE POSITIVE - {prospect.company}\n\n"
                    f"Prospect: {prospect.name}\n"
                    f"Email: {prospect.email}\n"
                    f"Deal: {prospect.offer_price_eur} EUR\n\n"
                    f"Action: Meeting booking déclenché"
                )

        elif reply_action == 'handle_objection':
            # Réponse négative / objection → closer_agent
            logger.info(f"Objection from {prospect.name} - forwarding to CloserAgent")
            prospect.status = SequenceStatus.NEGATIVE_REPLY
            self.total_negative_replies += 1

            # Pause la séquence temporairement
            if self.sequence_engine:
                self.sequence_engine.pause_sequence(prospect.sequence_id)

            # Passer au closer_agent si disponible
            if self.closer_agent:
                closer_response = await self.closer_agent.handle_objection(
                    prospect_id=prospect_id,
                    prospect_data=prospect.to_dict(),
                    objection_text=reply_text,
                    offer_data={
                        'title': prospect.offer_title,
                        'price_eur': float(prospect.offer_price_eur),
                        'description': prospect.offer_description
                    }
                )
                result['closer_response'] = closer_response

            # Notification Telegram
            if self.telegram_notifier:
                await self.telegram_notifier.send(
                    f"⚠️ OBJECTION - {prospect.company}\n\n"
                    f"Prospect: {prospect.name}\n"
                    f"Réponse: {reply_text[:200]}\n\n"
                    f"Action: Transféré au CloserAgent"
                )

        elif reply_action == 'stop_sequence':
            # Pas intéressé → arrêter la séquence
            logger.info(f"Stop request from {prospect.name} - stopping sequence")
            prospect.status = SequenceStatus.STOPPED

            if self.sequence_engine:
                self.sequence_engine.stop_sequence(prospect.sequence_id)

            # Recycler le contenu si ZeroWasteEngine disponible
            if self.zero_waste_engine:
                await self.zero_waste_engine.recycle_failed_outreach(prospect.to_dict())

        else:
            # Réponse neutre → continuer la séquence
            logger.info(f"Neutral reply from {prospect.name} - continuing sequence")
            result['action'] = 'continue_sequence'

        # 3. Persister
        if self.persistence_manager:
            await self.persistence_manager.save_prospect_outreach(prospect_id, prospect.to_dict())
            await self.persistence_manager.save_reply(prospect_id, result)

        return result

    async def track_email_opened(self, prospect_id: str) -> bool:
        """Track qu'un email a été ouvert"""
        if prospect_id in self.active_prospects:
            self.active_prospects[prospect_id].emails_opened += 1
            logger.info(f"Email opened by {self.active_prospects[prospect_id].name}")
            return True
        return False

    async def track_email_clicked(self, prospect_id: str) -> bool:
        """Track qu'un lien dans l'email a été cliqué"""
        if prospect_id in self.active_prospects:
            self.active_prospects[prospect_id].emails_clicked += 1
            logger.info(f"Email link clicked by {self.active_prospects[prospect_id].name}")
            return True
        return False

    async def pause_sequence(self, prospect_id: str) -> bool:
        """Pause une séquence outreach"""
        if prospect_id in self.active_prospects:
            prospect = self.active_prospects[prospect_id]
            prospect.status = SequenceStatus.PAUSED

            if self.sequence_engine:
                self.sequence_engine.pause_sequence(prospect.sequence_id)

            logger.info(f"Sequence paused for {prospect.name}")
            return True
        return False

    async def resume_sequence(self, prospect_id: str) -> bool:
        """Reprend une séquence en pause"""
        if prospect_id in self.active_prospects:
            prospect = self.active_prospects[prospect_id]
            prospect.status = SequenceStatus.ACTIVE

            if self.sequence_engine:
                self.sequence_engine.resume_sequence(prospect.sequence_id)

            logger.info(f"Sequence resumed for {prospect.name}")
            return True
        return False

    async def handle_silence_timeout(self, prospect_id: str) -> Dict[str, Any]:
        """
        Gère les prospects qui n'ont pas répondu après la séquence complète

        Déclenche le ZeroWasteEngine pour recycler le contenu

        Args:
            prospect_id: ID du prospect silencieux

        Returns:
            Résultat du recyclage
        """
        if prospect_id not in self.active_prospects:
            return {'error': 'Prospect not found'}

        prospect = self.active_prospects[prospect_id]

        logger.info(f"Silence timeout for {prospect.name} ({prospect.company}) - recycling content")

        # Marquer comme complété
        prospect.status = SequenceStatus.COMPLETED
        self.total_sequences_completed += 1

        # Recycler via ZeroWasteEngine si disponible
        result = {'prospect_id': prospect_id, 'recycled': False}

        if self.zero_waste_engine:
            recycled = await self.zero_waste_engine.recycle_silent_prospect(
                prospect_data=prospect.to_dict(),
                touches_sent=prospect.touches_sent,
                engagement={
                    'emails_opened': prospect.emails_opened,
                    'emails_clicked': prospect.emails_clicked
                }
            )
            result['recycled'] = True
            result['recycled_assets'] = recycled

        return result

    def get_prospect(self, prospect_id: str) -> Optional[ProspectOutreach]:
        """Récupère un prospect"""
        return self.active_prospects.get(prospect_id)

    def get_all_active_sequences(self) -> List[ProspectOutreach]:
        """Retourne tous les prospects avec séquences actives"""
        return [
            p for p in self.active_prospects.values()
            if p.status == SequenceStatus.ACTIVE
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'agent"""
        active = len([p for p in self.active_prospects.values() if p.status == SequenceStatus.ACTIVE])
        paused = len([p for p in self.active_prospects.values() if p.status == SequenceStatus.PAUSED])
        positive = len([p for p in self.active_prospects.values() if p.status == SequenceStatus.POSITIVE_REPLY])
        negative = len([p for p in self.active_prospects.values() if p.status == SequenceStatus.NEGATIVE_REPLY])

        reply_rate = (self.total_replies_received / self.total_touches_sent * 100) if self.total_touches_sent > 0 else 0
        positive_rate = (self.total_positive_replies / self.total_replies_received * 100) if self.total_replies_received > 0 else 0

        return {
            'total_sequences_started': self.total_sequences_started,
            'total_sequences_completed': self.total_sequences_completed,
            'sequences_active': active,
            'sequences_paused': paused,
            'sequences_positive_reply': positive,
            'sequences_negative_reply': negative,
            'total_touches_sent': self.total_touches_sent,
            'total_replies_received': self.total_replies_received,
            'total_meetings_booked': self.total_meetings_booked,
            'total_positive_replies': self.total_positive_replies,
            'total_negative_replies': self.total_negative_replies,
            'reply_rate_pct': round(reply_rate, 2),
            'positive_rate_pct': round(positive_rate, 2)
        }

    # ─── MÉTHODES PRIVÉES ───────────────────────────────────────────────────

    def _generate_prospect_id(self, email: str) -> str:
        """Génère un ID unique pour un prospect"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{email}_{timestamp}"
        return f"PROS_{hashlib.sha256(data.encode()).hexdigest()[:12].upper()}"

    def _generate_sequence_id(self, prospect_id: str) -> str:
        """Génère un ID unique pour une séquence"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{prospect_id}_{timestamp}"
        return f"SEQ_{hashlib.sha256(data.encode()).hexdigest()[:12].upper()}"

    async def _notify_sequence_started(self, prospect: ProspectOutreach) -> None:
        """Envoie une notification Telegram de démarrage de séquence"""
        if not self.telegram_notifier:
            return

        message = (
            f"🚀 SÉQUENCE OUTREACH DÉMARRÉE\n\n"
            f"🏢 Entreprise: {prospect.company}\n"
            f"👤 Contact: {prospect.name} ({prospect.decision_maker_title})\n"
            f"📧 Email: {prospect.email}\n"
            f"🎯 Secteur: {prospect.sector}\n\n"
            f"💰 Offre: {prospect.offer_title}\n"
            f"💵 Prix: {prospect.offer_price_eur} EUR\n\n"
            f"📊 Séquence: 7 touches sur 21 jours\n"
            f"📅 Prochaine touche: J+2 ({(datetime.now(timezone.utc) + timedelta(days=2)).strftime('%d/%m/%Y')})\n\n"
            f"🔥 Pain détecté: {prospect.pain_description[:150]}..."
        )

        await self.telegram_notifier.send(message)

    def _analyze_reply_simple(self, reply_text: str) -> tuple:
        """
        Analyse simple d'une réponse (sans ReplyHandler)

        Returns:
            (reply_type, reply_action)
        """
        reply_lower = reply_text.lower()

        # Positif
        positive_keywords = ['intéressé', 'interested', 'oui', 'yes', 'ok', 'rendez-vous', 'meeting', 'appel']
        if any(kw in reply_lower for kw in positive_keywords):
            return ('positive', 'book_meeting')

        # Négatif / Stop
        negative_keywords = ['non', 'no', 'pas intéressé', 'not interested', 'stop', 'unsubscribe']
        if any(kw in reply_lower for kw in negative_keywords):
            return ('negative', 'stop_sequence')

        # Objection
        objection_keywords = ['cher', 'expensive', 'budget', 'prix', 'déjà', 'already', 'temps', 'time']
        if any(kw in reply_lower for kw in objection_keywords):
            return ('objection', 'handle_objection')

        # Neutre
        return ('neutral', 'continue_sequence')

    async def _send_next_touch_simulated(self, prospect: ProspectOutreach) -> bool:
        """
        Envoie la prochaine touche en mode simulation (sans SequenceEngine)

        Args:
            prospect: ProspectOutreach

        Returns:
            True si succès, False sinon
        """
        next_touch = prospect.current_touch + 1

        if next_touch > 7:
            # Séquence terminée
            prospect.status = SequenceStatus.COMPLETED
            self.total_sequences_completed += 1
            logger.info(f"Sequence completed for {prospect.name}")

            # Déclencher recyclage silence
            await self.handle_silence_timeout(prospect.prospect_id)
            return True

        # Simuler l'envoi
        logger.info(f"Sending touch {next_touch} to {prospect.name} ({prospect.company})")

        prospect.current_touch = next_touch
        prospect.touches_sent += 1
        prospect.last_touch_at = datetime.now(timezone.utc)

        # Planifier la prochaine touche si pas la dernière
        if next_touch < 7:
            prospect.next_touch_at = datetime.now(timezone.utc) + timedelta(days=self.SEQUENCE_DAYS[next_touch])
        else:
            prospect.next_touch_at = None

        self.total_touches_sent += 1

        return True


    # ------------------------------------------------------------------
    # V19.3 — Cycle unifié pour le multi_agent_orchestrator
    # ------------------------------------------------------------------
    async def run_cycle(self, prospects: List[Dict[str, Any]] = None,
                        offers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cycle complet d'outreach appelé par multi_agent_orchestrator.

        1. Démarre les séquences pour les nouveaux prospects
        2. Traite les touches programmées
        3. Retourne les métriques
        """
        prospects = prospects or []
        offers = offers or []

        started = 0
        errors = 0

        # Démarrer les séquences pour chaque prospect fourni
        for i, p in enumerate(prospects):
            try:
                offer = offers[i] if i < len(offers) else {
                    'price_eur': max(MIN_CONTRACT_VALUE_EUR, p.get('budget_estimate_eur', 5000)),
                    'title': p.get('offer_title', 'NAYA Solution'),
                    'pain_point': p.get('pain_point', ''),
                }
                await self.start_outreach_sequence(p, offer)
                started += 1
            except Exception as exc:
                errors += 1
                logger.warning(f"[outreach_agent] start failed: {exc}")

        # Traiter les touches planifiées
        touches_processed = 0
        try:
            touches_processed = await self.process_scheduled_touches()
        except Exception as exc:
            errors += 1
            logger.warning(f"[outreach_agent] process touches failed: {exc}")

        return {
            'total_started': started,
            'total_touches_processed': touches_processed,
            'total_active': len(self.active_prospects),
            'total_sequences_started': self.total_sequences_started,
            'total_sequences_completed': self.total_sequences_completed,
            'total_touches_sent': self.total_touches_sent,
            'total_positive_replies': self.total_positive_replies,
            'total_revenue_cycle': sum(
                (p.offer_price_eur if hasattr(p, 'offer_price_eur') else 0)
                for p in self.active_prospects.values()
                if p.status == SequenceStatus.POSITIVE_REPLY
            ),
            'errors': errors,
        }


# ---------------------------------------------------------------------------
# Singleton partagé utilisé par l'orchestrateur et les bridges de compat
# ---------------------------------------------------------------------------
def _build_outreach_agent() -> "OutreachAgent":
    """Construit l'instance avec les vraies dépendances disponibles."""
    telegram_notifier = None
    persistence_manager = None

    try:  # Telegram réel (si configuré)
        from NAYA_CORE.notifier import get_notifier
        telegram_notifier = get_notifier()
    except Exception:
        pass

    try:  # Persistance réelle (SQLite WAL)
        from PERSISTENCE.database.db_manager import DatabaseManager
        persistence_manager = DatabaseManager()
    except Exception:
        pass

    return OutreachAgent(
        telegram_notifier=telegram_notifier,
        persistence_manager=persistence_manager,
    )


outreach_agent = _build_outreach_agent()


__all__ = [
    'OutreachAgent',
    'ProspectOutreach',
    'SequenceStatus',
    'OutreachChannel',
    'MIN_CONTRACT_VALUE_EUR',
    'outreach_agent',
]
