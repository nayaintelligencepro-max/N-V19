"""NAYA V19 - LLM Orchestrator - Orchestre les appels LLM entre providers."""
import time, logging
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.ORCH.LLM")

class LLMOrchestrator:
    """Orchestre les appels LLM: routing, fallback, cache, budget."""

    def __init__(self):
        self._call_log: List[Dict] = []
        self._provider_stats: Dict[str, Dict] = {}
        self._cache: Dict[str, Dict] = {}
        self._total_calls = 0
        self._total_cached = 0

    def route_call(self, prompt: str, task_type: str = "general",
                   max_tokens: int = 2048) -> Dict:
        """Route un appel LLM vers le meilleur provider."""
        # Check cache
        cache_key = f"{task_type}:{prompt[:100]}"
        if cache_key in self._cache:
            age = time.time() - self._cache[cache_key]["ts"]
            if age < 1800:
                self._total_cached += 1
                return {**self._cache[cache_key], "cached": True}
        # Get provider chain
        try:
            from NAYA_CORE.execution.policies.fallback_policy import FallbackPolicy
            chain = FallbackPolicy().get_chain(task_type)
        except Exception:
            chain = ["groq", "deepseek", "huggingface", "ollama"]
        self._total_calls += 1
        return {
            "provider_chain": chain, "task_type": task_type,
            "max_tokens": max_tokens, "total_calls": self._total_calls,
            "status": "ready_to_execute"
        }

    def record_result(self, provider: str, success: bool, latency_ms: float, tokens: int = 0) -> None:
        if provider not in self._provider_stats:
            self._provider_stats[provider] = {"calls": 0, "success": 0, "total_latency": 0, "tokens": 0}
        stats = self._provider_stats[provider]
        stats["calls"] += 1
        if success:
            stats["success"] += 1
        stats["total_latency"] += latency_ms
        stats["tokens"] += tokens

    def cache_result(self, key: str, result: Dict) -> None:
        self._cache[key] = {**result, "ts": time.time()}
        if len(self._cache) > 500:
            oldest = sorted(self._cache.keys(), key=lambda k: self._cache[k]["ts"])[:100]
            for k in oldest:
                del self._cache[k]

    def get_provider_ranking(self) -> List[Dict]:
        ranking = []
        for p, s in self._provider_stats.items():
            rate = s["success"] / s["calls"] if s["calls"] > 0 else 0
            avg_lat = s["total_latency"] / s["calls"] if s["calls"] > 0 else 0
            ranking.append({"provider": p, "success_rate": round(rate, 3), "avg_latency_ms": round(avg_lat, 1), "calls": s["calls"]})
        ranking.sort(key=lambda x: x["success_rate"], reverse=True)
        return ranking

    def get_stats(self) -> Dict:
        return {
            "total_calls": self._total_calls, "cached_calls": self._total_cached,
            "cache_hit_rate": self._total_cached / self._total_calls if self._total_calls > 0 else 0,
            "provider_ranking": self.get_provider_ranking(),
            "cache_size": len(self._cache)
        }
