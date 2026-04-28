"""
NAYA — Distributed Memory System
Mémoire persistante, indexée, exportable.
Stocke chaque décision, opportunité, mission et résultat.
"""
import json
import time
import threading
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("NAYA.MEMORY")

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "data" / "naya_memory.json"


class DistributedMemory:
    """
    Mémoire distribuée NAYA.
    - Stockage JSON persistant
    - Indexation par catégorie, projet, date
    - Export Notion-ready
    - Thread-safe
    """

    def __init__(self, path: str = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: List[Dict] = []
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache = data if isinstance(data, list) else []
            else:
                self._cache = []
                self._save()
        except Exception as e:
            log.warning(f"Memory load error: {e}")
            self._cache = []

    def _save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False, default=str)
            tmp.replace(self.path)
        except Exception as e:
            log.warning(f"Memory save error: {e}")

    def store(self, opportunity: Any = None, decision: Any = None,
              category: str = "decision", project: str = None,
              tags: List[str] = None, metadata: Dict = None) -> str:
        entry_id = f"MEM_{int(time.time()*1000)}"
        entry = {
            "id": entry_id,
            "ts": time.time(),
            "datetime": datetime.now(timezone.utc).isoformat() + "Z",
            "category": category,
            "project": project,
            "tags": tags or [],
            "opportunity": opportunity,
            "decision": decision,
            "metadata": metadata or {},
        }
        with self._lock:
            self._cache.append(entry)
            if len(self._cache) > 10000:
                self._cache = self._cache[-10000:]
            self._save()
        return entry_id

    def recall(self, category: str = None, project: str = None,
               tags: List[str] = None, limit: int = 20) -> List[Dict]:
        with self._lock:
            results = list(self._cache)
        if category:
            results = [e for e in results if e.get("category") == category]
        if project:
            results = [e for e in results if e.get("project") == project]
        if tags:
            results = [e for e in results if any(t in e.get("tags", []) for t in tags)]
        results.sort(key=lambda e: e.get("ts", 0), reverse=True)
        return results[:limit]

    def load(self) -> List[Dict]:
        with self._lock:
            return list(self._cache)

    def stats(self) -> Dict:
        with self._lock:
            total = len(self._cache)
            by_category: Dict[str, int] = {}
            by_project: Dict[str, int] = {}
            for e in self._cache:
                cat = e.get("category", "unknown")
                proj = e.get("project") or "global"
                by_category[cat] = by_category.get(cat, 0) + 1
                by_project[proj] = by_project.get(proj, 0) + 1
            oldest = min((e.get("ts", 0) for e in self._cache), default=0)
            newest = max((e.get("ts", 0) for e in self._cache), default=0)
        return {
            "total_entries": total,
            "by_category": by_category,
            "by_project": by_project,
            "oldest": datetime.fromtimestamp(oldest).isoformat() if oldest else None,
            "newest": datetime.fromtimestamp(newest).isoformat() if newest else None,
            "path": str(self.path),
            "size_kb": round(self.path.stat().st_size / 1024, 1) if self.path.exists() else 0,
        }

    def export_for_notion(self, limit: int = 50, category: str = None) -> List[Dict]:
        entries = self.recall(category=category, limit=limit)
        return [{
            "id": e["id"],
            "Date": e.get("datetime", ""),
            "Catégorie": e.get("category", ""),
            "Projet": e.get("project") or "global",
            "Tags": ", ".join(e.get("tags", [])),
            "Opportunité": str(e.get("opportunity", ""))[:500],
            "Décision": str(e.get("decision", ""))[:500],
        } for e in entries]

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        query_lower = query.lower()
        with self._lock:
            results = []
            for e in reversed(self._cache):
                if query_lower in json.dumps(e, ensure_ascii=False).lower():
                    results.append(e)
                    if len(results) >= limit:
                        break
        return results

    def clear_old(self, days: int = 90) -> int:
        cutoff = time.time() - (days * 86400)
        with self._lock:
            before = len(self._cache)
            self._cache = [e for e in self._cache if e.get("ts", 0) > cutoff]
            removed = before - len(self._cache)
            if removed > 0:
                self._save()
        return removed


_memory: Optional[DistributedMemory] = None


def get_memory() -> DistributedMemory:
    global _memory
    if _memory is None:
        _memory = DistributedMemory()
    return _memory
