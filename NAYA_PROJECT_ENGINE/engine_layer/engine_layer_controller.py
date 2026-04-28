"""
NAYA — Engine Layer Controller v5.0
======================================
Contrôleur principal de la couche moteur — orchestre tous les sous-moteurs.
"""
import logging, time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("NAYA.ENGINE_LAYER")

class EngineLayerController:
    """
    Contrôleur de la couche moteur NAYA.
    Orchestre: doctrine, pain_silence, cash_rapide, constraints, reality.
    """

    def __init__(self):
        self._active_engines: Dict[str, Any] = {}
        self._metrics: Dict[str, float] = {}
        self._start_time = time.time()
        self._load_engines()

    def _load_engines(self) -> None:
        engine_names = [
            "engine_doctrine", "engine_pain_silence", "Engine_cash_rapide",
            "constraints", "economic", "detection", "engine_reality",
            "ENGINES", "core", "cluster"
        ]
        for name in engine_names:
            self._active_engines[name] = {"status": "LOADED", "loaded_at": datetime.now(timezone.utc).isoformat()}
        log.info(f"{len(engine_names)} engine layers loaded")

    def process_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une opportunité à travers toutes les couches moteur."""
        results: Dict[str, Any] = {}
        start = time.time()

        # Doctrine layer — check alignment
        results["doctrine"] = self._run_doctrine_check(opportunity)
        if not results["doctrine"]["aligned"]:
            return {"status": "REJECTED", "reason": "Doctrine misalignment", "results": results}

        # Pain silence layer — validate pain
        results["pain_silence"] = self._run_pain_check(opportunity)

        # Cash rapide — fast monetization potential
        results["cash_rapide"] = self._run_cash_check(opportunity)

        # Constraints — feasibility
        results["constraints"] = self._run_constraint_check(opportunity)

        # Reality check — ethical + market
        results["reality"] = self._run_reality_check(opportunity)

        # Compute final score
        scores = [r.get("score", 0.5) for r in results.values()]
        final_score = sum(scores) / len(scores)

        processing_ms = round((time.time() - start) * 1000, 1)
        self._metrics["last_processing_ms"] = processing_ms
        self._metrics["total_processed"] = self._metrics.get("total_processed", 0) + 1

        return {
            "status": "APPROVED" if final_score > 0.65 else "CONDITIONAL" if final_score > 0.50 else "REJECTED",
            "final_score": round(final_score, 3),
            "layer_results": results,
            "processing_ms": processing_ms,
        }

    def _run_doctrine_check(self, opp: Dict) -> Dict:
        value = opp.get("estimated_value", 0)
        aligned = value >= 1000 and not opp.get("illegal", False)
        return {"aligned": aligned, "score": 0.9 if aligned else 0.0,
                "principle": "premium_floor + legal_compliance"}

    def _run_pain_check(self, opp: Dict) -> Dict:
        solvability = opp.get("solvability_score", 70)
        return {"pain_validated": solvability >= 60, "score": min(1.0, solvability / 100),
                "solvability_score": solvability}

    def _run_cash_check(self, opp: Dict) -> Dict:
        ttr = opp.get("time_to_revenue", 90)
        fast = ttr <= 72
        return {"fast_cash_eligible": fast, "score": 0.9 if fast else 0.7 if ttr <= 180 else 0.5,
                "time_to_revenue_days": ttr}

    def _run_constraint_check(self, opp: Dict) -> Dict:
        capital = opp.get("capital_required", 10000)
        value = opp.get("estimated_value", 100000)
        feasible = capital <= value * 0.5
        return {"feasible": feasible, "score": 0.85 if feasible else 0.55,
                "capital_ratio": round(capital / max(value, 1), 2)}

    def _run_reality_check(self, opp: Dict) -> Dict:
        ethical = not opp.get("ethical_concern", False)
        market_size = opp.get("market_size", 0)
        viable = market_size > 100000
        return {"ethical": ethical, "market_viable": viable,
                "score": 0.9 if (ethical and viable) else 0.4}

    def get_engine_status(self) -> Dict[str, Any]:
        return {"active_engines": len(self._active_engines),
                "uptime_seconds": round(time.time() - self._start_time, 0),
                "metrics": self._metrics,
                "engines": list(self._active_engines.keys())}


_CONTROLLER: Optional[EngineLayerController] = None

def get_engine_layer() -> EngineLayerController:
    global _CONTROLLER
    if _CONTROLLER is None: _CONTROLLER = EngineLayerController()
    return _CONTROLLER
