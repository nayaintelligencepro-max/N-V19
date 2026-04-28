"""
NAYA FOLLOWUP SEQUENCER
Gestion adaptative des relances basée sur le comportement prospect
Ajustement dynamique des délais et canaux selon engagement
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EngagementLevel(Enum):
    """Niveau d'engagement du prospect"""
    COLD = "cold"  # Aucune interaction
    WARM = "warm"  # Email ouvert ou profil LinkedIn visité
    HOT = "hot"  # Cliqué sur lien ou répondu
    MEETING_BOOKED = "meeting_booked"  # Meeting réservé


@dataclass
class ProspectBehavior:
    """Comportement observé d'un prospect"""
    prospect_id: str
    emails_sent: int = 0
    emails_opened: int = 0
    links_clicked: int = 0
    linkedin_profile_viewed: bool = False
    linkedin_message_read: bool = False
    last_interaction: Optional[datetime] = None
    engagement_level: EngagementLevel = EngagementLevel.COLD

    def update_engagement(self):
        """Met à jour le niveau d'engagement basé sur le comportement"""
        if self.emails_opened > 0 or self.linkedin_message_read:
            self.engagement_level = EngagementLevel.WARM
        if self.links_clicked > 0:
            self.engagement_level = EngagementLevel.HOT


class FollowupSequencer:
    """
    Séquenceur de relances adaptatif

    Capacités:
    - Ajustement automatique des délais selon engagement
    - Choix intelligent du canal (email vs LinkedIn vs WhatsApp)
    - Règles de fatigue: max 3 emails/semaine, pause si pas d'ouverture
    - Escalade automatique vers humain si prospect très engagé
    """

    # Règles de délai par niveau d'engagement
    FOLLOWUP_DELAYS = {
        EngagementLevel.COLD: {
            'min_days': 3,
            'max_days': 5,
            'preferred_channel': 'email'
        },
        EngagementLevel.WARM: {
            'min_days': 2,
            'max_days': 3,
            'preferred_channel': 'linkedin'
        },
        EngagementLevel.HOT: {
            'min_days': 1,
            'max_days': 2,
            'preferred_channel': 'phone'  # Escalade vers appel
        }
    }

    # Règles anti-spam
    MAX_EMAILS_PER_WEEK = 3
    MAX_TOTAL_TOUCHES = 7
    PAUSE_AFTER_NO_OPEN_COUNT = 2  # Pause si 2 emails non ouverts consécutifs

    def __init__(self):
        """Initialise le sequencer"""
        self.prospect_behaviors: Dict[str, ProspectBehavior] = {}
        logger.info("FollowupSequencer initialized")

    def track_prospect_behavior(self,
                               prospect_id: str,
                               event: str,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Enregistre un comportement prospect

        Args:
            prospect_id: ID du prospect
            event: Type d'événement ('email_sent', 'email_opened', 'link_clicked', etc.)
            metadata: Métadonnées additionnelles
        """
        if prospect_id not in self.prospect_behaviors:
            self.prospect_behaviors[prospect_id] = ProspectBehavior(prospect_id=prospect_id)

        behavior = self.prospect_behaviors[prospect_id]
        behavior.last_interaction = datetime.now(timezone.utc)

        # Mettre à jour selon le type d'événement
        if event == 'email_sent':
            behavior.emails_sent += 1
        elif event == 'email_opened':
            behavior.emails_opened += 1
        elif event == 'link_clicked':
            behavior.links_clicked += 1
        elif event == 'linkedin_profile_viewed':
            behavior.linkedin_profile_viewed = True
        elif event == 'linkedin_message_read':
            behavior.linkedin_message_read = True

        # Recalculer le niveau d'engagement
        behavior.update_engagement()

        logger.info(f"Tracked {event} for prospect {prospect_id} - engagement: {behavior.engagement_level.value}")

    def should_send_followup(self,
                           prospect_id: str,
                           days_since_last_touch: int,
                           consecutive_unopened: int = 0) -> Dict[str, Any]:
        """
        Détermine si une relance doit être envoyée

        Args:
            prospect_id: ID du prospect
            days_since_last_touch: Jours depuis la dernière touche
            consecutive_unopened: Nombre d'emails consécutifs non ouverts

        Returns:
            Dict avec 'should_send' (bool), 'reason' (str), 'recommended_channel' (str)
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            # Nouveau prospect, OK pour première touche
            return {
                'should_send': True,
                'reason': 'New prospect - first touch',
                'recommended_channel': 'email',
                'delay_days': 0
            }

        # Vérifier le nombre total de touches
        if behavior.emails_sent >= self.MAX_TOTAL_TOUCHES:
            return {
                'should_send': False,
                'reason': f'Max touches reached ({self.MAX_TOTAL_TOUCHES})',
                'recommended_channel': None,
                'delay_days': None
            }

        # Vérifier la règle anti-spam (emails par semaine)
        if behavior.emails_sent >= self.MAX_EMAILS_PER_WEEK:
            return {
                'should_send': False,
                'reason': f'Max emails per week reached ({self.MAX_EMAILS_PER_WEEK})',
                'recommended_channel': 'linkedin',  # Suggérer canal alternatif
                'delay_days': 7
            }

        # Vérifier la règle de pause (emails non ouverts consécutifs)
        if consecutive_unopened >= self.PAUSE_AFTER_NO_OPEN_COUNT:
            return {
                'should_send': False,
                'reason': f'Too many unopened emails ({consecutive_unopened}), pausing sequence',
                'recommended_channel': 'linkedin',
                'delay_days': 14  # Pause de 2 semaines
            }

        # Obtenir les règles de délai selon l'engagement
        delay_rules = self.FOLLOWUP_DELAYS.get(behavior.engagement_level)

        if not delay_rules:
            delay_rules = self.FOLLOWUP_DELAYS[EngagementLevel.COLD]

        # Vérifier si assez de temps s'est écoulé
        if days_since_last_touch < delay_rules['min_days']:
            return {
                'should_send': False,
                'reason': f'Too soon (min {delay_rules["min_days"]} days)',
                'recommended_channel': delay_rules['preferred_channel'],
                'delay_days': delay_rules['min_days'] - days_since_last_touch
            }

        # OK pour envoyer
        return {
            'should_send': True,
            'reason': f'Ready for followup (engagement: {behavior.engagement_level.value})',
            'recommended_channel': delay_rules['preferred_channel'],
            'delay_days': 0
        }

    def calculate_next_touch_date(self,
                                 prospect_id: str,
                                 last_touch_date: datetime) -> Optional[datetime]:
        """
        Calcule la date optimale pour la prochaine touche

        Args:
            prospect_id: ID du prospect
            last_touch_date: Date de la dernière touche

        Returns:
            Date optimale pour la prochaine touche, ou None si séquence terminée
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            # Premier contact: immédiatement
            return datetime.now(timezone.utc)

        # Si max touches atteint, pas de prochaine touche
        if behavior.emails_sent >= self.MAX_TOTAL_TOUCHES:
            return None

        # Obtenir les règles de délai
        delay_rules = self.FOLLOWUP_DELAYS.get(behavior.engagement_level,
                                              self.FOLLOWUP_DELAYS[EngagementLevel.COLD])

        # Calculer le délai optimal (moyenne entre min et max)
        optimal_delay_days = (delay_rules['min_days'] + delay_rules['max_days']) / 2

        next_date = last_touch_date + timedelta(days=optimal_delay_days)

        logger.info(f"Next touch for {prospect_id} calculated: {next_date.isoformat()} (engagement: {behavior.engagement_level.value})")

        return next_date

    def get_recommended_message_tone(self, prospect_id: str) -> str:
        """
        Recommande le ton du message selon l'engagement

        Args:
            prospect_id: ID du prospect

        Returns:
            Ton recommandé ('formal', 'casual', 'urgent')
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            return 'formal'

        if behavior.engagement_level == EngagementLevel.COLD:
            if behavior.emails_sent == 0:
                return 'formal'
            elif behavior.emails_sent >= 5:
                return 'urgent'  # Dernière tentative
            else:
                return 'casual'

        elif behavior.engagement_level == EngagementLevel.WARM:
            return 'casual'  # Prospect engagé, ton plus décontracté

        elif behavior.engagement_level == EngagementLevel.HOT:
            return 'urgent'  # Prospect très intéressé, pousser vers action

        return 'formal'

    def get_prospect_score(self, prospect_id: str) -> int:
        """
        Calcule un score d'intérêt du prospect (0-100)

        Args:
            prospect_id: ID du prospect

        Returns:
            Score d'intérêt (0-100)
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            return 0

        score = 0

        # Points pour ouvertures d'emails
        score += min(behavior.emails_opened * 10, 30)  # Max 30 points

        # Points pour clics
        score += min(behavior.links_clicked * 20, 40)  # Max 40 points

        # Points pour LinkedIn
        if behavior.linkedin_profile_viewed:
            score += 10
        if behavior.linkedin_message_read:
            score += 20

        return min(score, 100)

    def should_escalate_to_human(self, prospect_id: str) -> bool:
        """
        Détermine si le prospect doit être escaladé vers un humain

        Args:
            prospect_id: ID du prospect

        Returns:
            True si escalade recommandée
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            return False

        # Escalade si engagement HOT
        if behavior.engagement_level == EngagementLevel.HOT:
            return True

        # Escalade si score > 70
        score = self.get_prospect_score(prospect_id)
        if score > 70:
            return True

        # Escalade si plusieurs interactions
        if behavior.emails_opened >= 3 and behavior.links_clicked >= 1:
            return True

        return False

    def get_behavior_summary(self, prospect_id: str) -> Dict[str, Any]:
        """
        Obtient un résumé du comportement d'un prospect

        Args:
            prospect_id: ID du prospect

        Returns:
            Résumé complet du comportement
        """
        behavior = self.prospect_behaviors.get(prospect_id)

        if not behavior:
            return {
                'prospect_id': prospect_id,
                'exists': False
            }

        return {
            'prospect_id': prospect_id,
            'exists': True,
            'emails_sent': behavior.emails_sent,
            'emails_opened': behavior.emails_opened,
            'links_clicked': behavior.links_clicked,
            'linkedin_engagement': behavior.linkedin_profile_viewed or behavior.linkedin_message_read,
            'engagement_level': behavior.engagement_level.value,
            'score': self.get_prospect_score(prospect_id),
            'last_interaction': behavior.last_interaction.isoformat() if behavior.last_interaction else None,
            'should_escalate': self.should_escalate_to_human(prospect_id),
            'recommended_tone': self.get_recommended_message_tone(prospect_id)
        }

    def get_all_hot_prospects(self) -> List[str]:
        """
        Retourne la liste des prospects HOT (à escalader)

        Returns:
            Liste des IDs de prospects HOT
        """
        hot_prospects = [
            prospect_id
            for prospect_id, behavior in self.prospect_behaviors.items()
            if behavior.engagement_level == EngagementLevel.HOT
        ]

        logger.info(f"Found {len(hot_prospects)} hot prospects")
        return hot_prospects

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        total = len(self.prospect_behaviors)
        if total == 0:
            return {'total_prospects': 0}

        by_engagement = {
            'cold': 0,
            'warm': 0,
            'hot': 0,
            'meeting_booked': 0
        }

        for behavior in self.prospect_behaviors.values():
            by_engagement[behavior.engagement_level.value] += 1

        return {
            'total_prospects': total,
            'by_engagement': by_engagement,
            'hot_prospects': by_engagement['hot'],
            'avg_emails_sent': sum(b.emails_sent for b in self.prospect_behaviors.values()) / total,
            'avg_open_rate': (sum(b.emails_opened for b in self.prospect_behaviors.values()) /
                            sum(b.emails_sent for b in self.prospect_behaviors.values()) * 100)
                            if sum(b.emails_sent for b in self.prospect_behaviors.values()) > 0 else 0
        }


__all__ = ['FollowupSequencer', 'EngagementLevel', 'ProspectBehavior']
