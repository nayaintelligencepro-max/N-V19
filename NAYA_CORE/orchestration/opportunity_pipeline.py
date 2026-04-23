"""NAYA — Opportunity Pipeline. Manages the lifecycle of business opportunities."""
import logging, time, hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
log = logging.getLogger("NAYA.PIPELINE")

@dataclass
class Opportunity:
    opp_id: str; company: str; stage: str = "detected"
    score: float = 0.0; value_eur: float = 0.0
    signals: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

STAGES = ["detected", "qualified", "contacted", "negotiating", "closing", "won", "lost"]

class OpportunityPipeline:
    def __init__(self):
        self._opportunities: Dict[str, Opportunity] = {}

    def add(self, company: str, score: float = 0, value: float = 0,
            signals: List[str] = None) -> Opportunity:
        uid = hashlib.md5(f"{company}{time.time()}".encode()).hexdigest()[:10]
        opp = Opportunity(opp_id=f"OPP-{uid}", company=company, score=score,
                          value_eur=value, signals=signals or [])
        self._opportunities[opp.opp_id] = opp
        log.info("Pipeline: +%s (%s, score=%.0f)", opp.opp_id, company, score)
        return opp

    def advance(self, opp_id: str) -> Optional[str]:
        opp = self._opportunities.get(opp_id)
        if not opp: return None
        idx = STAGES.index(opp.stage) if opp.stage in STAGES else 0
        if idx < len(STAGES) - 2:
            opp.stage = STAGES[idx + 1]
            opp.updated_at = time.time()
            log.info("Pipeline advance: %s → %s", opp_id, opp.stage)
        return opp.stage

    def mark_won(self, opp_id: str): self._set_stage(opp_id, "won")
    def mark_lost(self, opp_id: str): self._set_stage(opp_id, "lost")

    def _set_stage(self, opp_id: str, stage: str):
        opp = self._opportunities.get(opp_id)
        if opp: opp.stage = stage; opp.updated_at = time.time()

    def get_by_stage(self, stage: str) -> List[Opportunity]:
        return [o for o in self._opportunities.values() if o.stage == stage]

    def get_stats(self) -> Dict:
        stages = {}
        total_value = 0
        for o in self._opportunities.values():
            stages[o.stage] = stages.get(o.stage, 0) + 1
            if o.stage not in ("lost",): total_value += o.value_eur
        return {"total": len(self._opportunities), "by_stage": stages,
                "pipeline_value_eur": total_value}
