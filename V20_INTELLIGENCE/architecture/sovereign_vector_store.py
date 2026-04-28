"""
NAYA V20 — Sovereign Vector Store
══════════════════════════════════════════════════════════════════════════════
Pure-Python vector store using cosine similarity. Zero external dependencies.

DOCTRINE:
  NAYA must be able to run its full memory layer without Pinecone, Chroma or
  any cloud service.  This store is the offline-sovereign fallback that keeps
  all semantic search capabilities alive even in OFFLINE resilience mode.

ALGORITHM:
  Brute-force cosine similarity over stored float vectors.
  Acceptable for collections up to ~50k documents; sufficient for NAYA's
  operational volumes.

COLLECTIONS:
  Each collection is stored as a separate JSON file under
  ROOT/data/vector_store/{collection}.json.
  Documents: {"id": str, "vector": List[float], "metadata": Dict, "created_at": str}
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import math
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SOVEREIGN_VECTOR_STORE")

ROOT = Path(__file__).resolve().parent.parent.parent
_STORE_DIR = ROOT / "data" / "vector_store"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class SovereignVectorStore:
    """
    Fully local vector store — no external dependencies.

    Each collection is an independent JSON file.
    Thread-safe via per-collection locking.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        _STORE_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _collection_path(self, collection: str) -> Path:
        return _STORE_DIR / f"{collection}.json"

    def _load_collection(self, collection: str) -> Dict[str, Dict]:
        """Load collection from disk. Returns empty dict on missing/corrupt file."""
        path = self._collection_path(collection)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_collection(self, collection: str, docs: Dict[str, Dict]) -> None:
        path = self._collection_path(collection)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Compute cosine similarity between two float vectors.

        Args:
            a: Query vector.
            b: Stored document vector.

        Returns:
            Cosine similarity in [-1, 1]. Returns 0.0 for zero-length vectors.
        """
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def upsert(
        self,
        collection: str,
        doc_id: str,
        vector: List[float],
        metadata: Dict,
    ) -> bool:
        """
        Insert or update a document in a collection.

        Args:
            collection: Collection name (alphanumeric + underscores).
            doc_id: Unique document identifier.
            vector: Embedding float list.
            metadata: Arbitrary key-value payload stored alongside the vector.

        Returns:
            True on success.
        """
        with self._lock:
            docs = self._load_collection(collection)
            docs[doc_id] = {
                "id": doc_id,
                "vector": vector,
                "metadata": metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_collection(collection, docs)
        return True

    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Find the most similar documents in a collection.

        Args:
            collection: Target collection name.
            query_vector: Embedding to search for.
            top_k: Maximum number of results to return.
            filter_metadata: If provided, only docs whose metadata contains all
                             key-value pairs in this dict are considered.

        Returns:
            List of result dicts sorted by score descending.
            Each dict: {doc_id, score, metadata}.
        """
        with self._lock:
            docs = self._load_collection(collection)

        results = []
        for doc_id, doc in docs.items():
            # Apply metadata filter
            if filter_metadata:
                meta = doc.get("metadata", {})
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue
            score = self._cosine_similarity(query_vector, doc["vector"])
            results.append({
                "doc_id": doc_id,
                "score": score,
                "metadata": doc.get("metadata", {}),
            })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def delete(self, collection: str, doc_id: str) -> bool:
        """
        Remove a document from a collection.

        Args:
            collection: Collection name.
            doc_id: Document identifier to remove.

        Returns:
            True if the document existed and was removed, False if not found.
        """
        with self._lock:
            docs = self._load_collection(collection)
            if doc_id not in docs:
                return False
            del docs[doc_id]
            self._save_collection(collection, docs)
        return True

    def get_collection_stats(self, collection: str) -> Dict:
        """
        Return stats for a single collection.

        Args:
            collection: Collection name.

        Returns:
            Dict with collection, doc_count, file_size_bytes.
        """
        path = self._collection_path(collection)
        with self._lock:
            docs = self._load_collection(collection)
        file_size = path.stat().st_size if path.exists() else 0
        return {
            "collection": collection,
            "doc_count": len(docs),
            "file_size_bytes": file_size,
        }

    def get_stats(self) -> Dict:
        """
        Return aggregate stats across all collections.

        Returns:
            Dict with collections list and total_docs count.
        """
        collections = [p.stem for p in _STORE_DIR.glob("*.json")]
        total_docs = 0
        for col in collections:
            with self._lock:
                docs = self._load_collection(col)
            total_docs += len(docs)
        return {"collections": collections, "total_docs": total_docs}


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_store: Optional[SovereignVectorStore] = None


def get_sovereign_vector_store() -> SovereignVectorStore:
    """Return the process-wide singleton SovereignVectorStore instance."""
    global _store
    if _store is None:
        _store = SovereignVectorStore()
    return _store
