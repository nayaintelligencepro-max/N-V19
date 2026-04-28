"""
NAYA IMPROVEMENTS — Cache System
Amélioration #1: Système de cache intelligent multicouche L1/L2/L3
"""

from .multicache_engine import (
    MultiCacheEngine,
    CacheL1Memory,
    CacheL2Redis,
    CacheL3SQLite,
    get_multicache,
    cached
)

__all__ = [
    "MultiCacheEngine",
    "CacheL1Memory",
    "CacheL2Redis",
    "CacheL3SQLite",
    "get_multicache",
    "cached"
]
