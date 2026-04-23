"""
NAYA V19.3 — GENERIC PAIN ENGINE
Moteur de douleur unifié (remplace 39 fichiers dupliqués pain_engine.py + pain_hunt_engine.py).

Philosophie:
- Un SEUL moteur, configuré par un descripteur PainSpec
- Deux modes: TIER (P1-P6, pricing floor/target) et THEMATIC (pain sectoriel qualitatif)
- Thread-safe, métriques, persistance JSON
- Zéro gaspillage: chaque ancien fichier devient un descripteur YAML
"""
import time
import uuid
import json
import logging
import threading
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Literal
from enum import Enum

log = logging.getLogger("NAYA.PAIN")


class PainMode(str, Enum):
    TIER = "tier"             # Pricing floor/target (P1..P6)
    THEMATIC = "thematic"     # Pain sectoriel (regulatory, market, etc.)


@dataclass
class PainSpec:
    """Descripteur immuable d'un pain — remplace chaque ancien pain_engine.py"""
    pain_id: str                       # ex: "P1_PREMIUM", "PAYE_01_NO_MODERN_BANKING"
    name: str                          # nom humain
    project: str                       # ex: "PROJECT_01_CASH_RAPIDE"
    mode: PainMode                     # tier | thematic
    description: str = ""
    # TIER mode
    floor_price: float = 1000.0
    target_price: float = 5000.0
    offer_types: List[str] = field(default_factory=list)
    # THEMATIC mode
    pain_type: str = ""                # ex: "NO_MODERN_BANKING", "LEGACY_SCADA"
    sector: str = ""                   # ex: "fintech", "energy"
    default_signal: Dict[str, Any] = field(default_factory=dict)
    regulatory_complexity: float = 0.5
    # Global
    weights: Dict[str, float] = field(default_factory=lambda: {
        "solvability": 0.4, "urgency": 0.3, "value": 0.3
    })


@dataclass
class PainOpportunity:
    """Opportunité détectée (compatible legacy TIER + THEMATIC)"""
    id: str = field(default_factory=lambda: f"OPP_{uuid.uuid4().hex[:8].upper()}")
    pain_id: str = ""
    project: str = ""
    tier: str = ""
    sector: str = ""
    description: str = ""
    annual_cost: float = 0.0
    floor_price: float = 1000.0
    target_price: float = 5000.0
    solvability: float = 0.5
    urgency: float = 0.5
    regulatory_complexity: float = 0.5
    affected_population: int = 0
    estimated_market_eur: float = 0.0
    detected_at: float = field(default_factory=time.time)
    status: str = "detected"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class GenericPainEngine:
    """
    Moteur de douleur unifié V19.3.

    Remplace:
    - Les 26 × pain_engine.py (templates TIER/THEMATIC copiés)
    - Les 13 × pain_hunt_engine.py (variations projet)

    Usage:
        engine = GenericPainEngine(PainSpec(
            pain_id="P1_PREMIUM", project="CASH_RAPIDE",
            mode=PainMode.TIER, floor_price=1000, target_price=5000
        ))
        opp = engine.detect({"estimated_value": 3000, "sector": "Manufacturing"})
        engine.qualify(opp.id)
        engine.convert(opp.id, 3500)
    """

    def __init__(self, spec: PainSpec, persistence_dir: Optional[Path] = None):
        self.spec = spec
        self._lock = threading.RLock()
        self._opportunities: List[PainOpportunity] = []
        self._research: List[Dict] = []
        self._metrics: Dict[str, Any] = {
            "total_detected": 0,
            "total_qualified": 0,
            "total_converted": 0,
            "total_revenue": 0.0,
            "error_count": 0,
            "initialized_at": time.time(),
        }
        self._persistence_dir = persistence_dir
        if persistence_dir:
            persistence_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f"[PainEngine:{spec.pain_id}] Initialized (mode={spec.mode.value})")

    # ─────────────────────────────────────────────
    # DETECTION (équivalent de detect() ou record_signal())
    # ─────────────────────────────────────────────
    def detect(self, signal: Dict) -> Optional[PainOpportunity]:
        """Détection d'opportunité à partir d'un signal brut."""
        with self._lock:
            try:
                if self.spec.mode == PainMode.TIER:
                    value = float(signal.get("estimated_value", 0))
                    if value < self.spec.floor_price * 0.5:
                        return None
                    opp = PainOpportunity(
                        pain_id=self.spec.pain_id,
                        project=self.spec.project,
                        tier=self.spec.pain_id.split("_")[0] if "_" in self.spec.pain_id else "",
                        sector=signal.get("sector", ""),
                        description=signal.get("description", self.spec.description),
                        annual_cost=float(signal.get("annual_cost", value * 5)),
                        solvability=float(signal.get("solvability", 0.5)),
                        urgency=float(signal.get("urgency", 0.5)),
                        floor_price=self.spec.floor_price,
                        target_price=max(self.spec.floor_price, min(self.spec.target_price, value)),
                        metadata=signal.get("metadata", {}),
                    )
                else:  # THEMATIC
                    merged = {**self.spec.default_signal, **signal}
                    opp = PainOpportunity(
                        pain_id=self.spec.pain_id,
                        project=self.spec.project,
                        sector=self.spec.sector or merged.get("sector", ""),
                        description=self.spec.description,
                        urgency=float(merged.get("urgency", 0.5)),
                        regulatory_complexity=float(
                            merged.get("regulatory_complexity", self.spec.regulatory_complexity)
                        ),
                        affected_population=int(merged.get("population", 0)),
                        estimated_market_eur=float(merged.get("market_size", 0)),
                        metadata=merged.get("metadata", {}),
                    )

                self._opportunities.append(opp)
                self._metrics["total_detected"] += 1
                log.info(
                    f"[{self.spec.pain_id}] Detected: {opp.sector or opp.description[:40]} "
                    f"| target={opp.target_price:.0f}EUR"
                )
                return opp
            except Exception as e:
                self._metrics["error_count"] += 1
                log.error(f"[{self.spec.pain_id}] detect error: {e}")
                return None

    # Alias legacy
    def record_signal(self, data: Dict) -> Optional[PainOpportunity]:
        """Alias legacy: utilisé par les anciens thematic engines."""
        return self.detect(data)

    # ─────────────────────────────────────────────
    # QUALIFICATION
    # ─────────────────────────────────────────────
    def qualify(self, opp_id: str) -> Dict:
        with self._lock:
            opp = self._find(opp_id)
            if opp is None:
                return {"error": "not_found"}
            w = self.spec.weights
            value_norm = min(1.0, (opp.annual_cost or opp.estimated_market_eur) /
                             max(self.spec.target_price, 1))
            score = (
                opp.solvability * w.get("solvability", 0.4)
                + opp.urgency * w.get("urgency", 0.3)
                + value_norm * w.get("value", 0.3)
            )
            qualified = score >= 0.5
            opp.status = "qualified" if qualified else "disqualified"
            if qualified:
                self._metrics["total_qualified"] += 1
            return {
                "qualified": qualified,
                "score": round(score, 3),
                "pain_id": self.spec.pain_id,
                "opp_id": opp_id,
            }

    # ─────────────────────────────────────────────
    # CONVERSION
    # ─────────────────────────────────────────────
    def convert(self, opp_id: str, revenue: float) -> Dict:
        with self._lock:
            opp = self._find(opp_id)
            if opp is None:
                return {"error": "not_found"}
            if revenue < self.spec.floor_price:
                log.warning(f"[{self.spec.pain_id}] Revenue {revenue} < floor {self.spec.floor_price}")
            opp.status = "converted"
            self._metrics["total_converted"] += 1
            self._metrics["total_revenue"] += revenue
            self._persist()
            return {
                "converted": True,
                "revenue": revenue,
                "pain_id": self.spec.pain_id,
                "opp_id": opp_id,
            }

    # ─────────────────────────────────────────────
    # RESEARCH (thematic only)
    # ─────────────────────────────────────────────
    def add_research(self, title: str, findings: str, source: str = "") -> Dict:
        entry = {"title": title, "findings": findings, "source": source, "ts": time.time()}
        with self._lock:
            self._research.append(entry)
        return entry

    # ─────────────────────────────────────────────
    # FEASIBILITY (thematic only)
    # ─────────────────────────────────────────────
    def feasibility_score(self) -> Dict:
        with self._lock:
            sigs = [o for o in self._opportunities
                    if self.spec.mode == PainMode.THEMATIC]
            if not sigs:
                return {"score": 0, "data_points": 0}
            avg_market = sum(s.estimated_market_eur for s in sigs) / len(sigs)
            avg_complexity = sum(s.regulatory_complexity for s in sigs) / len(sigs)
            score = min(1.0,
                (avg_market / 100_000_000) * 0.4
                + (1 - avg_complexity) * 0.3
                + 0.3
            )
            return {
                "score": round(score, 3),
                "market_size_avg": avg_market,
                "regulatory_complexity": avg_complexity,
                "data_points": len(sigs),
                "research_entries": len(self._research),
            }

    # ─────────────────────────────────────────────
    # QUERIES
    # ─────────────────────────────────────────────
    def get_active(self) -> List[PainOpportunity]:
        with self._lock:
            return [o for o in self._opportunities
                    if o.status in ("detected", "qualified")]

    def get_stats(self) -> Dict:
        with self._lock:
            detected = self._metrics["total_detected"]
            converted = self._metrics["total_converted"]
            base = {
                "pain_id": self.spec.pain_id,
                "project": self.spec.project,
                "mode": self.spec.mode.value,
                "floor": self.spec.floor_price,
                "target": self.spec.target_price,
                "detected": detected,
                "qualified": self._metrics["total_qualified"],
                "converted": converted,
                "revenue": self._metrics["total_revenue"],
                "conversion_rate": (converted / detected) if detected else 0,
                "active": len(self.get_active()),
                "errors": self._metrics["error_count"],
            }
            if self.spec.mode == PainMode.THEMATIC:
                base["feasibility"] = self.feasibility_score()
            return base

    # ─────────────────────────────────────────────
    # INTERNES
    # ─────────────────────────────────────────────
    def _find(self, opp_id: str) -> Optional[PainOpportunity]:
        for o in self._opportunities:
            if o.id == opp_id:
                return o
        return None

    def _persist(self):
        if not self._persistence_dir:
            return
        try:
            path = self._persistence_dir / f"{self.spec.pain_id}.json"
            payload = {
                "spec": {**asdict(self.spec), "mode": self.spec.mode.value},
                "metrics": self._metrics,
                "opportunities": [o.to_dict() for o in self._opportunities[-200:]],
            }
            path.write_text(json.dumps(payload, indent=2, default=str))
        except Exception as e:
            log.debug(f"Persist error: {e}")


# ═════════════════════════════════════════════════════════════════
# REGISTRY — Récupère la liste de tous les PainSpec depuis configs
# ═════════════════════════════════════════════════════════════════

class PainEngineRegistry:
    """Registre central de tous les PainEngines actifs du système."""

    def __init__(self):
        self._engines: Dict[str, GenericPainEngine] = {}
        self._lock = threading.RLock()

    def register(self, spec: PainSpec, persistence_dir: Optional[Path] = None) -> GenericPainEngine:
        with self._lock:
            key = f"{spec.project}::{spec.pain_id}"
            if key not in self._engines:
                self._engines[key] = GenericPainEngine(spec, persistence_dir=persistence_dir)
            return self._engines[key]

    def get(self, project: str, pain_id: str) -> Optional[GenericPainEngine]:
        return self._engines.get(f"{project}::{pain_id}")

    def all(self) -> List[GenericPainEngine]:
        return list(self._engines.values())

    def global_stats(self) -> Dict:
        engines = self.all()
        total_detected = sum(e._metrics["total_detected"] for e in engines)
        total_revenue = sum(e._metrics["total_revenue"] for e in engines)
        return {
            "engines": len(engines),
            "total_detected": total_detected,
            "total_converted": sum(e._metrics["total_converted"] for e in engines),
            "total_revenue": total_revenue,
            "by_pain": [e.get_stats() for e in engines],
        }


# Singleton global
pain_registry = PainEngineRegistry()


__all__ = [
    "PainMode", "PainSpec", "PainOpportunity",
    "GenericPainEngine", "PainEngineRegistry", "pain_registry",
]
