"""NAYA — KPI Engine — Mesure la performance réelle."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class KPISnapshot:
    timestamp: datetime; revenue_mtd: float
    clients_active: int; mrr: float; churn_rate: float
    avg_deal_size: float; conversion_rate: float
    nps_score: float; automation_rate: float

    @property
    def health_score(self) -> float:
        return (
            min(self.mrr/50000, 1) * 0.3 +
            (1 - self.churn_rate) * 0.25 +
            self.conversion_rate * 0.2 +
            self.nps_score/100 * 0.15 +
            self.automation_rate * 0.1
        ) * 100

class KPIEngine:
    """Mesure et analyse les KPIs critiques du système."""

    def evaluate_performance(self, revenue: float, execution_speed: float, 
                             reliability: float) -> float:
        return round((revenue * 0.4) + (execution_speed * 0.3) + (reliability * 0.3), 2)

    def compute_health(self, snapshot: KPISnapshot) -> Dict:
        score = snapshot.health_score
        return {
            "overall_health": round(score, 1),
            "status": "EXCELLENT" if score >= 80 else "GOOD" if score >= 60 else "NEEDS_ATTENTION",
            "mrr": snapshot.mrr, "churn": snapshot.churn_rate,
            "conversion": snapshot.conversion_rate,
            "recommendations": self._get_recommendations(snapshot)
        }

    def _get_recommendations(self, snap: KPISnapshot) -> List[str]:
        recs = []
        if snap.churn_rate > 0.05: recs.append("Améliorer l'onboarding client")
        if snap.conversion_rate < 0.10: recs.append("Optimiser le pitch et closing")
        if snap.automation_rate < 0.50: recs.append("Automatiser les tâches répétitives")
        if snap.nps_score < 50: recs.append("Programme satisfaction client urgent")
        return recs

    def track_growth(self, snapshots: List[KPISnapshot]) -> Dict:
        if len(snapshots) < 2: return {"growth": 0, "trend": "STABLE"}
        growth = (snapshots[-1].mrr - snapshots[0].mrr) / max(snapshots[0].mrr, 1)
        return {"growth": round(growth * 100, 1), "trend": "UP" if growth > 0 else "DOWN",
                "mrr_delta": snapshots[-1].mrr - snapshots[0].mrr}
