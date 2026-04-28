"""Gestionnaire de pipeline parallèle (4 slots par défaut)."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(order=True)
class PipelineTask:
    """Tâche ordonnée par priorité décroissante."""

    sort_index: int = field(init=False, repr=False)
    priority: int
    created_at: float
    task_id: str
    payload: Dict[str, Any]

    def __post_init__(self) -> None:
        self.sort_index = -self.priority


class PipelineManager:
    """Planifie et distribue les tâches sur des slots parallèles."""

    def __init__(self, max_slots: int = 4) -> None:
        self.max_slots = max_slots
        self._queue: List[PipelineTask] = []
        self._active: Dict[int, PipelineTask] = {}

    @staticmethod
    def score_payload(payload: Dict[str, Any]) -> int:
        """Score orienté revenu/priorité business.

        Heuristique:
        - budget_estimate_eur élevé => priorité
        - score_lead / pain_score élevé => priorité
        - urgent=true => boost
        - offer_price < 1000 => pénalité (plancher business)
        """
        budget = float(payload.get("budget_estimate_eur", 0) or 0)
        lead_score = float(payload.get("score", payload.get("pain_score", 0)) or 0)
        urgent = 15 if bool(payload.get("urgent", False)) else 0
        offer_price = float(payload.get("offer_price", 0) or 0)

        score = int((budget / 1000.0) * 2 + lead_score + urgent)
        if 0 < offer_price < 1000:
            score -= 30
        return max(1, min(100, score))

    def enqueue(self, task_id: str, payload: Dict[str, Any], priority: int = 50) -> None:
        if priority == 50:
            priority = self.score_payload(payload)
        heapq.heappush(
            self._queue,
            PipelineTask(priority=priority, created_at=time.time(), task_id=task_id, payload=payload),
        )

    def age_queue(self, max_boost: int = 10) -> int:
        """Augmente progressivement la priorité des tâches anciennes (anti-starvation)."""
        if not self._queue:
            return 0
        now = time.time()
        updated = 0
        rebuilt: List[PipelineTask] = []
        while self._queue:
            t = heapq.heappop(self._queue)
            age_s = max(0.0, now - t.created_at)
            boost = min(max_boost, int(age_s // 300))  # +1 toutes les 5 min
            if boost > 0:
                t.priority = min(100, t.priority + boost)
                t.sort_index = -t.priority
                updated += 1
            rebuilt.append(t)
        for t in rebuilt:
            heapq.heappush(self._queue, t)
        return updated

    def dispatch_next(self) -> Optional[Dict[str, Any]]:
        """Assigne une tâche au premier slot libre."""
        if len(self._active) >= self.max_slots or not self._queue:
            return None

        free_slot = next(i for i in range(self.max_slots) if i not in self._active)
        task = heapq.heappop(self._queue)
        self._active[free_slot] = task
        return {
            "slot": free_slot,
            "task_id": task.task_id,
            "payload": task.payload,
            "priority": task.priority,
        }

    def release_slot(self, slot: int) -> bool:
        """Libère un slot occupé."""
        if slot not in self._active:
            return False
        del self._active[slot]
        return True

    def stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de file et slots."""
        return {
            "max_slots": self.max_slots,
            "active_slots": len(self._active),
            "queued_tasks": len(self._queue),
            "active_task_ids": [t.task_id for t in self._active.values()],
            "queued_top": [
                {"task_id": t.task_id, "priority": t.priority}
                for t in sorted(self._queue, key=lambda x: x.priority, reverse=True)[:5]
            ],
        }


pipeline_manager = PipelineManager()
