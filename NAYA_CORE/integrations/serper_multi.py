"""
NAYA V19 — SERPER MULTI-CLÉS (Google Search API)
Rotation automatique sur 2 clés Serper pour doubler la capacité.
Clé 1: 26390f1e... (default) → Clé 2: 4165556d... (backup)

Capacité: 2x2500 = 5000 recherches/mois GRATUITEMENT.
Utilisé pour: trouver de vrais prospects avec emails, trouver des entreprises,
              enrichir les prospects avec données réelles.
"""

import os
import json
import time
import logging
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.SERPER.MULTI")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class SerperMultiKeySearch:
    """
    Google Search via Serper.dev avec 2 clés en rotation.
    Parfait pour trouver des prospects réels avec emails de contact.
    """

    BASE_URL = "https://google.serper.dev/"
    RATE_LIMIT_SLEEP = 1.0  # 1 seconde entre les requêtes

    def __init__(self):
        self._keys = self._load_keys()
        self._current_idx = 0
        self._key_calls: Dict[str, int] = {}
        self._key_errors: Dict[str, int] = {}
        self._total_calls = 0
        self._total_results = 0

        if self._keys:
            log.info(f"✅ Serper multi-clés: {len(self._keys)} clé(s) — ~{len(self._keys)*2500} req/mois")
        else:
            log.debug("Serper: aucune clé configurée")

    def _load_keys(self) -> List[str]:
        """Charge toutes les clés Serper disponibles."""
        keys = []
        sources = [
            "SERPER_API_KEY", "SERPER_API_KEY_DEFAULT",
            "SERPER_API_KEY_2", "SERPER_API_KEY_3",
        ]
        for src in sources:
            key = _gs(src)
            if key and len(key) > 20 and key not in keys and "METS" not in key:
                keys.append(key)
        return keys

    @property
    def available(self) -> bool:
        return len(self._keys) > 0

    def _get_key(self) -> Optional[str]:
        """Retourne la prochaine clé valide."""
        if not self._keys:
            return None
        for _ in range(len(self._keys)):
            key = self._keys[self._current_idx % len(self._keys)]
            self._current_idx += 1
            if self._key_errors.get(key, 0) < 5:
                return key
        # Reset et réessayer
        self._key_errors.clear()
        return self._keys[0]

    def _request(self, endpoint: str, payload: Dict) -> Optional[Dict]:
        """Effectue une requête Serper avec rotation de clés."""
        key = self._get_key()
        if not key:
            return None

        self._total_calls += 1
        self._key_calls[key] = self._key_calls.get(key, 0) + 1

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.BASE_URL + endpoint,
                data=data,
                headers={
                    "X-API-KEY": key,
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                time.sleep(self.RATE_LIMIT_SLEEP)
                return result

        except urllib.error.HTTPError as e:
            if e.code == 429:
                self._key_errors[key] = self._key_errors.get(key, 0) + 1
                log.debug(f"[Serper] Rate limit clé {self._keys.index(key)+1}, rotation")
                # Réessayer avec une autre clé
                return self._request(endpoint, payload)
            log.warning(f"[Serper] HTTP {e.code}")
            return None

        except Exception as e:
            log.debug(f"[Serper] Error: {e}")
            return None

    def search(self, query: str, num: int = 10, lang: str = "fr",
               country: str = "fr", type: str = "search") -> List[Dict]:
        """Recherche Google générique."""
        result = self._request(type, {
            "q": query,
            "gl": country,
            "hl": lang,
            "num": min(num, 10),
        })
        if not result:
            return []

        organic = result.get("organic", [])
        self._total_results += len(organic)
        return organic

    def find_companies(self, sector: str, city: str = "France",
                       count: int = 10) -> List[Dict]:
        """
        Trouve des entreprises réelles pour un secteur donné.
        Retourne: nom, URL, email si trouvé, téléphone si trouvé.
        """
        from NAYA_REVENUE_ENGINE.prospect_finder import SECTOR_PAIN_MAP
        sector_info = SECTOR_PAIN_MAP.get(sector, {})
        keywords = sector_info.get("keywords", [sector.replace("_", " ")])

        companies = []
        queries = [
            f'"{keywords[0]}" {city} email contact "nous contacter"',
            f'{keywords[0]} {city} site:fr OR site:pf "contacter" téléphone',
        ]

        for query in queries[:1]:  # 1 requête par appel (économiser les crédits)
            results = self.search(query, num=count)
            for r in results:
                title = r.get("title", "").split(" - ")[0].split(" | ")[0].strip()
                url = r.get("link", "")
                snippet = r.get("snippet", "")

                if not title or len(title) < 3:
                    continue

                # Extraire email du snippet si présent
                import re
                email_match = re.search(
                    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
                    snippet
                )
                email = email_match.group(0) if email_match else ""

                # Extraire téléphone
                phone_match = re.search(
                    r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.\-]?\d{2}){4}|(?:\+689|00689)\s*\d{2}(?:[\s.\-]?\d{2}){3}',
                    snippet
                )
                phone = phone_match.group(0) if phone_match else ""

                companies.append({
                    "name": title[:80],
                    "url": url,
                    "email": email,
                    "phone": phone,
                    "snippet": snippet[:300],
                    "sector": sector,
                    "city": city,
                    "source": "serper",
                })

            if len(companies) >= count:
                break

        log.info(f"[Serper] {sector}/{city}: {len(companies)} entreprises trouvées")
        return companies[:count]

    def find_decision_maker(self, company_name: str, sector: str = "") -> Dict:
        """
        Trouve le dirigeant/décideur d'une entreprise.
        Cherche: nom, titre, LinkedIn, email.
        """
        queries = [
            f'"{company_name}" dirigeant OR gérant OR PDG OR CEO linkedin',
            f'"{company_name}" directeur email contact',
        ]

        for query in queries:
            results = self.search(query, num=5)
            for r in results:
                snippet = r.get("snippet", "")
                title = r.get("title", "")
                combined = f"{title} {snippet}"

                # Détecter le nom du dirigeant
                import re
                name_patterns = [
                    r'(?:fondé(?:e)? par|dirigé(?:e)? par|géré(?:e)? par)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                    r'(?:PDG|CEO|Directeur|Gérant|Fondateur)[,:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-,]\s*(?:PDG|CEO|Gérant|Directeur)',
                ]
                for pat in name_patterns:
                    m = re.search(pat, combined)
                    if m:
                        return {
                            "name": m.group(1),
                            "company": company_name,
                            "source_url": r.get("link", ""),
                            "snippet": snippet[:200],
                        }

        return {"name": "", "company": company_name}

    def research_pain_signals(self, sector: str, pain_type: str) -> List[str]:
        """
        Recherche des signaux de douleur actuels dans un secteur.
        Utilisé pour enrichir les offres avec des références sectorielles.
        """
        queries = [
            f'{sector.replace("_", " ")} problème "{pain_type.replace("_", " ")}" 2024 OR 2025',
            f'{sector.replace("_", " ")} difficulté coût {pain_type.replace("_", " ")}',
        ]

        signals = []
        for query in queries[:1]:
            results = self.search(query, num=5)
            for r in results:
                snippet = r.get("snippet", "")
                if snippet and len(snippet) > 50:
                    signals.append(snippet[:200])
            if signals:
                break

        return signals[:5]

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "keys_count": len(self._keys),
            "total_calls": self._total_calls,
            "total_results": self._total_results,
            "key_calls": {
                f"key_{i+1}": self._key_calls.get(k, 0)
                for i, k in enumerate(self._keys)
            },
            "key_errors": {
                f"key_{i+1}": self._key_errors.get(k, 0)
                for i, k in enumerate(self._keys)
            },
            "estimated_remaining": max(0, len(self._keys) * 2500 - self._total_calls),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_SERPER: Optional[SerperMultiKeySearch] = None


def get_serper() -> SerperMultiKeySearch:
    global _SERPER
    if _SERPER is None:
        _SERPER = SerperMultiKeySearch()
    return _SERPER
