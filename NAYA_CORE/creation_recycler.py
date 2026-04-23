"""
NAYA V19 — Creation Recycler
Tout ce qui est créé est cloné, reversionné, recyclé. Rien n'est jeté.
Transforme chaque service/offre vendu en template réutilisable.
"""
import time, logging, threading, json, hashlib, copy
from typing import Dict, List, Optional
from pathlib import Path

log = logging.getLogger("NAYA.RECYCLER")

TEMPLATES_FILE = Path("data/cache/creation_templates.json")


class CreationRecycler:
    """Rien n'est jeté — tout est recyclé, cloné, reversionné."""
    
    def __init__(self):
        self._templates: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._recycle_count = 0
        self._clone_count = 0
        self._load()
    
    def recycle(self, creation: Dict) -> Dict:
        """Transforme une création exécutée en template réutilisable."""
        template_id = hashlib.sha256(
            json.dumps(creation, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        
        template = {
            "id": template_id,
            "original": creation.get("id", "unknown"),
            "type": creation.get("type", "service"),
            "sector": creation.get("sector", "general"),
            "base_price_eur": creation.get("price", 0),
            "components": creation.get("components", []),
            "description_template": creation.get("description", ""),
            "success_rate": creation.get("success_rate", 0.5),
            "times_reused": 0,
            "created_at": time.time(),
            "tags": creation.get("tags", []),
            "adaptable_fields": ["sector", "price", "description", "target_audience"],
        }
        
        with self._lock:
            self._templates[template_id] = template
            self._recycle_count += 1
            self._save()
        
        log.info(f"[RECYCLER] ♻️ Recycled: {creation.get('type', '?')} → template {template_id}")
        return template
    
    def clone(self, template_id: str, adaptations: Dict = None) -> Optional[Dict]:
        """Clone un template avec des adaptations pour un nouveau contexte."""
        with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return None
            
            clone = copy.deepcopy(template)
            clone["id"] = f"CLONE_{int(time.time())}_{self._clone_count}"
            clone["cloned_from"] = template_id
            clone["cloned_at"] = time.time()
            
            if adaptations:
                for field in template.get("adaptable_fields", []):
                    if field in adaptations:
                        clone[field] = adaptations[field]
            
            template["times_reused"] += 1
            self._clone_count += 1
            self._save()
        
        log.info(f"[RECYCLER] 🔄 Cloned: {template_id} → {clone['id']}")
        return clone
    
    def reversion(self, template_id: str, version: str, changes: Dict) -> Optional[Dict]:
        """Crée une nouvelle version d'un template existant."""
        with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return None
            
            new_id = f"{template_id}_v{version}"
            new_template = copy.deepcopy(template)
            new_template["id"] = new_id
            new_template["version"] = version
            new_template["parent_id"] = template_id
            new_template.update(changes)
            new_template["created_at"] = time.time()
            
            self._templates[new_id] = new_template
            self._save()
        
        return new_template
    
    def find_templates(self, sector: str = None, type_filter: str = None,
                       min_success: float = 0) -> List[Dict]:
        """Cherche des templates réutilisables."""
        with self._lock:
            results = list(self._templates.values())
        
        if sector:
            results = [t for t in results if sector.lower() in t.get("sector", "").lower()]
        if type_filter:
            results = [t for t in results if type_filter.lower() in t.get("type", "").lower()]
        if min_success > 0:
            results = [t for t in results if t.get("success_rate", 0) >= min_success]
        
        results.sort(key=lambda t: t.get("times_reused", 0), reverse=True)
        return results
    
    def get_best_templates(self, n: int = 10) -> List[Dict]:
        """Retourne les templates les plus réutilisés."""
        with self._lock:
            all_templates = list(self._templates.values())
        all_templates.sort(key=lambda t: t.get("times_reused", 0), reverse=True)
        return all_templates[:n]
    
    def _save(self):
        try:
            TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                TEMPLATES_FILE.write_text(json.dumps(self._templates, default=str, indent=2))
        except Exception as e:
            log.debug(f"[RECYCLER] Save error: {e}")
    
    def _load(self):
        try:
            if TEMPLATES_FILE.exists():
                self._templates = json.loads(TEMPLATES_FILE.read_text())
                log.info(f"[RECYCLER] {len(self._templates)} templates loaded")
        except Exception as e:
            log.debug(f"[RECYCLER] Load error: {e}")
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_templates": len(self._templates),
                "total_recycled": self._recycle_count,
                "total_cloned": self._clone_count,
                "most_reused": self.get_best_templates(3),
                "total_reuses": sum(t.get("times_reused", 0) for t in self._templates.values()),
            }

_recycler = None
_recycler_lock = threading.Lock()
def get_recycler():
    global _recycler
    if _recycler is None:
        with _recycler_lock:
            if _recycler is None: _recycler = CreationRecycler()
    return _recycler
