"""NAYA V19 - Core Doctrine Mutation - Mutations controlees de la doctrine."""
import logging, time, hashlib
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.EVOLUTION.MUTATION")

class CoreDoctrineMutation:
    """Mutations controlees: le systeme evolue mais jamais au-dela des invariants."""

    IMMUTABLE_RULES = {
        "premium_floor_min": 1000,
        "founder_loyalty": True,
        "non_vendable": True,
        "stealth_default": True,
        "legal_only": True,
        "non_regression": True,
    }

    def __init__(self):
        self._mutations: List[Dict] = []
        self._rejected: List[Dict] = []

    def propose_mutation(self, target: str, new_value, reason: str) -> Dict:
        """Propose une mutation de doctrine. Rejetee si touche un invariant."""
        if target in self.IMMUTABLE_RULES:
            rejection = {
                "target": target, "proposed": new_value,
                "reason": f"INVARIANT - {target} est immutable", "ts": time.time()
            }
            self._rejected.append(rejection)
            log.warning(f"[MUTATION] REJETEE: {target} est immutable")
            return {"accepted": False, **rejection}

        mutation = {
            "id": hashlib.md5(f"{target}{time.time()}".encode()).hexdigest()[:10],
            "target": target, "new_value": new_value,
            "reason": reason, "ts": time.time(), "applied": False
        }
        self._mutations.append(mutation)
        log.info(f"[MUTATION] Proposee: {target} -> {new_value} ({reason})")
        return {"accepted": True, **mutation}

    def apply_mutation(self, mutation_id: str) -> Dict:
        for m in self._mutations:
            if m["id"] == mutation_id and not m["applied"]:
                m["applied"] = True
                m["applied_at"] = time.time()
                log.info(f"[MUTATION] Appliquee: {m['target']}")
                return {"applied": True, "mutation": m}
        return {"applied": False, "reason": "Mutation non trouvee ou deja appliquee"}

    def get_pending(self) -> List[Dict]:
        return [m for m in self._mutations if not m["applied"]]

    def get_stats(self) -> Dict:
        return {
            "total_proposed": len(self._mutations),
            "total_applied": sum(1 for m in self._mutations if m["applied"]),
            "total_rejected": len(self._rejected),
            "immutable_rules": len(self.IMMUTABLE_RULES)
        }
