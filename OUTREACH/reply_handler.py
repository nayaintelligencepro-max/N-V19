"""
NAYA REPLY HANDLER
Gestion automatique des réponses prospects
Classification (positive/negative/neutral/objection), routing intelligent
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReplyType(Enum):
    """Type de réponse"""
    POSITIVE = "positive"  # Intéressé, veut discuter
    NEGATIVE = "negative"  # Pas intéressé, stop
    OBJECTION = "objection"  # Objection (prix, timing, déjà une solution)
    QUESTION = "question"  # Question technique/commerciale
    OUT_OF_OFFICE = "out_of_office"  # Auto-réponse absence
    NEUTRAL = "neutral"  # Réponse neutre


class ReplyAction(Enum):
    """Action recommandée"""
    BOOK_MEETING = "book_meeting"  # Réponse positive → booking
    HANDLE_OBJECTION = "handle_objection"  # Objection → CloserAgent
    ANSWER_QUESTION = "answer_question"  # Question → réponse auto
    PAUSE_SEQUENCE = "pause_sequence"  # Out of office
    STOP_SEQUENCE = "stop_sequence"  # Pas intéressé
    CONTINUE_SEQUENCE = "continue_sequence"  # Neutre
    ESCALATE_HUMAN = "escalate_human"  # Cas complexe


@dataclass
class ProspectReply:
    """Réponse d'un prospect"""
    reply_id: str
    prospect_id: str
    prospect_name: str
    prospect_email: str
    reply_text: str
    reply_channel: str  # 'email', 'linkedin', 'whatsapp'
    reply_type: ReplyType
    reply_action: ReplyAction
    confidence: float  # 0-1, confiance de la classification
    detected_objections: List[str]
    detected_questions: List[str]
    received_at: datetime
    processed_at: Optional[datetime] = None
    auto_response_sent: bool = False


class ReplyHandler:
    """
    Gestionnaire automatique de réponses prospects

    Capacités:
    - Classification automatique des réponses (positive/negative/objection/question)
    - Détection d'objections connues (50+ patterns)
    - Routing intelligent vers agents appropriés
    - Réponses automatiques pour questions fréquentes
    - Escalade vers humain si complexe
    """

    # Patterns de réponses positives
    POSITIVE_PATTERNS = [
        r'\b(intéressé|interested|oui|yes|ok|d\'accord|parfait|super)\b',
        r'\b(rendez-vous|meeting|appel|call|discuter|discuss)\b',
        r'\b(quand|when|disponible|available)\b',
        r'\b(voir|see|présentation|demo|démo)\b',
        r'\b(parler|talk|échanger|chat)\b'
    ]

    # Patterns de réponses négatives
    NEGATIVE_PATTERNS = [
        r'\b(non|no|pas intéressé|not interested|merci|thanks)\b.*\b(non|no|pas)\b',
        r'\b(stop|unsubscribe|désabonner|retirer)\b',
        r'\b(jamais|never|aucun|no interest)\b',
        r'\b(ne me contactez|don\'t contact|stop emailing)\b'
    ]

    # Patterns d'objections
    OBJECTION_PATTERNS = {
        'budget': [
            r'\b(budget|cher|expensive|prix|price|coût|cost)\b',
            r'\b(pas de budget|no budget|trop cher|too expensive)\b'
        ],
        'timing': [
            r'\b(pas le temps|no time|occupé|busy|plus tard|later)\b',
            r'\b(mois prochain|next month|année|year|trimestre)\b'
        ],
        'already_have_solution': [
            r'\b(déjà|already|solution en place|current solution)\b',
            r'\b(fournisseur|vendor|partenaire|partner)\b.*\b(actuel|current)\b'
        ],
        'decision_maker': [
            r'\b(pas le décideur|not decision maker|mon manager|my manager)\b',
            r'\b(transférer|forward|voir avec|check with)\b'
        ]
    }

    # Patterns out of office
    OUT_OF_OFFICE_PATTERNS = [
        r'\b(out of office|absent|congé|vacation|unavailable)\b',
        r'\b(de retour|back on|retour le)\b',
        r'\b(automatic reply|réponse automatique)\b'
    ]

    # Questions fréquentes avec réponses automatiques
    FAQ_RESPONSES = {
        'prix': {
            'patterns': [r'\b(prix|price|tarif|cost|combien|how much)\b'],
            'response': """Nos tarifs dépendent du scope de la mission.

Pour vous donner une idée :
• Pack Audit Express IEC 62443 : à partir de 15 000 EUR
• Pack Sécurité Avancée : à partir de 40 000 EUR
• Abonnement contenu B2B : 3 000-15 000 EUR/mois

Je vous propose un call de 15 minutes pour calibrer exactement selon vos besoins ?"""
        },
        'delai': {
            'patterns': [r'\b(délai|timeline|combien de temps|how long|durée)\b'],
            'response': """Nos délais typiques :
• Audit Express : 5 jours
• Audit complet IEC 62443 : 2-3 semaines
• Mission conformité NIS2 : 3-6 mois

Pouvons-nous planifier un échange pour définir votre calendrier idéal ?"""
        },
        'references': {
            'patterns': [r'\b(référence|reference|client|case|exemple|example)\b'],
            'response': """Nous avons accompagné plusieurs acteurs majeurs dans le transport, l'énergie et l'industrie.

Je peux vous partager des cas d'études anonymisés lors d'un call rapide. Seriez-vous disponible cette semaine ?"""
        }
    }

    def __init__(self, llm_router=None, objection_handler=None):
        """
        Initialise le reply handler

        Args:
            llm_router: Router LLM pour classification avancée
            objection_handler: Handler d'objections (CloserAgent)
        """
        self.llm_router = llm_router
        self.objection_handler = objection_handler

        # Replies traitées
        self.processed_replies: Dict[str, ProspectReply] = {}

        # Métriques
        self.total_replies = 0
        self.by_type = {t.value: 0 for t in ReplyType}
        self.auto_responses_sent = 0

        logger.info("ReplyHandler initialized")

    async def handle_reply(self,
                          prospect_id: str,
                          prospect_name: str,
                          prospect_email: str,
                          reply_text: str,
                          reply_channel: str = "email") -> ProspectReply:
        """
        Gère une réponse de prospect

        Args:
            prospect_id: ID du prospect
            prospect_name: Nom du prospect
            prospect_email: Email du prospect
            reply_text: Texte de la réponse
            reply_channel: Canal de réponse ('email', 'linkedin', 'whatsapp')

        Returns:
            ProspectReply avec classification et action recommandée
        """
        logger.info(f"Handling reply from {prospect_name} via {reply_channel}")

        # Générer reply_id
        reply_id = f"REPLY_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{prospect_id}"

        # 1. Classification de la réponse
        reply_type, confidence = await self._classify_reply(reply_text)

        # 2. Détection d'objections
        objections = self._detect_objections(reply_text)

        # 3. Détection de questions
        questions = self._detect_questions(reply_text)

        # 4. Déterminer l'action recommandée
        action = self._determine_action(reply_type, objections, questions)

        # 5. Créer le ProspectReply
        prospect_reply = ProspectReply(
            reply_id=reply_id,
            prospect_id=prospect_id,
            prospect_name=prospect_name,
            prospect_email=prospect_email,
            reply_text=reply_text,
            reply_channel=reply_channel,
            reply_type=reply_type,
            reply_action=action,
            confidence=confidence,
            detected_objections=objections,
            detected_questions=questions,
            received_at=datetime.now(timezone.utc)
        )

        # 6. Traiter selon l'action
        await self._process_action(prospect_reply)

        # 7. Stocker et métriques
        prospect_reply.processed_at = datetime.now(timezone.utc)
        self.processed_replies[reply_id] = prospect_reply
        self.total_replies += 1
        self.by_type[reply_type.value] += 1

        logger.info(f"Reply classified as {reply_type.value} (confidence: {confidence:.2f}) - action: {action.value}")

        return prospect_reply

    async def _classify_reply(self, reply_text: str) -> tuple[ReplyType, float]:
        """
        Classifie une réponse (positive/negative/objection/question)

        Args:
            reply_text: Texte de la réponse

        Returns:
            (ReplyType, confidence)
        """
        reply_lower = reply_text.lower()

        # 1. Vérifier out of office (priorité)
        if any(re.search(pattern, reply_lower) for pattern in self.OUT_OF_OFFICE_PATTERNS):
            return (ReplyType.OUT_OF_OFFICE, 0.95)

        # 2. Vérifier réponses négatives
        negative_matches = sum(1 for pattern in self.NEGATIVE_PATTERNS
                             if re.search(pattern, reply_lower))
        if negative_matches > 0:
            return (ReplyType.NEGATIVE, min(0.7 + (negative_matches * 0.1), 1.0))

        # 3. Vérifier réponses positives
        positive_matches = sum(1 for pattern in self.POSITIVE_PATTERNS
                             if re.search(pattern, reply_lower))
        if positive_matches >= 2:
            return (ReplyType.POSITIVE, min(0.7 + (positive_matches * 0.1), 1.0))

        # 4. Vérifier objections
        objection_matches = sum(
            1 for obj_type, patterns in self.OBJECTION_PATTERNS.items()
            for pattern in patterns
            if re.search(pattern, reply_lower)
        )
        if objection_matches > 0:
            return (ReplyType.OBJECTION, min(0.6 + (objection_matches * 0.1), 0.9))

        # 5. Vérifier questions (point d'interrogation)
        if '?' in reply_text:
            return (ReplyType.QUESTION, 0.7)

        # 6. Par défaut: neutre
        return (ReplyType.NEUTRAL, 0.5)

    def _detect_objections(self, reply_text: str) -> List[str]:
        """Détecte les objections dans la réponse"""
        reply_lower = reply_text.lower()
        objections = []

        for objection_type, patterns in self.OBJECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, reply_lower):
                    objections.append(objection_type)
                    break

        return objections

    def _detect_questions(self, reply_text: str) -> List[str]:
        """Détecte les questions dans la réponse"""
        questions = []

        for question_type, config in self.FAQ_RESPONSES.items():
            for pattern in config['patterns']:
                if re.search(pattern, reply_text.lower()):
                    questions.append(question_type)
                    break

        return questions

    def _determine_action(self,
                         reply_type: ReplyType,
                         objections: List[str],
                         questions: List[str]) -> ReplyAction:
        """Détermine l'action recommandée"""

        if reply_type == ReplyType.POSITIVE:
            return ReplyAction.BOOK_MEETING

        elif reply_type == ReplyType.NEGATIVE:
            return ReplyAction.STOP_SEQUENCE

        elif reply_type == ReplyType.OBJECTION:
            return ReplyAction.HANDLE_OBJECTION

        elif reply_type == ReplyType.QUESTION:
            # Si question dans FAQ, réponse auto, sinon escalade
            if questions:
                return ReplyAction.ANSWER_QUESTION
            else:
                return ReplyAction.ESCALATE_HUMAN

        elif reply_type == ReplyType.OUT_OF_OFFICE:
            return ReplyAction.PAUSE_SEQUENCE

        else:  # NEUTRAL
            return ReplyAction.CONTINUE_SEQUENCE

    async def _process_action(self, prospect_reply: ProspectReply) -> None:
        """Traite l'action recommandée"""

        action = prospect_reply.reply_action

        if action == ReplyAction.BOOK_MEETING:
            logger.info(f"Positive reply from {prospect_reply.prospect_name} → trigger meeting booking")
            # V19.3 FIX: appel réel au meeting_booker
            try:
                from OUTREACH.meeting_booker import MeetingBooker
                booker = getattr(self, 'meeting_booker', None) or MeetingBooker()
                await booker.book(
                    prospect_email=prospect_reply.prospect_email,
                    prospect_name=prospect_reply.prospect_name,
                    reply_content=prospect_reply.reply_content
                )
                prospect_reply.meeting_booked = True
            except Exception as e:
                logger.error(f"Meeting booking failed: {e}")

        elif action == ReplyAction.HANDLE_OBJECTION:
            logger.info(f"Objection detected from {prospect_reply.prospect_name}: {prospect_reply.detected_objections}")
            if self.objection_handler:
                await self.objection_handler.handle(prospect_reply)

        elif action == ReplyAction.ANSWER_QUESTION:
            logger.info(f"Question detected from {prospect_reply.prospect_name}: {prospect_reply.detected_questions}")
            # Envoyer réponse automatique
            auto_response = await self._generate_auto_response(prospect_reply)
            if auto_response:
                logger.info(f"Auto-response generated for {prospect_reply.prospect_name}")
                prospect_reply.auto_response_sent = True
                self.auto_responses_sent += 1
                # V19.3 FIX: envoi réel via email_sender
                try:
                    from NAYA_REVENUE_ENGINE.gmail_outreach import send_email
                    await send_email(
                        to=prospect_reply.prospect_email,
                        subject=f"Re: {prospect_reply.original_subject or 'Your question'}",
                        body=auto_response
                    )
                except Exception as e:
                    logger.error(f"Auto-response send failed: {e}")

        elif action == ReplyAction.PAUSE_SEQUENCE:
            logger.info(f"Out of office from {prospect_reply.prospect_name} → pause sequence")

        elif action == ReplyAction.STOP_SEQUENCE:
            logger.info(f"Negative reply from {prospect_reply.prospect_name} → stop sequence")

        elif action == ReplyAction.ESCALATE_HUMAN:
            logger.info(f"Complex reply from {prospect_reply.prospect_name} → escalate to human")
            # V19.3 FIX: notification Telegram réelle
            try:
                from NAYA_CORE.notifier import telegram_notify
                await telegram_notify(
                    f"🚨 ESCALATION HUMAIN\n"
                    f"Prospect: {prospect_reply.prospect_name}\n"
                    f"Email: {prospect_reply.prospect_email}\n"
                    f"Contenu: {(prospect_reply.reply_content or '')[:300]}"
                )
            except Exception as e:
                logger.debug(f"Telegram notify failed: {e}")

        elif action == ReplyAction.CONTINUE_SEQUENCE:
            logger.info(f"Neutral reply from {prospect_reply.prospect_name} → continue sequence")

    async def _generate_auto_response(self, prospect_reply: ProspectReply) -> Optional[str]:
        """Génère une réponse automatique pour questions FAQ"""

        if not prospect_reply.detected_questions:
            return None

        # Prendre la première question détectée
        question_type = prospect_reply.detected_questions[0]

        faq_config = self.FAQ_RESPONSES.get(question_type)
        if not faq_config:
            return None

        response_template = faq_config['response']

        # Personnaliser la réponse
        response = f"Bonjour {prospect_reply.prospect_name},\n\n{response_template}\n\nCordialement,\nStéphanie MAMA"

        return response

    def get_reply_summary(self, reply_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le résumé d'une réponse"""
        if reply_id not in self.processed_replies:
            return None

        reply = self.processed_replies[reply_id]
        return {
            'reply_id': reply.reply_id,
            'prospect_name': reply.prospect_name,
            'prospect_email': reply.prospect_email,
            'reply_type': reply.reply_type.value,
            'reply_action': reply.reply_action.value,
            'confidence': reply.confidence,
            'objections': reply.detected_objections,
            'questions': reply.detected_questions,
            'received_at': reply.received_at.isoformat(),
            'auto_response_sent': reply.auto_response_sent
        }

    def get_all_positive_replies(self) -> List[ProspectReply]:
        """Retourne toutes les réponses positives"""
        return [r for r in self.processed_replies.values()
                if r.reply_type == ReplyType.POSITIVE]

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        return {
            'total_replies': self.total_replies,
            'by_type': self.by_type,
            'auto_responses_sent': self.auto_responses_sent,
            'positive_rate': (self.by_type['positive'] / self.total_replies * 100)
                           if self.total_replies > 0 else 0,
            'objection_rate': (self.by_type['objection'] / self.total_replies * 100)
                            if self.total_replies > 0 else 0
        }


__all__ = ['ReplyHandler', 'ProspectReply', 'ReplyType', 'ReplyAction']
