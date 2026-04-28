"""
NAYA V19 — Serper.dev Hunter
Recherche Google en temps réel pour détection de signaux de douleur.
Serper = Google Search API gratuit (2 500 requêtes/mois plan gratuit).
"""
import os, logging, json, urllib.request, urllib.parse, time, hashlib
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SERPER")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


PAIN_QUERIES = {
    "restructuration": [
        'site:linkedin.com "en cours de recrutement" "directeur" "transformation"',
        '"plan de restructuration" site:fr.indeed.com',
        '"appel d\'offres" "transformation digitale" filetype:pdf',
    ],
    "marchés_publics": [
        'site:marches-publics.info "DSI" "transformation"',
        'site:boamp.fr "informatique" "mission" 2025',
        '"avis de marché" "prestataire" "numérique" site:data.gouv.fr',
    ],
    "polynesie": [
        '"Polynésie française" "marché" "prestation" "DSI"',
        '"Nouvelle-Calédonie" "appel d\'offres" "transformation"',
        '"Pacifique" "entreprise" "recrutement" "directeur"',
    ],
    "douleur_operationnelle": [
        '"perte de temps" "processus manuel" "inefficace" site:linkedin.com',
        '"nous cherchons" "urgent" "prestataire" site:fr.linkedin.com',
        '"coût" "réduction" "optimisation" "devis" site:leboncoin.fr',
    ],
    "afrique_francophone": [
        '"Côte d\'Ivoire" "appel d\'offres" "IT" "consultant" 2025',
        '"Maroc" "marché" "digitalisation" "mission" 2025',
        '"Sénégal" "transformation" "technologie" "budget" 2025',
    ],
}


class SerperHunter:
    """Chasse de signaux de douleur via Google Search (Serper API)."""

    BASE = "https://google.serper.dev/search"

    def __init__(self):
        self._keys: List[str] = []
        self._key_idx = 0
        self._cache: Dict[str, List] = {}
        self._calls = 0
        self._load_keys()

    def _load_keys(self):
        # Support multiple keys (rotation)
        raw = _gs("SERPER_API_KEY", "")
        if raw:
            self._keys = [k.strip() for k in raw.split(",") if k.strip()]
        if not self._keys:
            # Try loading from SECRETS JSON
            try:
                from pathlib import Path
                import json
                f = Path("SECRETS/keys/serper.json")
                if f.exists():
                    data = json.loads(f.read_text())
                    keys = data.get("api_keys", data.get("api_key", ""))
                    if isinstance(keys, list):
                        self._keys = keys
                    elif keys:
                        self._keys = [keys]
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return bool(self._keys)

    def _next_key(self) -> str:
        if not self._keys:
            return ""
        k = self._keys[self._key_idx % len(self._keys)]
        self._key_idx += 1
        return k

    def search(self, query: str, num: int = 5) -> List[Dict]:
        """Recherche Google via Serper."""
        if not self._keys:
            return []
        ck = hashlib.md5(query.encode()).hexdigest()
        if ck in self._cache:
            return self._cache[ck]

        key = self._next_key()
        try:
            payload = json.dumps({"q": query, "num": num, "gl": "fr", "hl": "fr"}).encode()
            req = urllib.request.Request(
                self.BASE,
                data=payload,
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            results = [
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "source": "serper",
                }
                for r in data.get("organic", [])[:num]
            ]
            self._cache[ck] = results
            self._calls += 1
            return results
        except Exception as e:
            log.debug(f"[SERPER] Search failed: {e}")
            return []

    def hunt_pains(self, categories: Optional[List[str]] = None) -> List[Dict]:
        """Chasse multi-catégories de signaux de douleur."""
        cats = categories or list(PAIN_QUERIES.keys())
        signals = []
        for cat in cats:
            queries = PAIN_QUERIES.get(cat, [])
            for q in queries[:2]:  # max 2 queries par catégorie pour économiser les crédits
                results = self.search(q, num=3)
                for r in results:
                    signals.append({
                        "category": cat,
                        "title": r["title"],
                        "url": r["link"],
                        "snippet": r["snippet"],
                        "confidence": 0.6,
                        "source": "serper_google",
                    })
                time.sleep(0.5)  # Rate limiting
        log.info(f"[SERPER] Hunt complete — {len(signals)} signals found")
        return signals

    def stats(self) -> Dict:
        return {
            "keys_loaded": len(self._keys),
            "calls_made": self._calls,
            "cached": len(self._cache),
            "available": self.available,
        }


_instance: Optional[SerperHunter] = None

def get_serper() -> SerperHunter:
    global _instance
    if _instance is None:
        _instance = SerperHunter()
    return _instance
