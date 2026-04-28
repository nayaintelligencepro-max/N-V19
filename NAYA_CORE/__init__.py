"""NAYA CORE — Intelligence centrale V6.0"""
VERSION = "6.0.0"
# Lazy imports to avoid circular dependencies
def get_brain():
    from .super_brain_hybrid_v6_0 import get_super_brain
    return get_super_brain()

__all__ = ["VERSION", "get_brain"]
