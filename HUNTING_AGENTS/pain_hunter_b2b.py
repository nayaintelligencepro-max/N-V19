"""
NAYA SUPREME — PAIN HUNTER B2B/B2A/GOUVERNEMENTAL
══════════════════════════════════════════════════════════════════════════════════
Agent autonome de chasse de douleurs RÉELLES, discrètes, confidentielles.

DOCTRINE:
  La douleur la plus rentable est celle que personne ne voit.
  L'entreprise qui souffre en silence PAIE le prix fort pour la discrétion.
  NAYA détecte, classe, et convertit — en mode PHANTOM.

SOURCES RÉELLES:
  - LinkedIn Sales Navigator API (signaux de recrutement, postes ouverts = douleur)
  - Crunchbase API (levées, pivots, layoffs = douleur structurelle)
  - Apollo.io API (enrichissement contacts décisionnaires)
  - Hunter.io API (emails vérifiés)
  - Google News API (alertes sectorielles)
  - Data.gouv.fr / SIRENE (marchés publics, entreprises françaises)
  - Pappers API (bilans, défaillances, tribunaux de commerce)

CLASSIFICATION:
  CAT_1 — CASH RAPIDE : 24h-7j, valeur 10k-150k€
  CAT_2 — MOYEN TERME : 7j-30j, valeur 50k-500k€
  CAT_3 — LONG TERME  : 30j+/abonnement, valeur 100k-2M€/an

INTÉGRATION:
  → NAYA_CORE.cash_engine_real (injection deals)
  → NAYA_CORE.scheduler (cycles automatiques)
  → PERSISTENCE.database (stockage SQLite)
  → BUSINESS_ENGINES.discretion_protocol (mode PHANTOM)
  → NAYA_REVENUE_ENGINE (pipeline prospect→closing)
══════════════════════════════════════════════════════════════════════════════════
"""

import os
import time
import uuid
import json
import logging
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.HUNTER.PAIN_B2B")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATACLASSES
# ══════════════════════════════════════════════════════════════════════════════

class HuntCategory(Enum):
    """Les 3 catégories de classification des opportunités."""
    CASH_RAPIDE = "cash_rapide"     # 24h-7j, 10k-150k€
    MOYEN_TERME = "moyen_terme"     # 7j-30j, 50k-500k€
    LONG_TERME  = "long_terme"      # 30j+/abo, 100k-2M€/an


class TargetType(Enum):
    B2B           = "b2b"
    B2A           = "b2a"             # Business-to-Administration
    GOUVERNEMENTAL = "gouvernemental"
    INFRASTRUCTURE = "infrastructure"  # Grandes infras (transport, énergie, telecom)


class PainSeverity(Enum):
    CRITICAL   = "critical"    # Perd de l'argent MAINTENANT
    HIGH       = "high"        # Douleur forte, action dans 30j
    MEDIUM     = "medium"      # Douleur réelle mais supportable
    LATENT     = "latent"      # Douleur cachée, pas encore conscient


class ConfidentialityLevel(Enum):
    PUBLIC     = "public"      # Info publique, approche directe OK
    DISCRETE   = "discrete"    # Approche indirecte, pas de trace
    STEALTH    = "stealth"     # Zéro trace, contact via intermédiaire
    PHANTOM    = "phantom"     # Opération invisible, résultat seul


class SignalSource(Enum):
    LINKEDIN        = "linkedin"
    CRUNCHBASE      = "crunchbase"
    APOLLO          = "apollo"
    HUNTER_IO       = "hunter_io"
    GOOGLE_NEWS     = "google_news"
    PAPPERS         = "pappers"
    DATA_GOUV       = "data_gouv"
    SIRENE          = "sirene"
    TRIBUNAL_COM    = "tribunal_commerce"
    INDEED_SIGNALS  = "indeed_signals"
    GLASSDOOR       = "glassdoor"
    WEB_SCRAPE      = "web_scrape"


@dataclass
class PainSignal:
    """Signal brut détecté depuis une source."""
    id: str = field(default_factory=lambda: f"SIG_{uuid.uuid4().hex[:10].upper()}")
    source: SignalSource = SignalSource.WEB_SCRAPE
    raw_data: Dict = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    detected_at: float = field(default_factory=time.time)
    confidence: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "source": self.source.value,
            "keywords": self.keywords, "confidence": self.confidence,
            "detected_at": datetime.fromtimestamp(self.detected_at).isoformat(),
        }


@dataclass
class HuntedPain:
    """Douleur détectée, qualifiée et classifiée."""
    id: str = field(default_factory=lambda: f"PAIN_{uuid.uuid4().hex[:10].upper()}")
    
    # Cible
    target_name: str = ""
    target_type: TargetType = TargetType.B2B
    target_sector: str = ""
    target_country: str = "FR"
    target_city: str = ""
    target_size: str = ""           # PME, ETI, GE, Administration
    target_revenue_estimate: float = 0.0
    
    # Douleur
    pain_description: str = ""
    pain_severity: PainSeverity = PainSeverity.MEDIUM
    pain_category: str = ""         # Ex: "trésorerie", "RH", "IT", "compliance"
    pain_financial_impact: float = 0.0  # Coût annuel de la douleur
    pain_is_discrete: bool = True   # Pas verbalisée publiquement
    pain_signals: List[PainSignal] = field(default_factory=list)
    
    # Classification
    hunt_category: HuntCategory = HuntCategory.CASH_RAPIDE
    estimated_deal_value: float = 0.0
    estimated_delivery_days: int = 3
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.DISCRETE
    
    # Contact décisionnaire
    decision_maker_name: str = ""
    decision_maker_title: str = ""
    decision_maker_email: str = ""
    decision_maker_linkedin: str = ""
    decision_maker_phone: str = ""
    
    # Scoring
    hunt_score: float = 0.0         # 0-100, score global
    conversion_probability: float = 0.0  # 0-1
    urgency_score: float = 0.0      # 0-10
    
    # Offre générée
    offer_title: str = ""
    offer_description: str = ""
    offer_price: float = 0.0
    offer_roi_ratio: float = 0.0    # ROI pour le client
    
    # Timestamps
    detected_at: float = field(default_factory=time.time)
    qualified_at: Optional[float] = None
    contacted_at: Optional[float] = None
    converted_at: Optional[float] = None
    
    @property
    def age_hours(self) -> float:
        return (time.time() - self.detected_at) / 3600
    
    def compute_hunt_score(self) -> float:
        """Score composite 0-100."""
        severity_w = {
            PainSeverity.CRITICAL: 1.0, PainSeverity.HIGH: 0.75,
            PainSeverity.MEDIUM: 0.5, PainSeverity.LATENT: 0.25
        }
        s = severity_w.get(self.pain_severity, 0.5)
        
        financial = min(self.pain_financial_impact / 500000, 1.0)
        discrete_bonus = 0.15 if self.pain_is_discrete else 0.0
        urgency = min(self.urgency_score / 10, 1.0)
        signal_quality = min(len(self.pain_signals) / 5, 1.0)
        
        self.hunt_score = round((
            s * 30 +
            financial * 25 +
            urgency * 20 +
            signal_quality * 10 +
            discrete_bonus * 100 * 0.15
        ), 2)
        return self.hunt_score
    
    def classify(self) -> HuntCategory:
        """Classe automatiquement selon les critères NAYA."""
        if (self.pain_severity in (PainSeverity.CRITICAL, PainSeverity.HIGH)
                and self.estimated_deal_value >= 10000
                and self.estimated_deal_value <= 150000
                and self.estimated_delivery_days <= 7):
            self.hunt_category = HuntCategory.CASH_RAPIDE
        elif (self.estimated_deal_value > 150000
              or self.estimated_delivery_days > 7 and self.estimated_delivery_days <= 30):
            self.hunt_category = HuntCategory.MOYEN_TERME
        else:
            self.hunt_category = HuntCategory.LONG_TERME
        return self.hunt_category
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "target": {
                "name": self.target_name, "type": self.target_type.value,
                "sector": self.target_sector, "country": self.target_country,
                "city": self.target_city, "size": self.target_size,
                "revenue_estimate": self.target_revenue_estimate,
            },
            "pain": {
                "description": self.pain_description,
                "severity": self.pain_severity.value,
                "category": self.pain_category,
                "financial_impact": self.pain_financial_impact,
                "is_discrete": self.pain_is_discrete,
                "signals_count": len(self.pain_signals),
            },
            "classification": {
                "category": self.hunt_category.value,
                "deal_value": self.estimated_deal_value,
                "delivery_days": self.estimated_delivery_days,
                "confidentiality": self.confidentiality.value,
            },
            "decision_maker": {
                "name": self.decision_maker_name,
                "title": self.decision_maker_title,
                "has_email": bool(self.decision_maker_email),
                "has_linkedin": bool(self.decision_maker_linkedin),
            },
            "scoring": {
                "hunt_score": self.hunt_score,
                "conversion_probability": self.conversion_probability,
                "urgency": self.urgency_score,
            },
            "offer": {
                "title": self.offer_title,
                "price": self.offer_price,
                "roi_ratio": self.offer_roi_ratio,
            },
            "detected_at": datetime.fromtimestamp(self.detected_at).isoformat(),
            "age_hours": round(self.age_hours, 1),
        }


# ══════════════════════════════════════════════════════════════════════════════
# API CONNECTORS — Sources réelles
# ══════════════════════════════════════════════════════════════════════════════

class LinkedInHunter:
    """Chasse via LinkedIn Sales Navigator API / RapidAPI."""
    
    def __init__(self):
        self.api_key = _gs("LINKEDIN_API_KEY")
        self.rapid_api_key = _gs("RAPIDAPI_KEY")
        self.base_url = "https://linkedin-api8.p.rapidapi.com"
    
    def hunt_pain_signals(self, sector: str, country: str = "FR",
                          keywords: List[str] = None) -> List[PainSignal]:
        """Détecte les signaux de douleur via LinkedIn."""
        signals = []
        if not self.rapid_api_key:
            log.debug("[LinkedIn] API key manquante — skip")
            return signals
        
        try:
            import requests
            # Recherche de postes ouverts = signal de douleur organisationnelle
            pain_keywords = keywords or [
                "urgent hiring", "restructuration", "transformation digitale",
                "cost reduction", "compliance officer", "interim manager",
                "crisis management", "turnaround", "dette technique",
            ]
            
            for kw in pain_keywords[:5]:  # Limiter les appels API
                headers = {
                    "X-RapidAPI-Key": self.rapid_api_key,
                    "X-RapidAPI-Host": "linkedin-api8.p.rapidapi.com",
                }
                params = {
                    "keywords": kw,
                    "locationId": "105015875" if country == "FR" else "",
                    "datePosted": "pastWeek",
                }
                
                resp = requests.get(
                    f"{self.base_url}/search-jobs",
                    headers=headers, params=params, timeout=15
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    for job in data.get("data", [])[:10]:
                        sig = PainSignal(
                            source=SignalSource.LINKEDIN,
                            raw_data=job,
                            keywords=[kw, job.get("title", "")],
                            confidence=self._score_job_signal(job, kw),
                        )
                        signals.append(sig)
                
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            log.warning(f"[LinkedIn] Erreur chasse: {e}")
        
        return signals
    
    def _score_job_signal(self, job: Dict, keyword: str) -> float:
        """Score la pertinence d'un signal LinkedIn."""
        score = 0.3
        title = job.get("title", "").lower()
        
        urgency_words = ["urgent", "asap", "immédiat", "interim", "crise"]
        pain_words = ["restructuration", "transformation", "compliance", "dette", "turnover"]
        
        for w in urgency_words:
            if w in title: score += 0.15
        for w in pain_words:
            if w in title: score += 0.1
        
        return min(score, 1.0)
    
    def enrich_company(self, company_url: str) -> Dict:
        """Enrichit les données d'une entreprise via LinkedIn."""
        if not self.rapid_api_key:
            return {}
        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/get-company-details",
                headers={
                    "X-RapidAPI-Key": self.rapid_api_key,
                    "X-RapidAPI-Host": "linkedin-api8.p.rapidapi.com",
                },
                params={"username": company_url},
                timeout=15,
            )
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            log.debug(f"[LinkedIn] Enrich error: {e}")
            return {}


class CrunchbaseHunter:
    """Chasse via Crunchbase API — levées, pivots, layoffs."""
    
    def __init__(self):
        self.api_key = _gs("CRUNCHBASE_API_KEY")
        self.base_url = "https://api.crunchbase.com/api/v4"
    
    def hunt_pain_signals(self, sector: str = "", country: str = "FR") -> List[PainSignal]:
        """Détecte signaux de douleur structurelle via Crunchbase."""
        signals = []
        if not self.api_key:
            log.debug("[Crunchbase] API key manquante — skip")
            return signals
        
        try:
            import requests
            
            # Recherche d'entreprises avec signaux de stress
            pain_queries = [
                {"field_ids": ["identifier", "short_description", "num_employees_enum",
                               "last_funding_type", "funding_total"],
                 "query": [
                     {"type": "predicate", "field_id": "location_identifiers",
                      "operator_id": "includes", "values": [country.lower()]},
                     {"type": "predicate", "field_id": "last_funding_type",
                      "operator_id": "includes",
                      "values": ["series_unknown", "debt_financing", "convertible_note"]},
                 ],
                 "limit": 25},
            ]
            
            for query in pain_queries:
                resp = requests.post(
                    f"{self.base_url}/searches/organizations",
                    headers={"X-cb-user-key": self.api_key},
                    json=query, timeout=20,
                )
                if resp.status_code == 200:
                    for entity in resp.json().get("entities", []):
                        props = entity.get("properties", {})
                        sig = PainSignal(
                            source=SignalSource.CRUNCHBASE,
                            raw_data=props,
                            keywords=[
                                props.get("short_description", ""),
                                props.get("last_funding_type", ""),
                            ],
                            confidence=self._score_crunchbase_signal(props),
                        )
                        signals.append(sig)
                
                time.sleep(0.5)
                
        except Exception as e:
            log.warning(f"[Crunchbase] Erreur: {e}")
        
        return signals
    
    def _score_crunchbase_signal(self, props: Dict) -> float:
        score = 0.4
        funding_type = props.get("last_funding_type", "")
        if funding_type in ("debt_financing", "convertible_note"):
            score += 0.2  # Stress financier
        if props.get("num_employees_enum", "") in ("c_0011_0050", "c_0051_0100"):
            score += 0.1  # Taille PME = plus sensible
        return min(score, 1.0)


class ApolloHunter:
    """Enrichissement et recherche de contacts via Apollo.io."""
    
    def __init__(self):
        self.api_key = _gs("APOLLO_API_KEY")
        self.base_url = "https://api.apollo.io/v1"
    
    def find_decision_makers(self, company_name: str, domain: str = "") -> List[Dict]:
        """Trouve les décisionnaires d'une entreprise."""
        if not self.api_key:
            return []
        try:
            import requests
            resp = requests.post(
                f"{self.base_url}/mixed_people/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": self.api_key,
                    "q_organization_name": company_name,
                    "person_seniorities": ["c_suite", "vp", "director", "owner"],
                    "page": 1, "per_page": 5,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("people", [])
        except Exception as e:
            log.debug(f"[Apollo] Erreur: {e}")
        return []
    
    def enrich_email(self, email: str) -> Dict:
        """Enrichit un contact par email."""
        if not self.api_key:
            return {}
        try:
            import requests
            resp = requests.post(
                f"{self.base_url}/people/match",
                json={"api_key": self.api_key, "email": email},
                timeout=10,
            )
            return resp.json().get("person", {}) if resp.status_code == 200 else {}
        except Exception:
            return {}


class PappersHunter:
    """Chasse via Pappers API — bilans, défaillances, tribunaux de commerce."""
    
    def __init__(self):
        self.api_key = _gs("PAPPERS_API_KEY")
        self.base_url = "https://api.pappers.fr/v2"
    
    def hunt_distressed_companies(self, sector_code: str = "",
                                   departement: str = "") -> List[PainSignal]:
        """Détecte entreprises en difficulté via données légales."""
        signals = []
        if not self.api_key:
            log.debug("[Pappers] API key manquante — skip")
            return signals
        
        try:
            import requests
            
            # Entreprises avec procédures collectives récentes
            params = {
                "api_token": self.api_key,
                "statut_rcs": "procédure collective",
                "par_page": 20,
            }
            if departement:
                params["departement"] = departement
            if sector_code:
                params["code_naf"] = sector_code
            
            resp = requests.get(
                f"{self.base_url}/recherche",
                params=params, timeout=15,
            )
            
            if resp.status_code == 200:
                for ent in resp.json().get("resultats", []):
                    sig = PainSignal(
                        source=SignalSource.PAPPERS,
                        raw_data=ent,
                        keywords=[
                            ent.get("nom_entreprise", ""),
                            ent.get("objet_social", ""),
                            "procédure collective",
                        ],
                        confidence=0.85,  # Données légales = fiable
                    )
                    signals.append(sig)
            
            # Entreprises avec baisse de CA significative
            params2 = {
                "api_token": self.api_key,
                "par_page": 20,
                "chiffre_affaires_min": 500000,
                "chiffre_affaires_max": 50000000,
            }
            if departement:
                params2["departement"] = departement
            
            resp2 = requests.get(
                f"{self.base_url}/recherche",
                params=params2, timeout=15,
            )
            
            if resp2.status_code == 200:
                for ent in resp2.json().get("resultats", []):
                    finances = ent.get("finances", {})
                    if finances:
                        # Détecter baisse de CA
                        last_ca = finances.get("chiffre_affaires")
                        if last_ca and last_ca > 0:
                            sig = PainSignal(
                                source=SignalSource.PAPPERS,
                                raw_data=ent,
                                keywords=[
                                    ent.get("nom_entreprise", ""),
                                    "baisse_ca", ent.get("code_naf", ""),
                                ],
                                confidence=0.7,
                            )
                            signals.append(sig)
            
        except Exception as e:
            log.warning(f"[Pappers] Erreur: {e}")
        
        return signals


class GoogleNewsHunter:
    """Chasse via Google News / SERP API — alertes sectorielles."""
    
    def __init__(self):
        self.api_key = _gs("SERP_API_KEY")  # SerpAPI ou similaire
    
    def hunt_pain_signals(self, queries: List[str] = None) -> List[PainSignal]:
        """Détecte signaux de douleur via actualités."""
        signals = []
        if not self.api_key:
            log.debug("[GoogleNews] API key manquante — skip")
            return signals
        
        default_queries = [
            "entreprise en difficulté France",
            "restructuration entreprise",
            "pénurie compétences secteur",
            "dette technique transformation digitale",
            "conformité RGPD amende",
            "cybersécurité brèche données entreprise",
            "supply chain rupture approvisionnement",
        ]
        
        queries = queries or default_queries
        
        try:
            import requests
            for q in queries[:5]:
                resp = requests.get(
                    "https://serpapi.com/search",
                    params={
                        "engine": "google_news",
                        "q": q,
                        "gl": "fr",
                        "hl": "fr",
                        "api_key": self.api_key,
                    },
                    timeout=15,
                )
                
                if resp.status_code == 200:
                    for article in resp.json().get("news_results", [])[:5]:
                        sig = PainSignal(
                            source=SignalSource.GOOGLE_NEWS,
                            raw_data=article,
                            keywords=[
                                q, article.get("title", ""),
                                article.get("source", {}).get("name", ""),
                            ],
                            confidence=self._score_news(article, q),
                        )
                        signals.append(sig)
                
                time.sleep(1)
                
        except Exception as e:
            log.warning(f"[GoogleNews] Erreur: {e}")
        
        return signals
    
    def _score_news(self, article: Dict, query: str) -> float:
        title = article.get("title", "").lower()
        score = 0.3
        urgency = ["urgent", "crise", "faillite", "licenciement", "amende", "brèche"]
        for w in urgency:
            if w in title: score += 0.15
        return min(score, 1.0)


class HunterIOConnector:
    """Vérification d'emails via Hunter.io."""
    
    def __init__(self):
        self.api_key = _gs("HUNTER_IO_API_KEY")
    
    def verify_email(self, email: str) -> Dict:
        if not self.api_key:
            return {"status": "unknown"}
        try:
            import requests
            resp = requests.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": self.api_key},
                timeout=10,
            )
            return resp.json().get("data", {}) if resp.status_code == 200 else {}
        except Exception:
            return {}
    
    def find_emails(self, domain: str) -> List[Dict]:
        if not self.api_key:
            return []
        try:
            import requests
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": self.api_key, "limit": 5},
                timeout=10,
            )
            return resp.json().get("data", {}).get("emails", []) if resp.status_code == 200 else []
        except Exception:
            return []


# ══════════════════════════════════════════════════════════════════════════════
# QUALIFICATION ENGINE — Transforme signaux bruts en douleurs qualifiées
# ══════════════════════════════════════════════════════════════════════════════

class PainQualifier:
    """Qualifie et classifie les signaux bruts en douleurs actionnables."""
    
    # Mapping secteur → catégorie de douleur → valeur estimée
    SECTOR_PAIN_VALUES = {
        "tech_saas": {
            "churn": (80000, 7, HuntCategory.CASH_RAPIDE),
            "dette_technique": (250000, 30, HuntCategory.MOYEN_TERME),
            "scaling": (500000, 90, HuntCategory.LONG_TERME),
        },
        "finance_banque": {
            "compliance": (150000, 5, HuntCategory.CASH_RAPIDE),
            "cybersecurity": (300000, 14, HuntCategory.MOYEN_TERME),
            "legacy_migration": (1000000, 180, HuntCategory.LONG_TERME),
        },
        "industrie": {
            "supply_chain": (100000, 7, HuntCategory.CASH_RAPIDE),
            "maintenance_predictive": (200000, 30, HuntCategory.MOYEN_TERME),
            "industrie_4_0": (800000, 120, HuntCategory.LONG_TERME),
        },
        "sante": {
            "rgpd_donnees": (50000, 3, HuntCategory.CASH_RAPIDE),
            "burnout_rh": (120000, 30, HuntCategory.MOYEN_TERME),
            "transformation_digitale": (400000, 90, HuntCategory.LONG_TERME),
        },
        "gouvernement_admin": {
            "conformite_reglementaire": (80000, 7, HuntCategory.CASH_RAPIDE),
            "modernisation_si": (500000, 60, HuntCategory.MOYEN_TERME),
            "smart_city": (2000000, 365, HuntCategory.LONG_TERME),
        },
        "energie_infra": {
            "audit_energetique": (60000, 5, HuntCategory.CASH_RAPIDE),
            "transition_energetique": (400000, 60, HuntCategory.MOYEN_TERME),
            "smart_grid": (1500000, 365, HuntCategory.LONG_TERME),
        },
        "pme_b2b": {
            "tresorerie": (30000, 3, HuntCategory.CASH_RAPIDE),
            "processus_manuels": (80000, 14, HuntCategory.MOYEN_TERME),
            "croissance": (200000, 90, HuntCategory.LONG_TERME),
        },
    }
    
    # Signaux de douleur par mot-clé → catégorie
    KEYWORD_PAIN_MAP = {
        "restructuration": ("rh_organisation", PainSeverity.CRITICAL, 0.8),
        "licenciement": ("rh_organisation", PainSeverity.CRITICAL, 0.9),
        "interim manager": ("rh_organisation", PainSeverity.HIGH, 0.7),
        "conformité": ("compliance", PainSeverity.HIGH, 0.75),
        "rgpd": ("compliance", PainSeverity.HIGH, 0.8),
        "cybersécurité": ("securite", PainSeverity.CRITICAL, 0.85),
        "brèche": ("securite", PainSeverity.CRITICAL, 0.9),
        "dette technique": ("tech", PainSeverity.HIGH, 0.7),
        "transformation digitale": ("tech", PainSeverity.MEDIUM, 0.6),
        "pénurie": ("talent", PainSeverity.HIGH, 0.7),
        "turnover": ("rh_organisation", PainSeverity.HIGH, 0.75),
        "trésorerie": ("finance", PainSeverity.CRITICAL, 0.85),
        "impayés": ("finance", PainSeverity.CRITICAL, 0.9),
        "procédure collective": ("finance", PainSeverity.CRITICAL, 0.95),
        "supply chain": ("operations", PainSeverity.HIGH, 0.7),
        "rupture": ("operations", PainSeverity.HIGH, 0.75),
    }
    
    def qualify(self, signals: List[PainSignal],
                sector: str = "pme_b2b") -> List[HuntedPain]:
        """Transforme des signaux bruts en douleurs qualifiées."""
        pains: List[HuntedPain] = []
        
        # Grouper par entreprise/source
        grouped: Dict[str, List[PainSignal]] = {}
        for sig in signals:
            company = self._extract_company(sig)
            if company:
                grouped.setdefault(company, []).append(sig)
        
        for company, sigs in grouped.items():
            pain = self._build_pain(company, sigs, sector)
            if pain and pain.hunt_score > 30:  # Seuil minimum
                pains.append(pain)
        
        # Tri par score décroissant
        pains.sort(key=lambda p: p.hunt_score, reverse=True)
        return pains
    
    def _extract_company(self, signal: PainSignal) -> str:
        """Extrait le nom de l'entreprise d'un signal."""
        raw = signal.raw_data
        for key in ("company", "company_name", "nom_entreprise", "organization_name",
                     "name", "title"):
            if key in raw and raw[key]:
                return str(raw[key])[:100]
        # Fallback sur keywords
        if signal.keywords:
            return signal.keywords[0][:100]
        return ""
    
    def _build_pain(self, company: str, signals: List[PainSignal],
                    sector: str) -> Optional[HuntedPain]:
        """Construit une HuntedPain à partir de signaux groupés."""
        if not signals:
            return None
        
        # Déterminer la catégorie de douleur dominante
        categories = []
        severities = []
        for sig in signals:
            for kw in sig.keywords:
                kw_lower = kw.lower()
                for pain_kw, (cat, sev, conf) in self.KEYWORD_PAIN_MAP.items():
                    if pain_kw in kw_lower:
                        categories.append(cat)
                        severities.append(sev)
        
        pain_cat = max(set(categories), key=categories.count) if categories else "general"
        severity = min(severities) if severities else PainSeverity.MEDIUM
        
        # Valeur estimée
        sector_vals = self.SECTOR_PAIN_VALUES.get(sector, self.SECTOR_PAIN_VALUES["pme_b2b"])
        val_info = sector_vals.get(pain_cat, (50000, 14, HuntCategory.MOYEN_TERME))
        est_value, est_days, cat = val_info
        
        pain = HuntedPain(
            target_name=company,
            target_type=self._detect_target_type(company, signals),
            target_sector=sector,
            pain_description=f"Douleur [{pain_cat}] détectée via {len(signals)} signaux",
            pain_severity=severity,
            pain_category=pain_cat,
            pain_financial_impact=est_value * 1.5,  # Impact > valeur deal
            pain_is_discrete=self._is_discrete(signals),
            pain_signals=signals,
            hunt_category=cat,
            estimated_deal_value=est_value,
            estimated_delivery_days=est_days,
            confidentiality=self._determine_confidentiality(signals),
            urgency_score=self._compute_urgency(severity, signals),
        )
        
        pain.compute_hunt_score()
        pain.classify()
        pain.conversion_probability = min(pain.hunt_score / 100 * 0.8, 0.85)
        
        return pain
    
    def _detect_target_type(self, company: str, signals: List[PainSignal]) -> TargetType:
        company_lower = company.lower()
        gov_words = ["ministère", "mairie", "préfecture", "agence nationale",
                     "dgfip", "cnam", "urssaf", "administration"]
        infra_words = ["edf", "sncf", "engie", "orange", "bouygues", "vinci",
                       "airbus", "thales", "safran"]
        
        for w in gov_words:
            if w in company_lower: return TargetType.GOUVERNEMENTAL
        for w in infra_words:
            if w in company_lower: return TargetType.INFRASTRUCTURE
        
        # Check sources
        for sig in signals:
            if sig.source == SignalSource.DATA_GOUV:
                return TargetType.B2A
        
        return TargetType.B2B
    
    def _is_discrete(self, signals: List[PainSignal]) -> bool:
        """Douleur discrète = pas verbalisée publiquement."""
        public_sources = {SignalSource.GOOGLE_NEWS}
        public_count = sum(1 for s in signals if s.source in public_sources)
        return public_count < len(signals) * 0.5
    
    def _determine_confidentiality(self, signals: List[PainSignal]) -> ConfidentialityLevel:
        for sig in signals:
            if sig.source in (SignalSource.PAPPERS, SignalSource.TRIBUNAL_COM):
                return ConfidentialityLevel.STEALTH  # Données sensibles
        return ConfidentialityLevel.DISCRETE
    
    def _compute_urgency(self, severity: PainSeverity,
                          signals: List[PainSignal]) -> float:
        base = {
            PainSeverity.CRITICAL: 8.0, PainSeverity.HIGH: 6.0,
            PainSeverity.MEDIUM: 4.0, PainSeverity.LATENT: 2.0,
        }.get(severity, 4.0)
        
        # Bonus si signaux récents (< 48h)
        recent = sum(1 for s in signals if time.time() - s.detected_at < 172800)
        return min(base + recent * 0.5, 10.0)


# ══════════════════════════════════════════════════════════════════════════════
# OFFER BUILDER — Construit l'offre irrésistible
# ══════════════════════════════════════════════════════════════════════════════

class PainOfferBuilder:
    """Construit des offres irrésistibles basées sur la douleur détectée."""
    
    OFFER_TEMPLATES = {
        "compliance": {
            "title": "Mise en conformité {category} — Résultat garanti en {days}j",
            "description": "Audit + correction + certification en mode express. "
                          "Votre exposition financière de {impact}€ éliminée.",
            "roi_multiplier": 3.0,
        },
        "finance": {
            "title": "Récupération trésorerie — {value}€ identifiés en {days}j",
            "description": "Audit créances + recouvrement + optimisation cash-flow. "
                          "Résultat mesurable dès J3.",
            "roi_multiplier": 5.0,
        },
        "rh_organisation": {
            "title": "Stabilisation RH — Plan d'action en {days}j",
            "description": "Diagnostic turnover + plan rétention + exécution. "
                          "Coût actuel: {impact}€/an de pertes évitables.",
            "roi_multiplier": 2.5,
        },
        "tech": {
            "title": "Dette technique résolue — Sprint {days}j",
            "description": "Audit code/infra + remediation + documentation. "
                          "Risque actuel: {impact}€ de pertes potentielles.",
            "roi_multiplier": 2.0,
        },
        "securite": {
            "title": "Blindage sécurité — Protection en {days}j",
            "description": "Audit vulnérabilités + correction + monitoring. "
                          "Exposition actuelle: {impact}€.",
            "roi_multiplier": 4.0,
        },
        "operations": {
            "title": "Optimisation opérationnelle — ROI en {days}j",
            "description": "Audit processus + automatisation + suivi KPI. "
                          "Économies identifiées: {impact}€/an.",
            "roi_multiplier": 2.5,
        },
        "general": {
            "title": "Solution sur mesure — Livraison en {days}j",
            "description": "Diagnostic + solution + exécution. "
                          "Impact financier actuel: {impact}€.",
            "roi_multiplier": 2.0,
        },
    }
    
    def build_offer(self, pain: HuntedPain) -> HuntedPain:
        """Construit et attache l'offre à la douleur."""
        template = self.OFFER_TEMPLATES.get(
            pain.pain_category,
            self.OFFER_TEMPLATES["general"]
        )
        
        pain.offer_title = template["title"].format(
            category=pain.pain_category.replace("_", " ").title(),
            days=pain.estimated_delivery_days,
            value=f"{pain.estimated_deal_value:,.0f}",
            impact=f"{pain.pain_financial_impact:,.0f}",
        )
        
        pain.offer_description = template["description"].format(
            impact=f"{pain.pain_financial_impact:,.0f}",
            days=pain.estimated_delivery_days,
            value=f"{pain.estimated_deal_value:,.0f}",
        )
        
        # Prix = basé sur la douleur, pas sur le coût
        # Le prix doit être < impact financier mais > coût de production
        pain.offer_price = round(pain.pain_financial_impact * 0.3, -2)  # 30% de l'impact
        pain.offer_price = max(pain.offer_price, 5000)  # Minimum 5k€
        pain.offer_price = min(pain.offer_price, 150000)  # Cap selon catégorie
        
        if pain.hunt_category == HuntCategory.MOYEN_TERME:
            pain.offer_price = min(pain.offer_price * 2, 500000)
        elif pain.hunt_category == HuntCategory.LONG_TERME:
            pain.offer_price = min(pain.offer_price * 4, 2000000)
        
        pain.offer_roi_ratio = template["roi_multiplier"]
        
        return pain


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE — Orchestration complète
# ══════════════════════════════════════════════════════════════════════════════

class PainHunterB2B:
    """
    Agent principal de chasse de douleurs B2B/B2A/Gouvernemental.
    Intégré nativement dans NAYA SUPREME.
    """
    VERSION = "1.0.0"
    
    # Secteurs de chasse par défaut
    DEFAULT_HUNT_SECTORS = [
        "tech_saas", "finance_banque", "industrie", "sante",
        "gouvernement_admin", "energie_infra", "pme_b2b",
    ]
    
    # Départements français prioritaires (gros bassin économique)
    PRIORITY_DEPARTMENTS = ["75", "92", "69", "13", "31", "33", "44", "59", "67"]
    
    def __init__(self):
        # API Connectors
        self._linkedin = LinkedInHunter()
        self._crunchbase = CrunchbaseHunter()
        self._apollo = ApolloHunter()
        self._pappers = PappersHunter()
        self._news = GoogleNewsHunter()
        self._hunter_io = HunterIOConnector()
        
        # Processing
        self._qualifier = PainQualifier()
        self._offer_builder = PainOfferBuilder()
        
        # State
        self._hunted_pains: List[HuntedPain] = []
        self._cycle_count = 0
        self._total_detected = 0
        self._total_value_detected = 0.0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # NAYA integrations (set externally)
        self._db = None
        self._cash_engine = None
        self._discretion = None
        self._notifier = None
        self._event_stream = None
        
        log.info("[PainHunterB2B] Initialisé — V%s", self.VERSION)
    
    # ── NAYA Integration Setters ────────────────────────────────────────────
    
    def set_database(self, db):
        self._db = db
    
    def set_cash_engine(self, engine):
        self._cash_engine = engine
    
    def set_discretion(self, protocol):
        self._discretion = protocol
    
    def set_notifier(self, notifier):
        self._notifier = notifier
    
    def set_event_stream(self, stream):
        self._event_stream = stream
    
    # ── Core Hunt Cycle ─────────────────────────────────────────────────────
    
    def hunt_cycle(self, sectors: List[str] = None,
                   country: str = "FR") -> Dict:
        """
        Exécute un cycle complet de chasse.
        1. Collecte signaux depuis toutes les sources
        2. Qualifie et classifie
        3. Construit les offres
        4. Enrichit contacts décisionnaires
        5. Persiste + injecte dans le pipeline NAYA
        """
        cycle_id = f"HUNT_{uuid.uuid4().hex[:8].upper()}"
        self._cycle_count += 1
        sectors = sectors or self.DEFAULT_HUNT_SECTORS
        
        log.info(f"[{cycle_id}] Cycle de chasse #{self._cycle_count} — {len(sectors)} secteurs")
        
        result = {
            "cycle_id": cycle_id,
            "cycle_number": self._cycle_count,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "sectors_scanned": len(sectors),
            "signals_collected": 0,
            "pains_qualified": 0,
            "offers_built": 0,
            "by_category": {
                HuntCategory.CASH_RAPIDE.value: [],
                HuntCategory.MOYEN_TERME.value: [],
                HuntCategory.LONG_TERME.value: [],
            },
            "total_pipeline_value": 0.0,
            "errors": [],
        }
        
        all_signals: List[PainSignal] = []
        
        # ── Phase 1: Collecte multi-source ──────────────────────────────
        for sector in sectors:
            try:
                # LinkedIn
                sigs = self._linkedin.hunt_pain_signals(sector, country)
                all_signals.extend(sigs)
                
                # Crunchbase
                sigs = self._crunchbase.hunt_pain_signals(sector, country)
                all_signals.extend(sigs)
                
                # Pappers (FR uniquement)
                if country == "FR":
                    sigs = self._pappers.hunt_distressed_companies()
                    all_signals.extend(sigs)
                
            except Exception as e:
                result["errors"].append(f"Sector {sector}: {e}")
        
        # Google News (cross-secteur)
        try:
            sigs = self._news.hunt_pain_signals()
            all_signals.extend(sigs)
        except Exception as e:
            result["errors"].append(f"GoogleNews: {e}")
        
        result["signals_collected"] = len(all_signals)
        log.info(f"[{cycle_id}] {len(all_signals)} signaux collectés")
        
        # ── Phase 2: Qualification ──────────────────────────────────────
        qualified_pains = []
        for sector in sectors:
            sector_signals = [s for s in all_signals]  # Tous les signaux pour qualification
            pains = self._qualifier.qualify(sector_signals, sector)
            qualified_pains.extend(pains)
        
        # Déduplication par nom d'entreprise
        seen = set()
        unique_pains = []
        for p in qualified_pains:
            key = p.target_name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique_pains.append(p)
        
        result["pains_qualified"] = len(unique_pains)
        log.info(f"[{cycle_id}] {len(unique_pains)} douleurs qualifiées")
        
        # ── Phase 3: Offres + Enrichissement ────────────────────────────
        for pain in unique_pains:
            # Construire l'offre
            self._offer_builder.build_offer(pain)
            
            # Enrichir le contact décisionnaire
            self._enrich_decision_maker(pain)
            
            # Classifier dans la bonne catégorie
            cat = pain.hunt_category.value
            result["by_category"][cat].append(pain.to_dict())
            result["total_pipeline_value"] += pain.offer_price
            
            # Persister
            self._persist_pain(pain)
            
            # Injecter dans le cash engine NAYA
            self._inject_to_naya(pain)
            
            # Stream event
            self._stream_event("PAIN_DETECTED", {
                "pain_id": pain.id,
                "target": pain.target_name,
                "category": cat,
                "value": pain.offer_price,
                "score": pain.hunt_score,
            })
        
        result["offers_built"] = len(unique_pains)
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Stats globales
        self._total_detected += len(unique_pains)
        self._total_value_detected += result["total_pipeline_value"]
        
        with self._lock:
            self._hunted_pains.extend(unique_pains)
            # Garder les 500 dernières
            if len(self._hunted_pains) > 500:
                self._hunted_pains = self._hunted_pains[-500:]
        
        log.info(
            f"[{cycle_id}] Terminé — "
            f"CASH_RAPIDE: {len(result['by_category']['cash_rapide'])}, "
            f"MOYEN_TERME: {len(result['by_category']['moyen_terme'])}, "
            f"LONG_TERME: {len(result['by_category']['long_terme'])} | "
            f"Pipeline: {result['total_pipeline_value']:,.0f}€"
        )
        
        return result
    
    def _enrich_decision_maker(self, pain: HuntedPain):
        """Enrichit le contact décisionnaire via Apollo + Hunter.io."""
        try:
            # Apollo: trouver décisionnaires
            contacts = self._apollo.find_decision_makers(pain.target_name)
            if contacts:
                top = contacts[0]
                pain.decision_maker_name = f"{top.get('first_name', '')} {top.get('last_name', '')}"
                pain.decision_maker_title = top.get("title", "")
                pain.decision_maker_email = top.get("email", "")
                pain.decision_maker_linkedin = top.get("linkedin_url", "")
                pain.decision_maker_phone = top.get("phone_numbers", [{}])[0].get("sanitized_number", "") if top.get("phone_numbers") else ""
                
                # Vérifier l'email via Hunter.io
                if pain.decision_maker_email:
                    verification = self._hunter_io.verify_email(pain.decision_maker_email)
                    if verification.get("status") == "invalid":
                        pain.decision_maker_email = ""  # Email invalide
            
        except Exception as e:
            log.debug(f"[Enrich] {pain.target_name}: {e}")
    
    def _persist_pain(self, pain: HuntedPain):
        """Sauvegarde en base NAYA."""
        if not self._db:
            return
        try:
            data = pain.to_dict()
            # Masquer si mode discret
            if self._discretion:
                data = self._discretion.mask(data)
            
            self._db.log_event(
                event_type="PAIN_HUNTED",
                payload=data,
                source="HUNTING_AGENTS.pain_hunter_b2b",
                priority="HIGH" if pain.hunt_category == HuntCategory.CASH_RAPIDE else "NORMAL",
            )
        except Exception as e:
            log.debug(f"[Persist] Erreur: {e}")
    
    def _inject_to_naya(self, pain: HuntedPain):
        """Injecte la douleur dans le cash engine NAYA pour conversion."""
        if not self._cash_engine:
            return
        try:
            if hasattr(self._cash_engine, "inject_from_hunt"):
                deal_data = {
                    "top_pain": {
                        "category": pain.pain_category,
                        "description": pain.pain_description,
                        "financial_impact": pain.pain_financial_impact,
                        "severity": pain.pain_severity.value,
                    },
                    "offer": {
                        "title": pain.offer_title,
                        "delivery_hours": pain.estimated_delivery_days * 24,
                        "price": pain.offer_price,
                        "roi": pain.offer_roi_ratio,
                    },
                    "contact": {
                        "company": pain.target_name,
                        "name": pain.decision_maker_name,
                        "email": pain.decision_maker_email,
                        "title": pain.decision_maker_title,
                    },
                    "hunt_score": pain.hunt_score,
                    "category": pain.hunt_category.value,
                }
                self._cash_engine.inject_from_hunt(deal_data, pain.target_sector)
        except Exception as e:
            log.debug(f"[Inject] Erreur: {e}")
    
    def _stream_event(self, event_type: str, data: Dict):
        """Envoie un événement vers TORI/Event Stream."""
        if self._event_stream and hasattr(self._event_stream, "broadcast"):
            try:
                self._event_stream.broadcast({
                    "type": event_type,
                    "source": "PAIN_HUNTER_B2B",
                    "data": data,
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
    
    # ── Autonomous Mode ─────────────────────────────────────────────────────
    
    def start_autonomous(self, interval_seconds: int = 3600):
        """Lance la chasse autonome en boucle."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._autonomous_loop,
            args=(interval_seconds,),
            daemon=True, name="PainHunterB2B-Auto",
        )
        self._thread.start()
        log.info(f"[PainHunterB2B] Mode autonome démarré — cycle toutes les {interval_seconds}s")
    
    def stop_autonomous(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        log.info("[PainHunterB2B] Mode autonome arrêté")
    
    def _autonomous_loop(self, interval: int):
        while self._running:
            try:
                self.hunt_cycle()
            except Exception as e:
                log.error(f"[PainHunterB2B] Erreur cycle autonome: {e}")
            time.sleep(interval)
    
    # ── Query Methods ────────────────────────────────────────────────────────
    
    def get_cash_rapide(self) -> List[Dict]:
        """Retourne les opportunités CASH RAPIDE (24h-7j)."""
        with self._lock:
            return [p.to_dict() for p in self._hunted_pains
                    if p.hunt_category == HuntCategory.CASH_RAPIDE]
    
    def get_moyen_terme(self) -> List[Dict]:
        with self._lock:
            return [p.to_dict() for p in self._hunted_pains
                    if p.hunt_category == HuntCategory.MOYEN_TERME]
    
    def get_long_terme(self) -> List[Dict]:
        with self._lock:
            return [p.to_dict() for p in self._hunted_pains
                    if p.hunt_category == HuntCategory.LONG_TERME]
    
    def get_top_opportunities(self, n: int = 10) -> List[Dict]:
        """Top N opportunités par score."""
        with self._lock:
            sorted_pains = sorted(self._hunted_pains,
                                   key=lambda p: p.hunt_score, reverse=True)
            return [p.to_dict() for p in sorted_pains[:n]]
    
    def get_stats(self) -> Dict:
        with self._lock:
            cats = {c.value: 0 for c in HuntCategory}
            for p in self._hunted_pains:
                cats[p.hunt_category.value] += 1
            
            return {
                "version": self.VERSION,
                "total_cycles": self._cycle_count,
                "total_detected": self._total_detected,
                "total_pipeline_value": self._total_value_detected,
                "active_pains": len(self._hunted_pains),
                "by_category": cats,
                "autonomous_running": self._running,
                "apis_configured": {
                    "linkedin": bool(self._linkedin.rapid_api_key),
                    "crunchbase": bool(self._crunchbase.api_key),
                    "apollo": bool(self._apollo.api_key),
                    "pappers": bool(self._pappers.api_key),
                    "google_news": bool(self._news.api_key),
                    "hunter_io": bool(self._hunter_io.api_key),
                },
            }
    
    def to_dict(self) -> Dict:
        return self.get_stats()
