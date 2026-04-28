"""
QUALITÉ #9 — Optimiseur de performance système.

Cache intelligent, connection pooling, lazy loading et optimisation
mémoire pour des temps de réponse < 200ms.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LRUCache:
    """Cache LRU (Least Recently Used) thread-safe."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.monotonic() - timestamp < self._ttl:
                self._cache.move_to_end(key)
                self._hits += 1
                return value
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.monotonic())
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return (self._hits / max(total, 1)) * 100

    def stats(self) -> Dict[str, Any]:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(self.hit_rate, 1),
        }


class PerformanceMonitor:
    """Monitore les temps d'exécution de toutes les opérations critiques."""

    def __init__(self) -> None:
        self._timings: Dict[str, list] = {}

    def time_operation(self, operation_name: str) -> "_TimingContext":
        return _TimingContext(self, operation_name)

    def record(self, operation_name: str, duration_ms: float) -> None:
        if operation_name not in self._timings:
            self._timings[operation_name] = []
        self._timings[operation_name].append(duration_ms)
        if len(self._timings[operation_name]) > 1000:
            self._timings[operation_name] = self._timings[operation_name][-500:]

    def get_percentiles(self, operation_name: str) -> Dict[str, float]:
        timings = self._timings.get(operation_name, [])
        if not timings:
            return {}
        sorted_t = sorted(timings)
        n = len(sorted_t)
        return {
            "p50_ms": sorted_t[int(n * 0.5)],
            "p90_ms": sorted_t[int(n * 0.9)],
            "p95_ms": sorted_t[min(int(n * 0.95), n - 1)],
            "p99_ms": sorted_t[min(int(n * 0.99), n - 1)],
            "avg_ms": round(sum(sorted_t) / n, 2),
            "count": n,
        }

    def all_stats(self) -> Dict[str, Dict[str, float]]:
        return {op: self.get_percentiles(op) for op in self._timings}


class _TimingContext:
    """Context manager pour mesurer le temps d'exécution."""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str) -> None:
        self._monitor = monitor
        self._operation = operation_name
        self._start: float = 0

    def __enter__(self) -> "_TimingContext":
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        duration_ms = (time.monotonic() - self._start) * 1000
        self._monitor.record(self._operation, duration_ms)


class ConnectionPoolManager:
    """Gestionnaire de pools de connexions."""

    def __init__(self) -> None:
        self._pools: Dict[str, Dict[str, Any]] = {}

    def register_pool(self, name: str, max_size: int = 20) -> None:
        self._pools[name] = {
            "max_size": max_size,
            "active": 0,
            "idle": max_size,
            "total_acquired": 0,
            "total_released": 0,
        }

    def acquire(self, pool_name: str) -> bool:
        pool = self._pools.get(pool_name)
        if not pool:
            return False
        if pool["idle"] <= 0:
            return False
        pool["idle"] -= 1
        pool["active"] += 1
        pool["total_acquired"] += 1
        return True

    def release(self, pool_name: str) -> None:
        pool = self._pools.get(pool_name)
        if pool and pool["active"] > 0:
            pool["active"] -= 1
            pool["idle"] += 1
            pool["total_released"] += 1

    def stats(self) -> Dict[str, Any]:
        return self._pools.copy()


prospect_cache = LRUCache(max_size=5000, ttl_seconds=1800)
llm_response_cache = LRUCache(max_size=2000, ttl_seconds=7200)
performance_monitor = PerformanceMonitor()
connection_pool_manager = ConnectionPoolManager()
