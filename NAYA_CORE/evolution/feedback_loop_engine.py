"""
NAYA FEEDBACK LOOP ENGINE v1
Autonomous learning system - HuntingAgents apprennent de succès/échecs
Auto-optimisation des stratégies, messaging, timing
"""

import json, logging, asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import statistics

log = logging.getLogger("NAYA.FEEDBACK")

# ═══════════════════════════════════════════════════════════════════════════
# 1. OUTCOME TRACKING & METRICS
# ═══════════════════════════════════════════════════════════════════════════

class OutcomeType(Enum):
    SUCCESS = "success"           # Prospect convertis
    PARTIAL = "partial"           # Lead qualifié
    REJECTED = "rejected"         # Prospect dit non
    UNRESPONSIVE = "unresponsive" # Pas de réponse
    BOUNCED = "bounced"          # Email invalid
    SPAM = "spam"                # Marqué spam

@dataclass
class CampaignOutcome:
    campaign_id: str
    prospect_id: str
    outcome: OutcomeType
    timestamp: datetime
    message_variant: str          # Quel texte utilisé
    channel: str                  # Email, LinkedIn, etc
    time_to_response: Optional[int] = None  # Minutes
    response_text: Optional[str] = None
    value_usd: Optional[float] = None
    feedback_text: Optional[str] = None
    
    def is_positive(self) -> bool:
        return self.outcome in [OutcomeType.SUCCESS, OutcomeType.PARTIAL]

@dataclass 
class PerformanceMetric:
    metric_name: str
    value: float
    timestamp: datetime
    segment: str = "global"  # Segmentation: industry, company_size, etc
    
class OutcomeTracker:
    """Tracker tous les résultats campagnes"""
    
    def __init__(self):
        self.outcomes: List[CampaignOutcome] = []
        self.metrics_by_variant: Dict[str, List[float]] = defaultdict(list)
        self.metrics_by_channel: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "success": 0, "partial": 0, "rejected": 0, "unresponsive": 0
        })
    
    def record_outcome(self, outcome: CampaignOutcome):
        """Enregistrer résultat campagne"""
        self.outcomes.append(outcome)
        self.metrics_by_variant[outcome.message_variant].append(
            1 if outcome.is_positive() else 0
        )
        self.metrics_by_channel[outcome.channel][outcome.outcome.value] += 1
        log.info(f"📊 Outcome recorded: {outcome.campaign_id} → {outcome.outcome.value}")
    
    def get_variant_stats(self, variant: str) -> Dict[str, float]:
        """Stats pour une variante: taux conversion, avg response time"""
        outcomes = [o for o in self.outcomes if o.message_variant == variant]
        if not outcomes: return {}
        
        success_count = sum(1 for o in outcomes if o.is_positive())
        response_times = [o.time_to_response for o in outcomes if o.time_to_response]
        
        return {
            "conversion_rate": success_count / len(outcomes),
            "success_count": success_count,
            "total_sent": len(outcomes),
            "avg_response_minutes": statistics.mean(response_times) if response_times else None,
            "median_response_minutes": statistics.median(response_times) if response_times else None
        }
    
    def get_channel_stats(self) -> Dict[str, Dict[str, Any]]:
        """Performance par channel"""
        return dict(self.metrics_by_channel)

# ═══════════════════════════════════════════════════════════════════════════
# 2. SUCCESS PATTERN ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class SuccessAnalyzer:
    """Détecter patterns dans succès - quels messages, timing, channels marchent"""
    
    def __init__(self):
        self.patterns: Dict[str, Dict[str, Any]] = {}
    
    def analyze_successful_campaigns(self, outcomes: List[CampaignOutcome]) -> Dict[str, Any]:
        """Extraire patterns des campagnes réussies"""
        successful = [o for o in outcomes if o.is_positive()]
        
        if not successful:
            return {"warning": "No successful campaigns yet"}
        
        # Grouper par variante message
        variants_success = defaultdict(lambda: {"count": 0, "value": 0})
        for outcome in successful:
            variants_success[outcome.message_variant]["count"] += 1
            variants_success[outcome.message_variant]["value"] += outcome.value_usd or 0
        
        # Grouper par channel
        channels_success = defaultdict(lambda: {"count": 0, "value": 0})
        for outcome in successful:
            channels_success[outcome.channel]["count"] += 1
            channels_success[outcome.channel]["value"] += outcome.value_usd or 0
        
        # Timing: quand envoyer pour meilleure réponse
        response_times = [o.time_to_response for o in successful if o.time_to_response]
        
        patterns = {
            "best_variants": dict(variants_success),
            "best_channels": dict(channels_success),
            "optimal_send_time_minutes": statistics.mean(response_times) if response_times else "unknown",
            "total_revenue_from_successful": sum(o.value_usd or 0 for o in successful),
            "conversion_funnel": {
                "from_successful": len(successful),
                "from_total": len(outcomes),
                "rate": len(successful) / len(outcomes)
            }
        }
        
        self.patterns = patterns
        log.info(f"✅ Success patterns identified: {len(successful)} wins")
        return patterns

# ═══════════════════════════════════════════════════════════════════════════
# 3. FAILURE CORRECTOR - Apprendre des erreurs
# ═══════════════════════════════════════════════════════════════════════════

class FailureCorrector:
    """Analyser rejets/rebonds et recommander corrections"""
    
    def __init__(self):
        self.failure_patterns: Dict[str, List[str]] = defaultdict(list)
        self.corrections: Dict[str, str] = {}
    
    def analyze_failures(self, outcomes: List[CampaignOutcome]) -> Dict[str, Any]:
        """Identifier patterns d'échecs et proposer solutions"""
        failures = [o for o in outcomes if not o.is_positive()]
        
        if not failures:
            return {"status": "all_campaigns_successful"}
        
        # Catégoriser par type d'échec
        failure_breakdown = defaultdict(list)
        for outcome in failures:
            failure_breakdown[outcome.outcome.value].append({
                "variant": outcome.message_variant,
                "channel": outcome.channel,
                "feedback": outcome.feedback_text
            })
        
        recommendations = {}
        
        # Pour chaque type d'échec, recommander correction
        if "bounced" in failure_breakdown:
            recommendations["email_quality"] = {
                "issue": "Email addresses bouncing",
                "fix": "Use better email verification API (RocketReach, Clearbit)",
                "priority": "HIGH"
            }
        
        if "spam" in failure_breakdown:
            recommendations["spam_filtering"] = {
                "issue": "Emails marked as spam",
                "fix": "Remove aggressive selling language, use personal tone",
                "priority": "HIGH"
            }
        
        if "rejected" in failure_breakdown:
            rejected_reasons = [d.get("feedback") for d in failure_breakdown["rejected"]]
            recommendations["messaging"] = {
                "issue": f"Direct rejections: {rejected_reasons[:3]}",
                "fix": "Test softer opening, focus on value not pitch",
                "priority": "MEDIUM"
            }
        
        log.warning(f"⚠️ Failures detected: {len(failures)} outcomes")
        return {
            "failure_count": len(failures),
            "breakdown": dict(failure_breakdown),
            "recommendations": recommendations
        }

# ═══════════════════════════════════════════════════════════════════════════
# 4. A/B TESTING FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Experiment:
    name: str
    control_variant: str
    test_variant: str
    metric: str                    # "conversion_rate", "response_time", "revenue"
    sample_size: int              # Prospects à tester
    start_date: datetime
    end_date: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    winner: Optional[str] = None

class ABTestingEngine:
    """Framework A/B testing - tester messages, timing, channels"""
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.active_experiments: List[str] = []
    
    def create_experiment(self, 
                         name: str,
                         control: str,
                         test: str,
                         metric: str = "conversion_rate",
                         sample_size: int = 100) -> Experiment:
        """Lancer nouvel A/B test"""
        exp = Experiment(
            name=name,
            control_variant=control,
            test_variant=test,
            metric=metric,
            sample_size=sample_size,
            start_date=datetime.now(timezone.utc)
        )
        self.experiments[name] = exp
        self.active_experiments.append(name)
        log.info(f"🧪 A/B test started: {name} (control={control}, test={test})")
        return exp
    
    def analyze_experiment(self, 
                          exp_name: str,
                          outcomes: List[CampaignOutcome]) -> Dict[str, Any]:
        """Analyser résultats test - déterminer winner"""
        if exp_name not in self.experiments:
            return {"error": "Experiment not found"}
        
        exp = self.experiments[exp_name]
        control_outcomes = [o for o in outcomes if o.message_variant == exp.control_variant]
        test_outcomes = [o for o in outcomes if o.message_variant == exp.test_variant]
        
        if not control_outcomes or not test_outcomes:
            return {"status": "insufficient_data"}
        
        # Calculer métrique pour chaque
        control_rate = sum(1 for o in control_outcomes if o.is_positive()) / len(control_outcomes)
        test_rate = sum(1 for o in test_outcomes if o.is_positive()) / len(test_outcomes)
        
        # Significance test (chi-squared)
        from scipy import stats
        control_successes = sum(1 for o in control_outcomes if o.is_positive())
        test_successes = sum(1 for o in test_outcomes if o.is_positive())
        
        chi2, p_value = stats.chisquare(
            f_obs=[control_successes, test_successes],
            f_exp=[len(control_outcomes) * 0.5, len(test_outcomes) * 0.5]
        )
        
        results = {
            "control": {"rate": control_rate, "count": len(control_outcomes)},
            "test": {"rate": test_rate, "count": len(test_outcomes)},
            "improvement": (test_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0,
            "p_value": p_value,
            "statistically_significant": p_value < 0.05,
            "winner": exp.test_variant if test_rate > control_rate else exp.control_variant
        }
        
        exp.results = results
        exp.winner = results["winner"]
        exp.end_date = datetime.now(timezone.utc)
        
        if exp_name in self.active_experiments:
            self.active_experiments.remove(exp_name)
        
        log.info(f"✅ Test finished: {exp_name} → Winner: {results['winner']} (+{results['improvement']:.1f}%)")
        return results

# ═══════════════════════════════════════════════════════════════════════════
# 5. OPTIMIZATION LOOP - Continuous improvement
# ═══════════════════════════════════════════════════════════════════════════

class OptimizationLoop:
    """Boucle d'optimisation: mesurer → analyser → tester → adapter"""
    
    def __init__(self, tracker: OutcomeTracker, success_analyzer: SuccessAnalyzer, 
                 failure_corrector: FailureCorrector, ab_engine: ABTestingEngine):
        self.tracker = tracker
        self.success_analyzer = success_analyzer
        self.failure_corrector = failure_corrector
        self.ab_engine = ab_engine
        self.iteration_count = 0
        self.improvements_history: List[Dict[str, Any]] = []
    
    async def run_optimization_cycle(self) -> Dict[str, Any]:
        """1 cycle: récupérer outcomes → analyser → recommander actions"""
        self.iteration_count += 1
        
        outcomes = self.tracker.outcomes
        if len(outcomes) < 10:
            return {"status": "insufficient_data", "outcomes_count": len(outcomes)}
        
        # Phase 1: Analyser succès
        success_patterns = self.success_analyzer.analyze_successful_campaigns(outcomes)
        
        # Phase 2: Analyser échecs
        failure_analysis = self.failure_corrector.analyze_failures(outcomes)
        
        # Phase 3: Créer tests basés sur patterns
        actions = self._generate_actions(success_patterns, failure_analysis)
        
        cycle_result = {
            "iteration": self.iteration_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcomes_analyzed": len(outcomes),
            "success_patterns": success_patterns,
            "failure_analysis": failure_analysis,
            "recommended_actions": actions
        }
        
        self.improvements_history.append(cycle_result)
        log.info(f"🔄 Optimization cycle #{self.iteration_count} completed - {len(actions)} actions")
        return cycle_result
    
    def _generate_actions(self, successes: Dict, failures: Dict) -> List[Dict]:
        """Générer actions recommandées"""
        actions = []
        
        # Action 1: Scaling - si c'est marche, augmenter volume
        if successes.get("conversion_funnel", {}).get("rate", 0) > 0.1:
            actions.append({
                "type": "SCALE",
                "description": "Conversion rate > 10% - increase campaign volume by 50%",
                "priority": "HIGH",
                "expected_impact": "+50% revenue"
            })
        
        # Action 2: Message optimization - si variant performe, l'utiliser
        if successes.get("best_variants"):
            best_var = max(successes["best_variants"].items(), key=lambda x: x[1]["count"])
            actions.append({
                "type": "ADOPT_VARIANT",
                "variant": best_var[0],
                "description": f"Use '{best_var[0]}' as primary message",
                "priority": "HIGH"
            })
        
        # Action 3: Fix issues
        if failures.get("recommendations"):
            for issue, fix in failures["recommendations"].items():
                actions.append({
                    "type": "FIX",
                    "issue": issue,
                    "fix": fix.get("fix"),
                    "priority": fix.get("priority", "MEDIUM")
                })
        
        return actions

# ═══════════════════════════════════════════════════════════════════════════
# 6. UNIFIED FEEDBACK LOOP MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class FeedbackLoopManager:
    """Système complet d'apprentissage et optimisation"""
    
    def __init__(self):
        self.tracker = OutcomeTracker()
        self.success_analyzer = SuccessAnalyzer()
        self.failure_corrector = FailureCorrector()
        self.ab_engine = ABTestingEngine()
        self.optimizer = OptimizationLoop(
            self.tracker, self.success_analyzer, 
            self.failure_corrector, self.ab_engine
        )
        self._optimization_task = None
    
    def record_campaign_outcome(self,
                               campaign_id: str,
                               prospect_id: str,
                               outcome: OutcomeType,
                               message_variant: str,
                               channel: str,
                               value_usd: float = 0,
                               time_to_response: Optional[int] = None):
        """Enregistrer résultat campagne"""
        campaign_outcome = CampaignOutcome(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            outcome=outcome,
            timestamp=datetime.now(timezone.utc),
            message_variant=message_variant,
            channel=channel,
            value_usd=value_usd,
            time_to_response=time_to_response
        )
        self.tracker.record_outcome(campaign_outcome)
    
    async def optimize_continuous(self, interval_hours: int = 6):
        """Boucle optimisation continue"""
        while True:
            await self.optimizer.run_optimization_cycle()
            await asyncio.sleep(interval_hours * 3600)
    
    def start_continuous_optimization(self, interval_hours: int = 6):
        """Démarrer optimisation asynchrone"""
        self._optimization_task = asyncio.create_task(
            self.optimize_continuous(interval_hours)
        )
        log.info(f"🚀 Continuous optimization started (every {interval_hours}h)")
    
    def get_optimization_history(self) -> List[Dict]:
        """Historique des optimisations"""
        return self.optimizer.improvements_history

# ═══════════════════════════════════════════════════════════════════════════
# 7. SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_feedback_manager: Optional[FeedbackLoopManager] = None

def get_feedback_loop_manager() -> FeedbackLoopManager:
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackLoopManager()
        log.info("✅ Feedback Loop Manager initialized")
    return _feedback_manager
