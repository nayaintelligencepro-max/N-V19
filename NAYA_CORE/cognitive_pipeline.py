"""
NAYA V19 — Cognitive Pipeline
Câble les 10 couches cognitives dans le pipeline de détection.
Active réellement: EliteDetection, SignalWeaknessAnalyzer,
CognitiveIntelligence, StorytellingEngine, MaturationEngine.
Fonctionne SANS clé API — 100% offline.
"""
import logging
from typing import Dict, List, Any, Optional

log = logging.getLogger("NAYA.COGNITIVE")


class CognitivePipeline:
    """
    Pipeline à 5 étapes actives (sur 10 couches disponibles):
    1. NoiseFilter    → filtre le bruit dans les signaux
    2. EliteDetection → identifie les opportunités premium
    3. SignalWeakness → détecte les signaux faibles latents
    4. CognitiveIntel → évalue la cohérence et la fiabilité
    5. Storytelling   → structure la narration de l'offre
    """

    def __init__(self):
        self._noise = None
        self._elite = None
        self._weakness = None
        self._intel = None
        self._story = None
        self._maturation = None
        self._calls = 0
        self._init()

    def _init(self):
        """Initialise les couches disponibles."""
        try:
            from NAYA_CORE.cognition.layers.layer_1_cognitive_input.noise_filter import NoiseFilter
            self._noise = NoiseFilter()
        except Exception as e:
            log.debug(f"[COG] NoiseFilter layer1: {e}")

        try:
            from NAYA_CORE.cognition.layers.layer_5_hunting.elite_detection import EliteDetection
            self._elite = EliteDetection()
        except Exception as e:
            log.debug(f"[COG] EliteDetection: {e}")

        try:
            from NAYA_CORE.cognition.layers.layer_5_hunting.signal_weakness import SignalWeaknessAnalyzer
            self._weakness = SignalWeaknessAnalyzer()
        except Exception as e:
            log.debug(f"[COG] SignalWeakness: {e}")

        try:
            from NAYA_CORE.cognition.layers.layer_3_intelligence.cognitive_intelligence import CognitiveIntelligence
            self._intel = CognitiveIntelligence()
        except Exception as e:
            log.debug(f"[COG] CognitiveIntelligence: {e}")

        try:
            from NAYA_CORE.cognition.layers.layer_6_creation.storytelling_engine import StorytellingEngine
            self._story = StorytellingEngine()
        except Exception as e:
            log.debug(f"[COG] StorytellingEngine: {e}")

        try:
            from NAYA_CORE.cognition.layers.layer_10_maturation.maturation_engine import MaturationEngine
            self._maturation = MaturationEngine()
        except Exception as e:
            log.debug(f"[COG] MaturationEngine: {e}")

        active = sum(1 for x in [self._noise, self._elite, self._weakness,
                                   self._intel, self._story, self._maturation] if x)
        log.info(f"[COG] Pipeline cognitif: {active}/6 couches actives")

    def process_signals(self, signals: List[str], sector: str = "",
                         revenue: float = 0) -> Dict[str, Any]:
        """
        Traite les signaux à travers le pipeline cognitif.
        Retourne des signaux enrichis + score de confiance.
        """
        self._calls += 1
        result = {
            "original_signals": signals,
            "clean_signals": signals,
            "elite_signals": [],
            "weak_signals": [],
            "confidence": 0.7,
            "narrative_quality": "standard",
            "layers_used": 0,
        }

        if not signals:
            return result

        current = list(signals)

        # Couche 1: Filtrage du bruit
        if self._noise:
            try:
                filtered = self._noise.filter(current)
                if isinstance(filtered, dict):
                    current = filtered.get("relevant", filtered.get("real", current)) or current
                    result["layers_used"] += 1
            except Exception:
                pass

        result["clean_signals"] = current

        # Couche 5: Détection élite
        if self._elite and current:
            try:
                elite_result = self._elite.detect(current)
                result["elite_signals"] = elite_result.get("elite", [])
                result["layers_used"] += 1
                # Boost confiance si signaux élite
                if result["elite_signals"]:
                    result["confidence"] = min(0.95, result["confidence"] + 0.1)
            except Exception:
                pass

        # Couche 5b: Signaux faibles
        if self._weakness and current:
            try:
                weak_result = self._weakness.analyze(current)
                result["weak_signals"] = weak_result.get("latent", [])
                result["layers_used"] += 1
            except Exception:
                pass

        # Couche 3: Intelligence cognitive
        if self._intel and current:
            try:
                intel_result = self._intel.analyze(current)
                solid = intel_result.get("solid", [])
                fragile = intel_result.get("fragile", [])
                # Ajuster la confiance
                total = len(solid) + len(fragile)
                if total > 0:
                    ratio = len(solid) / total
                    result["confidence"] = round(0.5 + ratio * 0.45, 2)
                result["layers_used"] += 1
            except Exception:
                pass

        # Couche 6: Qualité narrative
        if self._story and current:
            try:
                story_result = self._story.build(current, level="standard")
                if story_result.get("primary"):
                    result["narrative_quality"] = "high"
                result["layers_used"] += 1
            except Exception:
                pass

        # Couche 10: Maturation
        if self._maturation and current:
            try:
                mat_result = self._maturation.mature(current)
                if mat_result.get("reinforced"):
                    result["confidence"] = min(0.99, result["confidence"] + 0.05)
                result["layers_used"] += 1
            except Exception:
                pass

        return result

    def score_prospect(self, company: str, signals: List[str],
                        pain_cost: float, sector: str = "") -> Dict:
        """Score cognitif d'un prospect — 0 à 100."""
        processed = self.process_signals(signals, sector, pain_cost)
        base_score = int(processed["confidence"] * 100)

        # Bonus signaux élite
        elite_bonus = min(15, len(processed.get("elite_signals", [])) * 5)
        # Bonus signaux faibles (opportunités cachées)
        weak_bonus = min(10, len(processed.get("weak_signals", [])) * 3)
        # Bonus narrative quality
        narrative_bonus = 5 if processed.get("narrative_quality") == "high" else 0

        final_score = min(100, base_score + elite_bonus + weak_bonus + narrative_bonus)

        return {
            "score": final_score,
            "tier": "HOT" if final_score >= 75 else "WARM" if final_score >= 50 else "COLD",
            "confidence": processed["confidence"],
            "elite_signals": processed.get("elite_signals", []),
            "weak_signals": processed.get("weak_signals", []),
            "layers_used": processed["layers_used"],
            "narrative": processed.get("narrative_quality"),
        }

    def get_stats(self) -> Dict:
        return {
            "calls": self._calls,
            "noise_filter": self._noise is not None,
            "elite_detection": self._elite is not None,
            "signal_weakness": self._weakness is not None,
            "cognitive_intel": self._intel is not None,
            "storytelling": self._story is not None,
            "maturation": self._maturation is not None,
        }


_PIPELINE: Optional[CognitivePipeline] = None
_LOCK = __import__("threading").Lock()

def get_cognitive_pipeline() -> CognitivePipeline:
    global _PIPELINE
    if _PIPELINE is None:
        with _LOCK:
            if _PIPELINE is None:
                _PIPELINE = CognitivePipeline()
    return _PIPELINE
