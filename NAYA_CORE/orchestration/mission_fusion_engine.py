"""NAYA V19 - Mission Fusion Engine - Fusionne des missions complementaires."""
import time, logging
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.MISSION.FUSION")

class MissionFusionEngine:
    """Detecte et fusionne des missions complementaires pour maximiser l efficacite."""

    def __init__(self):
        self._missions: Dict[str, Dict] = {}
        self._fusions: List[Dict] = []

    def register_mission(self, mission_id: str, mission_type: str,
                         sector: str, skills_required: List[str]) -> Dict:
        mission = {
            "id": mission_id, "type": mission_type, "sector": sector,
            "skills": skills_required, "created_at": time.time(), "fused_with": None
        }
        self._missions[mission_id] = mission
        return mission

    def find_fuseable(self, mission_id: str) -> List[Dict]:
        target = self._missions.get(mission_id)
        if not target:
            return []
        candidates = []
        for mid, m in self._missions.items():
            if mid == mission_id or m.get("fused_with"):
                continue
            # Same sector or overlapping skills
            skill_overlap = len(set(target["skills"]) & set(m["skills"]))
            same_sector = target["sector"] == m["sector"]
            if skill_overlap >= 1 or same_sector:
                score = skill_overlap * 0.4 + (0.6 if same_sector else 0)
                candidates.append({"mission_id": mid, "score": round(score, 2), "overlap_skills": skill_overlap})
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def fuse(self, mission_a: str, mission_b: str) -> Dict:
        a = self._missions.get(mission_a)
        b = self._missions.get(mission_b)
        if not a or not b:
            return {"error": "mission_not_found"}
        fused_skills = list(set(a["skills"] + b["skills"]))
        fusion = {
            "fusion_id": f"FUSION_{len(self._fusions)+1}",
            "missions": [mission_a, mission_b],
            "combined_skills": fused_skills,
            "sector": a["sector"],
            "created_at": time.time()
        }
        a["fused_with"] = mission_b
        b["fused_with"] = mission_a
        self._fusions.append(fusion)
        log.info(f"[FUSION] {mission_a} + {mission_b} -> {fusion['fusion_id']}")
        return fusion

    def get_stats(self) -> Dict:
        return {
            "total_missions": len(self._missions),
            "fused_missions": sum(1 for m in self._missions.values() if m.get("fused_with")),
            "total_fusions": len(self._fusions)
        }
