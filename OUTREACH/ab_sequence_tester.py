"""
NAYA A/B SEQUENCE TESTER
Tests A/B pour séquences d'outreach
Teste sujets, corps, timing, canaux
Apprentissage automatique des variantes gagnantes
"""

import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Statut du test A/B"""
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


@dataclass
class Variant:
    """Variante dans un test A/B"""
    variant_id: str
    variant_name: str  # "A", "B", "C"

    # Contenu
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    touch_schedule: Optional[List[int]] = None  # [0, 2, 5, 8] jours
    channels: Optional[List[str]] = None  # ['email', 'linkedin']

    # Métriques
    sent_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    replied_count: int = 0
    meetings_booked: int = 0

    # Taux calculés
    @property
    def open_rate(self) -> float:
        return (self.opened_count / self.sent_count * 100) if self.sent_count > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return (self.clicked_count / self.opened_count * 100) if self.opened_count > 0 else 0.0

    @property
    def reply_rate(self) -> float:
        return (self.replied_count / self.sent_count * 100) if self.sent_count > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.meetings_booked / self.sent_count * 100) if self.sent_count > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'variant_id': self.variant_id,
            'variant_name': self.variant_name,
            'subject': self.subject_template,
            'body': self.body_template[:100] + '...' if self.body_template else None,
            'sent': self.sent_count,
            'opened': self.opened_count,
            'clicked': self.clicked_count,
            'replied': self.replied_count,
            'meetings': self.meetings_booked,
            'open_rate': round(self.open_rate, 2),
            'click_rate': round(self.click_rate, 2),
            'reply_rate': round(self.reply_rate, 2),
            'conversion_rate': round(self.conversion_rate, 2)
        }


@dataclass
class ABTest:
    """Test A/B complet"""
    test_id: str
    test_name: str
    test_type: str  # 'subject', 'body', 'schedule', 'channel'
    variants: List[Variant]
    status: TestStatus = TestStatus.RUNNING

    # Configuration
    min_sample_size: int = 50  # Minimum d'envois par variante
    confidence_threshold: float = 0.95  # Seuil de confiance statistique

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Résultats
    winner_variant_id: Optional[str] = None
    winner_confidence: float = 0.0

    def get_variant(self, variant_name: str) -> Optional[Variant]:
        """Récupère une variante par nom"""
        for variant in self.variants:
            if variant.variant_name == variant_name:
                return variant
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'status': self.status.value,
            'variants': [v.to_dict() for v in self.variants],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'winner': self.winner_variant_id,
            'confidence': round(self.winner_confidence, 2)
        }


class ABSequenceTester:
    """
    Moteur de tests A/B pour séquences d'outreach

    Teste:
    - Sujets d'emails (emojis vs pas emojis, long vs court, question vs affirmation)
    - Corps de message (format, longueur, ton)
    - Timing des touches (J+2/J+4 vs J+3/J+7)
    - Canaux (email first vs LinkedIn first)

    Apprentissage automatique:
    - Détecte automatiquement le gagnant (confiance > 95%)
    - Stocke les variantes gagnantes en vector memory
    - Applique automatiquement les gagnants aux nouvelles séquences
    """

    def __init__(self, vector_memory=None):
        """
        Initialise l'A/B tester

        Args:
            vector_memory: Mémoire vectorielle pour stocker les gagnants
        """
        self.vector_memory = vector_memory

        # Tests actifs
        self.active_tests: Dict[str, ABTest] = {}

        # Tests complétés
        self.completed_tests: List[ABTest] = []

        # Métriques globales
        self.total_tests_created = 0
        self.total_tests_completed = 0

        logger.info("ABSequenceTester initialized")

    def create_test(self,
                   test_name: str,
                   test_type: str,
                   variant_configs: List[Dict[str, Any]],
                   min_sample_size: int = 50) -> ABTest:
        """
        Crée un nouveau test A/B

        Args:
            test_name: Nom du test
            test_type: Type ('subject', 'body', 'schedule', 'channel')
            variant_configs: Liste de configs des variantes
            min_sample_size: Taille minimale échantillon par variante

        Returns:
            ABTest créé
        """
        test_id = self._generate_test_id(test_name)

        # Créer les variantes
        variants = []
        variant_names = ['A', 'B', 'C', 'D', 'E']

        for i, config in enumerate(variant_configs):
            variant = Variant(
                variant_id=f"{test_id}_VAR_{variant_names[i]}",
                variant_name=variant_names[i],
                subject_template=config.get('subject'),
                body_template=config.get('body'),
                touch_schedule=config.get('schedule'),
                channels=config.get('channels')
            )
            variants.append(variant)

        # Créer le test
        ab_test = ABTest(
            test_id=test_id,
            test_name=test_name,
            test_type=test_type,
            variants=variants,
            min_sample_size=min_sample_size,
            started_at=datetime.now(timezone.utc)
        )

        self.active_tests[test_id] = ab_test
        self.total_tests_created += 1

        logger.info(f"A/B test created: {test_name} ({len(variants)} variants)")

        return ab_test

    def assign_variant(self, test_id: str, prospect_id: str) -> Optional[Variant]:
        """
        Assigne une variante à un prospect (random split)

        Args:
            test_id: ID du test
            prospect_id: ID du prospect

        Returns:
            Variante assignée
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return None

        ab_test = self.active_tests[test_id]

        if ab_test.status != TestStatus.RUNNING:
            logger.warning(f"Test {test_id} not running, cannot assign variant")
            return None

        # Assignation random uniforme
        variant = random.choice(ab_test.variants)

        logger.debug(f"Assigned variant {variant.variant_name} to prospect {prospect_id}")

        return variant

    def track_event(self,
                   test_id: str,
                   variant_name: str,
                   event_type: str) -> bool:
        """
        Enregistre un événement pour une variante

        Args:
            test_id: ID du test
            variant_name: Nom de la variante ('A', 'B', etc.)
            event_type: Type d'événement ('sent', 'opened', 'clicked', 'replied', 'meeting_booked')

        Returns:
            True si enregistré avec succès
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return False

        ab_test = self.active_tests[test_id]
        variant = ab_test.get_variant(variant_name)

        if not variant:
            logger.error(f"Variant {variant_name} not found in test {test_id}")
            return False

        # Incrémenter le compteur approprié
        if event_type == 'sent':
            variant.sent_count += 1
        elif event_type == 'opened':
            variant.opened_count += 1
        elif event_type == 'clicked':
            variant.clicked_count += 1
        elif event_type == 'replied':
            variant.replied_count += 1
        elif event_type == 'meeting_booked':
            variant.meetings_booked += 1
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return False

        logger.debug(f"Tracked {event_type} for variant {variant_name} in test {test_id}")

        # Vérifier si le test peut être complété
        self._check_test_completion(test_id)

        return True

    def _check_test_completion(self, test_id: str) -> None:
        """Vérifie si un test peut être complété (winner déterminé)"""
        ab_test = self.active_tests[test_id]

        # Vérifier que toutes les variantes ont le minimum d'échantillons
        all_have_min_sample = all(v.sent_count >= ab_test.min_sample_size
                                  for v in ab_test.variants)

        if not all_have_min_sample:
            return

        # Calculer le gagnant (basé sur conversion_rate)
        variants_by_conversion = sorted(ab_test.variants,
                                       key=lambda v: v.conversion_rate,
                                       reverse=True)

        winner = variants_by_conversion[0]
        runner_up = variants_by_conversion[1] if len(variants_by_conversion) > 1 else None

        # Calculer la confiance (simplifiée, utiliser un vrai test statistique en prod)
        if runner_up:
            confidence = self._calculate_confidence(winner, runner_up)
        else:
            confidence = 1.0

        # Si confiance > seuil, déclarer le gagnant
        if confidence >= ab_test.confidence_threshold:
            ab_test.winner_variant_id = winner.variant_id
            ab_test.winner_confidence = confidence
            ab_test.status = TestStatus.COMPLETED
            ab_test.completed_at = datetime.now(timezone.utc)

            logger.info(f"Test {test_id} COMPLETED - Winner: Variant {winner.variant_name} "
                       f"(conversion: {winner.conversion_rate:.2f}%, confidence: {confidence:.2%})")

            # Déplacer vers completed_tests
            self.completed_tests.append(ab_test)
            self.total_tests_completed += 1

            # Sauvegarder le gagnant en mémoire
            asyncio.create_task(self._save_winner_to_memory(ab_test, winner))

    def _calculate_confidence(self, variant_a: Variant, variant_b: Variant) -> float:
        """
        Calcule la confiance statistique (simplifiée)

        En production, utiliser un vrai test statistique (Chi-square, Z-test, etc.)
        """
        # Simplification: si écart > 20% relatif ET échantillons suffisants, confiance haute
        if variant_a.sent_count < 50 or variant_b.sent_count < 50:
            return 0.5

        if variant_a.conversion_rate == 0 and variant_b.conversion_rate == 0:
            return 0.5

        if variant_a.conversion_rate == 0:
            return 0.5

        relative_diff = abs(variant_a.conversion_rate - variant_b.conversion_rate) / variant_a.conversion_rate

        if relative_diff > 0.3:  # 30% de différence
            return 0.98
        elif relative_diff > 0.2:  # 20% de différence
            return 0.95
        elif relative_diff > 0.1:  # 10% de différence
            return 0.85
        else:
            return 0.7

    async def _save_winner_to_memory(self, ab_test: ABTest, winner: Variant) -> None:
        """Sauvegarde le gagnant en vector memory"""
        if not self.vector_memory:
            logger.warning("Vector memory not available, cannot save winner")
            return

        try:
            winner_data = {
                'test_id': ab_test.test_id,
                'test_name': ab_test.test_name,
                'test_type': ab_test.test_type,
                'variant_name': winner.variant_name,
                'subject': winner.subject_template,
                'body': winner.body_template,
                'conversion_rate': winner.conversion_rate,
                'reply_rate': winner.reply_rate,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            await self.vector_memory.save_ab_test_winner(winner_data)
            logger.info(f"Winner saved to memory: {ab_test.test_name} - Variant {winner.variant_name}")

        except Exception as e:
            logger.error(f"Error saving winner to memory: {e}")

    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le statut d'un test"""
        if test_id in self.active_tests:
            return self.active_tests[test_id].to_dict()

        # Chercher dans les tests complétés
        for test in self.completed_tests:
            if test.test_id == test_id:
                return test.to_dict()

        return None

    def get_all_active_tests(self) -> List[Dict[str, Any]]:
        """Retourne tous les tests actifs"""
        return [test.to_dict() for test in self.active_tests.values()]

    def get_winning_templates(self, test_type: str = None) -> List[Dict[str, Any]]:
        """Retourne les templates gagnants"""
        winners = []

        for test in self.completed_tests:
            if test_type and test.test_type != test_type:
                continue

            if test.winner_variant_id:
                winner = next((v for v in test.variants if v.variant_id == test.winner_variant_id), None)
                if winner:
                    winners.append({
                        'test_name': test.test_name,
                        'test_type': test.test_type,
                        'variant': winner.variant_name,
                        'subject': winner.subject_template,
                        'body': winner.body_template,
                        'conversion_rate': winner.conversion_rate,
                        'confidence': test.winner_confidence
                    })

        return winners

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        return {
            'total_tests_created': self.total_tests_created,
            'total_tests_completed': self.total_tests_completed,
            'active_tests': len(self.active_tests),
            'winning_templates_available': len(self.completed_tests)
        }

    def _generate_test_id(self, test_name: str) -> str:
        """Génère un ID unique pour un test"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{test_name}_{timestamp}"
        return f"TEST_{hashlib.sha256(data.encode()).hexdigest()[:12].upper()}"


# Exemples de tests A/B prêts à l'emploi
EXAMPLE_SUBJECT_TEST = {
    'test_name': 'Email Touch 1 - Subject Test',
    'test_type': 'subject',
    'variants': [
        {'subject': '🎯 {signal_detected} — {company_name}'},
        {'subject': 'Re: Cybersécurité OT — {company_name}'},
        {'subject': '{company_name} : audit IEC 62443 ?'}
    ]
}

EXAMPLE_BODY_TEST = {
    'test_name': 'Email Touch 1 - Body Length Test',
    'test_type': 'body',
    'variants': [
        {'body': 'COURT (< 50 mots): Bonjour {name}, audit OT pour {company} ? 15 min call cette semaine ?'},
        {'body': 'MOYEN (100 mots): Bonjour {name}, j\'ai détecté {signal}. Nous aidons {sector} à sécuriser OT. Cas d\'étude ? Call ?'},
        {'body': 'LONG (150 mots): Email complet avec contexte, stats secteur, cas client, preuve sociale, CTA'}
    ]
}


__all__ = ['ABSequenceTester', 'ABTest', 'Variant', 'TestStatus']
