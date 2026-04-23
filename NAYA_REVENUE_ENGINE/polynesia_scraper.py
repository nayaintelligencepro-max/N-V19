"""
NAYA V19 — GOOGLE MAPS POLYNÉSIE SCRAPER
Trouve de vrais prospects locaux en Polynésie française et dans le Pacifique.
Utilise Google Maps + Serper pour trouver restaurants, hôtels, commerces, etc.

Marchés prioritaires:
  - Tahiti / Papeete (commerce, restauration, santé)
  - Moorea, Bora Bora (hôtellerie, tourisme)
  - Nouvelle-Calédonie (PME, services)
  - Îles Cook, Fidji (tourisme)

Ces marchés sont sous-exploités par les solutions SaaS standards.
NAYA a un avantage compétitif énorme ici.
"""

import os
import re
import json
import time
import logging
import urllib.request
import urllib.parse
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger("NAYA.SCRAPER.regional")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


regional_SECTORS = {
    "restaurant_food": {
        "search_terms": [
            "restaurant Papeete", "brasserie Tahiti", "pizzeria Moorea",
            "snack Papeete", "café Tahiti", "traiteur Papeete",
        ],
        "pain": "marges compressées par les coûts logistiques et le gaspillage alimentaire",
        "avg_pain_cost": 35000,
        "avg_price": 5000,
    },
    "hotel_tourism": {
        "search_terms": [
            "hôtel Bora Bora", "pension famille Moorea", "lodge Tahiti",
            "gîte Huahine", "resort Raiatea",
        ],
        "pain": "taux d'occupation variable et coûts de distribution élevés (OTA 20-25%)",
        "avg_pain_cost": 80000,
        "avg_price": 12000,
    },
    "health_wellness": {
        "search_terms": [
            "cabinet médecin Papeete", "kinésithérapeute Tahiti",
            "dentiste Papeete", "pharmacie Tahiti", "psychologue Papeete",
        ],
        "pain": "rendez-vous non honorés et gestion administrative chronophage",
        "avg_pain_cost": 40000,
        "avg_price": 7500,
    },
    "commerce_retail": {
        "search_terms": [
            "boutique Papeete", "magasin Tahiti", "commerce Moorea",
            "superette Papeete", "artisan Tahiti",
        ],
        "pain": "coûts d'importation élevés et marge nette compressée",
        "avg_pain_cost": 45000,
        "avg_price": 8000,
    },
    "services_b2b": {
        "search_terms": [
            "cabinet comptable Papeete", "avocat Tahiti",
            "agence communication Papeete", "consultant Tahiti",
            "expert-comptable Polynésie",
        ],
        "pain": "facturation sous-optimale et clients qui paient en retard",
        "avg_pain_cost": 55000,
        "avg_price": 10000,
    },
    "real_estate": {
        "search_terms": [
            "agence immobilière Papeete", "agent immobilier Tahiti",
            "promoteur immobilier Polynésie",
        ],
        "pain": "actifs immobiliers dormants et gestion locative inefficace",
        "avg_pain_cost": 60000,
        "avg_price": 9000,
    },
}


@dataclass
class regionalProspect:
    """Prospect Polynésie avec données locales."""
    id: str
    company_name: str
    sector: str
    city: str = "Papeete"
    island: str = "Tahiti"
    phone: str = ""
    email: str = ""
    website: str = ""
    address: str = ""
    google_maps_url: str = ""
    pain_description: str = ""
    pain_annual_cost: float = 0.0
    offer_price: float = 0.0
    offer_title: str = ""
    priority: str = "HIGH"
    source: str = "google_maps"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_prospect(self):
        """Convertit en objet Prospect standard."""
        from NAYA_REVENUE_ENGINE.prospect_finder import Prospect, SECTOR_PAIN_MAP
        sector_info = SECTOR_PAIN_MAP.get(self.sector, SECTOR_PAIN_MAP.get("restaurant_food", {}))

        import hashlib
        pid = hashlib.md5(f"{self.company_name}_{self.city}".encode()).hexdigest()[:10]

        p = Prospect(
            id=f"PF_{pid.upper()}",
            company_name=self.company_name,
            sector=self.sector,
            city=self.city,
            country="PF",  # Polynésie française
            phone=self.phone,
            email=self.email,
            website=self.website,
            pain_category=sector_info.get("pain_category", "MARGIN_INVISIBLE_LOSS"),
            pain_signals=[self.pain_description] if self.pain_description else sector_info.get("pain_signals", []),
            pain_annual_cost_eur=self.pain_annual_cost or sector_info.get("avg_pain_cost", 30000),
            estimated_revenue_eur=sector_info.get("avg_revenue", 200000),
            offer_price_eur=self.offer_price or 5000,
            offer_title=self.offer_title,
            source=self.source,
            notes=self.notes,
        )
        # Boost score Polynésie
        p.solvability_score = 75.0
        if self.email:
            p.solvability_score += 20
        if self.phone:
            p.solvability_score += 10
        p.solvability_score = min(p.solvability_score, 100)
        p.priority = "CRITICAL" if p.solvability_score >= 90 else "HIGH"
        return p


class regionalScraper:
    """
    Scraper spécialisé Polynésie française et Pacifique.
    Utilise Serper (Google) + DuckDuckGo + Pages Jaunes PF.
    """

    regionalN_CITIES = [
        "Papeete", "Faaa", "Pirae", "Moorea", "Bora-Bora",
        "Huahine", "Raiatea", "Rangiroa", "Nuku Hiva",
        "Tahiti", "Polynésie française",
    ]

    def __init__(self):
        self._serper = None
        self._found_total = 0
        self._cache: Dict[str, List] = {}
        self._init_serper()

    def _init_serper(self):
        try:
            from NAYA_CORE.integrations.serper_multi import get_serper
            self._serper = get_serper()
            if self._serper.available:
                log.info("✅ regionalScraper: Serper disponible")
            else:
                log.info("regionalScraper: Mode DuckDuckGo (gratuit)")
        except Exception as e:
            log.debug(f"[regionalScraper] Serper: {e}")

    def find_prospects(self, sector: str = None, count: int = 10,
                       island: str = None) -> List[regionalProspect]:
        """Trouve des prospects en Polynésie française."""
        sectors = [sector] if sector and sector in regional_SECTORS else list(regional_SECTORS.keys())
        islands = [island] if island else self.regionalN_CITIES[:5]

        all_prospects = []
        for s in sectors:
            if len(all_prospects) >= count:
                break
            for isl in islands[:2]:
                if len(all_prospects) >= count:
                    break
                prospects = self._search_sector(s, isl, min(5, count - len(all_prospects)))
                all_prospects.extend(prospects)

        # Dédupliquer
        seen = set()
        unique = []
        for p in all_prospects:
            key = p.company_name.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(p)

        self._found_total += len(unique)
        return unique[:count]

    def _search_sector(self, sector: str, city: str, count: int) -> List[regionalProspect]:
        """Recherche un secteur dans une ville polynésienne."""
        cache_key = f"{sector}_{city}"
        if cache_key in self._cache:
            return self._cache[cache_key][:count]

        sector_data = regional_SECTORS.get(sector, {})
        search_terms = sector_data.get("search_terms", [f"{sector} {city}"])
        prospects = []

        for term in search_terms[:2]:  # Limiter pour économiser les crédits
            if len(prospects) >= count:
                break

            # Essayer Serper d'abord
            if self._serper and self._serper.available:
                results = self._serper_search(term, count)
            else:
                results = self._ddg_search(term, count)

            for r in results:
                p = self._parse_result(r, sector, city, sector_data)
                if p:
                    prospects.append(p)

            time.sleep(1.5)  # Rate limiting

        self._cache[cache_key] = prospects
        return prospects[:count]

    def _serper_search(self, query: str, count: int) -> List[Dict]:
        """Recherche via Serper."""
        try:
            return self._serper.search(
                f"{query} contact téléphone email",
                num=count,
                lang="fr",
                country="pf"  # Polynésie française
            )
        except Exception:
            return []

    def _ddg_search(self, query: str, count: int) -> List[Dict]:
        """Recherche via DuckDuckGo (gratuit)."""
        try:
            import time as _time
            _time.sleep(2)  # Rate limiting DDG
            data = urllib.parse.urlencode({
                "q": f"{query} contact",
                "kl": "fr-pf",
                "ia": "web"
            }).encode()

            req = urllib.request.Request(
                "https://html.duckduckgo.com/html/",
                data=data,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            results = []
            blocks = re.findall(
                r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?'
                r'class="result__snippet"[^>]*>([^<]*)',
                html, re.DOTALL
            )
            for url, title, snippet in blocks[:count]:
                results.append({"link": url, "title": title.strip(), "snippet": snippet.strip()})
            return results

        except Exception as e:
            log.debug(f"[regional] DDG: {e}")
            return []

    def _parse_result(self, result: Dict, sector: str, city: str,
                       sector_data: Dict) -> Optional[regionalProspect]:
        """Parse un résultat de recherche en prospect."""
        title = result.get("title", "") or result.get("name", "")
        url = result.get("link", "") or result.get("url", "")
        snippet = result.get("snippet", "")

        if not title or len(title) < 3:
            return None

        # Nettoyer le nom
        name = title.split(" - ")[0].split(" | ")[0].strip()[:80]
        if not name:
            return None

        # Extraire email du snippet
        email_match = re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', snippet)
        email = email_match.group(0) if email_match else ""

        # Extraire téléphone (format PF: +689 xx xx xx xx ou 40 xx xx xx)
        phone_patterns = [
            r'(?:\+689|00689)\s*\d{2}(?:[\s.\-]?\d{2}){3}',
            r'(?:40|87|89)\s*\d{2}(?:\s?\d{2}){2}',
        ]
        phone = ""
        for pat in phone_patterns:
            m = re.search(pat, snippet)
            if m:
                phone = m.group(0)
                break

        # Calculer l'offre
        avg_pain = sector_data.get("avg_pain_cost", 30000)
        avg_price = sector_data.get("avg_price", 5000)

        import hashlib
        pid = hashlib.md5(f"pf_{name}_{city}".encode()).hexdigest()[:10]

        return regionalProspect(
            id=f"PF_{pid.upper()}",
            company_name=name,
            sector=sector,
            city=city,
            island=city,
            phone=phone,
            email=email,
            website=url if "http" in url else "",
            pain_description=sector_data.get("pain", ""),
            pain_annual_cost=avg_pain,
            offer_price=avg_price,
            offer_title=f"Optimisation {sector.replace('_', ' ')} — +{int(avg_pain/avg_price)}x ROI",
            priority="CRITICAL" if email else "HIGH",
            source="regional_serper" if (self._serper and self._serper.available) else "regional_ddg",
            notes=snippet[:200],
        )

    def generate_regional_offer(self, prospect: regionalProspect) -> str:
        """
        Génère une offre adaptée au marché polynésien.
        Prend en compte les spécificités locales:
        - Coûts logistiques élevés (isolation géographique)
        - Marges compressées par l'importation
        - Marché de niche = pas de concurrence locale sur le conseil
        """
        sector_data = regional_SECTORS.get(prospect.sector, {})
        pain = sector_data.get("pain", "problème opérationnel")
        monthly = round(prospect.pain_annual_cost / 12)

        offer = (
            f"En Polynésie française, {pain} est encore plus critique qu'en métropole. "
            f"Les coûts d'importation et l'isolement géographique amplifient chaque inefficacité. "
            f"\n\n{prospect.company_name} perd environ {monthly:,.0f}€ par mois sur ce problème. "
            f"Notre intervention à {prospect.offer_price:,.0f}€ s'amortit en "
            f"{round(prospect.offer_price / max(monthly, 1))} mois. "
            f"\n\nGarantie : résultats mesurables en 30 jours ou remboursement total. "
            f"Mission réalisable à distance (visio + outils en ligne)."
        )
        return offer

    def get_stats(self) -> Dict:
        return {
            "total_found": self._found_total,
            "sectors_covered": list(regional_SECTORS.keys()),
            "islands_targeted": self.regionalN_CITIES,
            "serper_active": self._serper is not None and self._serper.available,
            "cached_searches": len(self._cache),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_regional_SCRAPER: Optional[regionalScraper] = None


def get_regional_scraper() -> regionalScraper:
    global _regional_SCRAPER
    if _regional_SCRAPER is None:
        _regional_SCRAPER = regionalScraper()
    return _regional_SCRAPER
