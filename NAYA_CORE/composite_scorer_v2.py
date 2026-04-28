"""
NAYA SUPREME — Composite Scorer V2
══════════════════════════════════════════════════════════════════════════════
Remplace le score binaire 0-100 par un vecteur 6 dimensions.
Chaque dimension mesure un facteur de conversion indépendant.

POURQUOI 6 DIMENSIONS :
  Un score unique mélange des signaux contradictoires.
  Exemple : score=75 peut signifier "budget élevé + décideur inaccessible"
  OU "budget faible + décideur très accessible". Même score, actions opposées.

  Le vecteur 6D donne la vérité : chaque dimension est exploitable.

6 DIMENSIONS :
  D1 — URGENCY          : La douleur est-elle urgente ? (signal récent, deadline, incident)
  D2 — BUDGET_CONFIDENCE: Le budget est-il confirmé ? (offre emploi, M&A, pénalité)
  D3 — ACCESSIBILITY    : Le décideur est-il joignable ? (LinkedIn, email, connexion commune)
  D4 — REGULATORY_PRESS : Pression réglementaire active ? (NIS2, DORA, IEC62443 deadline)
  D5 — COMPETITIVE_ISOLATION: Peu de concurrents positionnés ? (niche, discret, early)
  D6 — TIMING_WINDOW    : Le timing est-il optimal ? (début de trimestre, avant budget)

SCORE COMPOSITE :
  composite_score = weighted_average(D1..D6, weights)
  win_probability = monte_carlo_simulation(composite_score, historical_data)

OUTPUT :
  CompositeScorerResult — vecteur 6D + score composite + probabilité de victoire
══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math
import random
import time
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.COMPOSITE_SCORER")


# ─── Structures ────────────────────────────────────────────────────────────────

@dataclass
class ScoreVector:
    """Vecteur 6D de scoring d'un prospect."""
    urgency: float = 0.0             # D1 [0-1]
    budget_confidence: float = 0.0   # D2 [0-1]
    accessibility: float = 0.0       # D3 [0-1]
    regulatory_pressure: float = 0.0 # D4 [0-1]
    competitive_isolation: float = 0.0 # D5 [0-1]
    timing_window: float = 0.0       # D6 [0-1]

    def to_list(self) -> List[float]:
        return [
            self.urgency, self.budget_confidence, self.accessibility,
            self.regulatory_pressure, self.competitive_isolation, self.timing_window,
        ]

    def weakest(self) -> str:
        """Dimension la plus faible → action corrective recommandée."""
        dims = {
            "urgency": self.urgency,
            "budget_confidence": self.budget_confidence,
            "accessibility": self.accessibility,
            "regulatory_pressure": self.regulatory_pressure,
            "competitive_isolation": self.competitive_isolation,
            "timing_window": self.timing_window,
        }
        return min(dims, key=dims.get)

    def strongest(self) -> str:
        dims = {
            "urgency": self.urgency,
            "budget_confidence": self.budget_confidence,
            "accessibility": self.accessibility,
            "regulatory_pressure": self.regulatory_pressure,
            "competitive_isolation": self.competitive_isolation,
            "timing_window": self.timing_window,
        }
        return max(dims, key=dims.get)


@dataclass
class CompositeScorerResult:
    """Résultat complet de l'évaluation d'un prospect."""
    prospect_id: str
    vector: ScoreVector
    composite_score: float           # [0-100] moyenne pondérée
    win_probability: float           # [0-1] estimation Monte Carlo
    tier: str                        # HOT | WARM | COOL | COLD
    recommended_action: str          # action OODA recommandée
    action_rationale: str
    best_angle: str                  # angle de message recommandé
    estimated_deal_eur: float
    scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─── Weights ───────────────────────────────────────────────────────────────────

# Calibrés sur les données historiques IEC 62443 / NIS2
DEFAULT_WEIGHTS = {
    "urgency":               0.25,
    "budget_confidence":     0.22,
    "accessibility":         0.18,
    "regulatory_pressure":   0.17,
    "competitive_isolation": 0.10,
    "timing_window":         0.08,
}

# Facteurs de deal size par secteur (multiplicateur base 20k EUR)
SECTOR_DEAL_MULTIPLIERS = {
    "Energie": 3.5,
    "Infrastructure Critique": 4.0,
    "Transport": 2.0,
    "Manufacturing": 1.8,
    "Ferroviaire": 2.5,
    "Numérique": 1.2,
    "Santé": 2.2,
    "Eau": 1.5,
    "Chimie": 2.0,
    "Banque": 3.0,
    "Assurance": 2.5,
}

BASE_DEAL_EUR = 20_000


# ─── Dimension Calculators ─────────────────────────────────────────────────────

class DimensionCalculators:
    """
    Calcule chaque dimension du vecteur à partir des signaux disponibles.
    Chaque méthode est indépendante et robuste (pas d'erreur si champ manquant).
    """

    @staticmethod
    def urgency(signals: Dict[str, Any]) -> float:
        """
        D1 — Urgence : la douleur est-elle urgente ?
        Inputs : signal_age_days, has_incident, has_job_post, pain_score
        """
        score = 0.0
        signal_age = float(signals.get("signal_age_days", 30))
        if signal_age <= 3:
            score += 0.40
        elif signal_age <= 7:
            score += 0.30
        elif signal_age <= 14:
            score += 0.20
        elif signal_age <= 30:
            score += 0.10

        if signals.get("has_incident"):
            score += 0.35
        if signals.get("has_job_post"):
            score += 0.15
        if float(signals.get("pain_score", 0)) >= 80:
            score += 0.10

        return min(1.0, score)

    @staticmethod
    def budget_confidence(signals: Dict[str, Any]) -> float:
        """
        D2 — Confiance budget : le budget est-il réel et confirmé ?
        Inputs : has_job_post, budget_estimate_eur, has_regulatory_penalty,
                 has_recent_investment, company_revenue_m
        """
        score = 0.0
        budget = float(signals.get("budget_estimate_eur", 0))

        if signals.get("has_job_post"):
            score += 0.30  # job post = budget alloué
        if signals.get("has_regulatory_penalty"):
            score += 0.35  # pénalité = budget forcé
        if signals.get("has_recent_investment"):
            score += 0.20  # levée de fonds = budget disponible

        revenue_m = float(signals.get("company_revenue_m", 0))
        if revenue_m >= 100:
            score += 0.15
        elif revenue_m >= 20:
            score += 0.10
        elif revenue_m >= 5:
            score += 0.05

        if budget >= 50000:
            score += 0.10
        elif budget >= 15000:
            score += 0.05

        return min(1.0, score)

    @staticmethod
    def accessibility(signals: Dict[str, Any]) -> float:
        """
        D3 — Accessibilité : le décideur est-il joignable ?
        Inputs : has_email, has_linkedin, mutual_connections, has_warm_intro
        """
        score = 0.0
        if signals.get("has_warm_intro"):
            score += 0.50  # introduction directe = max score
        if signals.get("has_email"):
            score += 0.25
        if signals.get("has_linkedin"):
            score += 0.15
        mutual = int(signals.get("mutual_connections", 0))
        if mutual >= 3:
            score += 0.15
        elif mutual >= 1:
            score += 0.08
        if signals.get("has_phone"):
            score += 0.10

        return min(1.0, score)

    @staticmethod
    def regulatory_pressure(signals: Dict[str, Any]) -> float:
        """
        D4 — Pression réglementaire : deadline active ?
        Inputs : regulatory_pressure_score, regulations_applicable, days_to_deadline
        """
        reg_score = float(signals.get("regulatory_pressure_score", 0))
        if reg_score >= 80:
            return 1.0
        if reg_score >= 60:
            return 0.75
        if reg_score >= 40:
            return 0.50
        if reg_score >= 20:
            return 0.25

        # Fallback : calculer depuis les réglementations applicables
        regs = signals.get("regulations_applicable", [])
        base = min(0.8, len(regs) * 0.20)
        days = int(signals.get("days_to_deadline", 365))
        if days <= 30:
            return min(1.0, base + 0.30)
        if days <= 90:
            return min(1.0, base + 0.15)
        return base

    @staticmethod
    def competitive_isolation(signals: Dict[str, Any]) -> float:
        """
        D5 — Isolation concurrentielle : peu de concurrents sur ce prospect ?
        Inputs : competitors_count, is_niche_sector, has_incumbent, signal_discretion
        """
        score = 0.5  # neutre par défaut (information inconnue)
        competitors = int(signals.get("competitors_count", -1))
        if competitors == 0:
            score = 0.95
        elif competitors == 1:
            score = 0.70
        elif competitors >= 3:
            score = 0.30

        if signals.get("is_niche_sector"):
            score = min(1.0, score + 0.15)
        if signals.get("has_incumbent"):
            score = max(0.0, score - 0.20)

        return min(1.0, max(0.0, score))

    @staticmethod
    def timing_window(signals: Dict[str, Any]) -> float:
        """
        D6 — Fenêtre de timing : c'est le bon moment ?
        Inputs : month (budgets Q1/Q4), days_since_fiscal_year_start, contact_recent_change
        """
        score = 0.4  # base
        today = date.today()
        month = today.month

        # Fenêtres budgétaires optimales
        if month in (1, 2, 3):      # Q1 : budgets votés, décisions Q1
            score += 0.35
        elif month in (10, 11):     # Q4 : fin d'exercice, urgence dépenses
            score += 0.30
        elif month in (4, 5):       # Q2 : deuxième vague
            score += 0.15
        elif month in (9,):         # Rentrée septembre : nouvelle équipe, nouveaux projets
            score += 0.20

        # Changement récent du décideur = opportunité
        if signals.get("contact_recent_change"):
            score += 0.20

        # Signal très récent = fenêtre d'opportunité ouverte
        if int(signals.get("signal_age_days", 999)) <= 7:
            score += 0.10

        return min(1.0, score)


# ─── Monte Carlo Win Probability ───────────────────────────────────────────────

def monte_carlo_win_probability(
    composite_score: float,
    sector: str = "",
    n_simulations: int = 1000,
    historical_win_rate: float = 0.25,
) -> float:
    """
    Simule N conversions pour estimer la probabilité de victoire.

    Modèle : chaque simulation tire un score seuil aléatoire.
    Si composite_score > seuil → victoire.
    Le seuil est distribué selon une gaussienne centrée sur (1 - win_rate).
    """
    if composite_score <= 0:
        return 0.0
    if composite_score >= 95:
        return 0.90  # cap réaliste

    normalized = composite_score / 100.0
    wins = 0
    rng = random.Random(int(composite_score * 1000))  # reproducible

    for _ in range(n_simulations):
        # Seuil variable selon l'incertitude du marché
        threshold = rng.gauss(1.0 - historical_win_rate, 0.15)
        threshold = max(0.05, min(0.95, threshold))
        if normalized > threshold:
            wins += 1

    return round(wins / n_simulations, 3)


# ─── Engine ────────────────────────────────────────────────────────────────────

class CompositeScorerV2:
    """
    Évalue un prospect sur 6 dimensions indépendantes.
    Remplace le score binaire 0-100 par un vecteur exploitable.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or DEFAULT_WEIGHTS.copy()
        self._lock = threading.RLock()
        self._history: List[Dict] = []

    def score(
        self,
        prospect_id: str,
        signals: Dict[str, Any],
        sector: str = "",
        historical_win_rate: float = 0.25,
    ) -> CompositeScorerResult:
        """
        Évalue un prospect complet.

        Args:
            prospect_id: Identifiant unique du prospect
            signals: Dict de signaux disponibles (voir DimensionCalculators)
            sector: Secteur du prospect (pour multiplier deal size)
            historical_win_rate: Taux de conversion historique pour Monte Carlo

        Returns:
            CompositeScorerResult avec vecteur 6D et probabilités
        """
        # ── Calculer les 6 dimensions ──
        vec = ScoreVector(
            urgency=DimensionCalculators.urgency(signals),
            budget_confidence=DimensionCalculators.budget_confidence(signals),
            accessibility=DimensionCalculators.accessibility(signals),
            regulatory_pressure=DimensionCalculators.regulatory_pressure(signals),
            competitive_isolation=DimensionCalculators.competitive_isolation(signals),
            timing_window=DimensionCalculators.timing_window(signals),
        )

        # ── Score composite pondéré ──
        composite = sum(
            getattr(vec, dim) * w
            for dim, w in self._weights.items()
        ) * 100.0
        composite = round(min(100.0, max(0.0, composite)), 2)

        # ── Monte Carlo ──
        win_prob = monte_carlo_win_probability(
            composite, sector, historical_win_rate=historical_win_rate
        )

        # ── Tier classification ──
        if composite >= 75:
            tier = "HOT"
        elif composite >= 55:
            tier = "WARM"
        elif composite >= 35:
            tier = "COOL"
        else:
            tier = "COLD"

        # ── Recommended action & angle ──
        recommended_action, rationale, angle = self._recommend(vec, composite, tier, signals)

        # ── Deal size estimate ──
        multiplier = SECTOR_DEAL_MULTIPLIERS.get(sector, 1.5)
        deal_eur = BASE_DEAL_EUR * multiplier * (composite / 60.0)
        deal_eur = max(1000.0, round(deal_eur / 1000) * 1000)  # arrondi millier

        result = CompositeScorerResult(
            prospect_id=prospect_id,
            vector=vec,
            composite_score=composite,
            win_probability=win_prob,
            tier=tier,
            recommended_action=recommended_action,
            action_rationale=rationale,
            best_angle=angle,
            estimated_deal_eur=deal_eur,
        )

        with self._lock:
            self._history.append(asdict(result))
            if len(self._history) > 2000:
                self._history = self._history[-1000:]

        log.info(
            "CompositeScorerV2 [%s] composite=%.1f tier=%s win=%.0f%% deal=%.0fEUR",
            prospect_id[:12], composite, tier, win_prob * 100, deal_eur,
        )
        return result

    def _recommend(
        self, vec: ScoreVector, composite: float, tier: str, signals: Dict
    ) -> Tuple[str, str, str]:
        """
        Retourne (action, rationale, angle_message) selon le profil du vecteur.
        """
        weakest = vec.weakest()
        strongest = vec.strongest()

        # HOT → agir maintenant
        if tier == "HOT":
            if vec.accessibility >= 0.7:
                return (
                    "send_personalized_offer",
                    f"Score={composite:.0f} + décideur accessible → offre directe",
                    f"Angle {strongest.replace('_', ' ')}: urgence confirmée, solution immédiate",
                )
            return (
                "activate_warm_path",
                f"Score={composite:.0f} mais accessibilité={vec.accessibility:.2f} → trouver introduction",
                "Angle valeur : ROI rapide + conformité NIS2 avant deadline",
            )

        # WARM → qualifier + nourrir
        if tier == "WARM":
            if weakest == "budget_confidence":
                return (
                    "send_value_content",
                    "Budget incertain → envoyer contenu ROI avant l'offre",
                    "Angle éducatif : coût d'un incident OT vs coût de la conformité",
                )
            if weakest == "regulatory_pressure":
                return (
                    "send_regulatory_alert",
                    "Pression réglementaire faible → activer le levier NIS2/IEC62443",
                    "Angle risque : sanctions, deadline réglementaire imminente",
                )
            return (
                "qualify_and_enrich",
                f"Score WARM → enrichir dimension '{weakest}' avant pitch",
                "Angle curiosité : poser 1 question ouverte sur leur plan de conformité",
            )

        # COOL / COLD → nurture long terme
        return (
            "add_to_nurture_sequence",
            f"Score faible ({composite:.0f}) → nurture 90 jours",
            "Angle awareness : contenu LinkedIn sans démarche commerciale directe",
        )

    def batch_score(
        self, prospects: List[Dict[str, Any]]
    ) -> List[CompositeScorerResult]:
        """
        Score une liste de prospects et retourne triés par composite_score.
        """
        results = []
        for p in prospects:
            try:
                r = self.score(
                    prospect_id=p.get("id", f"p_{len(results)}"),
                    signals=p.get("signals", p),
                    sector=p.get("sector", ""),
                )
                results.append(r)
            except Exception as exc:
                log.error("CompositeScorerV2 batch_score error for %s: %s", p.get("id", "?"), exc)

        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results

    def calibrate_weights(self, historical_data: List[Dict]) -> Dict[str, float]:
        """
        Recalibre les poids à partir de données historiques won/lost.
        Utilise une heuristique gradient simple (pas de ML requis).
        """
        if len(historical_data) < 10:
            log.warning("CompositeScorerV2 — calibration ignorée: < 10 samples")
            return self._weights

        dims = ["urgency", "budget_confidence", "accessibility",
                "regulatory_pressure", "competitive_isolation", "timing_window"]

        # Corrélation simple victoire/dimension pour chaque dimension
        correlations = {}
        for dim in dims:
            won_vals = [d.get(dim, 0) for d in historical_data if d.get("outcome") == "won"]
            lost_vals = [d.get(dim, 0) for d in historical_data if d.get("outcome") == "lost"]
            if not won_vals or not lost_vals:
                correlations[dim] = self._weights[dim]
                continue
            avg_won = sum(won_vals) / len(won_vals)
            avg_lost = sum(lost_vals) / len(lost_vals)
            diff = avg_won - avg_lost
            correlations[dim] = max(0.03, self._weights[dim] + diff * 0.1)

        # Normaliser
        total = sum(correlations.values())
        new_weights = {k: round(v / total, 4) for k, v in correlations.items()}

        with self._lock:
            self._weights = new_weights

        log.info("CompositeScorerV2 — poids recalibrés: %s", new_weights)
        return new_weights

    def status(self) -> Dict:
        """État du scorer."""
        return {
            "weights": self._weights,
            "history_size": len(self._history),
            "base_deal_eur": BASE_DEAL_EUR,
            "sector_multipliers": SECTOR_DEAL_MULTIPLIERS,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

composite_scorer = CompositeScorerV2()
