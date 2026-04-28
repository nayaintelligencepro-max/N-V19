"""NAYA V19 — Decision Integrity Check"""
import time, logging, hashlib
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.DECISION.INTEGRITY")

class DecisionIntegrityCheck:
    """Vérifie que chaque décision respecte la constitution et la doctrine NAYA."""
    
    PREMIUM_FLOOR_EUR = 1000  # Plancher premium absolu
    MAX_RISK_SCORE = 0.85  # Risque maximum autorisé
    
    def __init__(self):
        self._checks_passed = 0
        self._checks_failed = 0
        self._violations: List[Dict] = []
    
    def validate_decision(self, decision: Dict) -> Dict:
        """Valide une décision business contre les règles du système."""
        issues = []
        
        # Vérifier le plancher premium
        price = decision.get("price", 0) or decision.get("offer_price", 0)
        if price > 0 and price < self.PREMIUM_FLOOR_EUR:
            issues.append(f"BELOW_PREMIUM_FLOOR: {price}€ < {self.PREMIUM_FLOOR_EUR}€")
        
        # Vérifier le score de risque
        risk = decision.get("risk_score", 0)
        if risk > self.MAX_RISK_SCORE:
            issues.append(f"EXCESSIVE_RISK: {risk:.2f} > {self.MAX_RISK_SCORE}")
        
        # Vérifier que la cible est solvable
        if decision.get("solvability_score", 1.0) < 0.3:
            issues.append("LOW_SOLVABILITY: target unlikely to pay")
        
        # Vérifier la légalité
        if decision.get("legal_risk", "low") == "high":
            issues.append("LEGAL_RISK: operation may not be legal")
        
        # Vérifier la discrétion
        if decision.get("discretion_required", False) and not decision.get("stealth_mode", False):
            issues.append("DISCRETION_BREACH: stealth mode not enabled for sensitive op")
        
        # Vérifier le non-one-shot
        if decision.get("reusable", True) is False and decision.get("type") != "urgent_cash":
            issues.append("ONE_SHOT_DETECTED: creation must be recyclable")
        
        valid = len(issues) == 0
        if valid:
            self._checks_passed += 1
        else:
            self._checks_failed += 1
            self._violations.append({
                "decision_id": decision.get("id", "unknown"),
                "issues": issues, "ts": time.time(),
            })
            if len(self._violations) > 500:
                self._violations = self._violations[-500:]
            log.warning(f"[INTEGRITY] Decision rejected: {issues}")
        
        return {
            "valid": valid, "issues": issues,
            "signature": hashlib.sha256(str(decision).encode()).hexdigest()[:16],
        }
    
    def validate_price(self, price: float) -> bool:
        return price >= self.PREMIUM_FLOOR_EUR
    
    def get_stats(self) -> Dict:
        total = self._checks_passed + self._checks_failed
        return {
            "total_checks": total,
            "passed": self._checks_passed,
            "failed": self._checks_failed,
            "pass_rate": round(self._checks_passed / max(total, 1) * 100, 1),
            "recent_violations": self._violations[-10:],
        }
