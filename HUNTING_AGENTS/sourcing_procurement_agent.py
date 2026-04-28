"""
NAYA SUPREME — SOURCING & PROCUREMENT AGENT
══════════════════════════════════════════════════════════════════════════════════
Agent autonome de sourcing, négociation, commande et logistique.

PROJETS ACTIFS:
  P03 — NAYA BOTANICA : Cosmétiques naturels (curcuma, plantes)
         → Fournisseurs matières premières, packaging, labs certifiés
  P04 — TINY HOUSE : Maisons pliables/modulaires 20m² énergie renouvelable
         → Usines directes (Chine, Turquie, Asie SE), certifications CE/ISO
  ALL — Tout futur business créé par NAYA

CYCLE COMPLET:
  1. SEARCH    — Trouver fournisseurs/usines via APIs réelles
  2. EVALUATE  — Scoring qualité/prix/certification/fiabilité
  3. NEGOTIATE — Stratégies de négociation automatisées
  4. SAMPLE    — Demander échantillons, tracker livraison
  5. ORDER     — Passer commande, gérer paiement
  6. SHIP      — Expédition, douanes, tracking
  7. DELIVER   — Livraison finale + montage (Tiny House)

SOURCES RÉELLES:
  - Alibaba Open Platform API (usines directes Chine)
  - Made-in-China (alternative Alibaba)
  - Global Sources (fournisseurs vérifiés)
  - IndiaMART (matières premières cosmétiques)
  - Europages (fournisseurs EU certifiés)
  - Google Search via Serper (recherche générale)
  - 1688.com (prix usine Chine, via proxy)

INTÉGRATION NAYA:
  → NAYA_CORE.scheduler (cycles recherche automatiques)
  → PERSISTENCE (stockage fournisseurs, commandes)
  → BUSINESS_ENGINES.supplier_intelligence_engine (scoring)
  → BUSINESS_ENGINES.discretion_protocol (négociation discrète)
  → NAYA_REVENUE_ENGINE (marge tracking)
══════════════════════════════════════════════════════════════════════════════════
"""

import os, time, uuid, json, logging, threading, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.AGENT.SOURCING")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class ProjectType(Enum):
    BOTANICA    = "botanica"        # Cosmétiques naturels
    TINY_HOUSE  = "tiny_house"      # Maisons modulaires
    GENERIC     = "generic"         # Tout futur projet

class SupplierSource(Enum):
    ALIBABA       = "alibaba"
    MADE_IN_CHINA = "made_in_china"
    GLOBAL_SOURCES = "global_sources"
    INDIAMART     = "indiamart"
    EUROPAGES     = "europages"
    GOOGLE_SEARCH = "google_search"
    DIRECT_CONTACT = "direct_contact"
    ONESEIGHT_COM = "1688_com"      # Prix usine Chine

class CertificationType(Enum):
    CE       = "CE"
    ISO_9001 = "ISO 9001"
    ISO_14001 = "ISO 14001"
    GMP      = "GMP"           # Cosmétiques
    FDA      = "FDA"
    CPSR     = "CPSR"          # EU cosmetics safety
    REACH    = "REACH"
    SGS      = "SGS"
    BV       = "Bureau Veritas"
    TUV      = "TUV"
    ORGANIC  = "Organic/Bio"
    HALAL    = "Halal"
    FAIR_TRADE = "Fair Trade"

class OrderStatus(Enum):
    SEARCHING     = "searching"
    CONTACTED     = "contacted"
    SAMPLE_REQUESTED = "sample_requested"
    SAMPLE_RECEIVED  = "sample_received"
    SAMPLE_APPROVED  = "sample_approved"
    NEGOTIATING   = "negotiating"
    ORDERED       = "ordered"
    PRODUCING     = "producing"
    SHIPPED       = "shipped"
    IN_CUSTOMS    = "in_customs"
    DELIVERED     = "delivered"
    ASSEMBLED     = "assembled"    # Tiny House montage
    COMPLETED     = "completed"
    CANCELLED     = "cancelled"

class ShippingMethod(Enum):
    SEA_FREIGHT   = "sea_freight"      # 25-45 jours
    AIR_FREIGHT   = "air_freight"      # 5-10 jours
    EXPRESS       = "express"          # 3-5 jours (DHL, FedEx)
    RAIL          = "rail"             # 18-25 jours (EU-Chine)
    LOCAL_TRUCK   = "local_truck"


# ══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SupplierContact:
    """Contact chez un fournisseur."""
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    wechat: str = ""
    language: str = "en"

@dataclass
class FoundSupplier:
    """Fournisseur trouvé et évalué."""
    id: str = field(default_factory=lambda: f"SUP_{uuid.uuid4().hex[:8].upper()}")
    
    # Identité
    name: str = ""
    company_name: str = ""
    source: SupplierSource = SupplierSource.ALIBABA
    url: str = ""
    country: str = ""
    city: str = ""
    
    # Contact
    contact: Optional[SupplierContact] = None
    
    # Produits
    project_type: ProjectType = ProjectType.GENERIC
    product_categories: List[str] = field(default_factory=list)
    product_description: str = ""
    
    # Prix
    unit_price_min: float = 0.0
    unit_price_max: float = 0.0
    currency: str = "USD"
    moq: int = 1                  # Minimum Order Quantity
    sample_price: float = 0.0
    sample_shipping: float = 0.0
    
    # Qualité & Certifications
    certifications: List[CertificationType] = field(default_factory=list)
    years_in_business: int = 0
    verified: bool = False         # Vérifié par la plateforme
    trade_assurance: bool = False  # Protection acheteur
    
    # Logistique
    production_time_days: int = 0
    shipping_methods: List[ShippingMethod] = field(default_factory=list)
    ships_to_destination: bool = False  # Important pour toi
    
    # Scoring
    quality_score: float = 0.0     # 0-100
    price_score: float = 0.0       # 0-100 (100=très bon marché)
    reliability_score: float = 0.0 # 0-100
    certification_score: float = 0.0
    overall_score: float = 0.0
    
    # Négociation
    negotiation_notes: str = ""
    best_negotiated_price: float = 0.0
    discount_obtained: float = 0.0  # %
    
    detected_at: float = field(default_factory=time.time)
    
    def compute_scores(self) -> float:
        # Prix: inverse — moins cher = meilleur score
        if self.unit_price_max > 0:
            self.price_score = max(0, min(100, 100 - (self.unit_price_min / self.unit_price_max * 50)))
        
        # Certifications
        cert_weight = min(len(self.certifications) / 3, 1.0) * 100
        self.certification_score = cert_weight
        
        # Fiabilité
        base_rel = 50
        if self.verified: base_rel += 15
        if self.trade_assurance: base_rel += 15
        if self.years_in_business > 5: base_rel += 10
        elif self.years_in_business > 2: base_rel += 5
        self.reliability_score = min(base_rel, 100)
        
        self.overall_score = round(
            self.quality_score * 0.25 +
            self.price_score * 0.30 +
            self.reliability_score * 0.25 +
            self.certification_score * 0.20,
            2
        )
        return self.overall_score
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "company": self.company_name,
            "source": self.source.value, "url": self.url,
            "country": self.country, "city": self.city,
            "project": self.project_type.value,
            "products": self.product_categories,
            "pricing": {
                "unit_min": self.unit_price_min, "unit_max": self.unit_price_max,
                "currency": self.currency, "moq": self.moq,
                "sample_price": self.sample_price,
            },
            "certifications": [c.value for c in self.certifications],
            "verified": self.verified, "trade_assurance": self.trade_assurance,
            "years": self.years_in_business,
            "logistics": {
                "production_days": self.production_time_days,
                "shipping": [s.value for s in self.shipping_methods],
                "ships_to_destination": self.ships_to_destination,
            },
            "scoring": {
                "quality": self.quality_score, "price": self.price_score,
                "reliability": self.reliability_score,
                "certification": self.certification_score,
                "overall": self.overall_score,
            },
            "negotiation": {
                "best_price": self.best_negotiated_price,
                "discount_pct": self.discount_obtained,
            },
        }


@dataclass
class SampleRequest:
    """Demande d'échantillon."""
    id: str = field(default_factory=lambda: f"SAMP_{uuid.uuid4().hex[:6].upper()}")
    supplier_id: str = ""
    supplier_name: str = ""
    project_type: ProjectType = ProjectType.GENERIC
    products: List[str] = field(default_factory=list)
    quantity: int = 1
    price: float = 0.0
    shipping_cost: float = 0.0
    status: OrderStatus = OrderStatus.SAMPLE_REQUESTED
    tracking_number: str = ""
    ship_to: str = "Polynésie française"
    requested_at: float = field(default_factory=time.time)
    received_at: Optional[float] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "supplier": self.supplier_name,
            "project": self.project_type.value, "products": self.products,
            "price": self.price, "shipping": self.shipping_cost,
            "status": self.status.value, "tracking": self.tracking_number,
            "ship_to": self.ship_to,
        }


@dataclass
class ProcurementOrder:
    """Commande d'achat complète."""
    id: str = field(default_factory=lambda: f"ORD_{uuid.uuid4().hex[:8].upper()}")
    supplier_id: str = ""
    supplier_name: str = ""
    project_type: ProjectType = ProjectType.GENERIC
    
    # Produits
    items: List[Dict] = field(default_factory=list)
    total_units: int = 0
    
    # Prix
    unit_price: float = 0.0
    total_price: float = 0.0
    currency: str = "USD"
    payment_method: str = ""        # Trade Assurance, PayPal, Wire, LC
    payment_terms: str = ""         # 30/70, 50/50, etc.
    
    # Logistique
    shipping_method: ShippingMethod = ShippingMethod.SEA_FREIGHT
    shipping_cost: float = 0.0
    incoterm: str = "FOB"           # FOB, CIF, DDP
    estimated_production_end: str = ""
    estimated_delivery: str = ""
    tracking_numbers: List[str] = field(default_factory=list)
    
    # Douanes & Taxes
    customs_duties_estimate: float = 0.0
    import_taxes_estimate: float = 0.0
    customs_broker: str = ""
    hs_code: str = ""               # Code douanier
    
    # Montage (Tiny House)
    assembly_needed: bool = False
    assembly_cost: float = 0.0
    assembly_time_days: int = 0
    
    # Status
    status: OrderStatus = OrderStatus.ORDERED
    created_at: float = field(default_factory=time.time)
    
    @property
    def total_landed_cost(self) -> float:
        """Coût total rendu destination."""
        return (self.total_price + self.shipping_cost +
                self.customs_duties_estimate + self.import_taxes_estimate +
                self.assembly_cost)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "supplier": self.supplier_name,
            "project": self.project_type.value,
            "items": self.items, "units": self.total_units,
            "pricing": {
                "unit_price": self.unit_price, "total": self.total_price,
                "shipping": self.shipping_cost,
                "customs": self.customs_duties_estimate,
                "taxes": self.import_taxes_estimate,
                "assembly": self.assembly_cost,
                "total_landed": self.total_landed_cost,
            },
            "logistics": {
                "method": self.shipping_method.value,
                "incoterm": self.incoterm,
                "production_end": self.estimated_production_end,
                "delivery": self.estimated_delivery,
                "tracking": self.tracking_numbers,
            },
            "status": self.status.value,
        }


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT SPECIFICATIONS — Ce qu'on cherche exactement
# ══════════════════════════════════════════════════════════════════════════════

BOTANICA_SPECS = {
    "project": ProjectType.BOTANICA,
    "name": "NAYA Botanica — Cosmétiques naturels",
    "categories": [
        {
            "name": "Curcuma en poudre cosmétique grade",
            "search_queries": [
                "turmeric powder cosmetic grade bulk",
                "curcumin extract skin whitening ingredient",
                "organic turmeric powder for skincare",
            ],
            "specs": {
                "grade": "cosmetic/pharmaceutical",
                "purity": ">95% curcumin",
                "certifications_required": [CertificationType.GMP, CertificationType.ORGANIC],
                "packaging": "1kg-25kg bags",
            },
            "moq_target": 10,  # kg
            "budget_per_kg": (15, 45),  # USD
        },
        {
            "name": "Huile de coco vierge bio (Monoï base)",
            "search_queries": [
                "virgin coconut oil organic cosmetic grade bulk",
                "cold pressed coconut oil skincare ingredient",
            ],
            "specs": {
                "grade": "cosmetic/food grade",
                "extraction": "cold pressed",
                "certifications_required": [CertificationType.ORGANIC, CertificationType.GMP],
            },
            "moq_target": 20,  # litres
            "budget_per_unit": (5, 15),
        },
        {
            "name": "Beurre de karité non raffiné",
            "search_queries": [
                "unrefined shea butter bulk cosmetic grade",
                "raw shea butter organic wholesale",
            ],
            "specs": {"grade": "cosmetic grade A", "origin": "West Africa preferred"},
            "moq_target": 10,
            "budget_per_kg": (8, 25),
        },
        {
            "name": "Packaging cosmétique (pots, flacons, étiquettes)",
            "search_queries": [
                "cosmetic packaging jars bottles wholesale",
                "skincare packaging bamboo eco-friendly",
                "custom label printing cosmetic",
            ],
            "specs": {"material": "glass/bamboo preferred, recyclable"},
            "moq_target": 100,
            "budget_per_unit": (0.5, 3),
        },
        {
            "name": "Laboratoire cosmétique sous-traitance",
            "search_queries": [
                "private label skincare manufacturer",
                "cosmetic contract manufacturer turmeric products",
                "OEM skincare factory small batch",
            ],
            "specs": {"batch_min": "100-500 units", "certifications": "GMP, ISO 22716"},
            "moq_target": 100,
            "budget_per_unit": (3, 15),
        },
    ],
}

TINY_HOUSE_SPECS = {
    "project": ProjectType.TINY_HOUSE,
    "name": "NAYA Tiny House — Maison pliable modulaire 20m²",
    "models": [
        {
            "name": "Modèle Personnel #1 — Famille",
            "description": "20m² pliable, 1 cuisine, 1 salon, 1 douche+WC, "
                          "1 chambre principale avec WC+douche, 1 chambre enfant",
            "search_queries": [
                "foldable container house 20sqm fully furnished",
                "expandable prefab house 20m2 with bathroom kitchen",
                "modular tiny house solar panel off-grid",
                "prefabricated folding house 2 bedroom complete",
            ],
            "specs": {
                "surface": "20m² déplié minimum",
                "rooms": "2 chambres, 1 salon, 1 cuisine, 2 SDB",
                "type": "pliable/expandable container",
                "energy": "panneaux solaires + batterie",
                "water": "réservoir + pompe",
                "insulation": "mousse PU ou laine de roche",
                "structure": "acier galvanisé + sandwich panel",
                "certifications_required": [
                    CertificationType.CE, CertificationType.ISO_9001,
                ],
                "climate": "tropical (Polynésie française)",
                "wind_resistance": "typhon-rated si possible",
            },
            "moq_target": 1,
            "budget_range": (8000, 25000),  # USD par unité
            "for_personal_use": True,
        },
        {
            "name": "Modèle Personnel #2 — Compact",
            "description": "20m² variante compacte, même aménagement, design différent",
            "search_queries": [
                "folding house 20sqm 2 bedroom modern design",
                "expandable container home tropical climate",
                "portable modular house 20m2 complete bathroom",
            ],
            "specs": {
                "surface": "20m² minimum",
                "same_layout": True,
                "design": "différent du modèle #1",
            },
            "moq_target": 1,
            "budget_range": (8000, 25000),
            "for_personal_use": True,
        },
    ],
    "accessories": [
        {
            "name": "Kit solaire off-grid",
            "search_queries": [
                "solar panel kit off grid 3kw complete system",
                "solar power system tiny house battery inverter",
            ],
            "budget_range": (1500, 5000),
        },
        {
            "name": "Système eau autonome",
            "search_queries": [
                "water tank pump filter system tiny house",
                "rainwater collection system prefab house",
            ],
            "budget_range": (500, 2000),
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# API CONNECTORS — Sources de fournisseurs réelles
# ══════════════════════════════════════════════════════════════════════════════

class AlibabaSearcher:
    """Recherche fournisseurs via Alibaba Open Platform / scraping Serper."""
    
    def __init__(self):
        self.app_key = _gs("ALIBABA_APP_KEY")
        self.serper_key = _gs("SERPER_API_KEY") or _gs("SERPER_API_KEY_1")
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche produits/fournisseurs sur Alibaba."""
        results = []
        
        # Méthode 1: Alibaba API (si clé dispo)
        if self.app_key:
            results = self._search_api(query, max_results)
        
        # Méthode 2: Via Serper Google Search (fallback fiable)
        if not results and self.serper_key:
            results = self._search_via_serper(query, max_results)
        
        return results
    
    def _search_api(self, query: str, max_results: int) -> List[Dict]:
        """Alibaba Open Platform API."""
        try:
            import requests
            resp = requests.get(
                "https://openapi.alibaba.com/product/search",
                params={
                    "app_key": self.app_key,
                    "keywords": query,
                    "page_size": max_results,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("products", data.get("result", []))
        except Exception as e:
            log.debug(f"[Alibaba API] {e}")
        return []
    
    def _search_via_serper(self, query: str, max_results: int) -> List[Dict]:
        """Recherche Alibaba via Google (Serper API)."""
        results = []
        try:
            import requests
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
                json={"q": f"site:alibaba.com {query}", "num": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                for r in resp.json().get("organic", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                        "source": "alibaba_via_serper",
                    })
        except Exception as e:
            log.debug(f"[Alibaba Serper] {e}")
        return results


class MadeInChinaSearcher:
    """Recherche sur Made-in-China.com."""
    
    def __init__(self):
        self.serper_key = _gs("SERPER_API_KEY") or _gs("SERPER_API_KEY_1")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        if not self.serper_key:
            return []
        try:
            import requests
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
                json={"q": f"site:made-in-china.com {query}", "num": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                return [{"title": r.get("title"), "url": r.get("link"),
                         "snippet": r.get("snippet"), "source": "made_in_china"}
                        for r in resp.json().get("organic", [])]
        except Exception as e:
            log.debug(f"[MadeInChina] {e}")
        return []


class GlobalSourceSearcher:
    """Recherche sur GlobalSources, Europages, IndiaMART via Serper."""
    
    def __init__(self):
        self.serper_key = _gs("SERPER_API_KEY") or _gs("SERPER_API_KEY_1")
    
    def search(self, query: str, platforms: List[str] = None) -> List[Dict]:
        if not self.serper_key:
            return []
        
        platforms = platforms or [
            "globalsources.com", "europages.com", "indiamart.com",
        ]
        all_results = []
        
        try:
            import requests
            for platform in platforms:
                resp = requests.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
                    json={"q": f"site:{platform} {query}", "num": 5},
                    timeout=15,
                )
                if resp.status_code == 200:
                    for r in resp.json().get("organic", []):
                        all_results.append({
                            "title": r.get("title"), "url": r.get("link"),
                            "snippet": r.get("snippet"), "source": platform,
                        })
                time.sleep(0.5)
        except Exception as e:
            log.debug(f"[GlobalSearch] {e}")
        
        return all_results


class DirectFactorySearcher:
    """Recherche directe d'usines via Google (prix usine, wholesale)."""
    
    def __init__(self):
        self.serper_key = _gs("SERPER_API_KEY") or _gs("SERPER_API_KEY_1")
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        if not self.serper_key:
            return []
        try:
            import requests
            enhanced_query = f"{query} factory direct manufacturer wholesale price"
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
                json={"q": enhanced_query, "num": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                return [{"title": r.get("title"), "url": r.get("link"),
                         "snippet": r.get("snippet"), "source": "direct_factory"}
                        for r in resp.json().get("organic", [])]
        except Exception as e:
            log.debug(f"[DirectFactory] {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# RESULT PARSER — Transforme résultats bruts en FoundSupplier
# ══════════════════════════════════════════════════════════════════════════════

class SupplierParser:
    """Parse les résultats de recherche en FoundSupplier structurés."""
    
    COUNTRY_INDICATORS = {
        "china": "CN", "chinese": "CN", "shenzhen": "CN", "guangzhou": "CN",
        "yiwu": "CN", "shanghai": "CN", "foshan": "CN", "hebei": "CN",
        "turkey": "TR", "istanbul": "TR", "turkish": "TR",
        "india": "IN", "indian": "IN", "mumbai": "IN", "delhi": "IN",
        "vietnam": "VN", "thai": "TH", "thailand": "TH",
        "europe": "EU", "germany": "DE", "france": "FR", "italy": "IT",
        "poland": "PL", "spain": "ES",
    }
    
    CERTIFICATION_KEYWORDS = {
        "ce": CertificationType.CE, "iso 9001": CertificationType.ISO_9001,
        "iso 14001": CertificationType.ISO_14001, "gmp": CertificationType.GMP,
        "fda": CertificationType.FDA, "sgs": CertificationType.SGS,
        "bv": CertificationType.BV, "tuv": CertificationType.TUV,
        "organic": CertificationType.ORGANIC, "bio": CertificationType.ORGANIC,
        "halal": CertificationType.HALAL,
    }
    
    def parse(self, raw_result: Dict, project_type: ProjectType,
              category_name: str = "") -> FoundSupplier:
        """Parse un résultat brut en FoundSupplier."""
        title = raw_result.get("title", "")
        snippet = raw_result.get("snippet", "")
        url = raw_result.get("url", "")
        source_str = raw_result.get("source", "")
        text = f"{title} {snippet}".lower()
        
        supplier = FoundSupplier(
            name=self._extract_company_name(title, url),
            company_name=self._extract_company_name(title, url),
            source=self._detect_source(source_str, url),
            url=url,
            country=self._detect_country(text),
            project_type=project_type,
            product_categories=[category_name] if category_name else [],
            product_description=snippet[:300],
            certifications=self._detect_certifications(text),
            verified="verified" in text or "gold supplier" in text,
            trade_assurance="trade assurance" in text,
        )
        
        # Extraire prix si mentionné
        prices = self._extract_prices(text)
        if prices:
            supplier.unit_price_min = prices[0]
            supplier.unit_price_max = prices[-1] if len(prices) > 1 else prices[0] * 1.5
        
        # Extraire MOQ
        moq = self._extract_moq(text)
        if moq:
            supplier.moq = moq
        
        # Extraire années d'expérience
        years = self._extract_years(text)
        if years:
            supplier.years_in_business = years
        
        supplier.compute_scores()
        return supplier
    
    def _extract_company_name(self, title: str, url: str) -> str:
        # Essayer d'extraire le nom de la company du titre
        parts = title.split(" - ")
        if len(parts) > 1:
            return parts[-1].strip()[:80]
        parts = title.split(" | ")
        if len(parts) > 1:
            return parts[0].strip()[:80]
        return title[:80]
    
    def _detect_source(self, source_str: str, url: str) -> SupplierSource:
        url_lower = url.lower()
        if "alibaba.com" in url_lower: return SupplierSource.ALIBABA
        if "made-in-china" in url_lower: return SupplierSource.MADE_IN_CHINA
        if "globalsources" in url_lower: return SupplierSource.GLOBAL_SOURCES
        if "indiamart" in url_lower: return SupplierSource.INDIAMART
        if "europages" in url_lower: return SupplierSource.EUROPAGES
        return SupplierSource.GOOGLE_SEARCH
    
    def _detect_country(self, text: str) -> str:
        for indicator, code in self.COUNTRY_INDICATORS.items():
            if indicator in text:
                return code
        return ""
    
    def _detect_certifications(self, text: str) -> List[CertificationType]:
        found = []
        for kw, cert in self.CERTIFICATION_KEYWORDS.items():
            if kw in text and cert not in found:
                found.append(cert)
        return found
    
    def _extract_prices(self, text: str) -> List[float]:
        """Extrait les prix d'un texte."""
        import re
        prices = []
        # Patterns: $500, USD 500, 500.00, €500
        for match in re.finditer(r'[\$€]?\s*(\d{1,7}(?:\.\d{1,2})?)\s*(?:usd|eur|€|\$|/unit|/piece|/set)?', text):
            try:
                p = float(match.group(1))
                if 0.1 < p < 1_000_000:
                    prices.append(p)
            except ValueError:
                pass
        return sorted(set(prices))[:5]
    
    def _extract_moq(self, text: str) -> Optional[int]:
        import re
        m = re.search(r'moq[:\s]*(\d+)', text)
        if m: return int(m.group(1))
        m = re.search(r'min(?:imum)?\s*(?:order)?[:\s]*(\d+)', text)
        if m: return int(m.group(1))
        return None
    
    def _extract_years(self, text: str) -> Optional[int]:
        import re
        m = re.search(r'(\d{1,2})\s*(?:years?|ans?|yrs?)\s*(?:experience|in business|supplier)', text)
        if m: return int(m.group(1))
        return None


# ══════════════════════════════════════════════════════════════════════════════
# NEGOTIATION ENGINE — Stratégies de négociation automatisées
# ══════════════════════════════════════════════════════════════════════════════

class NegotiationEngine:
    """Génère des stratégies de négociation optimales."""
    
    def generate_strategy(self, supplier: FoundSupplier, 
                          target_price: float = 0,
                          order_volume: int = 1) -> Dict:
        """Génère une stratégie de négociation."""
        strategy = {
            "supplier": supplier.name,
            "current_price": supplier.unit_price_min,
            "target_price": target_price or supplier.unit_price_min * 0.7,  # -30%
            "tactics": [],
            "email_templates": [],
            "leverage_points": [],
        }
        
        # Tactiques basées sur le contexte
        if order_volume > supplier.moq * 2:
            strategy["tactics"].append(
                "Volume leverage: commander plus que le MOQ pour obtenir -15-25%"
            )
            strategy["leverage_points"].append(f"Volume: {order_volume} unités vs MOQ {supplier.moq}")
        
        if supplier.country == "CN":
            strategy["tactics"].extend([
                "Demander le prix FOB (sans shipping) pour comparer",
                "Mentionner des devis concurrents (même si inventés)",
                "Proposer un paiement rapide (T/T 100% advance) pour -5-10%",
                "Demander échantillon gratuit si commande confirmée",
                "Négocier le packaging/étiquetage inclus dans le prix",
            ])
        
        if supplier.trade_assurance:
            strategy["leverage_points"].append(
                "Trade Assurance = protection acheteur, le fournisseur est motivé"
            )
        
        # Templates email
        strategy["email_templates"] = self._generate_emails(supplier, target_price, order_volume)
        
        return strategy
    
    def _generate_emails(self, supplier: FoundSupplier, 
                          target_price: float, volume: int) -> List[Dict]:
        """Génère des templates d'emails de négociation."""
        return [
            {
                "stage": "first_contact",
                "subject": f"Bulk Order Inquiry — {supplier.product_categories[0] if supplier.product_categories else 'Products'}",
                "body": (
                    f"Dear {supplier.name} team,\n\n"
                    f"We are NAYA Intelligence, a business development company. "
                    f"We are interested in placing a regular order for your products.\n\n"
                    f"Could you please provide:\n"
                    f"1. Your best FOB price for {volume}+ units\n"
                    f"2. Available certifications (CE, ISO, GMP)\n"
                    f"3. Production lead time\n"
                    f"4. Shipping options to your destination\n"
                    f"5. Free sample availability\n\n"
                    f"We plan to establish a long-term partnership with the right supplier.\n\n"
                    f"Best regards,\nNAYA Procurement"
                ),
            },
            {
                "stage": "price_negotiation",
                "subject": "Re: Price Discussion — Can We Find a Better Deal?",
                "body": (
                    f"Thank you for the quotation.\n\n"
                    f"We have received competitive offers from other suppliers at "
                    f"${target_price:.2f}/unit. We prefer to work with you based on "
                    f"your quality and certifications, but we need the price to be "
                    f"competitive.\n\n"
                    f"Can you match or come close to ${target_price:.2f}?\n"
                    f"We are ready to commit to {volume} units immediately "
                    f"with repeat orders every quarter.\n\n"
                    f"Best regards,\nNAYA Procurement"
                ),
            },
            {
                "stage": "sample_request",
                "subject": "Sample Request — Ready to Order After Testing",
                "body": (
                    f"We would like to order samples before placing our bulk order.\n\n"
                    f"Please send:\n"
                    f"- 1-2 samples of each product variant\n"
                    f"- Certificate copies (CE, ISO, GMP)\n"
                    f"- Shipping to: [YOUR_ADDRESS]\n\n"
                    f"We will cover sample + shipping cost via PayPal.\n"
                    f"If samples are satisfactory, we will place the full order within 7 days.\n\n"
                    f"Best regards,\nNAYA Procurement"
                ),
            },
        ]


# ══════════════════════════════════════════════════════════════════════════════
# SHIPPING CALCULATOR — Estimation coûts logistiques
# ══════════════════════════════════════════════════════════════════════════════

class ShippingCalculator:
    """Estime les coûts d'expédition vers la Polynésie française."""
    
    # Tarifs approximatifs par méthode (USD)
    # Ces tarifs servent d'estimation — le vrai prix vient du transitaire
    RATES = {
        ShippingMethod.SEA_FREIGHT: {
            "base_per_cbm": 150,     # USD par m³
            "min_charge": 500,
            "transit_days": (35, 55),  # Chine → Polynésie
        },
        ShippingMethod.AIR_FREIGHT: {
            "base_per_kg": 8,
            "min_charge": 200,
            "transit_days": (5, 10),
        },
        ShippingMethod.EXPRESS: {
            "base_per_kg": 25,       # DHL/FedEx
            "min_charge": 80,
            "transit_days": (3, 7),
        },
    }
    
    # Droits de douane Polynésie française (approximatifs)
    CUSTOMS_RATES = {
        "cosmetics": 0.05,           # 5%
        "raw_materials": 0.03,       # 3%
        "prefab_house": 0.08,        # 8%
        "solar_equipment": 0.02,     # 2% (souvent exonéré)
        "general": 0.10,             # 10%
    }
    
    # TVA Polynésie (TLP)
    TVA_RATE = 0.05  # 5% en PF (pas 20% comme en métropole)
    
    def estimate(self, weight_kg: float, volume_cbm: float,
                 method: ShippingMethod, product_category: str = "general",
                 origin_country: str = "CN") -> Dict:
        """Estime le coût total d'expédition + douanes."""
        rate = self.RATES.get(method, self.RATES[ShippingMethod.SEA_FREIGHT])
        
        if method == ShippingMethod.SEA_FREIGHT:
            shipping = max(volume_cbm * rate["base_per_cbm"], rate["min_charge"])
        elif method in (ShippingMethod.AIR_FREIGHT, ShippingMethod.EXPRESS):
            # Poids volumétrique vs réel
            vol_weight = volume_cbm * 167  # kg volumétriques
            chargeable = max(weight_kg, vol_weight)
            shipping = max(chargeable * rate["base_per_kg"], rate["min_charge"])
        else:
            shipping = rate.get("min_charge", 200)
        
        customs_rate = self.CUSTOMS_RATES.get(product_category, self.CUSTOMS_RATES["general"])
        
        transit_min, transit_max = rate.get("transit_days", (7, 30))
        
        return {
            "shipping_cost_usd": round(shipping, 2),
            "customs_rate": customs_rate,
            "tva_rate": self.TVA_RATE,
            "transit_days": {"min": transit_min, "max": transit_max},
            "method": method.value,
            "origin": origin_country,
            "destination": "[your region]",
            "notes": "Tarifs estimatifs — devis transitaire recommandé pour confirmation",
        }
    
    def estimate_tiny_house(self, units: int = 1) -> Dict:
        """Estimation spécifique Tiny House 20m²."""
        # Container 20' pliable ≈ 2.5 CBM plié, ~3500 kg
        weight = 3500 * units
        volume = 2.5 * units  # Plié dans un container
        
        sea = self.estimate(weight, volume, ShippingMethod.SEA_FREIGHT, "prefab_house")
        
        return {
            **sea,
            "units": units,
            "weight_kg": weight,
            "volume_cbm": volume,
            "assembly_note": "Montage local nécessaire — 2-5 jours par unité",
            "assembly_cost_estimate": 1500 * units,  # USD
            "crane_needed": True,
            "foundation_note": "Plots béton ou vis de fondation recommandés",
        }
    
    def estimate_botanica_samples(self) -> Dict:
        """Estimation expédition échantillons cosmétiques."""
        return self.estimate(
            weight_kg=5, volume_cbm=0.02,
            method=ShippingMethod.EXPRESS,
            product_category="cosmetics",
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class SourcingProcurementAgent:
    """
    Agent complet de sourcing et procurement.
    Cherche, évalue, négocie, commande et suit les livraisons.
    """
    VERSION = "1.0.0"
    
    def __init__(self):
        # Searchers
        self._alibaba = AlibabaSearcher()
        self._made_in_china = MadeInChinaSearcher()
        self._global_search = GlobalSourceSearcher()
        self._direct_factory = DirectFactorySearcher()
        
        # Processing
        self._parser = SupplierParser()
        self._negotiator = NegotiationEngine()
        self._shipping = ShippingCalculator()
        
        # State
        self._suppliers: Dict[str, List[FoundSupplier]] = {
            ProjectType.BOTANICA.value: [],
            ProjectType.TINY_HOUSE.value: [],
            ProjectType.GENERIC.value: [],
        }
        self._samples: List[SampleRequest] = []
        self._orders: List[ProcurementOrder] = []
        self._cycle_count = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # NAYA integrations
        self._db = None
        self._discretion = None
        self._event_stream = None
        
        log.info("[SourcingAgent] Initialisé — V%s", self.VERSION)
    
    def set_database(self, db): self._db = db
    def set_discretion(self, protocol): self._discretion = protocol
    def set_event_stream(self, stream): self._event_stream = stream
    
    # ── SEARCH CYCLES ────────────────────────────────────────────────────────
    
    def search_botanica_suppliers(self) -> Dict:
        """Recherche complète de fournisseurs pour NAYA Botanica."""
        return self._search_for_project(BOTANICA_SPECS)
    
    def search_tiny_house_suppliers(self) -> Dict:
        """Recherche complète de fournisseurs pour Tiny House."""
        return self._search_for_project(TINY_HOUSE_SPECS)
    
    def search_for_project(self, project_name: str, 
                           search_queries: List[str],
                           budget_range: Tuple[float, float] = (0, 100000)) -> Dict:
        """Recherche générique pour tout nouveau projet NAYA."""
        specs = {
            "project": ProjectType.GENERIC,
            "name": project_name,
            "categories": [{
                "name": project_name,
                "search_queries": search_queries,
                "specs": {},
                "moq_target": 1,
                "budget_per_unit": budget_range,
            }],
        }
        return self._search_for_project(specs)
    
    def _search_for_project(self, specs: Dict) -> Dict:
        """Recherche fournisseurs pour un projet donné."""
        cycle_id = f"SRC_{uuid.uuid4().hex[:6].upper()}"
        self._cycle_count += 1
        project_type = specs["project"]
        project_key = project_type.value if isinstance(project_type, ProjectType) else str(project_type)
        
        log.info(f"[{cycle_id}] Recherche fournisseurs: {specs['name']}")
        
        result = {
            "cycle_id": cycle_id,
            "project": specs["name"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "categories_searched": 0,
            "suppliers_found": 0,
            "top_suppliers": [],
            "shipping_estimates": {},
        }
        
        all_suppliers = []
        
        # Chercher pour chaque catégorie de produit
        categories = specs.get("categories", specs.get("models", []))
        for category in categories:
            cat_name = category.get("name", "")
            queries = category.get("search_queries", [])
            
            for query in queries[:3]:  # Max 3 queries par catégorie
                # Alibaba
                raw = self._alibaba.search(query, 5)
                for r in raw:
                    sup = self._parser.parse(r, project_type, cat_name)
                    all_suppliers.append(sup)
                
                # Made-in-China
                raw = self._made_in_china.search(query, 3)
                for r in raw:
                    sup = self._parser.parse(r, project_type, cat_name)
                    all_suppliers.append(sup)
                
                # GlobalSources + Europages + IndiaMART
                platforms = ["globalsources.com", "europages.com"]
                if project_type == ProjectType.BOTANICA:
                    platforms.append("indiamart.com")
                raw = self._global_search.search(query, platforms)
                for r in raw:
                    sup = self._parser.parse(r, project_type, cat_name)
                    all_suppliers.append(sup)
                
                # Direct Factory
                raw = self._direct_factory.search(query, 3)
                for r in raw:
                    sup = self._parser.parse(r, project_type, cat_name)
                    all_suppliers.append(sup)
                
                time.sleep(0.3)
            
            result["categories_searched"] += 1
        
        # Accessories (Tiny House)
        for acc in specs.get("accessories", []):
            for q in acc.get("search_queries", [])[:2]:
                raw = self._alibaba.search(q, 3)
                for r in raw:
                    sup = self._parser.parse(r, project_type, acc.get("name", ""))
                    all_suppliers.append(sup)
        
        # Déduplication par URL
        seen_urls = set()
        unique_suppliers = []
        for s in all_suppliers:
            if s.url and s.url not in seen_urls:
                seen_urls.add(s.url)
                s.compute_scores()
                unique_suppliers.append(s)
        
        # Tri par score
        unique_suppliers.sort(key=lambda s: s.overall_score, reverse=True)
        
        # Stocker
        with self._lock:
            self._suppliers[project_key] = unique_suppliers
        
        result["suppliers_found"] = len(unique_suppliers)
        result["top_suppliers"] = [s.to_dict() for s in unique_suppliers[:10]]
        
        # Estimations shipping
        if project_type == ProjectType.TINY_HOUSE or project_key == "tiny_house":
            result["shipping_estimates"]["tiny_house"] = self._shipping.estimate_tiny_house()
        if project_type == ProjectType.BOTANICA or project_key == "botanica":
            result["shipping_estimates"]["samples"] = self._shipping.estimate_botanica_samples()
        
        # Persist
        self._persist(f"SOURCING_{project_key.upper()}", result)
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        log.info(f"[{cycle_id}] {result['suppliers_found']} fournisseurs trouvés")
        
        return result
    
    # ── SAMPLE MANAGEMENT ────────────────────────────────────────────────────
    
    def request_sample(self, supplier_id: str, project_type: str,
                       products: List[str], ship_to: str = "Polynésie française") -> Dict:
        """Crée une demande d'échantillon."""
        # Trouver le fournisseur
        supplier = self._find_supplier(supplier_id)
        if not supplier:
            return {"error": f"Fournisseur {supplier_id} non trouvé"}
        
        sample = SampleRequest(
            supplier_id=supplier_id,
            supplier_name=supplier.name,
            project_type=ProjectType(project_type) if project_type in [p.value for p in ProjectType] else ProjectType.GENERIC,
            products=products,
            price=supplier.sample_price,
            shipping_cost=supplier.sample_shipping,
            ship_to=ship_to,
        )
        
        with self._lock:
            self._samples.append(sample)
        
        # Générer l'email de demande
        negotiation = self._negotiator.generate_strategy(supplier)
        sample_email = next(
            (e for e in negotiation.get("email_templates", []) if e["stage"] == "sample_request"),
            None
        )
        
        self._persist("SAMPLE_REQUEST", sample.to_dict())
        
        return {
            "sample_id": sample.id,
            "supplier": supplier.name,
            "status": sample.status.value,
            "email_template": sample_email,
            "shipping_estimate": self._shipping.estimate(
                5, 0.02, ShippingMethod.EXPRESS,
                "cosmetics" if project_type == "botanica" else "general",
            ),
        }
    
    def update_sample_status(self, sample_id: str, status: str,
                              tracking: str = "") -> Dict:
        """Met à jour le statut d'un échantillon."""
        with self._lock:
            for s in self._samples:
                if s.id == sample_id:
                    s.status = OrderStatus(status)
                    if tracking:
                        s.tracking_number = tracking
                    if status == "sample_received":
                        s.received_at = time.time()
                    return s.to_dict()
        return {"error": "Sample non trouvé"}
    
    # ── NEGOTIATION ──────────────────────────────────────────────────────────
    
    def get_negotiation_strategy(self, supplier_id: str,
                                  target_price: float = 0,
                                  order_volume: int = 1) -> Dict:
        """Génère une stratégie de négociation pour un fournisseur."""
        supplier = self._find_supplier(supplier_id)
        if not supplier:
            return {"error": "Fournisseur non trouvé"}
        return self._negotiator.generate_strategy(supplier, target_price, order_volume)
    
    # ── ORDER MANAGEMENT ─────────────────────────────────────────────────────
    
    def create_order(self, supplier_id: str, items: List[Dict],
                     shipping_method: str = "sea_freight",
                     incoterm: str = "FOB") -> Dict:
        """Crée une commande d'achat."""
        supplier = self._find_supplier(supplier_id)
        if not supplier:
            return {"error": "Fournisseur non trouvé"}
        
        total_units = sum(i.get("quantity", 1) for i in items)
        total_price = sum(i.get("quantity", 1) * i.get("unit_price", supplier.unit_price_min)
                         for i in items)
        
        method = ShippingMethod(shipping_method)
        
        # Estimer shipping
        weight = sum(i.get("weight_kg", 10) * i.get("quantity", 1) for i in items)
        volume = sum(i.get("volume_cbm", 0.1) * i.get("quantity", 1) for i in items)
        ship_est = self._shipping.estimate(weight, volume, method,
                                            items[0].get("category", "general"),
                                            supplier.country)
        
        order = ProcurementOrder(
            supplier_id=supplier_id,
            supplier_name=supplier.name,
            project_type=supplier.project_type,
            items=items,
            total_units=total_units,
            unit_price=total_price / max(total_units, 1),
            total_price=total_price,
            shipping_method=method,
            shipping_cost=ship_est["shipping_cost_usd"],
            incoterm=incoterm,
            customs_duties_estimate=total_price * ship_est["customs_rate"],
            import_taxes_estimate=(total_price + ship_est["shipping_cost_usd"]) * ship_est["tva_rate"],
            assembly_needed=supplier.project_type == ProjectType.TINY_HOUSE,
            assembly_cost=1500 if supplier.project_type == ProjectType.TINY_HOUSE else 0,
        )
        
        with self._lock:
            self._orders.append(order)
        
        self._persist("ORDER_CREATED", order.to_dict())
        
        return order.to_dict()
    
    # ── HELPERS ──────────────────────────────────────────────────────────────
    
    def _find_supplier(self, supplier_id: str) -> Optional[FoundSupplier]:
        with self._lock:
            for suppliers in self._suppliers.values():
                for s in suppliers:
                    if s.id == supplier_id:
                        return s
        return None
    
    def _persist(self, event_type: str, data: Dict):
        if not self._db: return
        try:
            if self._discretion: data = self._discretion.mask(data)
            self._db.log_event(event_type, data, "SOURCING_AGENT", "NORMAL")
        except Exception as e:
            log.debug(f"[Persist] {e}")
    
    # ── AUTONOMOUS ───────────────────────────────────────────────────────────
    
    def start_autonomous(self, interval_seconds: int = 86400):
        """Recherche automatique 1x/jour."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(
            target=self._auto_loop, args=(interval_seconds,),
            daemon=True, name="SourcingAgent-Auto",
        )
        self._thread.start()
    
    def stop_autonomous(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
    
    def _auto_loop(self, interval: int):
        while self._running:
            try:
                self.search_botanica_suppliers()
                self.search_tiny_house_suppliers()
            except Exception as e:
                log.error(f"[SourcingAgent] {e}")
            time.sleep(interval)
    
    # ── QUERY METHODS ────────────────────────────────────────────────────────
    
    def get_botanica_suppliers(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            sups = self._suppliers.get(ProjectType.BOTANICA.value, [])
            return [s.to_dict() for s in sups[:top_n]]
    
    def get_tiny_house_suppliers(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            sups = self._suppliers.get(ProjectType.TINY_HOUSE.value, [])
            return [s.to_dict() for s in sups[:top_n]]
    
    def get_all_samples(self) -> List[Dict]:
        with self._lock:
            return [s.to_dict() for s in self._samples]
    
    def get_all_orders(self) -> List[Dict]:
        with self._lock:
            return [o.to_dict() for o in self._orders]
    
    def get_shipping_estimate_tiny_house(self, units: int = 1) -> Dict:
        return self._shipping.estimate_tiny_house(units)
    
    def get_shipping_estimate_botanica(self) -> Dict:
        return self._shipping.estimate_botanica_samples()
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "version": self.VERSION,
                "total_cycles": self._cycle_count,
                "suppliers": {
                    k: len(v) for k, v in self._suppliers.items()
                },
                "total_samples": len(self._samples),
                "total_orders": len(self._orders),
                "autonomous_running": self._running,
                "apis_configured": {
                    "alibaba": bool(self._alibaba.app_key),
                    "serper": bool(self._alibaba.serper_key),
                },
            }
    
    def to_dict(self) -> Dict:
        return self.get_stats()
