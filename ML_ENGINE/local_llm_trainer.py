"""
NAYA V21 — Local LLM Trainer
Fine-tuning sur les 50 meilleures offres converties.
Entraîne un modèle de prompt optimization basé sur l'historique des deals gagnants.
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.ML_ENGINE.LOCAL_LLM_TRAINER")

ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = ROOT / "data" / "ml_training"
TRAINING_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainingExample:
    """Exemple d'entraînement : offre envoyée + résultat."""
    example_id: str
    company: str
    sector: str
    pain_description: str
    offer_text: str
    price_eur: int
    converted: bool
    conversion_value_eur: int
    time_to_close_days: int
    objections_handled: List[str] = field(default_factory=list)
    winning_phrases: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PromptOptimization:
    """Optimisation extraite de l'analyse des offres gagnantes."""
    sector: str
    winning_patterns: List[str]
    losing_patterns: List[str]
    optimal_price_range: Tuple[int, int]
    best_opening_phrases: List[str]
    best_cta: str
    avg_conversion_rate: float
    sample_size: int
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LocalLLMTrainer:
    """
    Entraîneur local : apprend des 50 meilleures offres converties.
    Extrait patterns gagnants → enrichit les prompts LLM automatiquement.
    """

    def __init__(self):
        self._examples: List[TrainingExample] = []
        self._optimizations: Dict[str, PromptOptimization] = {}
        self._load_data()
        log.info(
            "✅ LocalLLMTrainer initialisé (%d exemples, %d optimisations)",
            len(self._examples), len(self._optimizations),
        )

    def _examples_path(self) -> Path:
        return TRAINING_DIR / "training_examples.json"

    def _opts_path(self) -> Path:
        return TRAINING_DIR / "prompt_optimizations.json"

    def _load_data(self) -> None:
        # Load examples
        p = self._examples_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                self._examples = [TrainingExample(**e) for e in raw]
            except Exception as exc:
                log.warning("Training examples load error: %s", exc)
        # Load optimizations
        p2 = self._opts_path()
        if p2.exists():
            try:
                raw2 = json.loads(p2.read_text())
                for k, v in raw2.items():
                    v["optimal_price_range"] = tuple(v.get("optimal_price_range", [5000, 40000]))
                    self._optimizations[k] = PromptOptimization(**v)
            except Exception as exc:
                log.warning("Optimizations load error: %s", exc)

    def _save_data(self) -> None:
        try:
            self._examples_path().write_text(
                json.dumps([e.to_dict() for e in self._examples], ensure_ascii=False, indent=2)
            )
        except Exception as exc:
            log.warning("Save examples error: %s", exc)

    def add_example(self, example: TrainingExample) -> None:
        """Ajoute un exemple d'entraînement et déclenche une ré-analyse."""
        self._examples.append(example)
        self._save_data()
        # Ré-entraîner sur le secteur concerné
        self._train_sector(example.sector)
        log.info(
            "Exemple ajouté: %s sector=%s converted=%s",
            example.company, example.sector, example.converted,
        )

    def record_conversion(
        self,
        company: str,
        sector: str,
        pain: str,
        offer_text: str,
        price_eur: int,
        converted: bool,
        conversion_value_eur: int = 0,
        time_to_close_days: int = 0,
    ) -> TrainingExample:
        """Enregistre une conversion pour l'apprentissage."""
        import uuid
        example = TrainingExample(
            example_id=str(uuid.uuid4()),
            company=company,
            sector=sector,
            pain_description=pain,
            offer_text=offer_text,
            price_eur=price_eur,
            converted=converted,
            conversion_value_eur=conversion_value_eur,
            time_to_close_days=time_to_close_days,
            winning_phrases=self._extract_winning_phrases(offer_text) if converted else [],
        )
        self.add_example(example)
        return example

    def _train_sector(self, sector: str) -> None:
        """Analyse les exemples d'un secteur et extrait les patterns gagnants."""
        sector_examples = [e for e in self._examples if e.sector == sector]
        if len(sector_examples) < 3:
            return  # Pas assez de données

        wins = [e for e in sector_examples if e.converted]
        losses = [e for e in sector_examples if not e.converted]

        if not wins:
            return

        winning_patterns = self._extract_patterns(wins)
        losing_patterns = self._extract_patterns(losses)

        win_prices = [e.price_eur for e in wins]
        price_range = (min(win_prices), max(win_prices)) if win_prices else (5000, 40000)

        best_phrases = []
        for e in wins[:10]:
            best_phrases.extend(e.winning_phrases)
        best_phrases = list(dict.fromkeys(best_phrases))[:5]  # Unique, top 5

        conv_rate = round(len(wins) / len(sector_examples) * 100, 1) if sector_examples else 0

        opt = PromptOptimization(
            sector=sector,
            winning_patterns=winning_patterns[:10],
            losing_patterns=losing_patterns[:5],
            optimal_price_range=price_range,
            best_opening_phrases=best_phrases,
            best_cta=self._best_cta(wins),
            avg_conversion_rate=conv_rate,
            sample_size=len(sector_examples),
        )
        self._optimizations[sector] = opt
        try:
            self._opts_path().write_text(
                json.dumps(
                    {k: {**asdict(v), "optimal_price_range": list(v.optimal_price_range)}
                     for k, v in self._optimizations.items()},
                    ensure_ascii=False, indent=2,
                )
            )
        except Exception as exc:
            log.warning("Save optimizations error: %s", exc)
        log.info(
            "Secteur %s re-entraîné: %d exemples, conv_rate=%.1f%%, patterns=%d",
            sector, len(sector_examples), conv_rate, len(winning_patterns),
        )

    def _extract_winning_phrases(self, offer_text: str) -> List[str]:
        """Extrait des phrases clés d'une offre gagnante."""
        keywords = [
            "ROI", "conformité", "sécurité", "urgent", "deadline", "NIS2",
            "IEC 62443", "SCADA", "garantie", "résultats", "mission",
            "expertise", "certifié", "audit", "remédiation",
        ]
        phrases = []
        for sentence in offer_text.split("."):
            sentence = sentence.strip()
            if any(kw.lower() in sentence.lower() for kw in keywords) and len(sentence) > 20:
                phrases.append(sentence[:100])
        return phrases[:5]

    def _extract_patterns(self, examples: List[TrainingExample]) -> List[str]:
        """Extrait des patterns communs dans les offres."""
        if not examples:
            return []
        all_phrases: List[str] = []
        for e in examples:
            all_phrases.extend(e.winning_phrases)
            all_phrases.extend(self._extract_winning_phrases(e.offer_text))
        # Comptage des mots clés fréquents
        word_count: Dict[str, int] = {}
        for phrase in all_phrases:
            for word in phrase.lower().split():
                if len(word) > 4:
                    word_count[word] = word_count.get(word, 0) + 1
        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return [f"{w} (×{c})" for w, c in top_words]

    def _best_cta(self, wins: List[TrainingExample]) -> str:
        """Identifie le meilleur CTA (call-to-action) des offres gagnantes."""
        ctas = [
            "Disponible pour un appel de 30 min ?",
            "Je vous réserve un créneau cette semaine.",
            "Souhaitez-vous une démonstration de notre approche ?",
            "Pouvons-nous programmer un point de 20 min ?",
        ]
        # Simplification : retourner le CTA le plus fréquent dans les offres gagnantes
        if wins:
            offer_text_combined = " ".join(e.offer_text for e in wins[:5])
            for cta in ctas:
                if cta[:20].lower() in offer_text_combined.lower():
                    return cta
        return ctas[0]

    def get_optimization(self, sector: str) -> Optional[PromptOptimization]:
        return self._optimizations.get(sector)

    def get_rag_context(self, sector: str, pain: str, top_k: int = 3) -> List[str]:
        """
        RAG : récupère les k cas similaires gagnants pour enrichir le prompt.
        """
        relevant = [
            e for e in self._examples
            if e.sector == sector and e.converted
            and any(word in e.pain_description.lower() for word in pain.lower().split()[:5])
        ]
        if not relevant:
            # Fallback : n'importe quel exemple gagnant du secteur
            relevant = [e for e in self._examples if e.sector == sector and e.converted]
        # Trier par valeur de conversion
        relevant.sort(key=lambda e: e.conversion_value_eur, reverse=True)
        return [
            f"{e.company} ({e.sector}) — {e.price_eur:,} EUR — "
            f"Pain: {e.pain_description[:80]} — "
            f"Offre: {e.offer_text[:120]}"
            for e in relevant[:top_k]
        ]

    def get_stats(self) -> Dict:
        total = len(self._examples)
        converted = sum(1 for e in self._examples if e.converted)
        return {
            "total_examples": total,
            "converted": converted,
            "conversion_rate": round(converted * 100 / total, 1) if total > 0 else 0,
            "sectors_optimized": len(self._optimizations),
            "optimizations": {
                k: {
                    "conversion_rate": v.avg_conversion_rate,
                    "sample_size": v.sample_size,
                    "price_range": list(v.optimal_price_range),
                }
                for k, v in self._optimizations.items()
            },
        }

    def retrain_all(self) -> Dict[str, Any]:
        """Re-entraîne tous les secteurs."""
        sectors = list({e.sector for e in self._examples})
        for sector in sectors:
            self._train_sector(sector)
        return {"retrained_sectors": sectors, "total_examples": len(self._examples)}


# ── Singleton ─────────────────────────────────────────────────────────────────
_trainer: Optional[LocalLLMTrainer] = None


def get_local_trainer() -> LocalLLMTrainer:
    global _trainer
    if _trainer is None:
        _trainer = LocalLLMTrainer()
    return _trainer
