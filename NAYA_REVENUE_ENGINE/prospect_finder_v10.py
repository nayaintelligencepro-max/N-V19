"""
NAYA V19 — PROSPECT FINDER AMÉLIORÉ
Intègre le web scraper autonome pour trouver de VRAIS prospects.

Sources actives V10:
  1. Apollo.io (si clé dispo — premium)
  2. Web Scraper autonome (Pages Jaunes, DuckDuckGo, Societe.com)
  3. Serper Google Search (si clé dispo — semi-premium)
  4. Website email hunter (gratuit)
  5. Prospects tactiques (fallback offline)

Amélioration V10:
  - Emails réels trouvés via scraping (sans Hunter.io payant)
  - LLM pour personnaliser les offres si disponible
  - Scoring amélioré avec signaux réels
  - Polynésie locale prioritaire
  - Deduplication intelligente cross-sessions
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

log = logging.getLogger("NAYA.PROSPECT.V10")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# Import du SECTOR_PAIN_MAP original (réutilisation)
from NAYA_REVENUE_ENGINE.prospect_finder import (
    Prospect, SECTOR_PAIN_MAP,
    ProspectFinder as _OriginalProspectFinder
)


class ProspectFinderV10(_OriginalProspectFinder):
    """
    Extension V10 du ProspectFinder.
    Ajoute le web scraping autonome comme source primaire gratuite.
    """

    def __init__(self):
        super().__init__()
        self._scraper = None
        self._llm_router = None
        self._dedup_global: set = set()  # Dédup cross-secteurs
        self._init_enhanced()

    def _init_enhanced(self):
        """Initialise les composants V10."""
        try:
            from NAYA_REVENUE_ENGINE.web_scraper import get_web_scraper
            self._scraper = get_web_scraper()
            log.info("[ProspectV10] Web scraper autonome activé")
        except Exception as e:
            log.debug(f"[ProspectV10] Web scraper: {e}")

        try:
            from NAYA_CORE.execution.llm_router import LLMRouter
            self._llm_router = LLMRouter()
            log.info("[ProspectV10] LLM router activé")
        except Exception as e:
            log.debug(f"[ProspectV10] LLM router: {e}")

        # Pipeline cognitif — 10 couches actives
        try:
            from NAYA_CORE.cognitive_pipeline import get_cognitive_pipeline
            self._cognitive = get_cognitive_pipeline()
            log.info(f"[ProspectV10] Pipeline cognitif actif — {self._cognitive.get_stats()}")
        except Exception as e:
            self._cognitive = None
            log.debug(f"[ProspectV10] Cognitive pipeline: {e}")

    def find_prospects(self, sector: str, count: int = 10, city: str = "") -> List[Prospect]:
        """
        Trouve des prospects via toutes les sources disponibles.
        V10: intègre le web scraper autonome en premier.
        """
        cache_key = f"{sector}_{city}"
        CACHE_TTL = 7200

        if cache_key in self._cache:
            cached_data, cached_ts = self._cache[cache_key]
            if cached_data and (time.time() - cached_ts) < CACHE_TTL:
                return cached_data[:count]
            else:
                del self._cache[cache_key]

        prospects = []

        # 1. Apollo (premium, si dispo)
        if self.has_apollo:
            prospects = self._find_via_apollo(sector, count, city)
            log.info(f"[ProspectV10] Apollo: {len(prospects)} prospects")

        # 2. Web Scraper Autonome V10 (gratuit, no API needed)
        if len(prospects) < count and self._scraper:
            scraped = self._find_via_scraper(sector, count - len(prospects), city)
            prospects.extend(scraped)
            log.info(f"[ProspectV10] Scraper web: +{len(scraped)} prospects")

        # 3. Serper (si dispo)
        if len(prospects) < count and self.has_serper:
            serper = self._find_via_serper(sector, count - len(prospects), city)
            prospects.extend(serper)

        # 4. Tactiques (fallback offline garanti)
        if len(prospects) < count:
            tactical = self._generate_tactical_prospects(sector, count - len(prospects), city)
            prospects.extend(tactical)

        # Enrichir + scorer
        prospects = [self._enrich_with_pain(p) for p in prospects]

        # Enrichissement LLM des offres si disponible
        if self._llm_router:
            prospects = [self._enrich_offer_with_llm(p) for p in prospects[:5]]  # Top 5 seulement

        # Dédupliquer (global + local)
        prospects = self._deduplicate(prospects)

        # Trier par score
        prospects.sort(key=lambda x: x.solvability_score, reverse=True)

        self._cache[cache_key] = (prospects, time.time())
        self._found_total += len(prospects)

        log.info(f"[ProspectV10] {sector}: {len(prospects)} prospects qualifiés (total: {self._found_total})")
        return prospects[:count]

    def _find_via_scraper(self, sector: str, count: int, city: str) -> List[Prospect]:
        """Trouve des prospects via le web scraper autonome."""
        if not self._scraper:
            return []

        # Cibler des villes selon le contexte géographique
        search_cities = [city] if city else self._get_target_cities(sector)

        all_prospects = []
        for search_city in search_cities[:2]:  # Max 2 villes
            try:
                raw = self._scraper.find_real_prospects(sector, count, search_city)
                for r in raw:
                    company_name = r.get("company_name", "").strip()
                    if not company_name or len(company_name) < 3:
                        continue

                    pid = hashlib.md5(f"web_{company_name}_{search_city}".encode()).hexdigest()[:10]
                    p = Prospect(
                        id=f"WEB_{pid.upper()}",
                        company_name=company_name,
                        sector=sector,
                        city=r.get("city", search_city),
                        country="FR",
                        email=r.get("email", ""),
                        phone=r.get("phone", ""),
                        website=r.get("website", ""),
                        contact_name=r.get("contact_name", ""),
                        source=f"web_{r.get('source', 'scraper')}",
                        notes=r.get("description", "")[:200],
                    )
                    all_prospects.append(p)

                if len(all_prospects) >= count:
                    break

            except Exception as e:
                log.debug(f"[ProspectV10] Scraper {sector}/{search_city}: {e}")

        return all_prospects[:count]

    def _get_target_cities(self, sector: str) -> List[str]:
        """Retourne les villes prioritaires selon le secteur."""
        # Polynésie en priorité (marché local de Naya)
        regional_sectors = ["regional_market", "restaurant_food", "healthcare_wellness", "real_estate_investors"]
        if sector in regional_sectors:
            return ["your_city", "Paris", "Lyon", "Marseille", "Bordeaux"]
        return ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse", "Nantes", "Lille"]

    def _enrich_offer_with_llm(self, prospect: Prospect) -> Prospect:
        """Enrichit l'offre avec le LLM + pipeline cognitif."""
        # Score cognitif (sans API, 100% offline)
        if hasattr(self, "_cognitive") and self._cognitive:
            try:
                signals = getattr(prospect, "pain_signals",
                                  [prospect.pain_category.replace("_", " ")])
                cog_score = self._cognitive.score_prospect(
                    prospect.company_name, signals,
                    prospect.pain_annual_cost_eur, prospect.sector
                )
                # Mettre à jour le score de solvabilité
                cog_boost = cog_score.get("score", 50)
                prospect.solvability_score = round(
                    prospect.solvability_score * 0.6 + cog_boost * 0.4, 1
                )
                # Upgrad priority si élite signals détectés
                if cog_score.get("elite_signals") and prospect.priority != "CRITICAL":
                    prospect.priority = "HIGH"
            except Exception:
                pass

        if not self._llm_router:
            return prospect

        try:
            # Analyser l'opportunité
            opp_data = {
                "name": prospect.offer_title,
                "market": prospect.sector,
                "value": prospect.pain_annual_cost_eur,
                "description": f"Entreprise: {prospect.company_name}, Pain: {prospect.pain_category}",
            }
            analysis = self._llm_router.analyze_opportunity(opp_data)
            score = analysis.get("viability_score", 0)
            if score > 0:
                # Ajuster le score de solvabilité
                prospect.solvability_score = (prospect.solvability_score * 0.7 + score * 0.3)
                prospect.solvability_score = min(100, prospect.solvability_score)

            # Mettre à jour priority
            if prospect.solvability_score >= 80:
                prospect.priority = "CRITICAL"
            elif prospect.solvability_score >= 65:
                prospect.priority = "HIGH"

        except Exception as e:
            log.debug(f"[ProspectV10] LLM enrich: {e}")

        return prospect

    def _deduplicate(self, prospects: List[Prospect]) -> List[Prospect]:
        """Déduplication locale + globale cross-session."""
        seen_local = set()
        unique = []
        for p in prospects:
            key = p.company_name.lower().strip()
            if key and key not in seen_local and key not in self._dedup_global:
                seen_local.add(key)
                self._dedup_global.add(key)
                unique.append(p)

        # Pruning du set global (garder max 10000)
        if len(self._dedup_global) > 10000:
            self._dedup_global = set(list(self._dedup_global)[-5000:])

        return unique

    def get_stats(self) -> Dict:
        base = super().get_stats()
        base.update({
            "version": "V10",
            "web_scraper_active": self._scraper is not None,
            "llm_router_active": self._llm_router is not None,
            "dedup_global_count": len(self._dedup_global),
        })
        return base


# ── Singleton V10 ────────────────────────────────────────────────────────────

_FINDER_V10: Optional[ProspectFinderV10] = None


def get_prospect_finder_v10() -> ProspectFinderV10:
    global _FINDER_V10
    if _FINDER_V10 is None:
        _FINDER_V10 = ProspectFinderV10()
    return _FINDER_V10
