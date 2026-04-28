"""
GAP-004 RÉSOLU — Analyseur sémantique des réponses avancé.

Analyse les réponses des prospects (emails, messages) pour détecter l'intention,
le sentiment, les objections et le niveau d'intérêt.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponseIntent(str, Enum):
    INTERESTED = "interested"
    OBJECTION = "objection"
    QUESTION = "question"
    MEETING_REQUEST = "meeting_request"
    PRICE_INQUIRY = "price_inquiry"
    REFERRAL = "referral"
    UNSUBSCRIBE = "unsubscribe"
    AUTO_REPLY = "auto_reply"
    REJECTION = "rejection"
    POSITIVE_SIGNAL = "positive_signal"


class SentimentLevel(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class ObjectionDetected:
    """Une objection détectée dans la réponse."""
    category: str
    text_excerpt: str
    recommended_response: str
    severity: float


@dataclass
class AnalysisResult:
    """Résultat complet de l'analyse sémantique."""
    prospect_id: str
    primary_intent: ResponseIntent
    secondary_intents: List[ResponseIntent]
    sentiment: SentimentLevel
    interest_score: float
    objections: List[ObjectionDetected]
    key_phrases: List[str]
    recommended_action: str
    urgency_level: str
    analyzed_at: str = ""

    def __post_init__(self) -> None:
        if not self.analyzed_at:
            self.analyzed_at = datetime.now(timezone.utc).isoformat()


INTENT_PATTERNS: Dict[ResponseIntent, List[str]] = {
    ResponseIntent.INTERESTED: [
        r"intéress[ée]", r"tell me more", r"en savoir plus", r"curieux",
        r"pourriez.vous", r"can you", r"j'aimerais", r"we'?d like",
        r"ça m'intéresse", r"sounds interesting",
    ],
    ResponseIntent.OBJECTION: [
        r"trop cher", r"too expensive", r"pas le budget", r"no budget",
        r"pas maintenant", r"not now", r"pas prioritaire", r"not a priority",
        r"déjà un prestataire", r"already have", r"pas concerné",
    ],
    ResponseIntent.MEETING_REQUEST: [
        r"rendez.vous", r"meeting", r"appel", r"call", r"visio",
        r"calendly", r"disponible", r"available", r"quand.*rencontrer",
    ],
    ResponseIntent.PRICE_INQUIRY: [
        r"combien", r"how much", r"tarif", r"prix", r"price",
        r"coût", r"cost", r"devis", r"quote", r"budget",
    ],
    ResponseIntent.UNSUBSCRIBE: [
        r"désabonner", r"unsubscribe", r"stop", r"arrête",
        r"ne.*contactez.*plus", r"remove me", r"spam",
    ],
    ResponseIntent.AUTO_REPLY: [
        r"out of office", r"absence", r"automatique", r"auto.reply",
        r"de retour le", r"back on", r"congé", r"vacation",
    ],
    ResponseIntent.REJECTION: [
        r"non merci", r"no thank", r"pas intéressé", r"not interested",
        r"ne.*pas.*suite", r"decline", r"refus",
    ],
    ResponseIntent.REFERRAL: [
        r"collègue", r"colleague", r"transféré", r"forwarded",
        r"contactez plutôt", r"speak to", r"mon responsable", r"my manager",
    ],
    ResponseIntent.POSITIVE_SIGNAL: [
        r"excellent", r"parfait", r"great", r"wonderful", r"super",
        r"merci.*intéressant", r"envoyez.*plus", r"send more",
    ],
}

OBJECTION_HANDLERS: Dict[str, str] = {
    "budget": (
        "Je comprends la contrainte budgétaire. Notre audit initial à 5 000 EUR "
        "est un investissement minimal comparé aux 4.2M EUR de coût moyen d'un "
        "incident OT non-détecté. Nous proposons aussi des facilités de paiement."
    ),
    "timing": (
        "Le timing est effectivement important. Cependant, les deadlines NIS2 "
        "n'attendent pas — les sanctions sont actives. Un pré-audit de 2h "
        "peut vous donner une vision claire sans engagement."
    ),
    "existing_vendor": (
        "Avoir déjà un prestataire est une bonne chose. Notre approche est "
        "complémentaire — nous apportons une expertise terrain SCADA/OT "
        "spécifique que peu de prestataires généralistes maîtrisent."
    ),
    "not_concerned": (
        "Beaucoup d'entreprises pensent ne pas être concernées jusqu'au premier "
        "incident. Un diagnostic rapide gratuit de 15 min peut révéler des "
        "vulnérabilités insoupçonnées dans vos systèmes industriels."
    ),
}

SENTIMENT_WORDS: Dict[SentimentLevel, List[str]] = {
    SentimentLevel.VERY_POSITIVE: [
        "excellent", "parfait", "fantastique", "formidable", "exceptional", "amazing",
    ],
    SentimentLevel.POSITIVE: [
        "bien", "bon", "intéressant", "merci", "good", "nice", "thanks", "great",
    ],
    SentimentLevel.NEGATIVE: [
        "déçu", "problème", "mauvais", "difficile", "disappointed", "bad", "issue",
    ],
    SentimentLevel.VERY_NEGATIVE: [
        "inacceptable", "scandaleux", "horrible", "spam", "arnaque", "unacceptable",
    ],
}


class SemanticResponseAnalyzer:
    """
    Analyse sémantique multi-couche des réponses prospects.

    Couche 1: Détection d'intention (regex patterns)
    Couche 2: Analyse de sentiment (lexique pondéré)
    Couche 3: Extraction d'objections et recommandations
    """

    def __init__(self) -> None:
        self._compiled_patterns: Dict[ResponseIntent, List[re.Pattern]] = {}
        for intent, patterns in INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        self._history: List[AnalysisResult] = []
        logger.info("[SemanticResponseAnalyzer] Initialisé — patterns multi-langues chargés")

    def _detect_intents(self, text: str) -> List[ResponseIntent]:
        """Détecte les intentions dans le texte."""
        detected: List[ResponseIntent] = []
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    detected.append(intent)
                    break
        return detected or [ResponseIntent.QUESTION]

    def _analyze_sentiment(self, text: str) -> SentimentLevel:
        """Analyse le sentiment du texte."""
        text_lower = text.lower()
        scores = {level: 0 for level in SentimentLevel}
        for level, words in SENTIMENT_WORDS.items():
            for word in words:
                if word in text_lower:
                    scores[level] += 1
        max_level = max(scores, key=lambda l: scores[l])
        if scores[max_level] == 0:
            return SentimentLevel.NEUTRAL
        return max_level

    def _extract_objections(self, text: str) -> List[ObjectionDetected]:
        """Extrait les objections et recommande des réponses."""
        objections: List[ObjectionDetected] = []
        text_lower = text.lower()

        objection_keywords = {
            "budget": ["cher", "expensive", "budget", "coût", "cost", "prix"],
            "timing": ["maintenant", "now", "plus tard", "later", "priorité", "priority"],
            "existing_vendor": ["prestataire", "vendor", "fournisseur", "déjà"],
            "not_concerned": ["pas concerné", "not concerned", "ne s'applique pas"],
        }

        for category, keywords in objection_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    start = max(0, text_lower.index(kw) - 30)
                    end = min(len(text), text_lower.index(kw) + len(kw) + 30)
                    objections.append(ObjectionDetected(
                        category=category,
                        text_excerpt=text[start:end].strip(),
                        recommended_response=OBJECTION_HANDLERS.get(category, ""),
                        severity=0.7 if category in ("budget", "timing") else 0.4,
                    ))
                    break

        return objections

    def _calculate_interest_score(
        self, intents: List[ResponseIntent], sentiment: SentimentLevel
    ) -> float:
        """Calcule un score d'intérêt de 0 à 1."""
        intent_scores = {
            ResponseIntent.MEETING_REQUEST: 0.95,
            ResponseIntent.INTERESTED: 0.85,
            ResponseIntent.POSITIVE_SIGNAL: 0.80,
            ResponseIntent.PRICE_INQUIRY: 0.75,
            ResponseIntent.REFERRAL: 0.60,
            ResponseIntent.QUESTION: 0.50,
            ResponseIntent.OBJECTION: 0.35,
            ResponseIntent.AUTO_REPLY: 0.20,
            ResponseIntent.REJECTION: 0.10,
            ResponseIntent.UNSUBSCRIBE: 0.0,
        }
        sentiment_modifier = {
            SentimentLevel.VERY_POSITIVE: 0.15,
            SentimentLevel.POSITIVE: 0.05,
            SentimentLevel.NEUTRAL: 0.0,
            SentimentLevel.NEGATIVE: -0.10,
            SentimentLevel.VERY_NEGATIVE: -0.20,
        }

        if not intents:
            base = 0.5
        else:
            base = max(intent_scores.get(i, 0.5) for i in intents)

        modifier = sentiment_modifier.get(sentiment, 0)
        return round(max(0, min(1, base + modifier)), 3)

    def _recommend_action(
        self,
        primary_intent: ResponseIntent,
        interest_score: float,
        objections: List[ObjectionDetected],
    ) -> str:
        """Recommande une action basée sur l'analyse."""
        if primary_intent == ResponseIntent.MEETING_REQUEST:
            return "PRIORITÉ MAXIMALE — Proposer 3 créneaux immédiatement"
        if primary_intent == ResponseIntent.INTERESTED:
            return "Envoyer offre personnalisée + case study sectoriel"
        if primary_intent == ResponseIntent.PRICE_INQUIRY:
            return "Envoyer grille tarifaire + ROI calculator personnalisé"
        if primary_intent == ResponseIntent.REFERRAL:
            return "Contacter le référent mentionné + remercier l'intermédiaire"
        if objections:
            return f"Traiter objection '{objections[0].category}' avec réponse calibrée"
        if primary_intent == ResponseIntent.REJECTION:
            return "Archiver — recycler dans 90 jours avec angle différent"
        if primary_intent == ResponseIntent.UNSUBSCRIBE:
            return "Retirer immédiatement de la séquence — conformité RGPD"
        if primary_intent == ResponseIntent.AUTO_REPLY:
            return "Re-programmer l'envoi après la date de retour mentionnée"
        return "Envoyer contenu nurturing adapté au stade"

    def analyze(self, prospect_id: str, response_text: str) -> AnalysisResult:
        """Analyse complète d'une réponse prospect."""
        intents = self._detect_intents(response_text)
        sentiment = self._analyze_sentiment(response_text)
        objections = self._extract_objections(response_text)
        interest_score = self._calculate_interest_score(intents, sentiment)

        primary_intent = intents[0]

        urgency_map = {
            ResponseIntent.MEETING_REQUEST: "CRITIQUE",
            ResponseIntent.INTERESTED: "HAUTE",
            ResponseIntent.POSITIVE_SIGNAL: "HAUTE",
            ResponseIntent.PRICE_INQUIRY: "HAUTE",
            ResponseIntent.OBJECTION: "MOYENNE",
            ResponseIntent.REFERRAL: "MOYENNE",
            ResponseIntent.UNSUBSCRIBE: "IMMÉDIATE",
        }

        result = AnalysisResult(
            prospect_id=prospect_id,
            primary_intent=primary_intent,
            secondary_intents=intents[1:],
            sentiment=sentiment,
            interest_score=interest_score,
            objections=objections,
            key_phrases=self._extract_key_phrases(response_text),
            recommended_action=self._recommend_action(primary_intent, interest_score, objections),
            urgency_level=urgency_map.get(primary_intent, "BASSE"),
        )

        self._history.append(result)
        logger.info(
            f"[SemanticResponseAnalyzer] {prospect_id}: "
            f"intent={primary_intent.value} sentiment={sentiment.value} "
            f"interest={interest_score:.0%}"
        )
        return result

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extrait les phrases clés du texte."""
        sentences = re.split(r'[.!?\n]+', text)
        key_phrases = []
        for s in sentences:
            s = s.strip()
            if len(s) > 10 and len(s) < 200:
                key_phrases.append(s)
        return key_phrases[:5]

    def stats(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_analyzed": 0}
        intent_dist = {}
        for r in self._history:
            intent_dist[r.primary_intent.value] = intent_dist.get(r.primary_intent.value, 0) + 1
        avg_interest = sum(r.interest_score for r in self._history) / len(self._history)
        return {
            "total_analyzed": len(self._history),
            "intent_distribution": intent_dist,
            "average_interest_score": round(avg_interest, 3),
        }


semantic_response_analyzer = SemanticResponseAnalyzer()
