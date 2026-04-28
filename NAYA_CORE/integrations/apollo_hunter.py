"""
NAYA V19 — Apollo.io Hunter
Enrichissement et recherche de prospects via Apollo.io API.
Apollo.io = source principale pour emails vérifiés + données entreprises.
"""
import os, logging, json, time, urllib.request, urllib.parse
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.APOLLO")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


@dataclass
class ApolloProspect:
    id: str = ""
    name: str = ""
    email: str = ""
    title: str = ""
    company: str = ""
    company_size: str = ""
    industry: str = ""
    country: str = ""
    linkedin_url: str = ""
    phone: str = ""
    revenue_range: str = ""
    seniority: str = ""
    score: float = 0.0


class ApolloHunter:
    """
    Chasse prospects via Apollo.io.
    Plan gratuit: 50 emails/mois. Plan basique: 5 000/mois.
    """

    BASE = "https://api.apollo.io/v1"

    def __init__(self):
        self._key = _gs("APOLLO_API_KEY", "")
        self._cache: Dict[str, List] = {}
        self._calls = 0
        self._last_reset = time.time()

    @property
    def available(self) -> bool:
        return bool(self._key)

    def search_people(self, job_titles: List[str], industries: List[str] = None,
                      countries: List[str] = None, size_ranges: List[str] = None,
                      limit: int = 10) -> List[ApolloProspect]:
        """Cherche des décisionnaires par titre/industrie/pays."""
        if not self._key:
            log.debug("[APOLLO] No API key — returning empty")
            return []

        cache_key = f"{job_titles}_{industries}_{countries}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = {
            "api_key": self._key,
            "person_titles": job_titles,
            "page": 1,
            "per_page": min(limit, 25),
        }
        if industries:
            payload["organization_industry_tag_ids"] = industries
        if countries:
            payload["person_locations"] = countries
        if size_ranges:
            payload["organization_num_employees_ranges"] = size_ranges

        try:
            data = self._post("/mixed_people/search", payload)
            prospects = []
            for p in data.get("people", []):
                org = p.get("organization", {}) or {}
                prospect = ApolloProspect(
                    id=p.get("id", ""),
                    name=p.get("name", ""),
                    email=p.get("email", ""),
                    title=p.get("title", ""),
                    company=org.get("name", ""),
                    company_size=str(org.get("estimated_num_employees", "")),
                    industry=org.get("industry", ""),
                    country=p.get("country", ""),
                    linkedin_url=p.get("linkedin_url", ""),
                    phone=p.get("sanitized_phone", ""),
                    revenue_range=str(org.get("annual_revenue_printed", "")),
                    seniority=p.get("seniority", ""),
                )
                if prospect.email:
                    prospect.score = self._score(prospect)
                    prospects.append(prospect)

            self._cache[cache_key] = prospects
            log.info(f"[APOLLO] Found {len(prospects)} prospects")
            return prospects
        except Exception as e:
            log.warning(f"[APOLLO] Search failed: {e}")
            return []

    def enrich_company(self, domain: str) -> Dict:
        """Enrichit les données d'une entreprise via son domaine."""
        if not self._key:
            return {}
        try:
            data = self._post("/organizations/enrich", {
                "api_key": self._key, "domain": domain
            })
            org = data.get("organization", {})
            return {
                "name": org.get("name", ""),
                "industry": org.get("industry", ""),
                "size": org.get("estimated_num_employees", 0),
                "revenue": org.get("annual_revenue_printed", ""),
                "linkedin": org.get("linkedin_url", ""),
                "country": org.get("country", ""),
            }
        except Exception as e:
            log.debug(f"[APOLLO] Enrich failed: {e}")
            return {}

    def _score(self, p: ApolloProspect) -> float:
        """Score de qualification 0-1."""
        score = 0.5
        if p.email and "@" in p.email:
            score += 0.2
        if any(t in p.seniority.lower() for t in ["vp", "director", "ceo", "cto", "chief", "head"]):
            score += 0.2
        if p.company_size and int(p.company_size) > 50 if p.company_size.isdigit() else False:
            score += 0.1
        return min(score, 1.0)

    def _post(self, path: str, payload: dict) -> dict:
        self._calls += 1
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.BASE}{path}",
            data=data,
            headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())

    def stats(self) -> dict:
        return {"calls": self._calls, "cached_searches": len(self._cache), "available": self.available}


_instance: Optional[ApolloHunter] = None

def get_apollo() -> ApolloHunter:
    global _instance
    if _instance is None:
        _instance = ApolloHunter()
    return _instance
