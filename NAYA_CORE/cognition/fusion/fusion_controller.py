"""
NAYA_CORE — Cognitive Fusion Controller
=========================================
Fusionne les outputs des 10 couches cognitives en décision unifiée.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics, logging

log = logging.getLogger("NAYA.FUSION")

@dataclass
class FusionInput:
    layer_name: str
    output: Dict[str, Any]
    confidence: float
    weight: float = 1.0

@dataclass
class FusionResult:
    unified_signal: Dict[str, Any]
    fusion_confidence: float
    dominant_layer: str
    consensus_level: float  # 0-1
    conflicts: List[str]

class CognitiveFusionController:
    """
    Fusionne les 10 couches cognitives en signal décisionnel unifié.
    Utilise weighted voting + consensus detection.
    """

    LAYER_WEIGHTS = {
        "layer_1_cognitive_input": 0.8,
        "layer_2_precision":       1.0,
        "layer_3_intelligence":    1.2,
        "layer_4_strategy":        1.1,
        "layer_5_hunting":         1.0,
        "layer_6_creation":        0.9,
        "layer_7_hybrid":          1.1,
        "layer_8_safe":            1.3,
        "layer_9_repurse":         0.8,
        "layer_10_maturation":     1.0,
    }

    def fuse(self, inputs: List[FusionInput]) -> FusionResult:
        if not inputs:
            return FusionResult({}, 0.0, "none", 0.0, ["No inputs provided"])

        # Weighted confidence
        total_weight = sum(i.weight for i in inputs)
        weighted_conf = sum(i.confidence * i.weight for i in inputs) / total_weight

        # Find dominant layer (highest contribution)
        dominant = max(inputs, key=lambda x: x.confidence * x.weight)

        # Detect conflicts (layers with very different signals)
        confs = [i.confidence for i in inputs]
        std = statistics.stdev(confs) if len(confs) > 1 else 0
        conflicts = []
        if std > 0.25:
            low_layers = [i.layer_name for i in inputs if i.confidence < weighted_conf - 0.2]
            if low_layers:
                conflicts.append(f"Low confidence in: {', '.join(low_layers)}")

        # Consensus = 1 - normalized std
        consensus = max(0.0, 1.0 - (std / 0.5))

        # Build unified signal
        unified = {
            "weighted_confidence": round(weighted_conf, 3),
            "consensus_level": round(consensus, 3),
            "dominant_layer": dominant.layer_name,
            "layer_signals": {i.layer_name: i.confidence for i in inputs},
            "recommendation": "APPROVE" if weighted_conf > 0.70 else
                              "CAUTION" if weighted_conf > 0.50 else "REJECT"
        }

        log.debug(f"Fusion: conf={weighted_conf:.2f}, consensus={consensus:.2f}, "
                  f"dominant={dominant.layer_name}")

        return FusionResult(
            unified_signal=unified,
            fusion_confidence=weighted_conf,
            dominant_layer=dominant.layer_name,
            consensus_level=consensus,
            conflicts=conflicts
        )

    def fuse_from_dict(self, layer_outputs: Dict[str, Dict]) -> FusionResult:
        inputs = []
        for layer_name, output in layer_outputs.items():
            conf = output.get("confidence", output.get("score", 0.75))
            weight = self.LAYER_WEIGHTS.get(layer_name, 1.0)
            inputs.append(FusionInput(layer_name, output, conf, weight))
        return self.fuse(inputs)


_CONTROLLER: Optional[CognitiveFusionController] = None

def get_fusion_controller() -> CognitiveFusionController:
    global _CONTROLLER
    if _CONTROLLER is None: _CONTROLLER = CognitiveFusionController()
    return _CONTROLLER
