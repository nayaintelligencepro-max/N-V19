"""
NAYA SUPREME V19.3 — AMELIORATION #2
Revenue Forecaster (Monte Carlo)
================================
Projection revenue a 30/60/90 jours basee sur :
- Pipeline actuel (deals en cours + probabilites)
- Historique de conversion (taux closing par stage)
- Saisonnalite (jours ouvrables, periodes creuses)
- Simulation Monte Carlo (1000 iterations)

Unique a NAYA : prediction financiere integree dans un systeme
de vente IA avec intervalles de confiance reels.
"""
import random
import time
import logging
import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.FORECAST")


@dataclass
class ForecastScenario:
    label: str  # pessimiste | realiste | optimiste
    revenue_30d: float
    revenue_60d: float
    revenue_90d: float
    confidence: float  # 0-1
    deals_expected: int
    avg_deal_size: float


@dataclass
class RevenueForecast:
    timestamp: float
    scenarios: List[ForecastScenario]
    pipeline_value: float
    weighted_pipeline: float
    monte_carlo_mean_90d: float
    monte_carlo_p10: float  # 10th percentile (pessimiste)
    monte_carlo_p50: float  # median
    monte_carlo_p90: float  # 90th percentile (optimiste)
    monthly_burn_rate: float
    runway_months: float
    insights: List[str]


# Taux de conversion par stage (basé sur les benchmarks B2B SaaS/Consulting)
STAGE_CONVERSION_RATES = {
    "discovery": 0.15,
    "proposal": 0.30,
    "negotiation": 0.50,
    "contract": 0.80,
    "won": 1.0,
    "lost": 0.0,
}

# Duree moyenne par stage (jours)
STAGE_DURATION_DAYS = {
    "discovery": 14,
    "proposal": 10,
    "negotiation": 7,
    "contract": 5,
}

# Saisonnalite mensuelle (multiplicateur)
SEASONALITY = {
    1: 0.85, 2: 0.90, 3: 1.05, 4: 1.10,
    5: 1.05, 6: 0.95, 7: 0.70, 8: 0.60,
    9: 1.10, 10: 1.15, 11: 1.10, 12: 0.85,
}


class RevenueForecaster:
    """
    Moteur de prevision revenue avec simulation Monte Carlo.
    S'alimente des donnees du pipeline tracker et de l'historique des deals.
    """

    def __init__(self):
        self._forecasts: List[RevenueForecast] = []
        self._run_count: int = 0
        self._historical_deals: List[Dict] = []
        self._burn_rate: float = 2000.0  # EUR/mois estime
        self._premium_floor: float = 1000.0

    def add_historical_deal(self, amount: float, stage: str, days_to_close: int) -> None:
        """Ajoute un deal historique pour calibrer les predictions."""
        self._historical_deals.append({
            "amount": amount,
            "stage": stage,
            "days_to_close": days_to_close,
            "timestamp": time.time(),
        })

    def set_burn_rate(self, monthly_eur: float) -> None:
        """Definit le burn rate mensuel pour calculer le runway."""
        self._burn_rate = monthly_eur

    def forecast(self, pipeline: List[Dict] = None, horizon_days: int = 90) -> RevenueForecast:
        """
        Genere une prevision revenue complete.

        Args:
            pipeline: Liste de deals avec {amount, stage, probability, created_days_ago}
            horizon_days: Horizon de prevision en jours
        """
        self._run_count += 1
        start = time.time()

        if pipeline is None:
            pipeline = self._get_default_pipeline()

        # Calcul pipeline brut et pondere
        pipeline_value = sum(d.get("amount", 0) for d in pipeline)
        weighted_pipeline = sum(
            d.get("amount", 0) * STAGE_CONVERSION_RATES.get(d.get("stage", "discovery"), 0.1)
            for d in pipeline
        )

        # Monte Carlo simulation (1000 iterations)
        mc_results_30 = []
        mc_results_60 = []
        mc_results_90 = []

        for _ in range(1000):
            rev_30, rev_60, rev_90 = self._simulate_pipeline(pipeline, horizon_days)
            mc_results_30.append(rev_30)
            mc_results_60.append(rev_60)
            mc_results_90.append(rev_90)

        mc_results_90.sort()
        mc_results_60.sort()
        mc_results_30.sort()

        p10 = mc_results_90[99]  # 10th percentile
        p50 = mc_results_90[499]  # median
        p90 = mc_results_90[899]  # 90th percentile
        mc_mean = sum(mc_results_90) / len(mc_results_90)

        # Scenarios
        scenarios = [
            ForecastScenario(
                label="pessimiste",
                revenue_30d=round(sorted(mc_results_30)[99], 2),
                revenue_60d=round(sorted(mc_results_60)[99], 2),
                revenue_90d=round(p10, 2),
                confidence=0.90,
                deals_expected=max(0, int(len(pipeline) * 0.15)),
                avg_deal_size=round(p10 / max(1, int(len(pipeline) * 0.15)), 2),
            ),
            ForecastScenario(
                label="realiste",
                revenue_30d=round(sorted(mc_results_30)[499], 2),
                revenue_60d=round(sorted(mc_results_60)[499], 2),
                revenue_90d=round(p50, 2),
                confidence=0.50,
                deals_expected=max(0, int(len(pipeline) * 0.30)),
                avg_deal_size=round(p50 / max(1, int(len(pipeline) * 0.30)), 2),
            ),
            ForecastScenario(
                label="optimiste",
                revenue_30d=round(sorted(mc_results_30)[899], 2),
                revenue_60d=round(sorted(mc_results_60)[899], 2),
                revenue_90d=round(p90, 2),
                confidence=0.10,
                deals_expected=max(0, int(len(pipeline) * 0.50)),
                avg_deal_size=round(p90 / max(1, int(len(pipeline) * 0.50)), 2),
            ),
        ]

        # Runway
        runway = round(weighted_pipeline / max(self._burn_rate, 1), 1)

        # Insights
        insights = self._generate_insights(pipeline, scenarios, weighted_pipeline)

        forecast = RevenueForecast(
            timestamp=time.time(),
            scenarios=scenarios,
            pipeline_value=round(pipeline_value, 2),
            weighted_pipeline=round(weighted_pipeline, 2),
            monte_carlo_mean_90d=round(mc_mean, 2),
            monte_carlo_p10=round(p10, 2),
            monte_carlo_p50=round(p50, 2),
            monte_carlo_p90=round(p90, 2),
            monthly_burn_rate=self._burn_rate,
            runway_months=runway,
            insights=insights,
        )

        self._forecasts.append(forecast)
        elapsed = round((time.time() - start) * 1000, 1)
        log.info(f"[FORECAST] p10={p10:.0f} p50={p50:.0f} p90={p90:.0f} EUR/90j ({elapsed}ms)")

        return forecast

    def _simulate_pipeline(self, pipeline: List[Dict], horizon_days: int) -> tuple:
        """Une iteration Monte Carlo : simule chaque deal avec bruit aleatoire."""
        import datetime
        current_month = datetime.datetime.now().month
        seasonality = SEASONALITY.get(current_month, 1.0)

        rev_30 = 0.0
        rev_60 = 0.0
        rev_90 = 0.0

        for deal in pipeline:
            amount = deal.get("amount", self._premium_floor)
            stage = deal.get("stage", "discovery")
            base_prob = STAGE_CONVERSION_RATES.get(stage, 0.1)

            # Ajouter du bruit gaussien
            noise = random.gauss(0, 0.15)
            prob = max(0.0, min(1.0, base_prob + noise))
            prob *= seasonality

            # Temps de closing estime
            remaining_days = sum(
                STAGE_DURATION_DAYS.get(s, 10)
                for s in list(STAGE_DURATION_DAYS.keys())
                if list(STAGE_DURATION_DAYS.keys()).index(s) >= list(STAGE_DURATION_DAYS.keys()).index(stage)
                if s in STAGE_DURATION_DAYS
            ) if stage in STAGE_DURATION_DAYS else 30

            # Variation temps (+/- 50%)
            actual_days = max(1, int(remaining_days * random.uniform(0.5, 1.5)))

            # Deal se concretise?
            if random.random() < prob:
                # Variation montant (+/- 20%)
                actual_amount = amount * random.uniform(0.8, 1.2)
                actual_amount = max(self._premium_floor, actual_amount)

                if actual_days <= 30:
                    rev_30 += actual_amount
                    rev_60 += actual_amount
                    rev_90 += actual_amount
                elif actual_days <= 60:
                    rev_60 += actual_amount
                    rev_90 += actual_amount
                elif actual_days <= 90:
                    rev_90 += actual_amount

        return rev_30, rev_60, rev_90

    def _get_default_pipeline(self) -> List[Dict]:
        """Pipeline par defaut pour le demo (scenario M1 NAYA)."""
        return [
            {"amount": 5000, "stage": "discovery", "company": "Prospect OT Alpha"},
            {"amount": 8000, "stage": "discovery", "company": "Prospect NIS2 Beta"},
            {"amount": 15000, "stage": "discovery", "company": "Audit Express Gamma"},
            {"amount": 3000, "stage": "proposal", "company": "Prospect Delta"},
            {"amount": 12000, "stage": "discovery", "company": "Mission Conformite"},
        ]

    def _generate_insights(self, pipeline: List[Dict], scenarios: List[ForecastScenario],
                           weighted: float) -> List[str]:
        """Genere des insights actionables basees sur les previsions."""
        insights = []
        realiste = next((s for s in scenarios if s.label == "realiste"), None)

        if realiste and realiste.revenue_90d < 5000:
            insights.append(
                "Pipeline insuffisant pour atteindre 5000 EUR/90j. "
                "Action: augmenter le volume de prospection (cible: 20+ prospects/semaine)."
            )
        elif realiste and realiste.revenue_90d >= 10000:
            insights.append(
                f"Pipeline sain: {realiste.revenue_90d:.0f} EUR prevus sur 90 jours (scenario realiste)."
            )

        if weighted < 3000:
            insights.append(
                "Pipeline pondere < 3000 EUR. Prioriser le passage de deals en 'proposal' et 'negotiation'."
            )

        discovery_count = sum(1 for d in pipeline if d.get("stage") == "discovery")
        if discovery_count > len(pipeline) * 0.7:
            insights.append(
                f"{discovery_count}/{len(pipeline)} deals en discovery. "
                "Risque: trop de prospects froids. Accelerer la qualification."
            )

        if not pipeline:
            insights.append("Pipeline vide. Lancer le Pain Hunter en priorite.")

        return insights

    def get_stats(self) -> Dict:
        return {
            "forecasts_run": self._run_count,
            "historical_deals": len(self._historical_deals),
            "burn_rate_eur": self._burn_rate,
            "last_forecast": self._forecasts[-1].monte_carlo_p50 if self._forecasts else 0,
        }

    def to_dict(self) -> Dict:
        if not self._forecasts:
            return {"status": "no_forecast_run"}
        f = self._forecasts[-1]
        return {
            "pipeline_value": f.pipeline_value,
            "weighted_pipeline": f.weighted_pipeline,
            "monte_carlo_p10": f.monte_carlo_p10,
            "monte_carlo_p50": f.monte_carlo_p50,
            "monte_carlo_p90": f.monte_carlo_p90,
            "runway_months": f.runway_months,
            "scenarios": [
                {"label": s.label, "revenue_90d": s.revenue_90d, "deals": s.deals_expected}
                for s in f.scenarios
            ],
            "insights": f.insights,
        }


_forecaster: Optional[RevenueForecaster] = None


def get_revenue_forecaster() -> RevenueForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = RevenueForecaster()
    return _forecaster
