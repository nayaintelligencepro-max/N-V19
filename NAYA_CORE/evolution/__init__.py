"""NAYA CORE — Evolution"""
from .adaptative_evolution_core import AdaptiveEvolutionCore
# Alias pour compatibilité
AdaptativeEvolutionCore = AdaptiveEvolutionCore
try:
    from .core_doctrine_mutation import CoreDoctrineMutation
    from .restructuring_layer import RestructuringLayer
except ImportError:
    CoreDoctrineMutation = None
    RestructuringLayer = None
__all__ = ["AdaptiveEvolutionCore", "AdaptativeEvolutionCore", "CoreDoctrineMutation", "RestructuringLayer"]
