"""NAYA V19 - Zero Waste Recycler - Rien n est jete, tout est recycle."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.HUNT.ZEROWASTE")

class ZeroWasteRecycler:
    """Chaque rejet, echec ou creation partielle est recycle en valeur."""

    def __init__(self):
        self._waste_bin: List[Dict] = []
        self._recycled: List[Dict] = []
        self._total_recovered_value = 0.0

    def collect_waste(self, item_type: str, data: Dict, reason: str = "rejected") -> Dict:
        waste = {
            "type": item_type, "data": data, "reason": reason,
            "collected_at": time.time(), "recycled": False
        }
        self._waste_bin.append(waste)
        return waste

    def find_recyclable(self) -> List[Dict]:
        recyclable = []
        for waste in self._waste_bin:
            if waste["recycled"]:
                continue
            potential = self._assess_recycling_potential(waste)
            if potential > 0.3:
                recyclable.append({"waste": waste, "potential": potential})
        recyclable.sort(key=lambda x: x["potential"], reverse=True)
        return recyclable

    def recycle(self, waste_index: int, new_purpose: str, value_recovered: float = 0) -> Dict:
        if waste_index >= len(self._waste_bin):
            return {"error": "index_out_of_range"}
        waste = self._waste_bin[waste_index]
        waste["recycled"] = True
        recycled = {
            "original": waste, "new_purpose": new_purpose,
            "value_recovered": value_recovered, "recycled_at": time.time()
        }
        self._recycled.append(recycled)
        self._total_recovered_value += value_recovered
        log.info(f"[ZEROWASTE] Recycle: {waste['type']} -> {new_purpose} (+{value_recovered}EUR)")
        return recycled

    def _assess_recycling_potential(self, waste: Dict) -> float:
        data = waste.get("data", {})
        has_content = bool(data.get("description") or data.get("template") or data.get("analysis"))
        has_contacts = bool(data.get("prospect") or data.get("leads"))
        has_research = bool(data.get("sector_data") or data.get("market_data"))
        score = (0.3 if has_content else 0) + (0.4 if has_contacts else 0) + (0.3 if has_research else 0)
        return score

    def get_stats(self) -> Dict:
        return {
            "waste_collected": len(self._waste_bin),
            "recycled": len(self._recycled),
            "pending": sum(1 for w in self._waste_bin if not w["recycled"]),
            "value_recovered_eur": self._total_recovered_value
        }
