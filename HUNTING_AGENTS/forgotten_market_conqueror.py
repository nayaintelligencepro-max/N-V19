"""
NAYA SUPREME — FORGOTTEN MARKET CONQUEROR
══════════════════════════════════════════════════════════════════════════════════
Agent autonome de détection et conquête des marchés oubliés.

DOCTRINE:
  Un marché oublié = zéro concurrence = marge maximale.
  Les entreprises traditionnelles ignorent les marchés trop petits,
  trop complexes, ou trop "niche" pour elles. NAYA les conquiert.

STRATÉGIE:
  1. SCAN — Identifier les marchés sous-servis ou ignorés
  2. VALIDATE — Confirmer la demande latente et la solvabilité
  3. DESIGN — Créer l'offre parfaite pour ce marché
  4. LAUNCH — Déployer avec minimum de friction
  5. DOMINATE — Prendre la position dominante avant la concurrence

MARCHÉS TYPES:
  - Diaspora (services financiers, immobilier, éducation)
  - Seniors tech-exclus (formation, accompagnement)
  - Micro-entreprises rurales (digitalisation, comptabilité)
  - Secteurs réglementés sous-digitalisés (notaires, huissiers, experts judiciaires)
  - Communautés linguistiques sous-servies
  - Artisans spécialisés (métiers d'art, restauration patrimoine)
  - Agriculture de niche (permaculture, circuits courts)
  - Économie circulaire / recyclage B2B
  - Tourisme de niche (médical, spirituel, industriel)

INTÉGRATION NAYA:
  → NAYA_CORE.scheduler + autonomous_engine
  → PERSISTENCE (stockage marchés détectés)
  → BUSINESS_ENGINES (pricing, business model)
  → NAYA_REVENUE_ENGINE (conversion)
══════════════════════════════════════════════════════════════════════════════════
"""

import os, time, uuid, json, logging, threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("NAYA.HUNTER.FORGOTTEN_MARKET")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATA
# ══════════════════════════════════════════════════════════════════════════════

class MarketStatus(Enum):
    DETECTED       = "detected"
    VALIDATED      = "validated"
    OFFER_DESIGNED = "offer_designed"
    LAUNCHED       = "launched"
    GROWING        = "growing"
    DOMINANT       = "dominant"

class NeglectReason(Enum):
    TOO_SMALL       = "too_small"          # Trop petit pour les gros
    TOO_COMPLEX     = "too_complex"        # Réglementation, logistique
    INVISIBLE       = "invisible"          # Pas de données publiques
    STIGMATIZED     = "stigmatized"        # Marché tabou/honteux
    FRAGMENTED      = "fragmented"         # Trop éclaté, pas de leader
    TECH_EXCLUDED   = "tech_excluded"      # Population non-digitale
    LANGUAGE_BARRIER = "language_barrier"   # Barrière linguistique
    GEOGRAPHIC      = "geographic"         # Zones isolées/rurales

class ConquestStrategy(Enum):
    FIRST_MOVER    = "first_mover"         # Arriver premier, dominer
    AGGREGATOR     = "aggregator"          # Agréger offres fragmentées
    BRIDGE         = "bridge"              # Pont entre deux mondes
    DIGITIZER      = "digitizer"           # Numériser un process papier
    LOCALIZER      = "localizer"           # Adapter un produit existant
    UNBUNDLER      = "unbundler"           # Extraire un service d'un bundle


@dataclass
class ForgottenMarket:
    """Marché oublié détecté et analysé."""
    id: str = field(default_factory=lambda: f"MKT_{uuid.uuid4().hex[:8].upper()}")
    
    # Identification
    name: str = ""
    description: str = ""
    status: MarketStatus = MarketStatus.DETECTED
    neglect_reasons: List[NeglectReason] = field(default_factory=list)
    
    # Sizing
    estimated_population: int = 0        # Nb de clients potentiels
    estimated_tam: float = 0.0           # Total Addressable Market (€/an)
    avg_ticket: float = 0.0              # Panier moyen par client
    frequency: str = ""                  # "one_time", "monthly", "annual"
    willingness_to_pay: float = 0.0      # 0-1
    
    # Concurrence
    existing_competitors: int = 0
    competitor_quality: float = 0.0      # 0-1 (qualité actuelle)
    entry_barrier: float = 0.0           # 0-1 (difficulté d'entrée)
    
    # Stratégie
    conquest_strategy: ConquestStrategy = ConquestStrategy.FIRST_MOVER
    time_to_launch_days: int = 30
    launch_cost: float = 0.0
    expected_monthly_revenue: float = 0.0
    expected_margin: float = 0.0         # 0-1
    
    # Offre
    offer_name: str = ""
    offer_description: str = ""
    offer_price: float = 0.0
    channels: List[str] = field(default_factory=list)  # Canaux d'acquisition
    
    # Scoring
    opportunity_score: float = 0.0       # 0-100
    conquest_difficulty: float = 0.0     # 0-100 (inversé = facile si bas)
    roi_score: float = 0.0              # 0-100
    overall_score: float = 0.0
    
    # Détails
    geography: str = ""                  # Zone géographique ciblée
    language: str = "fr"
    regulatory_notes: str = ""
    key_insights: List[str] = field(default_factory=list)
    
    detected_at: float = field(default_factory=time.time)
    
    def compute_scores(self) -> float:
        opp = min(100, (
            min(self.estimated_tam / 50_000_000, 1.0) * 25 +
            self.willingness_to_pay * 25 +
            (1 - min(self.existing_competitors / 10, 1.0)) * 25 +
            (1 - self.competitor_quality) * 25
        ))
        self.opportunity_score = round(opp, 2)
        
        diff = min(100, (
            self.entry_barrier * 40 +
            min(self.launch_cost / 100000, 1.0) * 30 +
            min(self.time_to_launch_days / 180, 1.0) * 30
        ))
        self.conquest_difficulty = round(diff, 2)
        
        if self.launch_cost > 0:
            annual_profit = self.expected_monthly_revenue * 12 * self.expected_margin
            roi = min(100, (annual_profit / self.launch_cost) * 20)
        else:
            roi = 50
        self.roi_score = round(roi, 2)
        
        self.overall_score = round(
            self.opportunity_score * 0.40 +
            (100 - self.conquest_difficulty) * 0.30 +
            self.roi_score * 0.30,
            2
        )
        return self.overall_score
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "status": self.status.value,
            "neglect_reasons": [r.value for r in self.neglect_reasons],
            "market_size": {
                "population": self.estimated_population,
                "tam": self.estimated_tam, "avg_ticket": self.avg_ticket,
                "frequency": self.frequency,
            },
            "competition": {
                "competitors": self.existing_competitors,
                "quality": self.competitor_quality,
                "entry_barrier": self.entry_barrier,
            },
            "strategy": {
                "type": self.conquest_strategy.value,
                "launch_days": self.time_to_launch_days,
                "launch_cost": self.launch_cost,
                "monthly_revenue": self.expected_monthly_revenue,
                "margin": self.expected_margin,
            },
            "offer": {
                "name": self.offer_name, "price": self.offer_price,
                "channels": self.channels,
            },
            "scoring": {
                "opportunity": self.opportunity_score,
                "difficulty": self.conquest_difficulty,
                "roi": self.roi_score,
                "overall": self.overall_score,
            },
            "geography": self.geography, "language": self.language,
        }


# ══════════════════════════════════════════════════════════════════════════════
# MARKET DATABASE — Marchés oubliés connus + détection dynamique
# ══════════════════════════════════════════════════════════════════════════════

FORGOTTEN_MARKETS_LIBRARY = [
    {
        "name": "Digitalisation cabinets d'huissiers",
        "description": "90% des huissiers utilisent encore des processus papier pour significations. "
                      "Marché captif, réglementé, zéro solution SaaS dédiée.",
        "neglect": [NeglectReason.TOO_SMALL, NeglectReason.TOO_COMPLEX],
        "population": 3200, "tam": 48_000_000, "avg_ticket": 15000, "frequency": "annual",
        "wtp": 0.85, "competitors": 1, "comp_quality": 0.3, "barrier": 0.6,
        "strategy": ConquestStrategy.DIGITIZER, "launch_days": 60, "cost": 40000,
        "monthly_rev": 80000, "margin": 0.75,
        "channels": ["Chambre des huissiers", "bouche-à-oreille", "LinkedIn"],
        "geography": "France", "regulatory": "Réglementation CNCJ applicable",
    },
    {
        "name": "Services financiers diaspora africaine Europe",
        "description": "15M de personnes en Europe envoient 65Mds€/an en Afrique. "
                      "Frais exorbitants (7-12%), services inadaptés, zéro conseil patrimonial.",
        "neglect": [NeglectReason.INVISIBLE, NeglectReason.LANGUAGE_BARRIER, NeglectReason.STIGMATIZED],
        "population": 15_000_000, "tam": 4_500_000_000, "avg_ticket": 300, "frequency": "monthly",
        "wtp": 0.90, "competitors": 5, "comp_quality": 0.4, "barrier": 0.5,
        "strategy": ConquestStrategy.BRIDGE, "launch_days": 90, "cost": 80000,
        "monthly_rev": 200000, "margin": 0.60,
        "channels": ["WhatsApp communautés", "radios communautaires", "influenceurs diaspora", "mosquées/églises"],
        "geography": "France, Belgique, UK", "regulatory": "Licence Agent de paiement EMI",
    },
    {
        "name": "Formation digitale seniors isolés",
        "description": "4M de seniors français exclus du numérique. "
                      "Démarches en ligne obligatoires, aucune solution humaine + tech adaptée.",
        "neglect": [NeglectReason.TECH_EXCLUDED, NeglectReason.TOO_SMALL],
        "population": 4_000_000, "tam": 2_400_000_000, "avg_ticket": 50, "frequency": "monthly",
        "wtp": 0.70, "competitors": 3, "comp_quality": 0.35, "barrier": 0.3,
        "strategy": ConquestStrategy.BRIDGE, "launch_days": 45, "cost": 25000,
        "monthly_rev": 150000, "margin": 0.65,
        "channels": ["Mairies", "CCAS", "pharmacies", "La Poste", "associations"],
        "geography": "France rurale + péri-urbain",
    },
    {
        "name": "Marketplace artisans métiers d'art",
        "description": "280k artisans d'art en France, 80% sans présence en ligne. "
                      "Clientèle haut de gamme prête à payer premium, aucune plateforme dédiée quality.",
        "neglect": [NeglectReason.FRAGMENTED, NeglectReason.TOO_SMALL],
        "population": 280_000, "tam": 840_000_000, "avg_ticket": 3000, "frequency": "annual",
        "wtp": 0.75, "competitors": 2, "comp_quality": 0.25, "barrier": 0.35,
        "strategy": ConquestStrategy.AGGREGATOR, "launch_days": 60, "cost": 50000,
        "monthly_rev": 120000, "margin": 0.70,
        "channels": ["Chambres des métiers", "salons", "Instagram", "galeries"],
        "geography": "France puis Europe",
    },
    {
        "name": "Comptabilité micro-entreprises rurales",
        "description": "1.2M de micro-entrepreneurs ruraux sans comptable ni outil adapté. "
                      "Pennies & Ciel trop complexes, experts-comptables trop chers.",
        "neglect": [NeglectReason.TOO_SMALL, NeglectReason.GEOGRAPHIC],
        "population": 1_200_000, "tam": 720_000_000, "avg_ticket": 50, "frequency": "monthly",
        "wtp": 0.80, "competitors": 4, "comp_quality": 0.45, "barrier": 0.25,
        "strategy": ConquestStrategy.LOCALIZER, "launch_days": 30, "cost": 20000,
        "monthly_rev": 100000, "margin": 0.80,
        "channels": ["Chambres d'agriculture", "coopératives", "marchés locaux", "Facebook groups"],
        "geography": "France rurale",
    },
    {
        "name": "Recyclage B2B matériaux spécialisés",
        "description": "Déchets industriels spéciaux (composites, terres rares, batteries) — "
                      "aucun intermédiaire efficace entre producteurs et recycleurs.",
        "neglect": [NeglectReason.TOO_COMPLEX, NeglectReason.INVISIBLE],
        "population": 50_000, "tam": 3_000_000_000, "avg_ticket": 60000, "frequency": "annual",
        "wtp": 0.85, "competitors": 2, "comp_quality": 0.3, "barrier": 0.65,
        "strategy": ConquestStrategy.AGGREGATOR, "launch_days": 90, "cost": 60000,
        "monthly_rev": 250000, "margin": 0.55,
        "channels": ["Fédérations industrielles", "salons POLLUTEC", "LinkedIn B2B"],
        "geography": "France puis EU",
    },
    {
        "name": "Tourisme médical francophone",
        "description": "500k francophones/an cherchent soins à l'étranger (dentaire, ophtalmo, esthétique). "
                      "Zéro plateforme de confiance intégrée (booking + assurance + suivi).",
        "neglect": [NeglectReason.STIGMATIZED, NeglectReason.TOO_COMPLEX],
        "population": 500_000, "tam": 2_500_000_000, "avg_ticket": 5000, "frequency": "one_time",
        "wtp": 0.90, "competitors": 3, "comp_quality": 0.35, "barrier": 0.5,
        "strategy": ConquestStrategy.AGGREGATOR, "launch_days": 75, "cost": 70000,
        "monthly_rev": 180000, "margin": 0.60,
        "channels": ["Google Ads", "forums santé", "influenceurs", "partenariats cliniques"],
        "geography": "France → Turquie, Tunisie, Hongrie, Thaïlande",
    },
    {
        "name": "Experts judiciaires — gestion cabinet",
        "description": "12k experts judiciaires en France, workflow 100% papier. "
                      "Gestion missions tribunal, rapports, facturation — rien d'intégré.",
        "neglect": [NeglectReason.TOO_SMALL, NeglectReason.TOO_COMPLEX],
        "population": 12_000, "tam": 60_000_000, "avg_ticket": 5000, "frequency": "annual",
        "wtp": 0.80, "competitors": 0, "comp_quality": 0.0, "barrier": 0.55,
        "strategy": ConquestStrategy.FIRST_MOVER, "launch_days": 45, "cost": 35000,
        "monthly_rev": 60000, "margin": 0.80,
        "channels": ["Compagnies d'experts", "tribunaux", "barreaux"],
        "geography": "France",
    },
    {
        "name": "Gestion locative courte durée DOM-TOM",
        "description": "Airbnb sous-pénètre les DOM-TOM. Propriétaires locaux sans accompagnement. "
                      "Tourisme en forte croissance, aucune conciergerie pro locale.",
        "neglect": [NeglectReason.GEOGRAPHIC, NeglectReason.FRAGMENTED],
        "population": 25_000, "tam": 375_000_000, "avg_ticket": 15000, "frequency": "annual",
        "wtp": 0.85, "competitors": 1, "comp_quality": 0.2, "barrier": 0.4,
        "strategy": ConquestStrategy.LOCALIZER, "launch_days": 30, "cost": 15000,
        "monthly_rev": 90000, "margin": 0.65,
        "channels": ["Facebook local", "agences immobilières", "offices tourisme"],
        "geography": "Guadeloupe, Martinique, Réunion, Polynésie",
    },
    {
        "name": "Permaculture / agriculture régénérative — SaaS gestion",
        "description": "50k exploitations en transition écologique, aucun outil de gestion adapté. "
                      "Comptabilité carbone + rotation cultures + ventes directes intégrées.",
        "neglect": [NeglectReason.TOO_SMALL, NeglectReason.INVISIBLE],
        "population": 50_000, "tam": 150_000_000, "avg_ticket": 250, "frequency": "monthly",
        "wtp": 0.70, "competitors": 1, "comp_quality": 0.2, "barrier": 0.3,
        "strategy": ConquestStrategy.FIRST_MOVER, "launch_days": 45, "cost": 30000,
        "monthly_rev": 70000, "margin": 0.75,
        "channels": ["Réseaux permaculture", "AMAP", "salons bio", "YouTube"],
        "geography": "France puis EU",
    },
]


class ForgottenMarketScanner:
    """Scanne et détecte les marchés oubliés via sources multiples."""
    
    def __init__(self):
        self.serp_key = _gs("SERP_API_KEY")
    
    def scan(self, include_live_search: bool = True) -> List[ForgottenMarket]:
        """Retourne tous les marchés oubliés identifiés."""
        markets = []
        
        # Phase 1: Bibliothèque interne
        for m_data in FORGOTTEN_MARKETS_LIBRARY:
            market = self._build_from_library(m_data)
            markets.append(market)
        
        # Phase 2: Recherche live
        if include_live_search and self.serp_key:
            live_markets = self._search_live()
            markets.extend(live_markets)
        
        # Score et tri
        for m in markets:
            m.compute_scores()
        markets.sort(key=lambda m: m.overall_score, reverse=True)
        
        return markets
    
    def _build_from_library(self, data: Dict) -> ForgottenMarket:
        return ForgottenMarket(
            name=data["name"],
            description=data["description"],
            neglect_reasons=data["neglect"],
            estimated_population=data["population"],
            estimated_tam=data["tam"],
            avg_ticket=data["avg_ticket"],
            frequency=data["frequency"],
            willingness_to_pay=data["wtp"],
            existing_competitors=data["competitors"],
            competitor_quality=data["comp_quality"],
            entry_barrier=data["barrier"],
            conquest_strategy=data["strategy"],
            time_to_launch_days=data["launch_days"],
            launch_cost=data["cost"],
            expected_monthly_revenue=data["monthly_rev"],
            expected_margin=data["margin"],
            channels=data.get("channels", []),
            geography=data.get("geography", "France"),
            regulatory_notes=data.get("regulatory", ""),
        )
    
    def _search_live(self) -> List[ForgottenMarket]:
        """Recherche de marchés oubliés via SERP API."""
        markets = []
        queries = [
            "marché niche sous-servi France 2025",
            "underserved market opportunities Europe",
            "secteur sans concurrence digital France",
            "marchés oubliés opportunité business",
        ]
        try:
            import requests
            for q in queries[:3]:
                resp = requests.get(
                    "https://serpapi.com/search",
                    params={"engine": "google", "q": q, "api_key": self.serp_key,
                            "gl": "fr", "hl": "fr", "num": 5},
                    timeout=15,
                )
                if resp.status_code == 200:
                    for r in resp.json().get("organic_results", [])[:3]:
                        market = self._parse_result(r)
                        if market:
                            markets.append(market)
                time.sleep(1)
        except Exception as e:
            log.debug(f"[LiveSearch] {e}")
        return markets
    
    def _parse_result(self, result: Dict) -> Optional[ForgottenMarket]:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        if not any(w in f"{title} {snippet}".lower() for w in
                   ["marché", "niche", "oublié", "sous-servi", "underserved", "opportunity"]):
            return None
        return ForgottenMarket(
            name=title[:100],
            description=snippet[:300],
            neglect_reasons=[NeglectReason.INVISIBLE],
            estimated_tam=5_000_000,  # Estimation conservatrice
            willingness_to_pay=0.6,
            key_insights=[f"Source: {result.get('link', '')}"],
        )


class OfferDesigner:
    """Conçoit l'offre optimale pour un marché oublié."""
    
    def design_offer(self, market: ForgottenMarket) -> ForgottenMarket:
        strategy_templates = {
            ConquestStrategy.FIRST_MOVER: {
                "prefix": "Premier service de",
                "description": "Solution pionnière — aucun concurrent direct. "
                              "Position dominante garantie si exécution rapide.",
            },
            ConquestStrategy.AGGREGATOR: {
                "prefix": "Plateforme unifiée pour",
                "description": "Agrège une offre fragmentée en une expérience fluide. "
                              "Network effects = moat naturel.",
            },
            ConquestStrategy.BRIDGE: {
                "prefix": "Pont digital pour",
                "description": "Connecte un marché isolé au monde digital. "
                              "Solution adaptée culturellement et linguistiquement.",
            },
            ConquestStrategy.DIGITIZER: {
                "prefix": "Digitalisation de",
                "description": "Transforme un processus papier/manuel en SaaS moderne. "
                              "ROI immédiat pour les clients.",
            },
            ConquestStrategy.LOCALIZER: {
                "prefix": "Solution locale pour",
                "description": "Adapte un produit existant aux spécificités locales. "
                              "Avantage culturel + proximité.",
            },
            ConquestStrategy.UNBUNDLER: {
                "prefix": "Service spécialisé de",
                "description": "Extrait un service premium d'un bundle générique. "
                              "Meilleure qualité, meilleur prix.",
            },
        }
        
        template = strategy_templates.get(market.conquest_strategy,
                                          strategy_templates[ConquestStrategy.FIRST_MOVER])
        
        market.offer_name = f"{template['prefix']} {market.name}"
        market.offer_description = template["description"]
        market.offer_price = market.avg_ticket
        
        if not market.channels:
            market.channels = self._suggest_channels(market)
        
        market.status = MarketStatus.OFFER_DESIGNED
        return market
    
    def _suggest_channels(self, market: ForgottenMarket) -> List[str]:
        channels = ["LinkedIn"]
        if market.estimated_population > 100000:
            channels.extend(["Google Ads", "Facebook Ads"])
        if any(r in market.neglect_reasons for r in
               [NeglectReason.LANGUAGE_BARRIER, NeglectReason.TECH_EXCLUDED]):
            channels.extend(["WhatsApp", "bouche-à-oreille", "associations locales"])
        if NeglectReason.GEOGRAPHIC in market.neglect_reasons:
            channels.extend(["radios locales", "marchés physiques"])
        if NeglectReason.TOO_COMPLEX in market.neglect_reasons:
            channels.extend(["fédérations professionnelles", "salons spécialisés"])
        return channels


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ForgottenMarketConqueror:
    """Agent de détection et conquête des marchés oubliés."""
    VERSION = "1.0.0"
    
    def __init__(self):
        self._scanner = ForgottenMarketScanner()
        self._designer = OfferDesigner()
        
        self._markets: List[ForgottenMarket] = []
        self._cycle_count = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # NAYA integrations
        self._db = None
        self._discretion = None
        self._event_stream = None
        self._cash_engine = None
        
        log.info("[ForgottenMarketConqueror] Initialisé — V%s", self.VERSION)
    
    def set_database(self, db): self._db = db
    def set_discretion(self, protocol): self._discretion = protocol
    def set_event_stream(self, stream): self._event_stream = stream
    def set_cash_engine(self, engine): self._cash_engine = engine
    
    def hunt_cycle(self) -> Dict:
        """Cycle complet: scan → design offres → persist."""
        cycle_id = f"FMKT_{uuid.uuid4().hex[:6].upper()}"
        self._cycle_count += 1
        
        log.info(f"[{cycle_id}] Cycle Forgotten Markets #{self._cycle_count}")
        
        result = {
            "cycle_id": cycle_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "markets_scanned": 0,
            "markets_with_offer": 0,
            "total_tam": 0.0,
            "total_monthly_revenue_potential": 0.0,
            "top_markets": [],
        }
        
        # Scan
        markets = self._scanner.scan()
        result["markets_scanned"] = len(markets)
        
        # Design offres + persist
        for market in markets:
            self._designer.design_offer(market)
            market.compute_scores()
            
            with self._lock:
                # Éviter les doublons
                existing_names = {m.name for m in self._markets}
                if market.name not in existing_names:
                    self._markets.append(market)
            
            result["total_tam"] += market.estimated_tam
            result["total_monthly_revenue_potential"] += market.expected_monthly_revenue
            
            self._persist_market(market)
            
            if self._event_stream and hasattr(self._event_stream, "broadcast"):
                try:
                    self._event_stream.broadcast({
                        "type": "FORGOTTEN_MARKET_DETECTED",
                        "source": "FORGOTTEN_MARKET_CONQUEROR",
                        "data": {"id": market.id, "name": market.name,
                                 "tam": market.estimated_tam, "score": market.overall_score},
                    })
                except Exception: pass
        
        result["markets_with_offer"] = len([m for m in markets if m.status == MarketStatus.OFFER_DESIGNED])
        
        # Top 5
        sorted_markets = sorted(markets, key=lambda m: m.overall_score, reverse=True)
        result["top_markets"] = [m.to_dict() for m in sorted_markets[:5]]
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        log.info(
            f"[{cycle_id}] Terminé — {result['markets_scanned']} marchés, "
            f"TAM total: {result['total_tam']:,.0f}€"
        )
        return result
    
    def _persist_market(self, market: ForgottenMarket):
        if not self._db: return
        try:
            data = market.to_dict()
            if self._discretion: data = self._discretion.mask(data)
            self._db.log_event("FORGOTTEN_MARKET", data, "HUNTING_AGENTS.forgotten_market", "NORMAL")
        except Exception as e:
            log.debug(f"[Persist] {e}")
    
    def start_autonomous(self, interval_seconds: int = 43200):
        """Lance la chasse autonome (par défaut 2x/jour)."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(
            target=self._auto_loop, args=(interval_seconds,),
            daemon=True, name="ForgottenMarket-Auto",
        )
        self._thread.start()
    
    def stop_autonomous(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
    
    def _auto_loop(self, interval: int):
        while self._running:
            try: self.hunt_cycle()
            except Exception as e: log.error(f"[ForgottenMarket] {e}")
            time.sleep(interval)
    
    def get_top_markets(self, n: int = 10) -> List[Dict]:
        with self._lock:
            s = sorted(self._markets, key=lambda m: m.overall_score, reverse=True)
            return [m.to_dict() for m in s[:n]]
    
    def get_quick_wins(self) -> List[Dict]:
        """Marchés à lancer en < 30 jours avec fort ROI."""
        with self._lock:
            quick = [m for m in self._markets
                     if m.time_to_launch_days <= 30 and m.roi_score > 50]
            quick.sort(key=lambda m: m.roi_score, reverse=True)
            return [m.to_dict() for m in quick]
    
    def get_stats(self) -> Dict:
        with self._lock:
            total_tam = sum(m.estimated_tam for m in self._markets)
            total_rev = sum(m.expected_monthly_revenue for m in self._markets)
            return {
                "version": self.VERSION,
                "total_cycles": self._cycle_count,
                "total_markets": len(self._markets),
                "total_tam": total_tam,
                "total_monthly_revenue_potential": total_rev,
                "autonomous_running": self._running,
                "by_strategy": {s.value: sum(1 for m in self._markets if m.conquest_strategy == s)
                                for s in ConquestStrategy if any(m.conquest_strategy == s for m in self._markets)},
            }
    
    def to_dict(self) -> Dict:
        return self.get_stats()
