"""NAYA CORE — Core Engine (lazy imports)"""
def get_naya_core():
    from .naya_core import activate_naya_core
    return activate_naya_core()
__all__ = ["get_naya_core"]
