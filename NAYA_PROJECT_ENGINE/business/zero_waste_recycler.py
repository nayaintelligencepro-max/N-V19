"""Zero-Waste Asset Recycler — NAYA SUPREME V19.

Principe fondateur : RIEN n'est jetable dans NAYA.
Chaque email rédigé, chaque offre générée, chaque audit produit,
chaque séquence outreach, chaque contrat signé = actif réutilisable.

Ce module:
1) Enregistre chaque asset créé dans un registre persistant
2) Indexe par secteur / type / performance
3) Recommande des recyclages cross-projets
4) Versionne chaque asset (learning cumulatif)
5) Génère des bundles assets réutilisables par nouveau projet
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────────────────────── ASSET TYPES ─────────────────────────────────────

class AssetType(str, Enum):
    EMAIL_SEQUENCE = "email_sequence"
    OFFER_1PAGER = "offer_1pager"
    AUDIT_TEMPLATE = "audit_template"
    OBJECTION_FAQ = "objection_faq"
    CONTRACT_TEMPLATE = "contract_template"
    CONTENT_ARTICLE = "content_article"
    WHITEPAPER = "whitepaper"
    LEAD_LIST = "lead_list"
    CASE_STUDY = "case_study"
    OUTREACH_HOOK = "outreach_hook"
    PITCH_DECK = "pitch_deck"
    PAIN_SIGNAL = "pain_signal"
    BUSINESS_MODEL = "business_model"
    PLAYBOOK = "playbook"


class AssetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    TESTED = "tested"           # A/B testé
    WINNER = "winner"           # Version gagnante
    ARCHIVED = "archived"       # Obsolète mais conservé


@dataclass
class Asset:
    asset_id: str
    asset_type: str                     # AssetType value
    name: str
    source_project: str
    sector: str
    content_hash: str                   # SHA-256 du contenu (déduplication)
    performance_score: float = 0.0      # 0-100 basé sur résultats réels
    usage_count: int = 0
    recycled_to: List[str] = field(default_factory=list)   # projets qui ont réutilisé
    tags: List[str] = field(default_factory=list)
    version: int = 1
    status: str = AssetStatus.DRAFT.value
    payload: Dict[str, Any] = field(default_factory=dict)  # contenu réel
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used_at: Optional[str] = None


# ─────────────────────────── REGISTRY ────────────────────────────────────────

class ZeroWasteAssetRecycler:
    """Registre d'assets zéro-déchet pour NAYA SUPREME.

    Toute création → enregistrée.
    Toute réutilisation → tracée.
    Tout asset → versionné et appris.
    """

    REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "zero_waste_registry.json"

    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}
        self._load()

    # ── CORE CRUD ─────────────────────────────────────────────────────────

    def register(
        self,
        asset_type: str,
        name: str,
        source_project: str,
        sector: str,
        payload: Dict[str, Any],
        tags: Optional[List[str]] = None,
        performance_score: float = 0.0,
    ) -> str:
        """Enregistre un nouvel asset (ou incrémente sa version si existant)."""
        content_hash = self._hash(payload)

        # Déduplication par hash
        existing = self._find_by_hash(content_hash)
        if existing:
            existing.usage_count += 1
            existing.last_used_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return existing.asset_id

        asset_id = f"ASSET_{asset_type.upper()[:6]}_{content_hash[:8].upper()}"
        asset = Asset(
            asset_id=asset_id,
            asset_type=asset_type,
            name=name,
            source_project=source_project,
            sector=sector,
            content_hash=content_hash,
            performance_score=performance_score,
            tags=tags or [sector, asset_type],
            payload=payload,
            status=AssetStatus.DRAFT.value,
        )
        self._assets[asset_id] = asset
        self._save()
        return asset_id

    def recycle(self, asset_id: str, target_project: str, adaptations: Optional[Dict] = None) -> Dict[str, Any]:
        """Recycle un asset vers un nouveau projet avec adaptations optionnelles."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found")

        # crée une version adaptée si modifications
        if adaptations:
            new_payload = {**asset.payload, **adaptations}
            new_id = self.register(
                asset_type=asset.asset_type,
                name=f"{asset.name} [recycled→{target_project}]",
                source_project=target_project,
                sector=asset.sector,
                payload=new_payload,
                tags=asset.tags + ["recycled"],
                performance_score=asset.performance_score * 0.9,  # léger discount sur version adaptée
            )
            new_asset = self._assets[new_id]
            new_asset.version = asset.version + 1
            new_asset.status = AssetStatus.ACTIVE.value
        else:
            new_id = asset_id

        if target_project not in asset.recycled_to:
            asset.recycled_to.append(target_project)
        asset.usage_count += 1
        asset.last_used_at = datetime.now(timezone.utc).isoformat()
        self._save()

        return asdict(self._assets[new_id])

    def update_performance(self, asset_id: str, score: float, status: Optional[str] = None) -> None:
        """Met à jour le score de performance après test réel."""
        asset = self._assets.get(asset_id)
        if asset is None:
            return
        asset.performance_score = score
        if status:
            asset.status = status
        self._save()

    # ── SEARCH & RECOMMEND ───────────────────────────────────────────────

    def find_reusable(
        self,
        asset_type: Optional[str] = None,
        sector: Optional[str] = None,
        min_score: float = 0.0,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Trouve les meilleurs assets réutilisables."""
        assets = list(self._assets.values())

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        if sector:
            s = sector.lower()
            assets = [a for a in assets if s in a.sector.lower() or any(s in t.lower() for t in a.tags)]
        if min_score > 0:
            assets = [a for a in assets if a.performance_score >= min_score]
        if status:
            assets = [a for a in assets if a.status == status]

        assets.sort(key=lambda a: (a.performance_score, a.usage_count), reverse=True)
        return [asdict(a) for a in assets[:limit]]

    def get_winners(self, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retourne uniquement les assets validés gagnants."""
        return self.find_reusable(status=AssetStatus.WINNER.value, sector=sector)

    def recommend_for_project(self, project_id: str, sector: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recommande des assets à recycler pour un nouveau projet."""
        # Assets actifs/winners non encore utilisés par ce projet
        candidates = [
            a for a in self._assets.values()
            if project_id not in a.recycled_to
            and a.status in (AssetStatus.ACTIVE.value, AssetStatus.WINNER.value, AssetStatus.TESTED.value)
            and (not sector or sector.lower() in a.sector.lower() or any(sector.lower() in t.lower() for t in a.tags))
        ]
        candidates.sort(key=lambda a: a.performance_score, reverse=True)
        return [asdict(a) for a in candidates[:limit]]

    # ── BUNDLES ──────────────────────────────────────────────────────────

    def generate_starter_bundle(self, sector: str, project_id: str) -> Dict[str, Any]:
        """Génère un bundle de démarrage en recyclant les meilleurs assets existants."""
        bundle: Dict[str, List] = {
            AssetType.EMAIL_SEQUENCE.value: [],
            AssetType.OFFER_1PAGER.value: [],
            AssetType.OBJECTION_FAQ.value: [],
            AssetType.AUDIT_TEMPLATE.value: [],
        }

        for asset_type in bundle.keys():
            found = self.find_reusable(asset_type=asset_type, sector=sector, limit=2)
            if not found:
                # Essai cross-sectoriel: les tops performants tous secteurs
                found = self.find_reusable(asset_type=asset_type, min_score=60.0, limit=1)
            bundle[asset_type] = [a["asset_id"] for a in found]

        return {
            "project_id": project_id,
            "sector": sector,
            "bundle_type": "starter",
            "recyclable_count": sum(len(v) for v in bundle.values()),
            "assets": bundle,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── STATS ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Résumé global du registre zero-waste."""
        total = len(self._assets)
        if total == 0:
            return {"total_assets": 0, "total_recycled": 0, "avg_score": 0}

        status_counts: Dict[str, int] = {}
        for a in self._assets.values():
            status_counts[a.status] = status_counts.get(a.status, 0) + 1

        total_recycled = sum(a.usage_count for a in self._assets.values())
        avg_score = sum(a.performance_score for a in self._assets.values()) / total
        by_type: Dict[str, int] = {}
        for a in self._assets.values():
            by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1

        return {
            "total_assets": total,
            "total_recycled_usages": total_recycled,
            "avg_performance_score": round(avg_score, 1),
            "by_status": status_counts,
            "by_type": by_type,
            "winners_count": status_counts.get(AssetStatus.WINNER.value, 0),
        }

    def for_tori_dashboard(self) -> Dict[str, Any]:
        """Payload dashboard TORI_APP."""
        s = self.stats()
        top5 = self.find_reusable(min_score=50.0, limit=5)
        return {
            **s,
            "top5_assets": [{"id": a["asset_id"], "name": a["name"], "score": a["performance_score"]} for a in top5],
        }

    # ── PERSISTENCE ──────────────────────────────────────────────────────

    def _load(self) -> None:
        if self.REGISTRY_PATH.exists():
            try:
                raw = json.loads(self.REGISTRY_PATH.read_text(encoding="utf-8"))
                for item in raw.get("assets", []):
                    a = Asset(**item)
                    self._assets[a.asset_id] = a
            except Exception:
                self._assets = {}

    def _save(self) -> None:
        self.REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "total": len(self._assets),
            "assets": [asdict(a) for a in self._assets.values()],
        }
        self.REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _hash(payload: Dict) -> str:
        s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(s.encode()).hexdigest()

    def _find_by_hash(self, content_hash: str) -> Optional[Asset]:
        for a in self._assets.values():
            if a.content_hash == content_hash:
                return a
        return None


# ─────────────────────────── SINGLETON ───────────────────────────────────────

zero_waste_recycler = ZeroWasteAssetRecycler()


if __name__ == "__main__":
    r = ZeroWasteAssetRecycler()
    # Enregistre un asset de démo
    aid = r.register(
        asset_type=AssetType.EMAIL_SEQUENCE.value,
        name="Séquence 7-touch IEC62443 OT",
        source_project="PROJECT_04_TINY_HOUSE",
        sector="Transport",
        payload={"subject": "Votre conformité NIS2 OT", "body": "..."},
        performance_score=75.0,
    )
    print(f"Asset enregistré: {aid}")
    # Recycle vers autre projet
    recycled = r.recycle(aid, "PROJECT_002_TRADE_ACCELERATION")
    print(f"Recyclé vers PROJECT_002: {recycled['asset_id']}")
    print(f"Stats: {r.stats()}")
