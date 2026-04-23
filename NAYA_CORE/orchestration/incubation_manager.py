"""NAYA V19 - Incubation Manager - Gere les opportunites en incubation."""
import time, logging
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.INCUBATION")

class IncubationManager:
    """Gere les opportunites et projets en incubation - les surveille et les promeut."""

    MAX_INCUBATION_DAYS = 30

    def __init__(self):
        self._incubating: Dict[str, Dict] = {}
        self._promoted: List[Dict] = []
        self._expired: List[Dict] = []

    def incubate(self, item_id: str, item_type: str, data: Dict) -> Dict:
        entry = {
            "id": item_id, "type": item_type, "data": data,
            "incubated_at": time.time(), "check_count": 0,
            "promotion_score": 0.0, "status": "incubating"
        }
        self._incubating[item_id] = entry
        log.info(f"[INCUBATION] {item_type} {item_id} en incubation")
        return entry

    def check_promotion_readiness(self, item_id: str) -> Dict:
        entry = self._incubating.get(item_id)
        if not entry:
            return {"ready": False, "reason": "not_found"}
        entry["check_count"] += 1
        age_days = (time.time() - entry["incubated_at"]) / 86400
        data = entry.get("data", {})
        score = data.get("solvability", 0.5) * 0.3 + data.get("urgency", 0.3) * 0.3 + min(1, age_days / 7) * 0.2 + data.get("market_size", 0.5) * 0.2
        entry["promotion_score"] = score
        ready = score >= 0.6 or (age_days > 7 and score >= 0.4)
        return {"ready": ready, "score": round(score, 3), "age_days": round(age_days, 1)}

    def promote(self, item_id: str) -> Optional[Dict]:
        entry = self._incubating.pop(item_id, None)
        if not entry:
            return None
        entry["status"] = "promoted"
        entry["promoted_at"] = time.time()
        self._promoted.append(entry)
        log.info(f"[INCUBATION] {item_id} promu!")
        return entry

    def expire_old(self) -> List[str]:
        cutoff = time.time() - (self.MAX_INCUBATION_DAYS * 86400)
        expired_ids = []
        for iid, entry in list(self._incubating.items()):
            if entry["incubated_at"] < cutoff and entry["promotion_score"] < 0.3:
                entry["status"] = "expired"
                self._expired.append(entry)
                del self._incubating[iid]
                expired_ids.append(iid)
        return expired_ids

    def get_incubating(self) -> List[Dict]:
        return list(self._incubating.values())

    def get_stats(self) -> Dict:
        return {
            "incubating": len(self._incubating),
            "promoted": len(self._promoted),
            "expired": len(self._expired),
            "avg_score": round(
                sum(e["promotion_score"] for e in self._incubating.values()) / max(1, len(self._incubating)), 3
            )
        }
