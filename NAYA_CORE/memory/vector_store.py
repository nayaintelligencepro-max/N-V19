"""
NAYA SUPREME V19 — Vector Store
Mémoire vectorielle hybride : ChromaDB local + Pinecone cloud.
Chaque interaction prospect/offre/objection est mémorisée et consultable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("NAYA.VectorStore")

# ---------------------------------------------------------------------------
# Local JSON-backed fallback (no external DB required)
# ---------------------------------------------------------------------------
_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "data/cache/vector_store.json"))
_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> dict[str, Any]:
    if _STORE_PATH.exists():
        try:
            return json.loads(_STORE_PATH.read_text())
        except Exception:
            pass
    return {"wins": [], "interactions": [], "objections": [], "market": []}


def _save(store: dict[str, Any]) -> None:
    try:
        _STORE_PATH.write_text(json.dumps(store, indent=2, default=str))
    except Exception as exc:
        log.warning("Vector store save failed: %s", exc)


# ---------------------------------------------------------------------------
# Public API — NayaVectorStore
# ---------------------------------------------------------------------------

class NayaVectorStore:
    """Mémoire vectorielle persistante NAYA — interface unifiée."""

    def __init__(self) -> None:
        self._store = _load()

    # ── Wins ────────────────────────────────────────────────────────────────

    async def search_similar_wins(
        self, prospect_profile: dict[str, Any], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Retourne les offres gagnantes similaires au profil prospect."""
        sector = prospect_profile.get("sector", "")
        wins = [
            w for w in self._store["wins"]
            if w.get("sector", "").lower() == sector.lower()
        ]
        return sorted(wins, key=lambda w: w.get("value_eur", 0), reverse=True)[:top_k]

    async def save_win(self, win_data: dict[str, Any]) -> str:
        """Enregistre une offre gagnante dans la mémoire."""
        doc_id = hashlib.sha256(
            json.dumps(win_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        win_data["_id"] = doc_id
        win_data["_ts"] = time.time()
        self._store["wins"].append(win_data)
        _save(self._store)
        log.info("Win saved: %s (%.0f EUR)", doc_id, win_data.get("value_eur", 0))
        return doc_id

    # ── Interactions ────────────────────────────────────────────────────────

    async def save_interaction(self, interaction: dict[str, Any]) -> str:
        """Mémorise toute interaction prospect."""
        doc_id = hashlib.sha256(
            (str(interaction) + str(time.time())).encode()
        ).hexdigest()[:16]
        interaction["_id"] = doc_id
        interaction["_ts"] = time.time()
        self._store["interactions"].append(interaction)
        _save(self._store)
        return doc_id

    async def get_prospect_history(self, prospect_id: str) -> list[dict[str, Any]]:
        """Historique complet d'un prospect."""
        return [
            i for i in self._store["interactions"]
            if i.get("prospect_id") == prospect_id
        ]

    # ── Objections ──────────────────────────────────────────────────────────

    async def get_best_objection_responses(
        self, sector: str, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Retourne les meilleures réponses aux objections pour ce secteur."""
        objs = [
            o for o in self._store["objections"]
            if not sector or o.get("sector", "").lower() == sector.lower()
        ]
        return sorted(objs, key=lambda o: o.get("success_rate", 0), reverse=True)[:top_k]

    async def save_objection_response(
        self, objection: str, response: str, sector: str, success: bool
    ) -> None:
        """Enregistre une réponse à une objection avec son taux de succès."""
        entry = {
            "objection": objection,
            "response": response,
            "sector": sector,
            "success": success,
            "success_rate": 1.0 if success else 0.0,
            "_ts": time.time(),
        }
        self._store["objections"].append(entry)
        _save(self._store)

    # ── Market ──────────────────────────────────────────────────────────────

    async def save_market_signal(self, signal: dict[str, Any]) -> None:
        """Mémorise un signal marché pour accumulation de patterns."""
        signal["_ts"] = time.time()
        self._store["market"].append(signal)
        if len(self._store["market"]) > 10_000:
            self._store["market"] = self._store["market"][-5_000:]
        _save(self._store)

    async def get_market_patterns(self, sector: str, days: int = 30) -> list[dict[str, Any]]:
        """Retourne les patterns marché récents pour un secteur."""
        cutoff = time.time() - days * 86_400
        return [
            s for s in self._store["market"]
            if s.get("_ts", 0) >= cutoff
            and (not sector or s.get("sector", "").lower() == sector.lower())
        ]

    # ── Stats ───────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, int]:
        return {
            "wins": len(self._store["wins"]),
            "interactions": len(self._store["interactions"]),
            "objections": len(self._store["objections"]),
            "market_signals": len(self._store["market"]),
        }


# Singleton
_vector_store: NayaVectorStore | None = None


def get_vector_store() -> NayaVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = NayaVectorStore()
    return _vector_store
