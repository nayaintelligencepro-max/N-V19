"""
NAYA SUPREME V19.3 — AMELIORATION #5
Offer A/B Optimizer
===================
Optimisation automatique des offres basee sur les taux de reponse.
Teste differentes variantes (prix, ton, longueur, CTA) et converge
vers la variante qui genere le plus de reponses positives.

Unique a NAYA : A/B testing integre dans un systeme de vente IA
avec convergence automatique vers l'offre optimale par secteur.
"""
import time
import random
import logging
import threading
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.AB_OPTIMIZER")


class OfferVariant(Enum):
    CONTROL = "control"
    SHORTER = "shorter"         # Offre 30% plus courte
    PREMIUM_ANCHOR = "premium"  # Ancrage prix premium puis remise
    URGENCY = "urgency"         # Ton d'urgence + deadline
    SOCIAL_PROOF = "social"     # Temoignages + resultats chiffres
    QUESTION_LEAD = "question"  # Commence par une question


@dataclass
class VariantStats:
    variant: str
    sent: int = 0
    opened: int = 0
    replied: int = 0
    positive_replies: int = 0
    meetings_booked: int = 0
    deals_closed: int = 0
    revenue_generated: float = 0.0
    reply_rate: float = 0.0
    positive_rate: float = 0.0
    meeting_rate: float = 0.0
    confidence: float = 0.0


@dataclass
class ABExperiment:
    experiment_id: str
    sector: str
    variants: Dict[str, VariantStats]
    winner: Optional[str] = None
    winner_confidence: float = 0.0
    min_sample_size: int = 30
    started_at: float = field(default_factory=time.time)
    concluded_at: float = 0


class OfferABOptimizer:
    """
    Moteur d'optimisation A/B pour les offres NAYA.

    Fonctionnement :
    1. Pour chaque secteur, cree une experience avec 3-4 variantes
    2. Attribue aleatoirement les variantes aux prospects
    3. Mesure reply_rate, positive_rate, meeting_rate
    4. Declare un gagnant quand la confiance > 95%
    5. Applique automatiquement la variante gagnante
    """

    VARIANT_TEMPLATES = {
        OfferVariant.CONTROL: {
            "style": "standard",
            "length": "medium",
            "cta": "Disponible pour un call de 15min cette semaine?",
        },
        OfferVariant.SHORTER: {
            "style": "concis",
            "length": "short",
            "cta": "Dispo pour un call rapide?",
        },
        OfferVariant.PREMIUM_ANCHOR: {
            "style": "premium",
            "length": "medium",
            "cta": "Je vous propose un audit flash gratuit (valeur 5000 EUR) pour identifier vos 3 failles critiques.",
        },
        OfferVariant.URGENCY: {
            "style": "urgent",
            "length": "medium",
            "cta": "La deadline NIS2 arrive en octobre. Reservez votre audit avant le [DATE+14j].",
        },
        OfferVariant.SOCIAL_PROOF: {
            "style": "proof",
            "length": "long",
            "cta": "Comme [ENTREPRISE_SIMILAIRE] qui a reduit ses failles de 73%, je peux vous aider a atteindre la conformite.",
        },
        OfferVariant.QUESTION_LEAD: {
            "style": "question",
            "length": "short",
            "cta": "Savez-vous combien de failles NIS2 non-corrigees coute a une entreprise de votre taille?",
        },
    }

    def __init__(self):
        self._experiments: Dict[str, ABExperiment] = {}
        self._lock = threading.Lock()
        self._total_experiments: int = 0

    def get_variant_for_prospect(self, sector: str, prospect_id: str) -> Dict:
        """
        Retourne la variante d'offre a utiliser pour un prospect donne.
        Si une variante gagnante existe pour le secteur, l'utilise.
        Sinon, attribue aleatoirement parmi les variantes actives.
        """
        experiment = self._get_or_create_experiment(sector)

        # Si un gagnant existe, l'utiliser a 80% (20% exploration)
        if experiment.winner and random.random() < 0.80:
            return {
                "variant": experiment.winner,
                "template": self.VARIANT_TEMPLATES.get(
                    OfferVariant(experiment.winner),
                    self.VARIANT_TEMPLATES[OfferVariant.CONTROL]
                ),
                "source": "winner",
            }

        # Attribution deterministe basee sur le prospect_id (reproductible)
        variants = list(OfferVariant)
        hash_val = int(hashlib.md5(f"{sector}:{prospect_id}".encode()).hexdigest()[:8], 16)
        chosen = variants[hash_val % len(variants)]

        return {
            "variant": chosen.value,
            "template": self.VARIANT_TEMPLATES[chosen],
            "source": "experiment",
        }

    def record_event(self, sector: str, variant: str, event: str, value: float = 0) -> None:
        """
        Enregistre un evenement pour une variante.
        Events: sent, opened, replied, positive_reply, meeting_booked, deal_closed
        """
        experiment = self._get_or_create_experiment(sector)
        with self._lock:
            if variant not in experiment.variants:
                experiment.variants[variant] = VariantStats(variant=variant)
            stats = experiment.variants[variant]

            if event == "sent":
                stats.sent += 1
            elif event == "opened":
                stats.opened += 1
            elif event == "replied":
                stats.replied += 1
            elif event == "positive_reply":
                stats.positive_replies += 1
            elif event == "meeting_booked":
                stats.meetings_booked += 1
            elif event == "deal_closed":
                stats.deals_closed += 1
                stats.revenue_generated += value

            # Recalculer les taux
            if stats.sent > 0:
                stats.reply_rate = round(stats.replied / stats.sent, 4)
                stats.positive_rate = round(stats.positive_replies / stats.sent, 4)
                stats.meeting_rate = round(stats.meetings_booked / stats.sent, 4)

            # Verifier si on peut conclure l'experience
            self._check_significance(experiment)

    def _get_or_create_experiment(self, sector: str) -> ABExperiment:
        with self._lock:
            if sector not in self._experiments:
                exp_id = f"EXP_{sector.upper()[:10]}_{int(time.time())}"
                self._experiments[sector] = ABExperiment(
                    experiment_id=exp_id,
                    sector=sector,
                    variants={v.value: VariantStats(variant=v.value) for v in OfferVariant},
                )
                self._total_experiments += 1
            return self._experiments[sector]

    def _check_significance(self, experiment: ABExperiment) -> None:
        """Verifie si une variante est statistiquement gagnante."""
        if experiment.winner:
            return

        # Besoin d'un minimum de donnees
        variants_with_data = [
            v for v in experiment.variants.values()
            if v.sent >= experiment.min_sample_size
        ]

        if len(variants_with_data) < 2:
            return

        # Trouver le meilleur taux de reponse positif
        best = max(variants_with_data, key=lambda v: v.positive_rate)
        second_best = sorted(variants_with_data, key=lambda v: v.positive_rate, reverse=True)

        if len(second_best) >= 2:
            runner_up = second_best[1]
            # Difference significative? (simplifie: ecart > 30% relatif)
            if best.positive_rate > 0 and runner_up.positive_rate >= 0:
                lift = (best.positive_rate - runner_up.positive_rate) / max(0.01, runner_up.positive_rate)
                if lift > 0.30 and best.sent >= experiment.min_sample_size:
                    experiment.winner = best.variant
                    experiment.winner_confidence = min(0.95, 0.5 + lift * 0.3)
                    experiment.concluded_at = time.time()
                    log.info(
                        f"[A/B] WINNER for {experiment.sector}: variant '{best.variant}' "
                        f"(positive_rate={best.positive_rate:.1%}, lift={lift:.0%})"
                    )

    def get_experiment_results(self, sector: str) -> Dict:
        """Retourne les resultats de l'experience pour un secteur."""
        if sector not in self._experiments:
            return {"status": "no_experiment"}
        exp = self._experiments[sector]
        return {
            "experiment_id": exp.experiment_id,
            "sector": exp.sector,
            "winner": exp.winner,
            "winner_confidence": exp.winner_confidence,
            "variants": {
                name: {
                    "sent": v.sent,
                    "replied": v.replied,
                    "positive_replies": v.positive_replies,
                    "reply_rate": f"{v.reply_rate:.1%}",
                    "positive_rate": f"{v.positive_rate:.1%}",
                    "meetings_booked": v.meetings_booked,
                    "revenue": v.revenue_generated,
                }
                for name, v in exp.variants.items()
                if v.sent > 0
            },
        }

    def get_stats(self) -> Dict:
        total_sent = sum(
            v.sent for exp in self._experiments.values() for v in exp.variants.values()
        )
        winners = sum(1 for exp in self._experiments.values() if exp.winner)
        return {
            "total_experiments": self._total_experiments,
            "active_experiments": len(self._experiments),
            "experiments_with_winner": winners,
            "total_offers_tracked": total_sent,
        }


_optimizer: Optional[OfferABOptimizer] = None


def get_ab_optimizer() -> OfferABOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = OfferABOptimizer()
    return _optimizer
