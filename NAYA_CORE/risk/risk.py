"""NAYA V19 - Risk Assessment Engine."""
import time, logging
from typing import Dict, List
from dataclasses import dataclass, field
log = logging.getLogger("NAYA.RISK")

@dataclass
class RiskAssessment:
    risk_id: str
    source: str
    category: str  # financial, operational, legal, reputational, technical
    severity: float  # 0-1
    likelihood: float  # 0-1
    impact_eur: float = 0.0
    mitigation: str = ""
    status: str = "open"
    detected_at: float = field(default_factory=time.time)

class RiskEngine:
    """Evalue et gere les risques du systeme et des operations business."""

    RISK_MATRIX = {
        (0.7, 0.7): "critical",
        (0.7, 0.4): "high",
        (0.4, 0.7): "high",
        (0.4, 0.4): "medium",
    }

    def __init__(self):
        self._risks: List[RiskAssessment] = []
        self._mitigations: Dict[str, str] = {}

    def assess(self, source: str, category: str, severity: float,
               likelihood: float, impact_eur: float = 0) -> RiskAssessment:
        risk_id = f"RISK_{len(self._risks)+1:04d}"
        level = "low"
        for (s_thresh, l_thresh), lvl in self.RISK_MATRIX.items():
            if severity >= s_thresh and likelihood >= l_thresh:
                level = lvl
                break
        risk = RiskAssessment(
            risk_id=risk_id, source=source, category=category,
            severity=severity, likelihood=likelihood, impact_eur=impact_eur,
            status=level
        )
        self._risks.append(risk)
        if level in ("critical", "high"):
            log.warning(f"[RISK] {level.upper()}: {source}/{category} sev={severity} lik={likelihood}")
        return risk

    def mitigate(self, risk_id: str, action: str) -> Dict:
        for r in self._risks:
            if r.risk_id == risk_id:
                r.mitigation = action
                r.status = "mitigated"
                return {"mitigated": True, "risk_id": risk_id}
        return {"error": "not_found"}

    def get_open_risks(self) -> List[RiskAssessment]:
        return [r for r in self._risks if r.status not in ("mitigated", "closed")]

    def get_risk_score(self) -> float:
        open_risks = self.get_open_risks()
        if not open_risks:
            return 0
        return sum(r.severity * r.likelihood for r in open_risks) / len(open_risks)

    def get_stats(self) -> Dict:
        by_status = {}
        for r in self._risks:
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return {
            "total_risks": len(self._risks),
            "open": len(self.get_open_risks()),
            "risk_score": round(self.get_risk_score(), 3),
            "by_status": by_status
        }
