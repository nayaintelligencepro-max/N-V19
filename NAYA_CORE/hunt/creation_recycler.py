"""
NAYA V19 - Creation Recycler
Toute creation est clonee, reversionnee, recyclee pour d autres projets.
Rien n est jete. Chaque service vendu devient un template reutilisable.
"""
import time, logging, threading, json, hashlib, copy
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.HUNT.RECYCLER")

TEMPLATES_DIR = Path("data/cache/recycled_templates")

@dataclass
class RecyclableAsset:
    asset_id: str
    original_project: str
    asset_type: str  # service, chatbot, audit, saas, landing_page, offer
    sector: str
    description: str
    template_data: Dict[str, Any]
    times_recycled: int = 0
    revenue_generated: float = 0.0
    created_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    adaptable_sectors: List[str] = field(default_factory=list)

class CreationRecycler:
    """Recycle toute creation en template reutilisable multi-secteur."""

    def __init__(self):
        self._assets: Dict[str, RecyclableAsset] = {}
        self._lock = threading.RLock()
        self._total_recycled = 0
        self._total_value_recycled = 0.0
        self._load_templates()

    def register_creation(self, project: str, asset_type: str, sector: str,
                          description: str, template_data: Dict, tags: List[str] = None) -> RecyclableAsset:
        """Enregistre une nouvelle creation comme asset recyclable."""
        asset_id = f"ASSET_{hashlib.md5(f'{project}:{asset_type}:{time.time()}'.encode()).hexdigest()[:10].upper()}"
        adaptable = self._find_adaptable_sectors(sector, asset_type, tags or [])

        asset = RecyclableAsset(
            asset_id=asset_id,
            original_project=project,
            asset_type=asset_type,
            sector=sector,
            description=description,
            template_data=template_data,
            tags=tags or [],
            adaptable_sectors=adaptable
        )

        with self._lock:
            self._assets[asset_id] = asset
        self._save_templates()
        log.info(f"[RECYCLER] Asset enregistre: {asset_id} ({asset_type}) -> adaptable a {len(adaptable)} secteurs")
        return asset

    def recycle_for_sector(self, asset_id: str, target_sector: str,
                           customizations: Dict = None) -> Optional[Dict]:
        """Clone et adapte un asset pour un nouveau secteur."""
        with self._lock:
            asset = self._assets.get(asset_id)
            if not asset:
                return None

        recycled = copy.deepcopy(asset.template_data)
        recycled["_original_sector"] = asset.sector
        recycled["_target_sector"] = target_sector
        recycled["_recycled_from"] = asset_id
        recycled["_recycled_at"] = time.time()

        # Apply sector-specific adaptations
        recycled = self._adapt_to_sector(recycled, asset.sector, target_sector)

        # Apply custom overrides
        if customizations:
            recycled.update(customizations)

        with self._lock:
            asset.times_recycled += 1
            self._total_recycled += 1

        self._save_templates()
        log.info(f"[RECYCLER] {asset_id} recycle pour {target_sector} (total: {asset.times_recycled}x)")
        return recycled

    def find_recyclable_for(self, target_sector: str, asset_type: str = None) -> List[RecyclableAsset]:
        """Trouve les assets recyclables pour un secteur donne."""
        with self._lock:
            results = []
            for asset in self._assets.values():
                if target_sector in asset.adaptable_sectors or asset.sector == target_sector:
                    if asset_type is None or asset.asset_type == asset_type:
                        results.append(asset)
            results.sort(key=lambda a: a.times_recycled, reverse=True)
            return results

    def record_revenue(self, asset_id: str, amount: float) -> None:
        """Enregistre le revenu genere par un asset recycle."""
        with self._lock:
            asset = self._assets.get(asset_id)
            if asset:
                asset.revenue_generated += amount
                self._total_value_recycled += amount

    def _find_adaptable_sectors(self, source_sector: str, asset_type: str, tags: List[str]) -> List[str]:
        """Identifie les secteurs ou cet asset peut etre adapte."""
        SECTOR_FAMILIES = {
            "restaurant": ["hotel", "bar", "traiteur", "boulangerie", "food_truck"],
            "pme": ["startup", "artisan", "commerce", "freelance", "cabinet"],
            "immobilier": ["construction", "renovation", "location", "gestion_patrimoine"],
            "sante": ["pharmacie", "clinique", "laboratoire", "medecin"],
            "education": ["formation", "coaching", "e-learning", "universite"],
            "industrie": ["manufacture", "logistique", "transport", "energie"],
            "tech": ["saas", "fintech", "e-commerce", "marketplace"],
            "gouvernement": ["collectivite", "administration", "service_public"],
        }
        adaptable = set()
        for family, members in SECTOR_FAMILIES.items():
            if source_sector in members or source_sector == family:
                adaptable.update(members)
                adaptable.add(family)
        adaptable.discard(source_sector)

        # Certains types sont universels
        if asset_type in ["chatbot", "audit", "diagnostic", "landing_page"]:
            for members in SECTOR_FAMILIES.values():
                adaptable.update(members)

        return list(adaptable)[:20]

    def _adapt_to_sector(self, data: Dict, from_sector: str, to_sector: str) -> Dict:
        """Adapte les termes et references sectorielles."""
        adapted = {}
        for k, v in data.items():
            if isinstance(v, str):
                adapted[k] = v.replace(from_sector, to_sector)
            elif isinstance(v, dict):
                adapted[k] = self._adapt_to_sector(v, from_sector, to_sector)
            else:
                adapted[k] = v
        return adapted

    def _save_templates(self) -> None:
        try:
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            data = {}
            with self._lock:
                for aid, asset in self._assets.items():
                    data[aid] = {
                        "asset_id": asset.asset_id, "original_project": asset.original_project,
                        "asset_type": asset.asset_type, "sector": asset.sector,
                        "description": asset.description, "times_recycled": asset.times_recycled,
                        "revenue_generated": asset.revenue_generated, "tags": asset.tags,
                        "adaptable_sectors": asset.adaptable_sectors
                    }
            (TEMPLATES_DIR / "recycled_assets.json").write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.debug(f"[RECYCLER] Save: {e}")

    def _load_templates(self) -> None:
        try:
            f = TEMPLATES_DIR / "recycled_assets.json"
            if f.exists():
                data = json.loads(f.read_text())
                for aid, d in data.items():
                    self._assets[aid] = RecyclableAsset(
                        asset_id=d["asset_id"], original_project=d["original_project"],
                        asset_type=d["asset_type"], sector=d["sector"],
                        description=d["description"], template_data={},
                        times_recycled=d.get("times_recycled", 0),
                        revenue_generated=d.get("revenue_generated", 0),
                        tags=d.get("tags", []), adaptable_sectors=d.get("adaptable_sectors", [])
                    )
                log.info(f"[RECYCLER] {len(self._assets)} assets charges")
        except Exception as e:
            log.debug(f"[RECYCLER] Load: {e}")

    def get_stats(self) -> Dict:
        with self._lock:
            by_type = {}
            for a in self._assets.values():
                by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1
            return {
                "total_assets": len(self._assets),
                "total_recycled": self._total_recycled,
                "total_value_recycled_eur": self._total_value_recycled,
                "by_type": by_type,
                "top_recycled": sorted(
                    [{"id": a.asset_id, "type": a.asset_type, "recycled": a.times_recycled}
                     for a in self._assets.values()],
                    key=lambda x: x["recycled"], reverse=True
                )[:5]
            }

_recycler = None
_recycler_lock = threading.Lock()
def get_recycler() -> CreationRecycler:
    global _recycler
    if _recycler is None:
        with _recycler_lock:
            if _recycler is None:
                _recycler = CreationRecycler()
    return _recycler
