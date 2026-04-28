"""
NAYA V19 — Cash Rapide Classifier
Classe les opportunités détectées en 3 catégories:
  - IMMEDIAT: exécutable et solvable 24-72h (cash rapide)
  - MOYEN_TERME: nécessite 7-21 jours (douleurs plus complexes)
  - LONG_TERME: abonnement ou projet >30 jours
Exécute 3-4 en parallèle, incube le reste.
"""
import time, logging, threading
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CASH_CLASSIFIER")


class CashCategory(Enum):
    IMMEDIAT = "immediat_24_72h"
    MOYEN_TERME = "moyen_terme_7_21j"
    LONG_TERME = "long_terme_30j_plus"


@dataclass
class ClassifiedOpportunity:
    id: str
    category: CashCategory
    estimated_value_eur: float
    execution_days: int
    confidence: float
    pain_description: str
    sector: str
    status: str = "queued"  # queued | executing | incubating | completed
    created_at: float = field(default_factory=time.time)


class CashRapideClassifier:
    """Classifie et priorise les opportunités pour le cash rapide."""
    
    MAX_PARALLEL = 4  # Maximum d'exécutions simultanées
    PREMIUM_FLOOR = 1000  # Plancher premium en euros
    
    CATEGORY_RULES = {
        CashCategory.IMMEDIAT: {
            "max_days": 3,
            "min_value": 1000,
            "types": ["audit", "diagnostic", "chatbot", "ia_setup", "consulting", "saas_config"],
            "solvability_min": 0.8,
        },
        CashCategory.MOYEN_TERME: {
            "max_days": 21,
            "min_value": 5000,
            "types": ["platform", "integration", "custom_solution", "training_program"],
            "solvability_min": 0.6,
        },
        CashCategory.LONG_TERME: {
            "max_days": 365,
            "min_value": 10000,
            "types": ["subscription", "saas", "managed_service", "partnership", "infrastructure"],
            "solvability_min": 0.5,
        },
    }
    
    def __init__(self):
        self._classified: List[ClassifiedOpportunity] = []
        self._executing: List[ClassifiedOpportunity] = []
        self._incubating: List[ClassifiedOpportunity] = []
        self._completed: List[ClassifiedOpportunity] = []
        self._lock = threading.RLock()
    
    def classify(self, opportunity: Dict) -> ClassifiedOpportunity:
        """Classe une opportunité dans la bonne catégorie."""
        value = opportunity.get("estimated_value", 0) or opportunity.get("offer_price", 0)
        days = opportunity.get("execution_days", 30)
        opp_type = opportunity.get("type", "").lower()
        solvability = opportunity.get("solvability", 0.5)
        
        # Forcer le plancher premium
        if value < self.PREMIUM_FLOOR:
            value = self.PREMIUM_FLOOR
        
        # Classifier
        category = CashCategory.LONG_TERME  # Défaut
        confidence = 0.5
        
        for cat, rules in self.CATEGORY_RULES.items():
            if days <= rules["max_days"] and value >= rules["min_value"]:
                if solvability >= rules["solvability_min"]:
                    type_match = any(t in opp_type for t in rules["types"])
                    if type_match or solvability >= rules["solvability_min"] + 0.1:
                        category = cat
                        confidence = min(0.95, solvability * (1 + (type_match * 0.2)))
                        break
        
        classified = ClassifiedOpportunity(
            id=opportunity.get("id", f"OPP_{int(time.time())}"),
            category=category,
            estimated_value_eur=value,
            execution_days=days,
            confidence=round(confidence, 2),
            pain_description=opportunity.get("pain", "")[:200],
            sector=opportunity.get("sector", "unknown"),
        )
        
        with self._lock:
            self._classified.append(classified)
            self._dispatch(classified)
        
        log.info(f"[CLASSIFIER] {classified.id} → {category.value} ({value}€, {days}j, conf={confidence:.0%})")
        return classified
    
    def _dispatch(self, opp: ClassifiedOpportunity):
        """Dispatche: exécuter en parallèle ou incuber."""
        if len(self._executing) < self.MAX_PARALLEL:
            opp.status = "executing"
            self._executing.append(opp)
            log.info(f"[CLASSIFIER] 🚀 Executing: {opp.id} ({len(self._executing)}/{self.MAX_PARALLEL})")
        else:
            opp.status = "incubating"
            self._incubating.append(opp)
            log.info(f"[CLASSIFIER] 🔄 Incubating: {opp.id} ({len(self._incubating)} in queue)")
    
    def complete(self, opp_id: str, success: bool = True):
        """Marque une opportunité comme complétée et lance la suivante."""
        with self._lock:
            for i, opp in enumerate(self._executing):
                if opp.id == opp_id:
                    opp.status = "completed" if success else "failed"
                    self._completed.append(self._executing.pop(i))
                    break
            
            # Promouvoir depuis l'incubation
            if self._incubating and len(self._executing) < self.MAX_PARALLEL:
                # Prioriser: IMMEDIAT > MOYEN > LONG, puis par valeur
                self._incubating.sort(key=lambda o: (
                    0 if o.category == CashCategory.IMMEDIAT else
                    1 if o.category == CashCategory.MOYEN_TERME else 2,
                    -o.estimated_value_eur
                ))
                next_opp = self._incubating.pop(0)
                next_opp.status = "executing"
                self._executing.append(next_opp)
                log.info(f"[CLASSIFIER] ⬆️ Promoted from incubation: {next_opp.id}")
    
    def get_pipeline(self) -> Dict:
        with self._lock:
            return {
                "executing": [{
                    "id": o.id, "category": o.category.value,
                    "value": o.estimated_value_eur, "sector": o.sector,
                } for o in self._executing],
                "incubating": [{
                    "id": o.id, "category": o.category.value,
                    "value": o.estimated_value_eur,
                } for o in self._incubating[:10]],
                "completed": len(self._completed),
                "total_value_executing": sum(o.estimated_value_eur for o in self._executing),
                "total_value_pipeline": sum(o.estimated_value_eur for o in self._classified),
            }
    
    def get_stats(self) -> Dict:
        with self._lock:
            by_cat = {}
            for o in self._classified:
                cat = o.category.value
                by_cat[cat] = by_cat.get(cat, 0) + 1
            return {
                "total_classified": len(self._classified),
                "executing": len(self._executing),
                "incubating": len(self._incubating),
                "completed": len(self._completed),
                "by_category": by_cat,
                "total_pipeline_eur": sum(o.estimated_value_eur for o in self._classified),
                "max_parallel": self.MAX_PARALLEL,
            }
