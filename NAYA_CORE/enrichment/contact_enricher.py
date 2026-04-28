"""
NAYA V19 — Contact Enrichment Pipeline
Transforme un nom d'entreprise/URL en email de décideur contactable.
Sources: Apollo → Hunter.io → Scraping site → Pattern guessing.
SANS cet enrichissement, le pipeline tourne dans le vide.
"""
import os, re, logging, time, threading, json, hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.ENRICHMENT")


@dataclass
class EnrichedContact:
    company: str
    domain: str = ""
    decision_maker_name: str = ""
    decision_maker_title: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    source: str = ""
    confidence: float = 0.0
    enriched_at: float = field(default_factory=time.time)

    @property
    def is_valid(self) -> bool:
        return bool(self.email) and "@" in self.email and self.confidence >= 0.4


class ContactEnricher:
    """
    Pipeline d'enrichissement multi-source.
    Objectif: transformer un signal de douleur en contact actionable.
    
    Chaîne: Apollo API → Hunter.io → Page contact site web → Pattern email
    """

    CACHE_DIR = Path("data/cache/enrichment")
    CACHE_TTL = 86400 * 7  # 7 jours

    # Patterns email courants par pays
    EMAIL_PATTERNS = [
        "{first}.{last}@{domain}",
        "{first}@{domain}",
        "{f}{last}@{domain}",
        "{first}{l}@{domain}",
        "contact@{domain}",
        "info@{domain}",
        "direction@{domain}",
    ]

    # Titres de décideurs par langue
    DECISION_MAKER_TITLES = {
        "fr": ["directeur", "gérant", "pdg", "ceo", "fondateur", "responsable",
               "directrice", "gérante", "fondatrice", "dg"],
        "en": ["ceo", "founder", "director", "managing director", "owner",
               "head of", "vp", "chief"],
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._stats = {"total": 0, "enriched": 0, "cached": 0, "failed": 0}
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def enrich(self, company: str, url: str = "", sector: str = "",
               country: str = "FR") -> EnrichedContact:
        """Point d'entrée principal — enrichit un prospect."""
        self._stats["total"] += 1
        cache_key = hashlib.md5(f"{company}:{url}".encode()).hexdigest()

        # Check cache
        cached = self._load_cache(cache_key)
        if cached:
            self._stats["cached"] += 1
            return cached

        contact = EnrichedContact(company=company)

        # Extraire le domaine depuis l'URL
        domain = self._extract_domain(url) if url else ""
        contact.domain = domain

        # Source 1: Apollo API
        apollo_result = self._try_apollo(company, domain)
        if apollo_result and apollo_result.is_valid:
            self._save_cache(cache_key, apollo_result)
            self._stats["enriched"] += 1
            return apollo_result

        # Merge partiel Apollo
        if apollo_result:
            contact = self._merge(contact, apollo_result)

        # Source 2: Hunter.io
        if domain:
            hunter_result = self._try_hunter(domain, company)
            if hunter_result and hunter_result.is_valid:
                self._save_cache(cache_key, hunter_result)
                self._stats["enriched"] += 1
                return hunter_result
            if hunter_result:
                contact = self._merge(contact, hunter_result)

        # Source 3: Scraping page contact du site
        if url or domain:
            scrape_result = self._try_scrape_contact_page(url or f"https://{domain}")
            if scrape_result and scrape_result.is_valid:
                self._save_cache(cache_key, scrape_result)
                self._stats["enriched"] += 1
                return scrape_result
            if scrape_result:
                contact = self._merge(contact, scrape_result)

        # Source 4: Pattern guessing si on a le domaine
        if domain and not contact.email:
            guessed = self._guess_email(domain, contact.decision_maker_name)
            if guessed:
                contact.email = guessed
                contact.source = "pattern_guess"
                contact.confidence = 0.4

        if contact.is_valid:
            self._save_cache(cache_key, contact)
            self._stats["enriched"] += 1
        else:
            # Fallback: email générique
            if domain:
                contact.email = f"contact@{domain}"
                contact.source = "generic_fallback"
                contact.confidence = 0.3
            self._stats["failed"] += 1

        self._save_cache(cache_key, contact)
        return contact

    def enrich_batch(self, prospects: List[Dict]) -> List[EnrichedContact]:
        """Enrichit une liste de prospects."""
        results = []
        for p in prospects:
            contact = self.enrich(
                company=p.get("entity", p.get("company_name", "")),
                url=p.get("url", ""),
                sector=p.get("sector", ""),
                country=p.get("country", "FR"),
            )
            results.append(contact)
            time.sleep(0.5)  # Rate limiting
        return results

    # ── SOURCES ────────────────────────────────────────────

    def _try_apollo(self, company: str, domain: str) -> Optional[EnrichedContact]:
        """Enrichissement via Apollo.io API."""
        api_key = os.environ.get("APOLLO_API_KEY", "")
        if not api_key:
            return None

        try:
            import httpx
            # Recherche d'organisation
            resp = httpx.post(
                "https://api.apollo.io/v1/mixed_people/search",
                headers={"Content-Type": "application/json",
                         "Cache-Control": "no-cache"},
                json={
                    "api_key": api_key,
                    "q_organization_name": company,
                    "person_titles": ["CEO", "Founder", "Director", "Gérant",
                                      "Directeur", "Owner"],
                    "page": 1,
                    "per_page": 3,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                log.debug(f"[ENRICH] Apollo HTTP {resp.status_code}")
                return None

            data = resp.json()
            people = data.get("people", [])
            if not people:
                return None

            person = people[0]
            return EnrichedContact(
                company=company,
                domain=domain or person.get("organization", {}).get("primary_domain", ""),
                decision_maker_name=person.get("name", ""),
                decision_maker_title=person.get("title", ""),
                email=person.get("email", ""),
                phone=person.get("phone_numbers", [{}])[0].get("sanitized_number", "") if person.get("phone_numbers") else "",
                linkedin_url=person.get("linkedin_url", ""),
                source="apollo",
                confidence=0.9 if person.get("email") else 0.3,
            )
        except Exception as e:
            log.debug(f"[ENRICH] Apollo error: {e}")
            return None

    def _try_hunter(self, domain: str, company: str = "") -> Optional[EnrichedContact]:
        """Enrichissement via Hunter.io API."""
        api_key = os.environ.get("HUNTER_API_KEY", "")
        if not api_key:
            return None

        try:
            import httpx
            # Domain search
            resp = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": 5,
                        "type": "personal"},
                timeout=15,
            )
            if resp.status_code != 200:
                return None

            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            if not emails:
                return None

            # Prendre le décideur le plus haut
            best = None
            for e in emails:
                title = (e.get("position", "") or "").lower()
                if any(t in title for t in self.DECISION_MAKER_TITLES.get("fr", []) +
                       self.DECISION_MAKER_TITLES.get("en", [])):
                    best = e
                    break
            if not best:
                best = emails[0]

            return EnrichedContact(
                company=company or data.get("organization", ""),
                domain=domain,
                decision_maker_name=f"{best.get('first_name', '')} {best.get('last_name', '')}".strip(),
                decision_maker_title=best.get("position", ""),
                email=best.get("value", ""),
                phone=best.get("phone_number", ""),
                linkedin_url=best.get("linkedin", ""),
                source="hunter",
                confidence=best.get("confidence", 50) / 100.0,
            )
        except Exception as e:
            log.debug(f"[ENRICH] Hunter error: {e}")
            return None

    def _try_scrape_contact_page(self, base_url: str) -> Optional[EnrichedContact]:
        """Scrape la page contact/about pour trouver des emails."""
        try:
            import httpx

            contact_paths = ["/contact", "/nous-contacter", "/about",
                             "/a-propos", "/mentions-legales", "/impressum"]
            emails_found = []
            domain = self._extract_domain(base_url)

            for path in [""] + contact_paths:
                url = base_url.rstrip("/") + path
                try:
                    resp = httpx.get(url, timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        text = resp.text
                        # Extraire emails
                        found = re.findall(
                            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
                            text
                        )
                        # Filtrer les emails du même domaine
                        for e in found:
                            e_domain = e.split("@")[1].lower()
                            if domain and e_domain == domain.lower():
                                emails_found.append(e)
                            elif not domain:
                                emails_found.append(e)
                    time.sleep(0.3)
                except Exception:
                    continue

            if not emails_found:
                return None

            # Prioriser: pas info@/contact@ si possible
            generic = {"info", "contact", "admin", "support", "hello",
                        "bonjour", "webmaster", "no-reply", "noreply"}
            personal = [e for e in emails_found
                        if e.split("@")[0].lower() not in generic]
            best = personal[0] if personal else emails_found[0]

            return EnrichedContact(
                company="",
                domain=domain,
                email=best,
                source="scrape",
                confidence=0.6 if best in personal else 0.4,
            )
        except Exception as e:
            log.debug(f"[ENRICH] Scrape error: {e}")
            return None

    def _guess_email(self, domain: str, name: str = "") -> str:
        """Devine un email par pattern si on a le nom."""
        if not name or not domain:
            return f"contact@{domain}" if domain else ""

        parts = name.lower().strip().split()
        if len(parts) < 2:
            return f"contact@{domain}"

        first = re.sub(r'[^a-z]', '', parts[0])
        last = re.sub(r'[^a-z]', '', parts[-1])
        if not first or not last:
            return f"contact@{domain}"

        # Pattern le plus courant en France
        return f"{first}.{last}@{domain}"

    # ── HELPERS ────────────────────────────────────────────

    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL."""
        if not url:
            return ""
        url = url.lower().strip()
        # Retirer protocole
        for prefix in ["https://", "http://", "www."]:
            if url.startswith(prefix):
                url = url[len(prefix):]
        # Prendre jusqu'au premier /
        domain = url.split("/")[0].split("?")[0]
        # Valider
        if "." in domain and len(domain) > 3:
            return domain
        return ""

    def _merge(self, base: EnrichedContact, new: EnrichedContact) -> EnrichedContact:
        """Fusionne deux contacts en gardant les meilleures données."""
        if new.email and not base.email:
            base.email = new.email
        if new.decision_maker_name and not base.decision_maker_name:
            base.decision_maker_name = new.decision_maker_name
        if new.decision_maker_title and not base.decision_maker_title:
            base.decision_maker_title = new.decision_maker_title
        if new.phone and not base.phone:
            base.phone = new.phone
        if new.linkedin_url and not base.linkedin_url:
            base.linkedin_url = new.linkedin_url
        if new.domain and not base.domain:
            base.domain = new.domain
        if new.confidence > base.confidence:
            base.confidence = new.confidence
            base.source = new.source
        return base

    # ── CACHE ──────────────────────────────────────────────

    def _cache_path(self, key: str) -> Path:
        return self.CACHE_DIR / f"{key}.json"

    def _load_cache(self, key: str) -> Optional[EnrichedContact]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() - data.get("enriched_at", 0) > self.CACHE_TTL:
                path.unlink(missing_ok=True)
                return None
            return EnrichedContact(**data)
        except Exception:
            return None

    def _save_cache(self, key: str, contact: EnrichedContact) -> None:
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "company": contact.company,
                "domain": contact.domain,
                "decision_maker_name": contact.decision_maker_name,
                "decision_maker_title": contact.decision_maker_title,
                "email": contact.email,
                "phone": contact.phone,
                "linkedin_url": contact.linkedin_url,
                "source": contact.source,
                "confidence": contact.confidence,
                "enriched_at": contact.enriched_at,
            }
            self._cache_path(key).write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def get_stats(self) -> Dict:
        return {
            **self._stats,
            "cache_size": len(list(self.CACHE_DIR.glob("*.json")))
            if self.CACHE_DIR.exists() else 0,
            "enrichment_rate": (
                round(self._stats["enriched"] / max(self._stats["total"], 1) * 100, 1)
            ),
        }


# ── Singleton ──────────────────────────────────────────────
_enricher = None
_enricher_lock = threading.Lock()

def get_contact_enricher() -> ContactEnricher:
    global _enricher
    if _enricher is None:
        with _enricher_lock:
            if _enricher is None:
                _enricher = ContactEnricher()
    return _enricher
