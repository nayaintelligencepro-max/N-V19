"""NAYA V19 - Cost Policy - Politique de gestion des couts LLM et API."""
import logging, os
from typing import Dict, Optional

log = logging.getLogger("NAYA.POLICY.COST")

class CostPolicy:
    """Politique de couts: priorise les providers gratuits, limite les depenses."""

    DAILY_BUDGET_EUR = float(os.getenv("NAYA_DAILY_LLM_BUDGET", "5.0"))
    PROVIDER_COSTS = {
        "groq": 0.0, "ollama": 0.0, "huggingface": 0.0,
        "deepseek": 0.001, "anthropic": 0.015, "openai": 0.01, "grok": 0.005,
    }

    def __init__(self):
        self._daily_spent = 0.0
        self._provider_usage: Dict[str, int] = {}

    def can_use_provider(self, provider: str) -> bool:
        cost = self.PROVIDER_COSTS.get(provider, 0.1)
        if cost == 0:
            return True
        return self._daily_spent + cost <= self.DAILY_BUDGET_EUR

    def record_usage(self, provider: str, tokens: int = 0) -> None:
        cost = self.PROVIDER_COSTS.get(provider, 0.1) * (tokens / 1000 if tokens else 1)
        self._daily_spent += cost
        self._provider_usage[provider] = self._provider_usage.get(provider, 0) + 1

    def get_cheapest_provider(self, exclude: list = None) -> str:
        exclude = exclude or []
        available = [(p, c) for p, c in self.PROVIDER_COSTS.items() if p not in exclude]
        available.sort(key=lambda x: x[1])
        for p, c in available:
            if self.can_use_provider(p):
                return p
        return "groq"  # Fallback gratuit

    def reset_daily(self) -> None:
        self._daily_spent = 0.0

    def get_stats(self) -> Dict:
        return {
            "daily_budget": self.DAILY_BUDGET_EUR,
            "daily_spent": round(self._daily_spent, 4),
            "remaining": round(self.DAILY_BUDGET_EUR - self._daily_spent, 4),
            "usage": self._provider_usage
        }
