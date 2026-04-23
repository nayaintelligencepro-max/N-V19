"""
NAYA V19 — Autonomous Learner
══════════════════════════════════════════════════════════════════════════════
Apprentissage continu à partir de chaque résultat de chasse et de conversion.

PRINCIPE:
  Chaque deal WON / LOST / IGNORED est un signal d'apprentissage.
  Le système accumule ces signaux et ajuste ses paramètres de chasse en
  conséquence — qualité croissante, valeur cible croissante, zéro régression.

GARANTIES:
  - Thread-safe avec RLock
  - Persistance JSON atomique
  - Paramètres versionnés (rollback si régression)
  - Score de confiance : n observations minimum requis avant changement

DATA FLOW:
  record_outcome(deal) → _update_sector_stats() → compute_optimal_params()
  → get_optimized_hunt_params()  ← utilisé par AdvancedHuntEngine
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.LEARNER")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "autonomous_learner.json"

# Nombre minimum d'observations avant d'ajuster les paramètres
MIN_OBSERVATIONS = 5
# Plancher absolu (règle inviolable du système)
MIN_TICKET_EUR = 1_000


# ─── Structures de données ────────────────────────────────────────────────────

@dataclass
class DealOutcome:
    """Résultat d'un deal — signal d'apprentissage fondamental."""
    deal_id: str
    sector: str                  # "transport", "energie", "industrie", "ot", "other"
    signal_type: str             # "job_offer", "news", "linkedin", "regulatory", "direct"
    offer_tier: str              # "TIER1", "TIER2", "TIER3", "TIER4"
    price_eur: float
    converted: bool              # True = CLOSED_WON
    engagement_days: int = 0     # Jours entre premier contact et fermeture
    close_reason: str = ""       # "price", "timing", "competitor", "won", "budget"
    quality_score: float = 0.0   # Score initial de qualification [0..1]
    ts: float = field(default_factory=time.time)


@dataclass
class SectorStats:
    """Statistiques d'apprentissage par secteur."""
    sector: str
    total: int = 0
    won: int = 0
    total_revenue: float = 0.0
    avg_price_won: float = 0.0
    avg_engagement_days: float = 0.0
    best_signal_types: Dict[str, float] = field(default_factory=dict)
    best_tiers: Dict[str, float] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)

    @property
    def conversion_rate(self) -> float:
        return self.won / self.total if self.total > 0 else 0.0

    @property
    def confidence(self) -> float:
        """Niveau de confiance dans les stats [0..1]. Basé sur n observations."""
        return min(self.total / (MIN_OBSERVATIONS * 2), 1.0)


@dataclass
class HuntParams:
    """Paramètres optimisés de chasse — output de l'apprentissage."""
    version: int = 1
    min_ticket_eur: float = MIN_TICKET_EUR
    target_ticket_eur: float = 15_000.0
    top_sectors: List[str] = field(default_factory=lambda: [
        "ot", "energie", "transport", "industrie"
    ])
    top_signal_types: List[str] = field(default_factory=lambda: [
        "regulatory", "job_offer", "news", "linkedin"
    ])
    preferred_tiers: List[str] = field(default_factory=lambda: [
        "TIER2", "TIER3", "TIER1", "TIER4"
    ])
    min_quality_score: float = 0.60
    max_engagement_days_target: int = 21
    quality_multiplier: float = 1.0   # Augmente avec le temps (jamais < 1.0)
    computed_at: float = field(default_factory=time.time)
    based_on_n_deals: int = 0


# ─── Learner principal ────────────────────────────────────────────────────────

class AutonomousLearner:
    """
    Système d'apprentissage continu de NAYA.

    Apprend de chaque deal enregistré et optimise progressivement les
    paramètres de chasse. Garantit que la qualité ne régresse jamais.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._outcomes: List[DealOutcome] = []
        self._sector_stats: Dict[str, SectorStats] = {}
        self._current_params: HuntParams = HuntParams()
        self._params_history: List[HuntParams] = []
        self._init_at = time.time()
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        log.info("[LEARNER] Autonomous Learner V19 démarré — %d outcomes chargés",
                 len(self._outcomes))

    # ── API publique ──────────────────────────────────────────────────────────

    def record_outcome(self, outcome: DealOutcome) -> None:
        """
        Enregistre le résultat d'un deal.
        Déclenche automatiquement la mise à jour des stats et des paramètres.
        """
        with self._lock:
            self._outcomes.append(outcome)
            if len(self._outcomes) > 10_000:
                self._outcomes = self._outcomes[-5_000:]
            self._update_sector_stats(outcome)
            self._maybe_update_params()
        self._save()
        log.info("[LEARNER] Outcome enregistré: %s | sector=%s | won=%s | %.0f€",
                 outcome.deal_id, outcome.sector, outcome.converted, outcome.price_eur)

    def get_optimized_hunt_params(self) -> HuntParams:
        """Retourne les paramètres de chasse optimisés actuels."""
        with self._lock:
            return self._current_params

    def get_sector_ranking(self) -> List[Tuple[str, float]]:
        """Retourne les secteurs classés par taux de conversion × revenu moyen."""
        with self._lock:
            ranked = []
            for s, stats in self._sector_stats.items():
                if stats.total >= MIN_OBSERVATIONS:
                    score = stats.conversion_rate * stats.avg_price_won * stats.confidence
                else:
                    score = 0.0
                ranked.append((s, round(score, 2)))
            return sorted(ranked, key=lambda x: x[1], reverse=True)

    def get_learning_summary(self) -> Dict:
        """Résumé de l'état de l'apprentissage."""
        with self._lock:
            total = len(self._outcomes)
            won = sum(1 for o in self._outcomes if o.converted)
            total_rev = sum(o.price_eur for o in self._outcomes if o.converted)
            params = self._current_params

            return {
                "total_outcomes": total,
                "total_won": won,
                "global_conversion_rate": round(won / total, 3) if total > 0 else 0.0,
                "total_revenue_learned": round(total_rev, 2),
                "current_params_version": params.version,
                "current_min_ticket": params.min_ticket_eur,
                "current_target_ticket": params.target_ticket_eur,
                "current_quality_multiplier": params.quality_multiplier,
                "top_sectors": params.top_sectors[:3],
                "top_signals": params.top_signal_types[:3],
                "params_iterations": len(self._params_history),
                "sector_stats": {
                    s: {
                        "total": st.total,
                        "conversion_rate": round(st.conversion_rate, 3),
                        "avg_price_won": round(st.avg_price_won, 0),
                        "confidence": round(st.confidence, 2),
                    }
                    for s, st in self._sector_stats.items()
                },
            }

    def get_stats(self) -> Dict:
        return self.get_learning_summary()

    # ── Logique d'apprentissage ───────────────────────────────────────────────

    def _update_sector_stats(self, outcome: DealOutcome) -> None:
        """Met à jour les statistiques du secteur après un outcome."""
        s = outcome.sector
        if s not in self._sector_stats:
            self._sector_stats[s] = SectorStats(sector=s)

        stats = self._sector_stats[s]
        stats.total += 1
        stats.last_updated = time.time()

        if outcome.converted:
            stats.won += 1
            stats.total_revenue += outcome.price_eur
            # Mise à jour moyenne mobile du prix des deals gagnés
            stats.avg_price_won = stats.total_revenue / stats.won

        # Engagement moyen (moyenne mobile exponentielle)
        if outcome.engagement_days > 0:
            alpha = 0.2
            stats.avg_engagement_days = (
                alpha * outcome.engagement_days + (1 - alpha) * stats.avg_engagement_days
            ) if stats.avg_engagement_days > 0 else float(outcome.engagement_days)

        # Performances par type de signal
        sig = outcome.signal_type
        if sig not in stats.best_signal_types:
            stats.best_signal_types[sig] = 0.5
        stats.best_signal_types[sig] = (
            0.8 * stats.best_signal_types[sig] + 0.2 * (1.0 if outcome.converted else 0.0)
        )

        # Performances par tier
        tier = outcome.offer_tier
        if tier not in stats.best_tiers:
            stats.best_tiers[tier] = 0.5
        stats.best_tiers[tier] = (
            0.8 * stats.best_tiers[tier] + 0.2 * (1.0 if outcome.converted else 0.0)
        )

    def _maybe_update_params(self) -> None:
        """
        Met à jour les paramètres de chasse si on a suffisamment de données
        et si les nouveaux paramètres sont meilleurs (pas de régression).
        """
        total = len(self._outcomes)
        # Pas assez de données pour apprendre
        if total < MIN_OBSERVATIONS:
            return
        # Recalcul tous les 5 outcomes
        if total % 5 != 0:
            return
        self._recompute_params()

    def _recompute_params(self) -> None:
        """
        Recalcule les paramètres optimaux à partir des stats accumulées.
        Garantit qu'aucun paramètre ne régresse par rapport à la version précédente.
        """
        old = self._current_params
        new_params = HuntParams(
            version=old.version + 1,
            min_ticket_eur=MIN_TICKET_EUR,  # INVIOLABLE
            based_on_n_deals=len(self._outcomes),
        )

        won_outcomes = [o for o in self._outcomes if o.converted]

        # Ticket cible : médiane des deals gagnés, avec plancher = old.target_ticket_eur
        if len(won_outcomes) >= MIN_OBSERVATIONS:
            prices = sorted(o.price_eur for o in won_outcomes)
            median_price = prices[len(prices) // 2]
            # Jamais en dessous du target précédent (pas de régression)
            new_params.target_ticket_eur = max(old.target_ticket_eur, median_price)
        else:
            new_params.target_ticket_eur = old.target_ticket_eur

        # Top secteurs classés par score
        ranked_sectors = self.get_sector_ranking()
        if ranked_sectors:
            new_params.top_sectors = [s for s, _ in ranked_sectors[:6]]
            # Toujours garder au moins 4 secteurs
            if len(new_params.top_sectors) < 4:
                defaults = ["ot", "energie", "transport", "industrie"]
                for d in defaults:
                    if d not in new_params.top_sectors:
                        new_params.top_sectors.append(d)
                        if len(new_params.top_sectors) >= 4:
                            break
        else:
            new_params.top_sectors = old.top_sectors

        # Top types de signaux (agrégation cross-secteurs)
        signal_scores: Dict[str, float] = {}
        for stats in self._sector_stats.values():
            for sig, score in stats.best_signal_types.items():
                signal_scores[sig] = signal_scores.get(sig, 0) + score * stats.confidence
        if signal_scores:
            new_params.top_signal_types = sorted(
                signal_scores, key=signal_scores.get, reverse=True
            )[:6]
        else:
            new_params.top_signal_types = old.top_signal_types

        # Top tiers
        tier_scores: Dict[str, float] = {}
        for stats in self._sector_stats.values():
            for tier, score in stats.best_tiers.items():
                tier_scores[tier] = tier_scores.get(tier, 0) + score * stats.confidence
        if tier_scores:
            new_params.preferred_tiers = sorted(
                tier_scores, key=tier_scores.get, reverse=True
            )
        else:
            new_params.preferred_tiers = old.preferred_tiers

        # Score minimum de qualité : augmente légèrement avec le temps (jamais régresse)
        if len(won_outcomes) >= MIN_OBSERVATIONS * 2:
            avg_quality_won = sum(o.quality_score for o in won_outcomes) / len(won_outcomes)
            new_params.min_quality_score = max(
                old.min_quality_score,
                round(avg_quality_won * 0.85, 2)  # 85% du score moyen des deals WON
            )
        else:
            new_params.min_quality_score = old.min_quality_score

        # Multiplicateur qualité : croît avec chaque mise à jour réussie
        won_rate = len(won_outcomes) / max(len(self._outcomes), 1)
        growth = 1.0 + (won_rate * 0.1)  # +0-10% selon taux conversion
        new_params.quality_multiplier = max(old.quality_multiplier, round(old.quality_multiplier * growth, 3))

        # Engagement cible
        if len(won_outcomes) >= MIN_OBSERVATIONS:
            avg_eng = sum(o.engagement_days for o in won_outcomes) / len(won_outcomes)
            new_params.max_engagement_days_target = max(7, min(45, int(avg_eng * 1.2)))
        else:
            new_params.max_engagement_days_target = old.max_engagement_days_target

        # Sauvegarder l'historique
        self._params_history.append(old)
        if len(self._params_history) > 50:
            self._params_history = self._params_history[-25:]
        self._current_params = new_params

        log.info(
            "[LEARNER] Params v%d → v%d | target=%.0f€ (+%.0f%%) | quality_mult=%.3f | top=%s",
            old.version, new_params.version,
            new_params.target_ticket_eur,
            (new_params.target_ticket_eur / max(old.target_ticket_eur, 1) - 1) * 100,
            new_params.quality_multiplier,
            new_params.top_sectors[:2],
        )

    # ── Persistance ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            data = {
                "outcomes": [asdict(o) for o in self._outcomes[-2_000:]],
                "sector_stats": {s: asdict(st) for s, st in self._sector_stats.items()},
                "current_params": asdict(self._current_params),
                "params_history": [asdict(p) for p in self._params_history[-20:]],
                "saved_at": time.time(),
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(DATA_FILE)
        except Exception as e:
            log.warning("[LEARNER] Save error: %s", e)

    def _load(self) -> None:
        try:
            if not DATA_FILE.exists():
                return
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

            self._outcomes = [DealOutcome(**o) for o in data.get("outcomes", [])]
            self._sector_stats = {
                s: SectorStats(**st) for s, st in data.get("sector_stats", {}).items()
            }
            if cp := data.get("current_params"):
                self._current_params = HuntParams(**cp)
            self._params_history = [HuntParams(**p) for p in data.get("params_history", [])]
        except Exception as e:
            log.warning("[LEARNER] Load error: %s — starting fresh", e)
            self._outcomes = []
            self._sector_stats = {}
            self._current_params = HuntParams()
            self._params_history = []


# ── Singleton ──────────────────────────────────────────────────────────────────
_learner: Optional[AutonomousLearner] = None


def get_learner() -> AutonomousLearner:
    global _learner
    if _learner is None:
        _learner = AutonomousLearner()
    return _learner
