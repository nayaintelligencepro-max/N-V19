"""
NAYA V19 - Cash Rapide Classifier
Classe les opportunites detectees en 3 categories:
  - IMMEDIAT: executable et solvable 24-72h (cash rapide)
  - MOYEN_TERME: necessite 7 jours
  - LONG_TERME: douleur complexe / abonnement
Execute 3-4 en parallele, incube le reste.
"""
import time, logging, threading, uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.HUNT.CLASSIFIER")

class OpportunityTier(Enum):
    IMMEDIAT = "immediat"       # 24-72h, cash rapide
    MOYEN_TERME = "moyen_terme" # 7 jours
    LONG_TERME = "long_terme"   # 30+ jours, abonnement

class ExecutionStatus(Enum):
    QUEUED = "queued"
    ACTIVE = "active"
    INCUBATION = "incubation"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ClassifiedOpportunity:
    id: str
    pain_description: str
    sector: str
    estimated_value_eur: float
    tier: OpportunityTier
    status: ExecutionStatus = ExecutionStatus.QUEUED
    solvability_score: float = 0.0
    urgency_score: float = 0.0
    complexity_score: float = 0.0
    execution_days: int = 1
    created_at: float = field(default_factory=time.time)
    offer_type: str = ""
    target_entity: str = ""

class CashRapideClassifier:
    """Classe et priorise les opportunites pour execution parallele."""

    MAX_PARALLEL = 4
    PREMIUM_FLOOR_EUR = 1000
    CASH_RAPIDE_TARGETS = [5000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000]

    def __init__(self):
        self._opportunities: Dict[str, ClassifiedOpportunity] = {}
        self._active: List[str] = []
        self._incubation: List[str] = []
        self._lock = threading.RLock()
        self._total_classified = 0
        self._total_value_pipeline = 0.0

    def classify(self, pain: Dict[str, Any]) -> ClassifiedOpportunity:
        """Classe une douleur detectee dans le bon tier."""
        value = pain.get("estimated_value", 0)
        urgency = pain.get("urgency", 0.5)
        complexity = pain.get("complexity", 0.5)
        solvability = pain.get("solvability", 0.5)

        # Enforce premium floor
        if value < self.PREMIUM_FLOOR_EUR:
            value = self.PREMIUM_FLOOR_EUR

        # Determine tier
        if solvability >= 0.7 and complexity <= 0.4 and urgency >= 0.6:
            tier = OpportunityTier.IMMEDIAT
            execution_days = 1 if urgency >= 0.9 else 3
            offer_type = self._determine_offer_type(pain)
        elif complexity <= 0.6 and solvability >= 0.5:
            tier = OpportunityTier.MOYEN_TERME
            execution_days = 7
            offer_type = pain.get("offer_type", "service_premium")
        else:
            tier = OpportunityTier.LONG_TERME
            execution_days = 30
            offer_type = pain.get("offer_type", "abonnement_premium")

        opp = ClassifiedOpportunity(
            id=f"OPP_{uuid.uuid4().hex[:8].upper()}",
            pain_description=pain.get("description", ""),
            sector=pain.get("sector", "general"),
            estimated_value_eur=value,
            tier=tier,
            solvability_score=solvability,
            urgency_score=urgency,
            complexity_score=complexity,
            execution_days=execution_days,
            offer_type=offer_type,
            target_entity=pain.get("entity", "")
        )

        with self._lock:
            self._opportunities[opp.id] = opp
            self._total_classified += 1
            self._total_value_pipeline += value
            self._assign_to_queue(opp)

        log.info(f"[CLASSIFIER] {opp.id} -> {tier.value} | {value}EUR | {opp.sector}")
        return opp

    def _determine_offer_type(self, pain: Dict) -> str:
        """Determine le type d offre cash rapide selon la douleur."""
        sector = pain.get("sector", "").lower()
        keywords = pain.get("keywords", [])

        if any(k in keywords for k in ["audit", "diagnostic", "analyse"]):
            return "audit_diagnostic"
        if any(k in keywords for k in ["chatbot", "bot", "automatisation"]):
            return "chatbot_ia"
        if any(k in keywords for k in ["saas", "logiciel", "plateforme"]):
            return "saas_solution"
        if any(k in keywords for k in ["site", "web", "landing"]):
            return "site_web_premium"
        if any(k in keywords for k in ["data", "donnees", "reporting"]):
            return "data_intelligence"
        return "service_premium_custom"

    def _assign_to_queue(self, opp: ClassifiedOpportunity) -> None:
        """Assigne l opportunite: active si place, sinon incubation."""
        if len(self._active) < self.MAX_PARALLEL and opp.tier == OpportunityTier.IMMEDIAT:
            opp.status = ExecutionStatus.ACTIVE
            self._active.append(opp.id)
        elif len(self._active) < self.MAX_PARALLEL and opp.tier == OpportunityTier.MOYEN_TERME:
            opp.status = ExecutionStatus.ACTIVE
            self._active.append(opp.id)
        else:
            opp.status = ExecutionStatus.INCUBATION
            self._incubation.append(opp.id)

    def promote_from_incubation(self) -> Optional[ClassifiedOpportunity]:
        """Promeut la meilleure opportunite en incubation vers active."""
        with self._lock:
            if len(self._active) >= self.MAX_PARALLEL:
                return None
            if not self._incubation:
                return None

            # Trier par valeur * urgence
            scored = []
            for oid in self._incubation:
                opp = self._opportunities[oid]
                score = opp.estimated_value_eur * opp.urgency_score
                scored.append((oid, score))
            scored.sort(key=lambda x: x[1], reverse=True)

            best_id = scored[0][0]
            self._incubation.remove(best_id)
            self._active.append(best_id)
            self._opportunities[best_id].status = ExecutionStatus.ACTIVE
            return self._opportunities[best_id]

    def complete_opportunity(self, opp_id: str, success: bool = True) -> None:
        with self._lock:
            opp = self._opportunities.get(opp_id)
            if not opp:
                return
            opp.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
            if opp_id in self._active:
                self._active.remove(opp_id)
            # Auto-promote from incubation
            self.promote_from_incubation()

    def get_active(self) -> List[ClassifiedOpportunity]:
        with self._lock:
            return [self._opportunities[oid] for oid in self._active if oid in self._opportunities]

    def get_incubation(self) -> List[ClassifiedOpportunity]:
        with self._lock:
            return [self._opportunities[oid] for oid in self._incubation if oid in self._opportunities]

    def get_by_tier(self, tier: OpportunityTier) -> List[ClassifiedOpportunity]:
        with self._lock:
            return [o for o in self._opportunities.values() if o.tier == tier]

    def get_stats(self) -> Dict:
        with self._lock:
            by_tier = {}
            for o in self._opportunities.values():
                by_tier[o.tier.value] = by_tier.get(o.tier.value, 0) + 1
            return {
                "total_classified": self._total_classified,
                "pipeline_value_eur": self._total_value_pipeline,
                "active": len(self._active),
                "incubation": len(self._incubation),
                "max_parallel": self.MAX_PARALLEL,
                "by_tier": by_tier,
                "premium_floor": self.PREMIUM_FLOOR_EUR
            }

_clf = None
_clf_lock = threading.Lock()
def get_classifier() -> CashRapideClassifier:
    global _clf
    if _clf is None:
        with _clf_lock:
            if _clf is None:
                _clf = CashRapideClassifier()
    return _clf
