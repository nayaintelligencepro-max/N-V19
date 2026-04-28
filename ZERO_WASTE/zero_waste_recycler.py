"""
NAYA SUPREME V19 — ZERO WASTE RECYCLER
═══════════════════════════════════════════════════════════════
Principe fondateur: AUCUNE CRÉATION N'EST JETÉE.

Chaque livrable devient un ASSET permanent dans la bibliothèque.
Chaque asset peut être RECYCLÉ pour un autre client/secteur.
Chaque recyclage crée une VERSION supérieure (v+1).

Cycle de vie d'un asset:
  CRÉÉ → UTILISÉ → ARCHIVÉ → [RECYCLÉ pour nouveau contexte → v+1]
                                ↑__________________________|

Types d'assets recyclables:
  EMAIL_PITCH    → template multi-secteur
  RAPPORT_AUDIT  → base réutilisable audit suivant
  PROPOSITION    → clone + adaptation pour autre client
  FORMATION      → slides réutilisables
  SCRIPT_APPEL   → adapté au secteur/prospect
  ANALYSE_MARCHE → enrichit d'autres secteurs
  CODE_MODULE    → partagé entre projets
  CONTACT_LIST   → segmentée et enrichie
═══════════════════════════════════════════════════════════════
"""
import json, time, uuid, logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path

log = logging.getLogger("NAYA.ZERO_WASTE")
ROOT = Path(__file__).resolve().parent.parent


class AssetType(Enum):
    EMAIL_PITCH    = "email_pitch"
    PROPOSITION    = "proposition"
    RAPPORT_AUDIT  = "rapport_audit"
    FORMATION      = "formation"
    SCRIPT_APPEL   = "script_appel"
    ANALYSE_MARCHE = "analyse_marche"
    CODE_MODULE    = "code_module"
    CONTACT_LIST   = "contact_list"
    TEMPLATE       = "template"
    OFFRE_PRIX     = "offre_prix"


class AssetStatus(Enum):
    FRESH     = "fresh"      # Jamais utilisé
    USED      = "used"       # Utilisé au moins une fois
    RECYCLED  = "recycled"   # Recyclé dans un nouveau contexte


@dataclass
class Asset:
    id: str = field(default_factory=lambda: f"A{uuid.uuid4().hex[:7].upper()}")
    type: AssetType = AssetType.TEMPLATE
    nom: str = ""
    contenu: str = ""
    secteur: str = ""
    client: str = ""
    version: int = 1
    parent_id: Optional[str] = None
    status: AssetStatus = AssetStatus.FRESH
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    uses: int = 0
    revenue: float = 0.0     # Revenu généré via cet asset


class ZeroWasteRecycler:
    """
    Bibliothèque d'assets permanente.
    Tout ce qui est créé y entre. Tout peut en ressortir recyclé.
    """
    FILE = ROOT / "data" / "cache" / "zero_waste.json"

    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        log.info("ZeroWaste V19 — %d assets en bibliothèque", len(self.assets))

    # ── SAVE ──────────────────────────────────────────────────────────────
    def save(self, type: AssetType, nom: str, contenu: str,
             secteur: str = "", client: str = "",
             tags: List[str] = None, metadata: Dict = None,
             revenue: float = 0.0) -> Asset:
        """Sauvegarde un nouvel asset. Retourne l'Asset créé."""
        a = Asset(
            type=type, nom=nom, contenu=contenu,
            secteur=secteur, client=client,
            tags=tags or [], metadata=metadata or {},
            revenue=revenue,
        )
        self.assets[a.id] = a
        self._persist()
        log.info("Asset sauvé: %s [%s] — %s€", nom, type.value, revenue)
        return a

    # ── RECYCLE ───────────────────────────────────────────────────────────
    def recycle(self, asset_id: str, nouveau_client: str = "",
                nouveau_secteur: str = "", contexte: str = "") -> Asset:
        """
        Recycle un asset pour un nouveau contexte.
        Crée v+1 sans supprimer l'original.
        """
        orig = self.assets.get(asset_id)
        if not orig:
            raise ValueError(f"Asset {asset_id} introuvable")

        # Adapter le contenu
        contenu = self._adapter(orig.contenu, orig.client, nouveau_client,
                                orig.secteur, nouveau_secteur, contexte)

        recycled = Asset(
            type=orig.type,
            nom=f"[v{orig.version+1}] {orig.nom}",
            contenu=contenu,
            secteur=nouveau_secteur or orig.secteur,
            client=nouveau_client or orig.client,
            version=orig.version + 1,
            parent_id=asset_id,
            tags=orig.tags + ["recycled"],
            metadata={**orig.metadata, "recycled_from": asset_id, "contexte": contexte},
            status=AssetStatus.RECYCLED,
        )

        # MAJ de l'original
        orig.uses += 1
        orig.status = AssetStatus.USED

        self.assets[recycled.id] = recycled
        self._persist()
        log.info("Recyclé: %s → v%d pour [%s]", orig.nom, recycled.version, nouveau_client)
        return recycled

    def _adapter(self, contenu: str, ancien_client: str, nouveau_client: str,
                 ancien_secteur: str, nouveau_secteur: str, contexte: str) -> str:
        """Substitutions intelligentes pour adapter l'asset."""
        txt = contenu
        if ancien_client and nouveau_client:
            txt = txt.replace(ancien_client, nouveau_client)
        if ancien_secteur and nouveau_secteur:
            txt = txt.replace(ancien_secteur, nouveau_secteur)
        if contexte:
            txt = f"[Adapté pour: {contexte}]\n\n{txt}"
        return txt

    # ── MARK USED ────────────────────────────────────────────────────────
    def mark_used(self, asset_id: str, revenue: float = 0.0):
        """Marque un asset comme utilisé avec le revenu généré."""
        if a := self.assets.get(asset_id):
            a.uses += 1
            a.revenue += revenue
            a.status = AssetStatus.USED
            self._persist()

    # ── FIND ─────────────────────────────────────────────────────────────
    def find(self, type: AssetType = None, secteur: str = "",
             tags: List[str] = None, limit: int = 10) -> List[Asset]:
        """Recherche d'assets à recycler."""
        results = list(self.assets.values())
        if type:
            results = [a for a in results if a.type == type]
        if secteur:
            results = [a for a in results if secteur.lower() in a.secteur.lower()]
        if tags:
            results = [a for a in results if any(t in a.tags for t in tags)]
        return sorted(results, key=lambda a: a.uses, reverse=True)[:limit]

    def get_top_revenue_assets(self, n: int = 10) -> List[Dict]:
        """Assets ayant généré le plus de revenu."""
        return sorted(
            [{"id": a.id, "nom": a.nom, "type": a.type.value,
              "revenue": a.revenue, "uses": a.uses, "version": a.version}
             for a in self.assets.values()],
            key=lambda x: x["revenue"], reverse=True
        )[:n]

    # ── STATS ────────────────────────────────────────────────────────────
    def get_stats(self) -> Dict:
        total = len(self.assets)
        recycled = sum(1 for a in self.assets.values() if a.parent_id)
        total_rev = sum(a.revenue for a in self.assets.values())
        by_type = {}
        for a in self.assets.values():
            k = a.type.value
            by_type[k] = by_type.get(k, 0) + 1
        return {
            "total_assets": total,
            "assets_recycles": recycled,
            "taux_recyclage": f"{recycled/max(total,1)*100:.0f}%",
            "revenu_total_via_assets": total_rev,
            "par_type": by_type,
            "top5_revenue": self.get_top_revenue_assets(5),
            "doctrine": "Aucune creation jetee — tout asset est une ressource permanente",
        }

    # ── PERSIST ──────────────────────────────────────────────────────────
    def _persist(self):
        try:
            def _ser(a: Asset):
                d = asdict(a)
                d["type"] = a.type.value
                d["status"] = a.status.value
                return d
            self.FILE.write_text(
                json.dumps({k: _ser(v) for k, v in self.assets.items()},
                           indent=2, ensure_ascii=False),
                encoding="utf-8")
        except Exception as e:
            log.warning("ZeroWaste persist: %s", e)

    def _load(self):
        try:
            if self.FILE.exists():
                data = json.loads(self.FILE.read_text(encoding="utf-8"))
                for aid, d in data.items():
                    d["type"] = AssetType(d.get("type", "template"))
                    d["status"] = AssetStatus(d.get("status", "fresh"))
                    self.assets[aid] = Asset(**{k: v for k, v in d.items()
                                                if k in Asset.__dataclass_fields__})
        except Exception as e:
            log.warning("ZeroWaste load: %s", e)


# ── SINGLETON ────────────────────────────────────────────────────────────────
_inst: Optional[ZeroWasteRecycler] = None

def get_zero_waste() -> ZeroWasteRecycler:
    global _inst
    if _inst is None:
        _inst = ZeroWasteRecycler()
    return _inst
