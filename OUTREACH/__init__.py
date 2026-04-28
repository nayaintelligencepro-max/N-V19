"""
NAYA OUTREACH MODULE
10x meilleur que Instantly.ai — Séquenceur multi-touch autonome
7 touches sur 21 jours — Email + LinkedIn + WhatsApp + Video
"""

from .sequence_engine import SequenceEngine, TouchPoint, Sequence
from .email_personalizer import EmailPersonalizer
from .followup_sequencer import FollowupSequencer
from .linkedin_messenger import LinkedInMessenger
from .whatsapp_agent import WhatsAppAgent
from .reply_handler import ReplyHandler
from .ab_sequence_tester import ABSequenceTester
from .meeting_booker import MeetingBooker

__all__ = [
    'SequenceEngine',
    'TouchPoint',
    'Sequence',
    'EmailPersonalizer',
    'FollowupSequencer',
    'LinkedInMessenger',
    'WhatsAppAgent',
    'ReplyHandler',
    'ABSequenceTester',
    'MeetingBooker'
]
