"""
NAYA_CORE — Cognition Memory Store
====================================
Mémoire court-terme et long-terme pour la cognition NAYA.
Stocke les décisions, patterns et contextes pour apprentissage continu.
"""
import time, hashlib, logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import OrderedDict

log = logging.getLogger("NAYA.MEMORY")

@dataclass
class MemoryEntry:
    key: str
    content: Any
    memory_type: str  # "episodic" | "semantic" | "procedural" | "working"
    importance: float = 0.5   # 0-1
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # None = permanent

    def access(self) -> Any:
        self.access_count += 1
        self.last_accessed = time.time()
        return self.content

    def is_expired(self) -> bool:
        if self.ttl is None: return False
        return time.time() - self.created_at > self.ttl

    def importance_score(self) -> float:
        recency = max(0, 1 - (time.time() - self.last_accessed) / 86400)
        frequency = min(1, self.access_count / 100)
        return self.importance * 0.5 + recency * 0.3 + frequency * 0.2


class WorkingMemory:
    """Mémoire de travail — contexte immédiat (capacité limitée)."""
    MAX_CAPACITY = 7  # Limite cognitive standard

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def push(self, item: Dict[str, Any]) -> None:
        self._items.append(item)
        if len(self._items) > self.MAX_CAPACITY:
            self._items.pop(0)  # Oubli du plus ancien

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()

    def peek(self, n: int = 3) -> List[Dict[str, Any]]:
        return self._items[-n:]


class EpisodicMemory:
    """Mémoire épisodique — événements et expériences vécues."""

    def __init__(self, max_episodes: int = 10000):
        self._episodes: List[MemoryEntry] = []
        self._max = max_episodes

    def store(self, episode: Dict[str, Any], importance: float = 0.5) -> str:
        key = hashlib.md5(str(episode).encode()).hexdigest()[:12]
        entry = MemoryEntry(key=key, content=episode, memory_type="episodic",
                            importance=importance)
        self._episodes.append(entry)
        if len(self._episodes) > self._max:
            # Supprimer les moins importants
            self._episodes.sort(key=lambda e: e.importance_score())
            self._episodes = self._episodes[int(self._max * 0.1):]
        return key

    def recall(self, n: int = 10, min_importance: float = 0.0) -> List[Dict]:
        valid = [e for e in self._episodes if not e.is_expired()
                 and e.importance >= min_importance]
        valid.sort(key=lambda e: e.importance_score(), reverse=True)
        return [e.access() for e in valid[:n]]

    def search(self, query: str) -> List[Dict]:
        results = []
        for e in self._episodes:
            content_str = str(e.content).lower()
            if query.lower() in content_str:
                results.append(e.access())
        return results[:20]


class SemanticMemory:
    """Mémoire sémantique — connaissances et faits généraux."""

    def __init__(self):
        self._knowledge: Dict[str, MemoryEntry] = {}

    def learn(self, concept: str, knowledge: Any, importance: float = 0.7) -> None:
        entry = MemoryEntry(key=concept, content=knowledge,
                            memory_type="semantic", importance=importance)
        self._knowledge[concept] = entry

    def recall(self, concept: str) -> Optional[Any]:
        entry = self._knowledge.get(concept)
        if entry and not entry.is_expired():
            return entry.access()
        return None

    def get_related(self, concept: str, n: int = 5) -> List[Dict]:
        results = []
        for k, e in self._knowledge.items():
            if concept.lower() in k.lower() or k.lower() in concept.lower():
                results.append({"concept": k, "knowledge": e.content,
                                 "importance": e.importance})
        return sorted(results, key=lambda r: r["importance"], reverse=True)[:n]

    def list_concepts(self) -> List[str]:
        return [k for k, e in self._knowledge.items() if not e.is_expired()]


class CognitionMemoryStore:
    """
    Store de mémoire cognitif unifié.
    Intègre working, episodic et semantic memory.
    """

    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self._decision_cache: OrderedDict = OrderedDict()
        self._cache_max = 500

        # Pré-charger connaissances NAYA
        self._init_semantic_knowledge()

    def _init_semantic_knowledge(self) -> None:
        base_knowledge = {
            "fast_cash_tiers": {"24h": 20000, "48h": 50000, "72h": 80000},
            "credibility_levels": ["BUILDING", "SOLID", "STRONG", "EXCELLENT", "CATEGORY_LEADER"],
            "decision_thresholds": {"approve": 0.70, "conditional": 0.55, "reject": 0.45},
            "solvability_floor": 60.0,
            "premium_floor": 1000.0,
        }
        for concept, knowledge in base_knowledge.items():
            self.semantic.learn(concept, knowledge, importance=0.9)

    def remember_decision(self, decision_id: str, context: Dict, result: Dict,
                          confidence: float) -> None:
        """Mémorise une décision pour apprentissage futur."""
        episode = {"decision_id": decision_id, "context": context,
                   "result": result, "confidence": confidence,
                   "timestamp": time.time()}
        importance = min(1.0, confidence)
        self.episodic.store(episode, importance)

        # Cache LRU
        self._decision_cache[decision_id] = {"context": context, "result": result,
                                              "confidence": confidence}
        if len(self._decision_cache) > self._cache_max:
            self._decision_cache.popitem(last=False)

        # Mettre à jour le contexte de travail
        self.working.push({"type": "decision", "id": decision_id,
                           "status": result.get("status"), "confidence": confidence})

    def find_similar_decision(self, context: Dict, threshold: float = 0.8) -> Optional[Dict]:
        """Cherche une décision similaire dans le cache."""
        context_key = hashlib.md5(str(sorted(context.items())).encode()).hexdigest()
        for decision_id, cached in self._decision_cache.items():
            cached_key = hashlib.md5(str(sorted(cached["context"].items())).encode()).hexdigest()
            if context_key == cached_key and cached["confidence"] >= threshold:
                return cached
        return None

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "working_memory_items": len(self.working.get_all()),
            "episodic_memory_episodes": len(self.episodic._episodes),
            "semantic_concepts": len(self.semantic.list_concepts()),
            "decision_cache_size": len(self._decision_cache),
            "recent_decisions": self.working.peek(3),
        }


# Singleton
_MEMORY_STORE: Optional[CognitionMemoryStore] = None

def get_memory_store() -> CognitionMemoryStore:
    global _MEMORY_STORE
    if _MEMORY_STORE is None: _MEMORY_STORE = CognitionMemoryStore()
    return _MEMORY_STORE
