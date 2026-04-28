"""NAYA CORE — Risk Management"""
from .risk import Risk
RiskEngine = Risk  # Alias
from .guardian import Guardian
RiskGuardian = Guardian  # Alias
__all__ = ["Risk", "RiskEngine", "Guardian", "RiskGuardian"]
