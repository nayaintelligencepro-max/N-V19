"""
QUALITÉ #4 — Rate Limiter intelligent.

Contrôle le débit des appels API, emails et actions commerciales
pour rester dans les limites des services et éviter les blocages.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    name: str
    max_calls: int
    window_seconds: int
    burst_limit: Optional[int] = None


class TokenBucketRateLimiter:
    """
    Rate limiter basé sur le token bucket algorithm.

    Permet un débit soutenu avec autorisation de bursts contrôlés.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self._timestamps: Deque[float] = deque()
        self._total_allowed: int = 0
        self._total_rejected: int = 0
        logger.info(
            f"[RateLimiter:{config.name}] Initialisé — "
            f"{config.max_calls}/{config.window_seconds}s"
        )

    def _cleanup(self) -> None:
        now = time.monotonic()
        cutoff = now - self.config.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def allow(self) -> bool:
        """Vérifie si une action est autorisée."""
        self._cleanup()
        if len(self._timestamps) >= self.config.max_calls:
            self._total_rejected += 1
            return False

        burst = self.config.burst_limit or self.config.max_calls
        if len(self._timestamps) >= burst:
            self._total_rejected += 1
            return False

        self._timestamps.append(time.monotonic())
        self._total_allowed += 1
        return True

    def wait_time(self) -> float:
        """Retourne le temps d'attente avant qu'une action soit autorisée."""
        self._cleanup()
        if len(self._timestamps) < self.config.max_calls:
            return 0.0
        oldest = self._timestamps[0]
        return max(0, self.config.window_seconds - (time.monotonic() - oldest))

    def stats(self) -> Dict[str, Any]:
        self._cleanup()
        return {
            "name": self.config.name,
            "current_usage": len(self._timestamps),
            "max_calls": self.config.max_calls,
            "window_seconds": self.config.window_seconds,
            "utilization_pct": round(len(self._timestamps) / max(self.config.max_calls, 1) * 100, 1),
            "total_allowed": self._total_allowed,
            "total_rejected": self._total_rejected,
        }


DEFAULT_LIMITERS: Dict[str, RateLimitConfig] = {
    "email_outbound": RateLimitConfig("email_outbound", max_calls=50, window_seconds=3600, burst_limit=10),
    "llm_api": RateLimitConfig("llm_api", max_calls=100, window_seconds=60, burst_limit=20),
    "web_scraping": RateLimitConfig("web_scraping", max_calls=30, window_seconds=60, burst_limit=5),
    "hunter_api": RateLimitConfig("hunter_api", max_calls=50, window_seconds=3600),
    "apollo_api": RateLimitConfig("apollo_api", max_calls=100, window_seconds=3600),
    "telegram_notify": RateLimitConfig("telegram_notify", max_calls=30, window_seconds=60),
}


class RateLimiterRegistry:
    """Registre global de tous les rate limiters."""

    def __init__(self) -> None:
        self._limiters: Dict[str, TokenBucketRateLimiter] = {}
        for name, config in DEFAULT_LIMITERS.items():
            self._limiters[name] = TokenBucketRateLimiter(config)

    def get(self, name: str) -> Optional[TokenBucketRateLimiter]:
        return self._limiters.get(name)

    def allow(self, name: str) -> bool:
        limiter = self._limiters.get(name)
        if not limiter:
            return True
        return limiter.allow()

    def all_stats(self) -> Dict[str, Any]:
        return {name: lim.stats() for name, lim in self._limiters.items()}


rate_limiter_registry = RateLimiterRegistry()
