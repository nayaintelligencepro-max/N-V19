"""
NAYA IMPROVEMENTS — ML Conversion
Amélioration #2: Moteur ML de prédiction de conversion avec apprentissage continu
"""

from .ml_predictor import (
    MLConversionPredictor,
    ProspectFeatures,
    get_ml_predictor
)

__all__ = [
    "MLConversionPredictor",
    "ProspectFeatures",
    "get_ml_predictor"
]
