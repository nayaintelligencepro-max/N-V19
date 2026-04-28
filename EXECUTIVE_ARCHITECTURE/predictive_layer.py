"""NAYA V19 - Predictive Layer - Predictions strategiques basees sur les donnees."""
import logging, time, math
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.EXEC.PREDICT")

class PredictiveLayer:
    """Predit les revenus, tendances et risques a partir des donnees historiques."""

    def __init__(self):
        self._data_points: List[Dict] = []
        self._predictions: List[Dict] = []

    def add_data_point(self, metric: str, value: float, context: Dict = None) -> None:
        self._data_points.append({"metric": metric, "value": value, "context": context or {}, "ts": time.time()})
        if len(self._data_points) > 5000:
            self._data_points = self._data_points[-2500:]

    def predict_revenue(self, horizon_days: int = 30) -> Dict:
        """Predit le revenu sur un horizon donne base sur les tendances recentes."""
        rev_points = [d for d in self._data_points if d["metric"] == "revenue"]
        if len(rev_points) < 3:
            return {"predicted_eur": 0, "confidence": 0.1, "basis": "insufficient_data"}
        recent = rev_points[-30:]
        total = sum(d["value"] for d in recent)
        daily_avg = total / max(1, len(recent))
        # Tendance: comparer premiere moitie vs deuxieme moitie
        mid = len(recent) // 2
        first_half = sum(d["value"] for d in recent[:mid]) / max(1, mid)
        second_half = sum(d["value"] for d in recent[mid:]) / max(1, len(recent) - mid)
        trend = (second_half - first_half) / max(first_half, 1)
        projected = daily_avg * horizon_days * (1 + trend * 0.5)
        confidence = min(0.9, 0.3 + len(rev_points) * 0.02)
        prediction = {
            "predicted_eur": round(max(0, projected), 2),
            "daily_avg": round(daily_avg, 2),
            "trend": round(trend, 3),
            "trend_direction": "up" if trend > 0.05 else "down" if trend < -0.05 else "stable",
            "confidence": round(confidence, 2),
            "horizon_days": horizon_days
        }
        self._predictions.append(prediction)
        return prediction

    def predict_pipeline_conversion(self, pipeline_size: int, avg_conversion: float = 0.15) -> Dict:
        expected_deals = pipeline_size * avg_conversion
        return {
            "pipeline_size": pipeline_size,
            "expected_conversions": round(expected_deals, 1),
            "conversion_rate_used": avg_conversion,
            "confidence": min(0.8, 0.3 + pipeline_size * 0.01)
        }

    def risk_assessment(self) -> Dict:
        """Evalue les risques systemiques bases sur les metriques."""
        error_points = [d for d in self._data_points if d["metric"] == "error" and time.time() - d["ts"] < 86400]
        rev_trend = self.predict_revenue(7)
        risk_score = 0.0
        factors = []
        if len(error_points) > 10:
            risk_score += 0.3
            factors.append("high_error_rate")
        if rev_trend.get("trend", 0) < -0.1:
            risk_score += 0.3
            factors.append("declining_revenue")
        if rev_trend.get("confidence", 0) < 0.3:
            risk_score += 0.2
            factors.append("low_data_confidence")
        return {
            "risk_score": round(min(1.0, risk_score), 2),
            "level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
            "factors": factors
        }

    def get_stats(self) -> Dict:
        return {
            "data_points": len(self._data_points),
            "predictions_made": len(self._predictions),
            "last_prediction": self._predictions[-1] if self._predictions else None
        }
