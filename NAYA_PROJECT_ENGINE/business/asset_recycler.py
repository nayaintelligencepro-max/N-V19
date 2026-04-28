"""
NAYA V19 — Asset Recycler — Zero Waste Engine
==============================================
Principe absolu : AUCUNE CRÉATION N'EST JETÉE.

Tout asset créé dans NAYA (email, pitch, contenu, rapport, offre,
message, template) est enregistré, versionné et recyclable.

Cycle de vie :
  CRÉÉ → UTILISÉ → ARCHIVÉ → RECYCLÉ (v+1) → UTILISÉ → ...

Recyclage = adaptation d'un asset existant à un nouveau :
  · projet          (ex: contenu TINY_HOUSE → BOTANICA)
  · secteur         (ex: rapport OT → rapport ESG)
  · langue          (ex: pitch FR → pitch EN)
  · canal           (ex: email → LinkedIn)
  · taille          (ex: article 2000 mots → post 300 mots)

Règle : on ne crée from scratch que si aucun asset recyclable n'existe.
Métriques : taux de recyclage, gain de temps, diversité des secteurs.
"""
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

log = logging.getLogger("NAYA.ZERO_WASTE.RECYCLER")


class AssetType(Enum):
    CONTENT_POST    = "content_post"
    EMAIL_PITCH     = "email_pitch"
    OFFER_DOC       = "offer_doc"
    AUDIT_REPORT    = "audit_report"
    OBJECTION_REPLY = "objection_reply"
    STORYTELLING    = "storytelling"
    SUPPLIER_BRIEF  = "supplier_brief"
    ASSEMBLY_GUIDE  = "assembly_guide"
    CREDIBILITY_KIT = "credibility_kit"
    TEMPLATE        = "template"


class AssetStatus(Enum):
    FRESH     = "fresh"
    USED      = "used"
    ARCHIVED  = "archived"
    RECYCLED  = "recycled"


@dataclass
class Asset:
    id: str = field(default_factory=lambda: f"ASSET-{uuid.uuid4().hex[:8].upper()}")
    type: AssetType = AssetType.TEMPLATE
    name: str = ""
    content: str = ""
    project_id: str = ""
    sector: str = ""
    channel: str = ""
    language: str = "fr"
    tags: List[str] = field(default_factory=list)
    version: int = 1
    parent_id: Optional[str] = None     # ID de l'asset source si recyclé
    status: AssetStatus = AssetStatus.FRESH
    use_count: int = 0
    recycled_count: int = 0
    performance_score: float = 0.0      # 0–10, basé sur conversions
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_used(self) -> None:
        self.use_count += 1
        self.status = AssetStatus.USED
        self.updated_at = time.time()

    def mark_archived(self) -> None:
        self.status = AssetStatus.ARCHIVED
        self.updated_at = time.time()

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "type": self.type.value, "name": self.name,
            "project_id": self.project_id, "sector": self.sector,
            "channel": self.channel, "language": self.language,
            "tags": self.tags, "version": self.version,
            "parent_id": self.parent_id, "status": self.status.value,
            "use_count": self.use_count, "recycled_count": self.recycled_count,
            "performance_score": self.performance_score,
            "content_preview": self.content[:120] + ("..." if len(self.content) > 120 else ""),
            "created_at": self.created_at,
        }


class AssetRecycler:
    """
    Moteur zéro déchet — enregistre, retrouve et recycle tous les assets.

    Interface :
        register(asset)                       → enregistre un nouvel asset
        find(type, project_id, sector, ...)   → recherche asset réutilisable
        recycle(asset_id, new_context)        → crée version v+1 adaptée
        record_performance(asset_id, score)   → met à jour le score de performance
        get_best_performers(type, n)          → top N assets par performance
        get_stats()                           → métriques globales
        should_create_new(type, project, ...) → True si aucun asset recyclable
    """

    def __init__(self) -> None:
        self._lock   = threading.RLock()
        self._assets: Dict[str, Asset] = {}
        self._initialized_at = time.time()
        log.info("[ZERO_WASTE] AssetRecycler initialisé")

    # ── Enregistrement ─────────────────────────────────────────────────────

    def register(self, asset_type: str, name: str, content: str,
                 project_id: str = "", sector: str = "", channel: str = "",
                 language: str = "fr", tags: Optional[List[str]] = None,
                 metadata: Optional[Dict] = None) -> Asset:
        """Enregistre un nouvel asset dans la bibliothèque."""
        try:
            atype = AssetType(asset_type)
        except ValueError:
            atype = AssetType.TEMPLATE
        asset = Asset(
            type=atype, name=name, content=content,
            project_id=project_id, sector=sector, channel=channel,
            language=language, tags=tags or [],
            metadata=metadata or {},
        )
        with self._lock:
            self._assets[asset.id] = asset
        log.info(f"[ZERO_WASTE] Asset enregistré: {asset.id} | {asset_type} | {project_id}")
        return asset

    # ── Recherche ──────────────────────────────────────────────────────────

    def find(self, asset_type: Optional[str] = None, project_id: Optional[str] = None,
             sector: Optional[str] = None, channel: Optional[str] = None,
             language: str = "fr", min_score: float = 0.0,
             status: Optional[str] = None) -> List[Asset]:
        """Recherche des assets réutilisables selon critères."""
        with self._lock:
            assets = list(self._assets.values())

        results = []
        for a in assets:
            if asset_type and a.type.value != asset_type:
                continue
            if project_id and a.project_id and a.project_id != project_id:
                continue
            if sector and a.sector and a.sector != sector:
                continue
            if channel and a.channel and a.channel != channel:
                continue
            if a.language != language:
                continue
            if a.performance_score < min_score:
                continue
            if status and a.status.value != status:
                continue
            results.append(a)

        return sorted(results, key=lambda x: x.performance_score, reverse=True)

    def find_best(self, asset_type: str, project_id: Optional[str] = None,
                  sector: Optional[str] = None) -> Optional[Asset]:
        """Retourne le meilleur asset disponible selon critères."""
        candidates = self.find(asset_type=asset_type, project_id=project_id,
                               sector=sector)
        return candidates[0] if candidates else None

    # ── Recyclage ──────────────────────────────────────────────────────────

    def recycle(self, asset_id: str, new_project_id: Optional[str] = None,
                new_sector: Optional[str] = None, new_channel: Optional[str] = None,
                new_language: Optional[str] = None,
                content_override: Optional[str] = None,
                additional_tags: Optional[List[str]] = None) -> Asset:
        """
        Recycle un asset existant vers un nouveau contexte.
        Crée une version v+1 — l'original reste intact.
        """
        with self._lock:
            original = self._assets.get(asset_id)
        if not original:
            raise ValueError(f"Asset non trouvé: {asset_id}")

        new_content = content_override or self._adapt_content(
            original.content, new_sector, new_channel, new_language
        )
        recycled = Asset(
            type=original.type,
            name=f"{original.name} [v{original.version + 1}]",
            content=new_content,
            project_id=new_project_id or original.project_id,
            sector=new_sector or original.sector,
            channel=new_channel or original.channel,
            language=new_language or original.language,
            tags=list(original.tags) + (additional_tags or []),
            version=original.version + 1,
            parent_id=asset_id,
            metadata={**original.metadata, "recycled_from": asset_id,
                      "recycled_at": time.time()},
        )
        with self._lock:
            self._assets[recycled.id] = recycled
            original.recycled_count += 1
            original.status = AssetStatus.RECYCLED
            original.updated_at = time.time()

        log.info(f"[ZERO_WASTE] Recyclé: {asset_id} → {recycled.id} v{recycled.version} "
                 f"| {recycled.project_id} | {recycled.channel}")
        return recycled

    def clone_for_project(self, asset_id: str, target_project_id: str,
                          content_override: Optional[str] = None) -> Asset:
        """Clône un asset vers un autre projet — raccourci de recycle()."""
        return self.recycle(asset_id, new_project_id=target_project_id,
                            content_override=content_override,
                            additional_tags=[f"cloned_to:{target_project_id}"])

    # ── Performance ────────────────────────────────────────────────────────

    def record_performance(self, asset_id: str, score: float,
                           context: Optional[str] = None) -> Dict:
        """Met à jour le score de performance d'un asset (0–10)."""
        if not (0.0 <= score <= 10.0):
            return {"error": "Score hors plage (0–10)"}
        with self._lock:
            asset = self._assets.get(asset_id)
            if not asset:
                return {"error": "Asset non trouvé", "asset_id": asset_id}
            asset.mark_used()
            # First use: set directly; subsequent: weighted average 70/30
            if asset.use_count == 1:
                asset.performance_score = round(score, 2)
            else:
                asset.performance_score = round(
                    asset.performance_score * 0.7 + score * 0.3, 2
                )
            if context:
                asset.metadata.setdefault("performance_log", []).append(
                    {"score": score, "context": context, "ts": time.time()}
                )
        log.info(f"[ZERO_WASTE] Performance: {asset_id} → {asset.performance_score}/10")
        return {"asset_id": asset_id, "new_score": asset.performance_score,
                "use_count": asset.use_count}

    # ── Décision création ─────────────────────────────────────────────────

    def should_create_new(self, asset_type: str, project_id: Optional[str] = None,
                          sector: Optional[str] = None,
                          min_score: float = 6.0) -> Dict:
        """
        Détermine s'il faut créer un asset de zéro ou recycler un existant.
        Règle zéro déchet : toujours recycler si possible.
        """
        recyclable = self.find(asset_type=asset_type, sector=sector,
                               min_score=min_score)
        project_specific = [a for a in recyclable if a.project_id == project_id]

        if project_specific:
            return {"should_create": False, "reason": "Asset projet existant utilisable",
                    "recommended_asset_id": project_specific[0].id,
                    "score": project_specific[0].performance_score,
                    "action": "recycle_with_minor_adaptation"}
        if recyclable:
            return {"should_create": False, "reason": "Asset recyclable d'un autre projet",
                    "recommended_asset_id": recyclable[0].id,
                    "score": recyclable[0].performance_score,
                    "action": "clone_for_project"}
        return {"should_create": True, "reason": "Aucun asset recyclable disponible",
                "recommended_asset_id": None, "action": "create_from_scratch"}

    # ── Top performers ─────────────────────────────────────────────────────

    def get_best_performers(self, asset_type: Optional[str] = None,
                            top_n: int = 10) -> List[Dict]:
        """Retourne les N meilleurs assets par score de performance."""
        with self._lock:
            assets = list(self._assets.values())
        if asset_type:
            assets = [a for a in assets if a.type.value == asset_type]
        sorted_assets = sorted(assets, key=lambda a: a.performance_score, reverse=True)
        return [a.to_dict() for a in sorted_assets[:top_n]]

    # ── Stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Métriques zéro déchet complètes."""
        with self._lock:
            assets = list(self._assets.values())

        if not assets:
            return {"total_assets": 0, "recycle_rate": 0.0,
                    "uptime_seconds": int(time.time() - self._initialized_at)}

        recycled  = [a for a in assets if a.parent_id is not None]
        used      = [a for a in assets if a.use_count > 0]
        by_type   = {}
        by_project= {}
        for a in assets:
            by_type[a.type.value]     = by_type.get(a.type.value, 0) + 1
            by_project[a.project_id] = by_project.get(a.project_id, 0) + 1
        avg_score = sum(a.performance_score for a in assets) / len(assets)
        recycle_rate = len(recycled) / len(assets) if assets else 0.0

        return {
            "total_assets": len(assets),
            "recycled_assets": len(recycled),
            "recycle_rate": round(recycle_rate, 3),
            "used_assets": len(used),
            "avg_performance_score": round(avg_score, 2),
            "by_type": by_type,
            "by_project": by_project,
            "uptime_seconds": int(time.time() - self._initialized_at),
            "zero_waste_compliance": recycle_rate >= 0.30,  # Objectif ≥ 30% recyclés
        }

    # ── Interne ────────────────────────────────────────────────────────────

    def _adapt_content(self, content: str, new_sector: Optional[str],
                       new_channel: Optional[str], new_language: Optional[str]) -> str:
        """Adaptation légère du contenu pour le nouveau contexte."""
        adapted = content
        if new_channel == "tiktok" and len(adapted) > 300:
            adapted = adapted[:280] + " [résumé pour TikTok]"
        if new_channel == "linkedin":
            adapted = adapted.replace("👋", "").replace("🔥", "")
        if new_language == "en" and "fr" not in content[:20]:
            adapted = f"[EN adaptation] {adapted}"
        return adapted
