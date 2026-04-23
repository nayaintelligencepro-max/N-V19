"""NAYA V19 - Adaptive Evolution Core - Evolution adaptative continue."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.EVOLUTION.ADAPTIVE")

class AdaptiveEvolutionCore:
    """Le systeme evolue en continu en s adaptant aux resultats."""

    def __init__(self):
        self._evolution_log: List[Dict] = []
        self._fitness_scores: Dict[str, float] = {}

    def evaluate_fitness(self, module: str, metrics: Dict) -> float:
        """Evalue la fitness d un module (0-1)."""
        success_rate = metrics.get("success_rate", 0.5)
        efficiency = metrics.get("efficiency", 0.5)
        reliability = metrics.get("reliability", 0.5)
        fitness = success_rate * 0.4 + efficiency * 0.35 + reliability * 0.25
        self._fitness_scores[module] = fitness
        return round(fitness, 3)

    def suggest_evolution(self, module: str) -> Dict:
        fitness = self._fitness_scores.get(module, 0.5)
        if fitness >= 0.8:
            return {"action": "extend", "reason": "Haute performance - etendre les capacites"}
        elif fitness >= 0.5:
            return {"action": "optimize", "reason": "Performance correcte - optimiser"}
        else:
            return {"action": "redesign", "reason": "Performance faible - repenser le module"}

    def apply_evolution(self, module: str, evolution_type: str, details: str) -> Dict:
        entry = {
            "module": module, "type": evolution_type,
            "details": details, "fitness_before": self._fitness_scores.get(module, 0),
            "ts": time.time()
        }
        self._evolution_log.append(entry)
        log.info(f"[EVOLUTION] {module}: {evolution_type} - {details}")
        return entry

    def get_evolution_trajectory(self) -> List[Dict]:
        return self._evolution_log[-20:]

    def get_stats(self) -> Dict:
        return {
            "modules_tracked": len(self._fitness_scores),
            "avg_fitness": sum(self._fitness_scores.values()) / max(1, len(self._fitness_scores)),
            "total_evolutions": len(self._evolution_log),
            "top_modules": sorted(
                [{"module": m, "fitness": f} for m, f in self._fitness_scores.items()],
                key=lambda x: x["fitness"], reverse=True
            )[:5]
        }
