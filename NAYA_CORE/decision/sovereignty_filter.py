"""NAYA V19 — Sovereignty Filter"""
import logging
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.DECISION.SOVEREIGNTY")

class SovereigntyFilter:
    """
    Filtre de souveraineté — garantit que chaque décision respecte
    l'indépendance totale du système. Aucune dépendance externe obligatoire.
    """
    
    BLOCKED_DEPENDENCIES = [
        "mandatory_subscription", "exclusive_lock", "vendor_lock_in",
        "non_replaceable_service", "single_point_of_failure",
    ]
    
    def __init__(self):
        self._filtered_count = 0
        self._passed_count = 0
    
    def filter(self, decision: Dict) -> Dict:
        """Filtre une décision pour vérifier la souveraineté."""
        issues = []
        
        # Vérifier les dépendances bloquantes
        deps = decision.get("dependencies", [])
        for dep in deps:
            dep_type = dep.get("type", "") if isinstance(dep, dict) else str(dep)
            if dep_type in self.BLOCKED_DEPENDENCIES:
                issues.append(f"BLOCKED_DEP: {dep_type}")
            # Vérifier qu'il existe un fallback
            if isinstance(dep, dict) and not dep.get("fallback"):
                issues.append(f"NO_FALLBACK: {dep.get('name', dep_type)}")
        
        # Vérifier que le service peut fonctionner offline
        if decision.get("requires_internet", False) and not decision.get("offline_fallback"):
            issues.append("NO_OFFLINE_MODE: must work without internet")
        
        # Vérifier que les données restent sous contrôle
        if decision.get("data_export_required", False) and not decision.get("data_sovereignty_ok"):
            issues.append("DATA_SOVEREIGNTY: data must stay under system control")
        
        # Vérifier que le coût est remplaçable
        if decision.get("monthly_cost", 0) > 500 and not decision.get("free_alternative"):
            issues.append("EXPENSIVE_DEPENDENCY: >500€/mois sans alternative gratuite")
        
        passed = len(issues) == 0
        if passed:
            self._passed_count += 1
        else:
            self._filtered_count += 1
            log.info(f"[SOVEREIGNTY] Filtered: {issues}")
        
        return {
            "sovereign": passed,
            "issues": issues,
            "recommendation": "PROCEED" if passed else "REVIEW_DEPENDENCIES",
        }
    
    def check_api_dependency(self, api_name: str, has_fallback: bool) -> bool:
        """Vérifie qu'une API a un fallback."""
        if not has_fallback:
            log.warning(f"[SOVEREIGNTY] API {api_name} sans fallback")
        return has_fallback
    
    def get_stats(self) -> Dict:
        total = self._filtered_count + self._passed_count
        return {
            "total_checks": total,
            "passed": self._passed_count,
            "filtered": self._filtered_count,
            "sovereignty_rate": round(self._passed_count / max(total, 1) * 100, 1),
        }
