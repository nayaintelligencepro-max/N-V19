"""Routeur LLM avec fallback adaptatif et télémétrie santé."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Provider:
    name: str
    env_key: str


@dataclass
class ProviderHealth:
    success: int = 0
    failures: int = 0
    last_latency_ms: float = 0.0
    cooldown_until: float = 0.0


LLM_PRIORITY: List[Provider] = [
    Provider("groq", "GROQ_API_KEY"),
    Provider("anthropic", "ANTHROPIC_API_KEY"),
    Provider("openai", "OPENAI_API_KEY"),
    Provider("deepseek", "DEEPSEEK_API_KEY"),
    Provider("openai-mini", "OPENAI_API_KEY"),
]


class LLMRouter:
    """Sélectionne le meilleur provider disponible selon priorité + santé."""

    def __init__(self) -> None:
        self._health: Dict[str, ProviderHealth] = {
            p.name: ProviderHealth() for p in LLM_PRIORITY
        }

    def available(self) -> List[str]:
        """Liste ordonnée des providers configurés."""
        now = time.time()
        available: List[str] = []
        for p in LLM_PRIORITY:
            if not os.environ.get(p.env_key):
                continue
            if self._health[p.name].cooldown_until > now:
                continue
            available.append(p.name)
        return available

    def select(self) -> str:
        """Retourne le provider actif ou 'template'."""
        providers = self.available()
        return providers[0] if providers else "template"

    def report_result(self, provider: str, success: bool, latency_ms: float = 0.0) -> None:
        """Met à jour la santé d'un provider après appel."""
        if provider not in self._health:
            return
        h = self._health[provider]
        h.last_latency_ms = max(latency_ms, 0.0)
        if success:
            h.success += 1
            h.cooldown_until = 0.0
            return

        h.failures += 1
        # Backoff simple: 5s, 15s, 30s max
        penalty = min(30.0, 5.0 * max(1, h.failures))
        h.cooldown_until = time.time() + penalty

    def health(self) -> Dict[str, Dict[str, float]]:
        """Expose un snapshot santé par provider."""
        return {
            k: {
                "success": float(v.success),
                "failures": float(v.failures),
                "last_latency_ms": float(v.last_latency_ms),
                "cooldown_until": float(v.cooldown_until),
            }
            for k, v in self._health.items()
        }


llm_router = LLMRouter()
