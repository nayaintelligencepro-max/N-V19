"""
NAYA V19 — Asset Registry
Registre centralisé de tous les assets du système :
fichiers Python critiques, modules, configurations, templates.
Utilisé par le système de version et le REAPERS pour l'intégrité.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger("NAYA.registry.assets")

ROOT = Path(__file__).parent.parent.parent

__all__ = ["AssetRegistry", "Asset", "get_asset_registry"]


@dataclass
class Asset:
    """Représente un asset tracé par le registre."""
    path: str                    # Chemin relatif depuis ROOT
    category: str                # core, revenue, security, config, frontend
    critical: bool = False       # Si True, intégrité vérifiée au boot
    hash_sha256: str = ""        # Hash calculé au boot
    last_checked: str = ""       # ISO timestamp dernière vérification
    size_bytes: int = 0

    @property
    def full_path(self) -> Path:
        return ROOT / self.path

    @property
    def exists(self) -> bool:
        return self.full_path.exists()


class AssetRegistry:
    """
    Registre de tous les fichiers critiques du système NAYA.
    Permet la détection de modifications non autorisées et le suivi de version.
    """

    # Assets critiques vérifiés par REAPERS au démarrage
    CRITICAL_ASSETS: List[Dict] = [
        # Core système
        {"path": "main.py",                                        "category": "core",     "critical": True},
        {"path": "NAYA_CORE/execution/naya_brain.py",              "category": "core",     "critical": True},
        {"path": "NAYA_CORE/execution/providers/free_llm_provider.py", "category": "core", "critical": True},
        {"path": "NAYA_CORE/naya_sovereign_engine.py",             "category": "core",     "critical": True},
        {"path": "NAYA_CORE/scheduler.py",                         "category": "core",     "critical": True},
        # Revenue
        {"path": "NAYA_REVENUE_ENGINE/revenue_engine_v10.py",      "category": "revenue",  "critical": True},
        {"path": "NAYA_REVENUE_ENGINE/prospect_finder_v10.py",     "category": "revenue",  "critical": True},
        {"path": "NAYA_REVENUE_ENGINE/outreach_engine.py",         "category": "revenue",  "critical": True},
        {"path": "NAYA_REVENUE_ENGINE/payment_engine.py",          "category": "revenue",  "critical": True},
        # Sécurité
        {"path": "REAPERS/reapers_core.py",                        "category": "security", "critical": True},
        {"path": "REAPERS/survival_mode.py",                       "category": "security", "critical": True},
        {"path": "SECRETS/secrets_loader.py",                      "category": "security", "critical": True},
        # API
        {"path": "api/middleware.py",                              "category": "core",     "critical": False},
        {"path": "api/routers/revenue.py",                         "category": "revenue",  "critical": False},
        {"path": "api/routers/brain.py",                           "category": "core",     "critical": False},
        # Config
        {"path": "requirements.txt",                               "category": "config",   "critical": False},
        {"path": ".env.example",                                   "category": "config",   "critical": False},
    ]

    def __init__(self):
        self._assets: Dict[str, Asset] = {}
        self._initialized = False
        self._init_time: Optional[str] = None

    def initialize(self) -> Dict:
        """Initialise le registre et calcule les hashes de tous les assets critiques."""
        self._init_time = datetime.now(timezone.utc).isoformat()
        found = missing = 0

        for asset_def in self.CRITICAL_ASSETS:
            path = asset_def["path"]
            asset = Asset(
                path=path,
                category=asset_def["category"],
                critical=asset_def.get("critical", False),
            )

            if asset.exists:
                try:
                    content = asset.full_path.read_bytes()
                    asset.hash_sha256 = hashlib.sha256(content).hexdigest()
                    asset.size_bytes = len(content)
                    asset.last_checked = datetime.now(timezone.utc).isoformat()
                    found += 1
                except Exception as e:
                    log.warning(f"[ASSETS] Erreur hash {path}: {e}")
            else:
                log.warning(f"[ASSETS] Asset manquant: {path}")
                missing += 1

            self._assets[path] = asset

        self._initialized = True
        log.info(f"[ASSETS] Registre initialisé: {found} assets, {missing} manquants")
        return {"found": found, "missing": missing, "total": len(self._assets)}

    def verify_integrity(self) -> Dict[str, bool]:
        """Vérifie l'intégrité de tous les assets critiques. Retourne {path: ok}."""
        if not self._initialized:
            self.initialize()

        results = {}
        for path, asset in self._assets.items():
            if not asset.critical:
                continue
            if not asset.exists:
                results[path] = False
                continue
            try:
                current_hash = hashlib.sha256(asset.full_path.read_bytes()).hexdigest()
                results[path] = current_hash == asset.hash_sha256
                if not results[path]:
                    log.warning(f"[ASSETS] Intégrité compromise: {path}")
            except Exception:
                results[path] = False

        return results

    def get_asset(self, path: str) -> Optional[Asset]:
        return self._assets.get(path)

    def get_by_category(self, category: str) -> List[Asset]:
        return [a for a in self._assets.values() if a.category == category]

    def get_status(self) -> Dict:
        if not self._initialized:
            return {"initialized": False}

        all_present = all(a.exists for a in self._assets.values() if a.critical)
        critical_assets = [a for a in self._assets.values() if a.critical]

        return {
            "initialized": True,
            "init_time": self._init_time,
            "total_tracked": len(self._assets),
            "critical_assets": len(critical_assets),
            "all_critical_present": all_present,
            "categories": {
                cat: len([a for a in self._assets.values() if a.category == cat])
                for cat in {"core", "revenue", "security", "config", "frontend"}
            },
        }


# Singleton
_registry: Optional[AssetRegistry] = None


def get_asset_registry() -> AssetRegistry:
    global _registry
    if _registry is None:
        _registry = AssetRegistry()
        _registry.initialize()
    return _registry
