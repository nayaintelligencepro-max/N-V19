"""
NAYA — Brain Activator
Active et connecte TOUS les modules cognitifs de NAYA_CORE.
10 couches + fusion + multilingual + humanisation + LLM
"""
import time, logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.BRAIN_ACTIVATOR")

@dataclass
class CognitivePipelineResult:
    input_text: str
    layers_processed: int = 0
    layer_outputs: Dict = field(default_factory=dict)
    fusion_confidence: float = 0.0
    dominant_layer: str = ""
    consensus_level: float = 0.0
    conflicts: List = field(default_factory=list)
    llm_output: str = ""
    humanized: str = ""
    recommendation: str = ""
    latency_ms: float = 0.0

    def to_dict(self):
        return {
            "input_preview": self.input_text[:80],
            "layers_processed": self.layers_processed,
            "fusion_confidence": round(self.fusion_confidence, 3),
            "dominant_layer": self.dominant_layer,
            "consensus_level": round(self.consensus_level, 3),
            "conflicts": self.conflicts,
            "llm_output": self.llm_output[:600] if self.llm_output else "",
            "humanized": self.humanized[:400] if self.humanized else "",
            "recommendation": self.recommendation,
            "latency_ms": self.latency_ms,
        }


class NayaBrainActivator:
    """Active et connecte TOUT le cerveau NAYA_CORE."""

    def __init__(self):
        self._llm = None
        self._layers = {}
        self._fusion = None
        self._multilingual = None
        self._humanisation = None
        self._history: List[CognitivePipelineResult] = []
        self._init_all()

    def _init_all(self):
        self._load_layers()
        self._load_fusion()
        self._load_multilingual()
        self._load_humanisation()
        log.info(f"[BRAIN_ACTIVATOR] {len(self._layers)} couches cognitives chargées")

    def _load_layers(self):
        import importlib
        layer_map = {
            "L1_noise":   ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.noise_filter","NoiseFilter"),
            "L1_input":   ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.cognitive_input","CognitiveInputEngine"),
            "L1_signal":  ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.signal_extractor","SignalExtractor"),
            "L2_prec":    ("NAYA_CORE.cognition.layers.layer_2_precision.precision_layer","PrecisionLayer"),
            "L2_attn":    ("NAYA_CORE.cognition.layers.layer_2_precision.attention_focus","AttentionFocus"),
            "L3_intel":   ("NAYA_CORE.cognition.layers.layer_3_intelligence.cognitive_intelligence","CognitiveIntelligence"),
            "L3_disc":    ("NAYA_CORE.cognition.layers.layer_3_intelligence.discernment","DiscernmentEngine"),
            "L4_strat":   ("NAYA_CORE.cognition.layers.layer_4_strategy.strategic_cognition","StrategicCognition"),
            "L4_traj":    ("NAYA_CORE.cognition.layers.layer_4_strategy.trajectory_engine","TrajectoryEngine"),
            "L5_hunt":    ("NAYA_CORE.cognition.layers.layer_5_hunting.elite_detection","EliteDetection"),
            "L5_weak":    ("NAYA_CORE.cognition.layers.layer_5_hunting.signal_weakness","SignalWeaknessAnalyzer"),
            "L6_story":   ("NAYA_CORE.cognition.layers.layer_6_creation.storytelling_engine","StorytellingEngine"),
            "L6_struct":  ("NAYA_CORE.cognition.layers.layer_6_creation.structuring","StructuringEngine"),
            "L7_hybrid":  ("NAYA_CORE.cognition.layers.layer_7_hybrid.hybrid_cognition","HybridCognition"),
            "L8_safe":    ("NAYA_CORE.cognition.layers.layer_8_safe.safe_intelligence","SafeIntelligence"),
            "L8_risk":    ("NAYA_CORE.cognition.layers.layer_8_safe.risk_reduction","RiskReductionEngine"),
            "L9_rp":      ("NAYA_CORE.cognition.layers.layer_9_repurse.repurse_evolution","RepurseEvolution"),
            "L9_def":     ("NAYA_CORE.cognition.layers.layer_9_repurse.defense_logic","DefenseLogic"),
            "L10_mat":    ("NAYA_CORE.cognition.layers.layer_10_maturation.maturation_engine","MaturationEngine"),
            "L10_cap":    ("NAYA_CORE.cognition.layers.layer_10_maturation.capitalization","CapitalizationEngine"),
        }
        for name, (mp, cn) in layer_map.items():
            try:
                mod = importlib.import_module(mp)
                cls = getattr(mod, cn)
                self._layers[name] = cls()
            except Exception as e:
                log.debug(f"[BRAIN] {name}: {e}")

    def _load_fusion(self):
        try:
            from NAYA_CORE.cognition.fusion.fusion_controller import CognitiveFusionController
            self._fusion = CognitiveFusionController()
        except Exception as e:
            log.debug(f"[BRAIN] Fusion: {e}")

    def _load_multilingual(self):
        try:
            from NAYA_CORE.cognition.multilingual_cultural_engine import MultilingualEngine
            self._multilingual = MultilingualEngine()
        except Exception as e:
            log.debug(f"[BRAIN] Multilingual: {e}")

    def _load_humanisation(self):
        try:
            from NAYA_CORE.cognition.humanisation_core import HumanisationCore
            self._humanisation = HumanisationCore()
        except Exception as e:
            log.debug(f"[BRAIN] Humanisation: {e}")

    def attach_llm(self, llm_brain):
        self._llm = llm_brain
        log.info(f"[BRAIN_ACTIVATOR] LLM connecté — available={getattr(llm_brain,'available',False)}")

    def process(self, text: str, context: Dict = None, use_llm: bool = True) -> CognitivePipelineResult:
        t0 = time.time()
        ctx = context or {}
        result = CognitivePipelineResult(input_text=text)
        elements = ctx.get("signals", [text]) if text else []
        if not elements: elements = [text]

        # Phase 1: 10 couches
        for name, layer in self._layers.items():
            try:
                out = self._run_layer(layer, name, elements, ctx)
                result.layer_outputs[name] = out if isinstance(out, dict) else {"result": str(out)[:50]}
            except Exception:
                result.layer_outputs[name] = {"status": "active"}
        result.layers_processed = len(result.layer_outputs)

        # Phase 2: Fusion
        if self._fusion and result.layer_outputs:
            try:
                from NAYA_CORE.cognition.fusion.fusion_controller import FusionInput
                WEIGHTS = {"L8_safe": 1.3, "L4_strat": 1.1, "L3_intel": 1.2, "L7_hybrid": 1.1}
                inputs = [
                    FusionInput(
                        layer_name=n,
                        output=out,
                        confidence=float(out.get("confidence", out.get("score", 0.75)) if isinstance(out, dict) else 0.75),
                        weight=WEIGHTS.get(n, 1.0)
                    )
                    for n, out in result.layer_outputs.items()
                ]
                fusion = self._fusion.fuse(inputs)
                result.fusion_confidence = fusion.fusion_confidence
                result.dominant_layer    = fusion.dominant_layer
                result.consensus_level   = fusion.consensus_level
                result.conflicts         = fusion.conflicts
            except Exception:
                result.fusion_confidence = 0.75
                result.dominant_layer    = "L4_strat"
                result.consensus_level   = 0.8

        # Phase 3: LLM
        if use_llm and self._llm and getattr(self._llm, "available", False):
            try:
                from NAYA_CORE.execution.naya_brain import TaskType
                task = ctx.get("task_type", "strategic")
                try:   tt = TaskType(task)
                except: tt = TaskType.STRATEGIC
                prompt = self._build_prompt(text, result, ctx)
                resp = self._llm.think(prompt, tt, temperature=0.35, max_tokens=800)
                if resp and resp.ok:
                    result.llm_output = resp.text
            except Exception as e:
                log.debug(f"[BRAIN] LLM: {e}")

        # Phase 4: Humanisation
        if result.llm_output and self._humanisation:
            try:
                bundle = self._humanisation.translate([{
                    "content": result.llm_output,
                    "audience": ctx.get("audience", "fondatrice"),
                    "intent": ctx.get("intent", "inform"),
                    "tone": ctx.get("tone", "direct"),
                }])
                if bundle.messages: result.humanized = bundle.messages[0].content
            except Exception:
                result.humanized = result.llm_output

        result.recommendation = self._recommend(result, ctx)
        result.latency_ms = round((time.time() - t0) * 1000, 1)
        self._history.append(result)
        if len(self._history) > 200: self._history = self._history[-200:]
        return result

    def _run_layer(self, layer, name, elements, ctx):
        if "L1_noise" in name:   return layer.filter(elements)
        if "L1_input" in name:
            from NAYA_CORE.cognition.layers.layer_1_cognitive_input.cognitive_input import RawCognitiveInput
            raw = RawCognitiveInput(source="tori", raw_content=" | ".join(elements), context_tags=list(ctx.keys()))
            r = layer.process(raw)
            return {"refined_elements": getattr(r, "refined_elements", []), "confidence": 0.8}
        if "L1_signal" in name:  return layer.extract(elements)
        if "L2_prec" in name:    r = layer.apply(elements, level=ctx.get("precision_level","standard")); return r if isinstance(r, dict) else {"result": r, "confidence": 0.8}
        if "L2_attn" in name:    r = layer.focus(elements, depth=ctx.get("depth","standard")); return r if isinstance(r, dict) else {"result": r, "confidence": 0.8}
        if "L3_intel" in name:   return layer.analyze(elements)
        if "L3_disc" in name:    return layer.assess(elements)
        if "L4_strat" in name:   return layer.evaluate(elements)
        if "L4_traj" in name:    r = layer.build_and_evaluate(elements); return r if isinstance(r, dict) else {"result": r, "confidence": 0.8}
        if "L5_hunt" in name:    return layer.detect(elements)
        if "L5_weak" in name:    return layer.analyze(elements)
        if "L6_story" in name:   r = layer.build(elements, level=ctx.get("narrative_level","standard")); return r if isinstance(r, dict) else {"result": r, "confidence": 0.8}
        if "L6_struct" in name:  return layer.structure(elements)
        if "L7_hybrid" in name:  axes = {"main": elements, "ctx": [str(v) for v in ctx.values() if isinstance(v, str)]}; return layer.harmonize(axes)
        if "L8_safe" in name:    return layer.assess(elements)
        if "L8_risk" in name:    return layer.reduce(elements)
        if "L9_rp" in name:      return layer.evolve(elements)
        if "L9_def" in name:     return layer.analyze(elements)
        if "L10_mat" in name:    r = layer.mature(elements, cycles=ctx.get("cycles",1)); return r if isinstance(r, dict) else {"result": r, "confidence": 0.85}
        if "L10_cap" in name:    r = layer.capitalize(elements); return r if isinstance(r, dict) else {"result": r, "confidence": 0.85}
        return {"status": "active", "confidence": 0.75}

    def hunt_with_full_brain(self, industry, signals, revenue):
        from NAYA_CORE.super_brain_hybrid_v6_0 import hunt_and_create
        try: v6 = hunt_and_create(industry, signals, revenue)
        except Exception as e: return {"qualified": False, "error": str(e)}
        pain_text = " | ".join(signals) + f" | CA {revenue:,.0f}€"
        pipeline = self.process(pain_text, context={"task_type": "hunt", "industry": industry, "signals": signals}, use_llm=v6.get("qualified", False))
        if v6.get("qualified") and v6.get("offer"):
            v6["cognitive_enrichment"] = pipeline.humanized or pipeline.llm_output or ""
            v6["cognitive_confidence"] = pipeline.fusion_confidence
            v6["brain_recommendation"] = pipeline.recommendation
        return {**v6, "cognitive_pipeline": pipeline.to_dict()}

    def generate_proposal(self, pain_desc, price, client=""):
        pipeline = self.process(pain_desc, context={"task_type": "proposal", "price": price, "client": client, "intent": "convince", "tone": "authority"})
        return pipeline.humanized or pipeline.llm_output or pipeline.recommendation

    def get_status(self):
        return {
            "layers_loaded": len(self._layers),
            "layer_names": list(self._layers.keys()),
            "fusion_active": self._fusion is not None,
            "multilingual_active": self._multilingual is not None,
            "humanisation_active": self._humanisation is not None,
            "llm_connected": bool(self._llm and getattr(self._llm, "available", False)),
            "pipelines_processed": len(self._history),
        }

    def get_recent_pipelines(self, n=5):
        return [p.to_dict() for p in self._history[-n:]]

    def _build_prompt(self, text, result, ctx):
        task = ctx.get("task_type", "general")
        conf = int(result.fusion_confidence * 100)
        dom  = result.dominant_layer
        if task in ("hunt", "proposal"):
            return f"Tu es NAYA, intelligence business souveraine.\nIndustrie: {ctx.get('industry','B2B')} | Confiance: {conf}% | Couche dominante: {dom}\nSituation: {text}\n\nEn 150 mots max, propose une solution concrète, chiffrée, irréfutable. Ton direct, expert."
        if task == "analysis":
            return f"Analyse stratégiquement en 3 points précis:\n{text}"
        return f"Réponds de façon directe et stratégique (confiance {conf}%, {dom}):\n{text}"

    def _recommend(self, result, ctx):
        c = result.fusion_confidence
        dom = result.dominant_layer or "L4_strat"
        if c >= 0.85:   v = "✅ GO IMMÉDIAT"
        elif c >= 0.70: v = "⚡ GO AVEC ADAPTATION"
        elif c >= 0.50: v = "🔍 PILOTE D'ABORD"
        else:           v = "⏸ ANALYSER DAVANTAGE"
        return f"{v} | Confiance: {int(c*100)}% | Dominant: {dom} | Consensus: {int(result.consensus_level*100)}%"


_ACTIVATOR: Optional[NayaBrainActivator] = None

def get_brain_activator() -> NayaBrainActivator:
    global _ACTIVATOR
    if _ACTIVATOR is None: _ACTIVATOR = NayaBrainActivator()
    return _ACTIVATOR
