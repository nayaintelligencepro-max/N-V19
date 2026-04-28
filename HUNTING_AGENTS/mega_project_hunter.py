"""
NAYA SUPREME — MEGA PROJECT HUNTER
══════════════════════════════════════════════════════════════════════════════════
Agent autonome de chasse de projets innovants vendables 15M-40M€+.

DOCTRINE:
  Les GAFAM et grandes infrastructures ACHÈTENT l'innovation qu'elles ne peuvent
  pas produire assez vite en interne. Le timing est tout: détecter le besoin
  AVANT que le marché ne le voie, construire la solution, la vendre.

CIBLES ACQUÉREURS:
  - GAFAM: Google, Microsoft, Apple, Amazon, Meta
  - Cloud/Infra: AWS, Azure, GCP, Oracle, Salesforce, SAP
  - Telecom: Orange, SFR, Deutsche Telekom, Vodafone
  - Défense/Aéro: Thales, Airbus, Safran, Dassault
  - Énergie: EDF, Engie, TotalEnergies, Shell
  - Finance: BNP, Société Générale, AXA, Goldman Sachs
  - Santé: Sanofi, Roche, Novartis, Philips Healthcare

WORKFLOW:
  1. DETECT — Identifier les gaps technologiques des géants
  2. BUILD — Concevoir le projet/produit qui comble le gap
  3. VALIDATE — Vérifier taille de marché + fit acquéreur
  4. PITCH — Construire le dossier de vente complet
  5. TARGET — Identifier les bons contacts M&A / Corp Dev

INTÉGRATION NAYA:
  → NAYA_CORE.scheduler (cycles automatiques)
  → NAYA_CORE.autonomous_engine (missions autonomes)
  → PERSISTENCE (stockage projets)
  → BUSINESS_ENGINES.discretion_protocol (mode PHANTOM)
══════════════════════════════════════════════════════════════════════════════════
"""

import os
import time
import uuid
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.HUNTER.MEGA_PROJECT")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATACLASSES
# ══════════════════════════════════════════════════════════════════════════════

class ProjectStage(Enum):
    DETECTED       = "detected"        # Gap identifié
    RESEARCHED     = "researched"      # Marché validé
    DESIGNED       = "designed"        # Architecture technique prête
    PROTOTYPED     = "prototyped"      # MVP/PoC construit
    PITCH_READY    = "pitch_ready"     # Dossier vente complet
    TARGETING      = "targeting"       # Contacts acquéreurs identifiés
    PITCHED        = "pitched"         # Présenté à un acquéreur
    NEGOTIATING    = "negotiating"     # En discussion
    TERM_SHEET     = "term_sheet"      # Offre reçue
    SOLD           = "sold"            # Deal fermé

class TechDomain(Enum):
    AI_ML           = "ai_ml"
    CYBERSECURITY   = "cybersecurity"
    QUANTUM         = "quantum_computing"
    EDGE_COMPUTING  = "edge_computing"
    BIOTECH         = "biotech"
    CLEANTECH       = "cleantech"
    FINTECH         = "fintech"
    HEALTHTECH      = "healthtech"
    SPACETECH       = "spacetech"
    WEB3_BLOCKCHAIN = "web3_blockchain"
    ROBOTICS        = "robotics"
    AR_VR           = "ar_vr"
    IOT             = "iot"
    SAAS_B2B        = "saas_b2b"
    DATA_INFRA      = "data_infrastructure"
    DEVTOOLS        = "devtools"

class AcquirerType(Enum):
    GAFAM           = "gafam"
    CLOUD_INFRA     = "cloud_infrastructure"
    TELECOM         = "telecom"
    DEFENSE_AERO    = "defense_aerospace"
    ENERGY          = "energy"
    FINANCE         = "finance"
    HEALTHCARE      = "healthcare"
    AUTOMOTIVE      = "automotive"
    GOVERNMENT      = "government"


@dataclass
class TechGap:
    """Gap technologique détecté chez un acquéreur potentiel."""
    id: str = field(default_factory=lambda: f"GAP_{uuid.uuid4().hex[:8].upper()}")
    acquirer_name: str = ""
    acquirer_type: AcquirerType = AcquirerType.GAFAM
    gap_description: str = ""
    tech_domain: TechDomain = TechDomain.AI_ML
    evidence: List[str] = field(default_factory=list)  # Sources/preuves
    market_size_estimate: float = 0.0  # Taille marché adressable
    urgency: float = 0.0  # 0-10
    competitive_landscape: str = ""  # Qui d'autre attaque ce gap?
    detected_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "acquirer": self.acquirer_name,
            "acquirer_type": self.acquirer_type.value,
            "gap": self.gap_description, "domain": self.tech_domain.value,
            "market_size": self.market_size_estimate,
            "urgency": self.urgency, "evidence_count": len(self.evidence),
        }


@dataclass
class MegaProject:
    """Projet innovant vendable 15M-40M€+."""
    id: str = field(default_factory=lambda: f"MEGA_{uuid.uuid4().hex[:8].upper()}")
    
    # Projet
    name: str = ""
    description: str = ""
    tech_domain: TechDomain = TechDomain.AI_ML
    stage: ProjectStage = ProjectStage.DETECTED
    
    # Valeur
    estimated_sale_price_min: float = 15_000_000  # 15M€ min
    estimated_sale_price_max: float = 40_000_000  # 40M€ max
    tam: float = 0.0  # Total Addressable Market
    sam: float = 0.0  # Serviceable Addressable Market
    som: float = 0.0  # Serviceable Obtainable Market
    
    # Acquéreurs potentiels
    target_acquirers: List[Dict] = field(default_factory=list)
    primary_acquirer: str = ""
    acquirer_type: AcquirerType = AcquirerType.GAFAM
    
    # Tech gaps comblés
    gaps_addressed: List[TechGap] = field(default_factory=list)
    
    # Competitive moat
    moat_description: str = ""
    ip_assets: List[str] = field(default_factory=list)  # Brevets, propriété intellectuelle
    unique_data: bool = False
    network_effects: bool = False
    
    # Construction
    build_cost_estimate: float = 0.0
    build_time_months: int = 6
    team_needed: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    
    # Pitch
    pitch_deck_ready: bool = False
    financial_model_ready: bool = False
    executive_summary: str = ""
    key_metrics: Dict = field(default_factory=dict)
    
    # Contacts M&A
    ma_contacts: List[Dict] = field(default_factory=list)
    corp_dev_contacts: List[Dict] = field(default_factory=list)
    
    # Scoring
    innovation_score: float = 0.0  # 0-100
    acquisition_fit_score: float = 0.0  # 0-100
    timing_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # 0-100
    
    # Timestamps
    detected_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    def compute_scores(self) -> float:
        """Calcule les scores du projet."""
        # Innovation: taille marché + unicité
        self.innovation_score = min(100, (
            min(self.tam / 10_000_000_000, 1.0) * 30 +
            (0.2 if self.unique_data else 0) * 100 +
            (0.15 if self.network_effects else 0) * 100 +
            min(len(self.ip_assets) / 3, 1.0) * 20
        ))
        
        # Acquisition fit: nombre d'acquéreurs + urgency des gaps
        gap_urgency = max([g.urgency for g in self.gaps_addressed], default=0)
        self.acquisition_fit_score = min(100, (
            min(len(self.target_acquirers) / 5, 1.0) * 40 +
            (gap_urgency / 10) * 40 +
            (0.2 if self.primary_acquirer else 0) * 100
        ))
        
        # Timing: urgence + stade avancement
        stage_progress = {
            ProjectStage.DETECTED: 0.1, ProjectStage.RESEARCHED: 0.2,
            ProjectStage.DESIGNED: 0.35, ProjectStage.PROTOTYPED: 0.5,
            ProjectStage.PITCH_READY: 0.7, ProjectStage.TARGETING: 0.8,
            ProjectStage.PITCHED: 0.85, ProjectStage.NEGOTIATING: 0.9,
            ProjectStage.TERM_SHEET: 0.95, ProjectStage.SOLD: 1.0,
        }
        self.timing_score = min(100, (
            stage_progress.get(self.stage, 0.1) * 50 +
            (gap_urgency / 10) * 50
        ))
        
        self.overall_score = round(
            self.innovation_score * 0.35 +
            self.acquisition_fit_score * 0.40 +
            self.timing_score * 0.25,
            2
        )
        return self.overall_score
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "domain": self.tech_domain.value, "stage": self.stage.value,
            "value": {
                "min": self.estimated_sale_price_min,
                "max": self.estimated_sale_price_max,
                "tam": self.tam, "sam": self.sam, "som": self.som,
            },
            "acquirers": {
                "primary": self.primary_acquirer,
                "type": self.acquirer_type.value,
                "count": len(self.target_acquirers),
            },
            "moat": {
                "description": self.moat_description,
                "ip_count": len(self.ip_assets),
                "unique_data": self.unique_data,
                "network_effects": self.network_effects,
            },
            "build": {
                "cost": self.build_cost_estimate,
                "months": self.build_time_months,
                "team_size": len(self.team_needed),
            },
            "scoring": {
                "innovation": self.innovation_score,
                "acquisition_fit": self.acquisition_fit_score,
                "timing": self.timing_score,
                "overall": self.overall_score,
            },
            "stage_ready": {
                "pitch_deck": self.pitch_deck_ready,
                "financial_model": self.financial_model_ready,
            },
        }


# ══════════════════════════════════════════════════════════════════════════════
# GAP DETECTOR — Détecte les gaps technologiques des géants
# ══════════════════════════════════════════════════════════════════════════════

class GapDetector:
    """Détecte les gaps technologiques des grandes entreprises."""
    
    # Gaps connus et récurrents par type d'acquéreur
    KNOWN_GAP_PATTERNS = {
        AcquirerType.GAFAM: [
            {
                "domain": TechDomain.AI_ML,
                "pattern": "Enterprise AI agents autonomes pour workflows complexes",
                "keywords": ["ai agent", "autonomous workflow", "enterprise automation"],
                "market_size": 50_000_000_000,
                "acquirers": ["Microsoft", "Google", "Amazon", "Salesforce"],
            },
            {
                "domain": TechDomain.CYBERSECURITY,
                "pattern": "Zero-trust identity pour environnements multi-cloud",
                "keywords": ["zero trust", "identity mesh", "multi-cloud security"],
                "market_size": 25_000_000_000,
                "acquirers": ["Microsoft", "Google", "CrowdStrike", "Palo Alto"],
            },
            {
                "domain": TechDomain.DATA_INFRA,
                "pattern": "Data governance automatisée avec privacy-by-design",
                "keywords": ["data governance", "privacy engineering", "data mesh"],
                "market_size": 15_000_000_000,
                "acquirers": ["Snowflake", "Databricks", "Google", "Microsoft"],
            },
            {
                "domain": TechDomain.DEVTOOLS,
                "pattern": "AI-powered code review et security scanning",
                "keywords": ["ai code review", "devsecops", "automated security"],
                "market_size": 8_000_000_000,
                "acquirers": ["GitHub/Microsoft", "GitLab", "Snyk", "Google"],
            },
        ],
        AcquirerType.CLOUD_INFRA: [
            {
                "domain": TechDomain.EDGE_COMPUTING,
                "pattern": "Edge AI inference optimisé pour IoT industriel",
                "keywords": ["edge inference", "industrial iot", "real-time ml"],
                "market_size": 20_000_000_000,
                "acquirers": ["AWS", "Azure", "GCP", "Oracle"],
            },
            {
                "domain": TechDomain.SAAS_B2B,
                "pattern": "Vertical SaaS avec AI intégrée pour industries régulées",
                "keywords": ["vertical saas", "regulated industry", "compliance ai"],
                "market_size": 30_000_000_000,
                "acquirers": ["Salesforce", "SAP", "Oracle", "ServiceNow"],
            },
        ],
        AcquirerType.HEALTHCARE: [
            {
                "domain": TechDomain.HEALTHTECH,
                "pattern": "Diagnostic AI certifié pour imagerie médicale",
                "keywords": ["medical imaging ai", "diagnostic ai", "fda cleared"],
                "market_size": 12_000_000_000,
                "acquirers": ["Philips", "Siemens Healthineers", "GE Healthcare"],
            },
            {
                "domain": TechDomain.BIOTECH,
                "pattern": "Drug discovery accélérée par AI/ML",
                "keywords": ["drug discovery ai", "protein folding", "molecular design"],
                "market_size": 40_000_000_000,
                "acquirers": ["Roche", "Novartis", "Sanofi", "AstraZeneca"],
            },
        ],
        AcquirerType.ENERGY: [
            {
                "domain": TechDomain.CLEANTECH,
                "pattern": "Optimisation réseau électrique par AI prédictive",
                "keywords": ["smart grid ai", "energy optimization", "predictive grid"],
                "market_size": 18_000_000_000,
                "acquirers": ["EDF", "Engie", "TotalEnergies", "Shell"],
            },
        ],
        AcquirerType.DEFENSE_AERO: [
            {
                "domain": TechDomain.CYBERSECURITY,
                "pattern": "Cyberdéfense souveraine avec AI temps réel",
                "keywords": ["sovereign cyber", "defense ai", "threat hunting ai"],
                "market_size": 15_000_000_000,
                "acquirers": ["Thales", "Airbus CyberSecurity", "Atos"],
            },
        ],
        AcquirerType.FINANCE: [
            {
                "domain": TechDomain.FINTECH,
                "pattern": "RegTech AI pour conformité automatisée multi-juridiction",
                "keywords": ["regtech", "compliance automation", "aml ai"],
                "market_size": 20_000_000_000,
                "acquirers": ["BNP Paribas", "Société Générale", "Goldman Sachs", "JPMorgan"],
            },
        ],
    }
    
    def __init__(self):
        self.serp_key = _gs("SERP_API_KEY")
        self.crunchbase_key = _gs("CRUNCHBASE_API_KEY")
    
    def detect_gaps(self, acquirer_types: List[AcquirerType] = None) -> List[TechGap]:
        """Détecte les gaps technologiques via patterns + recherche live."""
        gaps = []
        types = acquirer_types or list(AcquirerType)
        
        for atype in types:
            patterns = self.KNOWN_GAP_PATTERNS.get(atype, [])
            for pattern in patterns:
                gap = TechGap(
                    acquirer_name=", ".join(pattern["acquirers"][:3]),
                    acquirer_type=atype,
                    gap_description=pattern["pattern"],
                    tech_domain=pattern["domain"],
                    evidence=pattern["keywords"],
                    market_size_estimate=pattern["market_size"],
                    urgency=self._estimate_urgency(pattern),
                )
                gaps.append(gap)
        
        # Enrichir avec recherche live si API disponible
        if self.serp_key:
            live_gaps = self._hunt_live_gaps()
            gaps.extend(live_gaps)
        
        # Trier par urgence
        gaps.sort(key=lambda g: g.urgency, reverse=True)
        return gaps
    
    def _estimate_urgency(self, pattern: Dict) -> float:
        """Estime l'urgence d'un gap (0-10)."""
        base = 5.0
        market = pattern.get("market_size", 0)
        if market > 30_000_000_000: base += 2.0
        elif market > 15_000_000_000: base += 1.0
        if len(pattern.get("acquirers", [])) > 3: base += 1.0
        return min(base, 10.0)
    
    def _hunt_live_gaps(self) -> List[TechGap]:
        """Recherche de gaps en temps réel via SERP API."""
        gaps = []
        queries = [
            "tech acquisition trends 2025 2026",
            "enterprise software gaps underserved",
            "corporate development priorities GAFAM",
            "emerging technology acquisition targets",
        ]
        
        try:
            import requests
            for q in queries[:3]:
                resp = requests.get(
                    "https://serpapi.com/search",
                    params={"engine": "google", "q": q, "api_key": self.serp_key, "num": 5},
                    timeout=15,
                )
                if resp.status_code == 200:
                    for result in resp.json().get("organic_results", [])[:3]:
                        # Analyser le titre/snippet pour détecter des gaps
                        title = result.get("title", "")
                        snippet = result.get("snippet", "")
                        gap = self._parse_search_for_gap(title, snippet)
                        if gap:
                            gaps.append(gap)
                time.sleep(1)
        except Exception as e:
            log.debug(f"[LiveGaps] Erreur: {e}")
        
        return gaps
    
    def _parse_search_for_gap(self, title: str, snippet: str) -> Optional[TechGap]:
        """Tente d'extraire un gap d'un résultat de recherche."""
        text = f"{title} {snippet}".lower()
        
        domain_keywords = {
            TechDomain.AI_ML: ["ai", "machine learning", "llm", "genai"],
            TechDomain.CYBERSECURITY: ["cybersecurity", "security", "zero trust"],
            TechDomain.FINTECH: ["fintech", "banking", "payments"],
            TechDomain.HEALTHTECH: ["healthtech", "medical", "clinical"],
            TechDomain.CLEANTECH: ["cleantech", "energy", "sustainability"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                if any(w in text for w in ["acquisition", "acquire", "buy", "invest", "gap", "need"]):
                    return TechGap(
                        gap_description=title[:200],
                        tech_domain=domain,
                        evidence=[title, snippet[:200]],
                        market_size_estimate=5_000_000_000,  # Estimation conservatrice
                        urgency=6.0,
                    )
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT BUILDER — Construit le projet vendable
# ══════════════════════════════════════════════════════════════════════════════

class MegaProjectBuilder:
    """Construit un projet vendable à partir d'un gap détecté."""
    
    # Coûts de construction estimés par domaine (en euros)
    BUILD_COSTS = {
        TechDomain.AI_ML: (500_000, 12),
        TechDomain.CYBERSECURITY: (400_000, 10),
        TechDomain.FINTECH: (600_000, 14),
        TechDomain.HEALTHTECH: (800_000, 18),
        TechDomain.CLEANTECH: (700_000, 16),
        TechDomain.DATA_INFRA: (450_000, 12),
        TechDomain.DEVTOOLS: (300_000, 8),
        TechDomain.EDGE_COMPUTING: (550_000, 14),
        TechDomain.SAAS_B2B: (400_000, 10),
        TechDomain.BIOTECH: (1_500_000, 24),
        TechDomain.ROBOTICS: (1_000_000, 18),
    }
    
    # Teams types par domaine
    TEAM_TEMPLATES = {
        TechDomain.AI_ML: ["ML Engineer Senior", "Data Scientist", "Backend Engineer", "DevOps", "Product Manager"],
        TechDomain.CYBERSECURITY: ["Security Architect", "Pentester Senior", "Backend Engineer", "DevOps"],
        TechDomain.FINTECH: ["Backend Engineer", "Compliance Expert", "Frontend Engineer", "Security Engineer"],
        TechDomain.HEALTHTECH: ["ML Engineer", "Clinical Data Expert", "Regulatory Affairs", "Backend Engineer"],
    }
    
    def build_from_gap(self, gap: TechGap) -> MegaProject:
        """Construit un MegaProject à partir d'un gap détecté."""
        cost_info = self.BUILD_COSTS.get(gap.tech_domain, (500_000, 12))
        
        # Prix de vente: 30x-80x le coût de construction (multiple tech standard)
        sale_min = max(15_000_000, cost_info[0] * 30)
        sale_max = max(40_000_000, cost_info[0] * 80)
        
        project = MegaProject(
            name=self._generate_project_name(gap),
            description=f"Solution innovante: {gap.gap_description}",
            tech_domain=gap.tech_domain,
            stage=ProjectStage.DETECTED,
            estimated_sale_price_min=sale_min,
            estimated_sale_price_max=sale_max,
            tam=gap.market_size_estimate,
            sam=gap.market_size_estimate * 0.15,  # 15% du TAM
            som=gap.market_size_estimate * 0.02,   # 2% du TAM
            target_acquirers=self._parse_acquirers(gap),
            primary_acquirer=gap.acquirer_name.split(",")[0].strip() if gap.acquirer_name else "",
            acquirer_type=gap.acquirer_type,
            gaps_addressed=[gap],
            build_cost_estimate=cost_info[0],
            build_time_months=cost_info[1],
            team_needed=self.TEAM_TEMPLATES.get(gap.tech_domain, ["Full-Stack Engineer", "Product Manager"]),
            tech_stack=self._suggest_tech_stack(gap.tech_domain),
        )
        
        # Évaluer le moat
        project.moat_description = self._assess_moat(gap)
        project.unique_data = gap.tech_domain in (TechDomain.HEALTHTECH, TechDomain.BIOTECH, TechDomain.FINTECH)
        project.network_effects = gap.tech_domain in (TechDomain.SAAS_B2B, TechDomain.DATA_INFRA)
        
        project.compute_scores()
        return project
    
    def _generate_project_name(self, gap: TechGap) -> str:
        domain_names = {
            TechDomain.AI_ML: "NeuraForge",
            TechDomain.CYBERSECURITY: "CyberVault",
            TechDomain.FINTECH: "FinEdge",
            TechDomain.HEALTHTECH: "MedSynth",
            TechDomain.CLEANTECH: "GreenPulse",
            TechDomain.DATA_INFRA: "DataNexus",
            TechDomain.DEVTOOLS: "DevForge",
            TechDomain.EDGE_COMPUTING: "EdgeMind",
            TechDomain.SAAS_B2B: "EnterprisePulse",
            TechDomain.BIOTECH: "BioSynth",
        }
        base = domain_names.get(gap.tech_domain, "InnoProject")
        return f"{base}_{uuid.uuid4().hex[:4].upper()}"
    
    def _parse_acquirers(self, gap: TechGap) -> List[Dict]:
        acquirers = []
        for name in gap.acquirer_name.split(","):
            name = name.strip()
            if name:
                acquirers.append({
                    "name": name,
                    "type": gap.acquirer_type.value,
                    "fit_reason": gap.gap_description[:100],
                })
        return acquirers
    
    def _suggest_tech_stack(self, domain: TechDomain) -> List[str]:
        stacks = {
            TechDomain.AI_ML: ["Python", "PyTorch", "FastAPI", "Kubernetes", "PostgreSQL", "Redis"],
            TechDomain.CYBERSECURITY: ["Rust", "Go", "Kubernetes", "Kafka", "PostgreSQL"],
            TechDomain.FINTECH: ["Python", "Go", "PostgreSQL", "Kafka", "Kubernetes", "React"],
            TechDomain.HEALTHTECH: ["Python", "R", "FastAPI", "PostgreSQL", "Docker", "FHIR"],
            TechDomain.DATA_INFRA: ["Rust", "Python", "Apache Arrow", "Kafka", "Kubernetes"],
            TechDomain.DEVTOOLS: ["TypeScript", "Rust", "PostgreSQL", "Redis", "Docker"],
        }
        return stacks.get(domain, ["Python", "FastAPI", "PostgreSQL", "Docker"])
    
    def _assess_moat(self, gap: TechGap) -> str:
        if gap.tech_domain in (TechDomain.HEALTHTECH, TechDomain.BIOTECH):
            return "Données cliniques propriétaires + certifications réglementaires = barrière élevée"
        elif gap.tech_domain == TechDomain.CYBERSECURITY:
            return "Brevets algorithmiques + base de menaces propriétaire = défensibilité forte"
        elif gap.tech_domain == TechDomain.AI_ML:
            return "Modèles fine-tunés sur données sectorielles + effets de réseau = avantage cumulatif"
        elif gap.tech_domain == TechDomain.FINTECH:
            return "Licences réglementaires + intégrations bancaires = time-to-market competitor 18+ mois"
        return "Expertise technique spécialisée + first-mover advantage"


# ══════════════════════════════════════════════════════════════════════════════
# M&A CONTACT FINDER — Trouve les contacts Corp Dev / M&A
# ══════════════════════════════════════════════════════════════════════════════

class MnAContactFinder:
    """Trouve les contacts M&A et Corporate Development."""
    
    def __init__(self):
        self._apollo_key = _gs("APOLLO_API_KEY")
        self._linkedin_key = _gs("RAPIDAPI_KEY")
    
    def find_contacts(self, acquirer_name: str) -> List[Dict]:
        """Trouve les décideurs M&A d'un acquéreur."""
        contacts = []
        
        if not self._apollo_key:
            return self._get_known_contacts(acquirer_name)
        
        try:
            import requests
            resp = requests.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json={
                    "api_key": self._apollo_key,
                    "q_organization_name": acquirer_name,
                    "person_titles": [
                        "corporate development", "m&a", "head of acquisitions",
                        "VP strategy", "business development", "CTO",
                        "chief strategy officer",
                    ],
                    "person_seniorities": ["c_suite", "vp", "director"],
                    "page": 1, "per_page": 5,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                for person in resp.json().get("people", []):
                    contacts.append({
                        "name": f"{person.get('first_name', '')} {person.get('last_name', '')}",
                        "title": person.get("title", ""),
                        "email": person.get("email", ""),
                        "linkedin": person.get("linkedin_url", ""),
                        "company": acquirer_name,
                    })
        except Exception as e:
            log.debug(f"[M&A] Contact search error: {e}")
        
        if not contacts:
            contacts = self._get_known_contacts(acquirer_name)
        
        return contacts
    
    def _get_known_contacts(self, company: str) -> List[Dict]:
        """Contacts M&A connus des grandes entreprises (public)."""
        # Ces infos sont publiques (LinkedIn, sites corporate)
        known = {
            "Google": [{"title": "VP Corporate Development", "department": "Corp Dev"}],
            "Microsoft": [{"title": "VP Corporate Strategy", "department": "M&A"}],
            "Amazon": [{"title": "Director Business Development", "department": "Corp Dev"}],
            "Salesforce": [{"title": "SVP Corporate Development", "department": "M&A"}],
            "Thales": [{"title": "VP Strategy & M&A", "department": "Strategy"}],
        }
        result = known.get(company, [{"title": "Corporate Development", "department": "M&A"}])
        return [{"name": "À identifier via Apollo", "company": company, **r} for r in result]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class MegaProjectHunter:
    """Agent de chasse de projets innovants 15M-40M€+."""
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self._gap_detector = GapDetector()
        self._project_builder = MegaProjectBuilder()
        self._contact_finder = MnAContactFinder()
        
        # State
        self._projects: List[MegaProject] = []
        self._gaps: List[TechGap] = []
        self._cycle_count = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # NAYA integrations
        self._db = None
        self._discretion = None
        self._event_stream = None
        
        log.info("[MegaProjectHunter] Initialisé — V%s", self.VERSION)
    
    def set_database(self, db): self._db = db
    def set_discretion(self, protocol): self._discretion = protocol
    def set_event_stream(self, stream): self._event_stream = stream
    
    def hunt_cycle(self, acquirer_types: List[AcquirerType] = None) -> Dict:
        """Cycle complet: detect gaps → build projects → find contacts."""
        cycle_id = f"MEGA_{uuid.uuid4().hex[:6].upper()}"
        self._cycle_count += 1
        
        log.info(f"[{cycle_id}] Cycle de chasse Mega Projects #{self._cycle_count}")
        
        result = {
            "cycle_id": cycle_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "gaps_detected": 0,
            "projects_built": 0,
            "total_pipeline_value": 0.0,
            "projects": [],
        }
        
        # Phase 1: Détecter les gaps
        gaps = self._gap_detector.detect_gaps(acquirer_types)
        self._gaps = gaps
        result["gaps_detected"] = len(gaps)
        
        # Phase 2: Construire les projets (top 10 gaps)
        for gap in gaps[:10]:
            project = self._project_builder.build_from_gap(gap)
            
            # Phase 3: Trouver contacts M&A
            if project.primary_acquirer:
                contacts = self._contact_finder.find_contacts(project.primary_acquirer)
                project.ma_contacts = contacts
            
            project.compute_scores()
            
            with self._lock:
                self._projects.append(project)
            
            result["projects"].append(project.to_dict())
            result["total_pipeline_value"] += project.estimated_sale_price_min
            
            # Persister
            self._persist_project(project)
            
            # Stream
            if self._event_stream and hasattr(self._event_stream, "broadcast"):
                try:
                    self._event_stream.broadcast({
                        "type": "MEGA_PROJECT_DETECTED",
                        "source": "MEGA_PROJECT_HUNTER",
                        "data": {"id": project.id, "name": project.name,
                                 "value_min": project.estimated_sale_price_min,
                                 "score": project.overall_score},
                    })
                except Exception:
                    pass
        
        result["projects_built"] = len(result["projects"])
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        log.info(
            f"[{cycle_id}] Terminé — {result['projects_built']} projets, "
            f"Pipeline: {result['total_pipeline_value']:,.0f}€"
        )
        return result
    
    def _persist_project(self, project: MegaProject):
        if not self._db: return
        try:
            data = project.to_dict()
            if self._discretion:
                data = self._discretion.mask(data)
            self._db.log_event("MEGA_PROJECT", data, "HUNTING_AGENTS.mega_project", "HIGH")
        except Exception as e:
            log.debug(f"[Persist] {e}")
    
    # ── Autonomous Mode ──────────────────────────────────────────────────
    
    def start_autonomous(self, interval_seconds: int = 86400):
        """Lance la chasse autonome (par défaut 1x/jour)."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(
            target=self._auto_loop, args=(interval_seconds,),
            daemon=True, name="MegaProjectHunter-Auto",
        )
        self._thread.start()
        log.info(f"[MegaProjectHunter] Autonome démarré — cycle toutes les {interval_seconds}s")
    
    def stop_autonomous(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
    
    def _auto_loop(self, interval: int):
        while self._running:
            try: self.hunt_cycle()
            except Exception as e: log.error(f"[MegaProjectHunter] Erreur: {e}")
            time.sleep(interval)
    
    # ── Query Methods ────────────────────────────────────────────────────
    
    def get_top_projects(self, n: int = 5) -> List[Dict]:
        with self._lock:
            sorted_p = sorted(self._projects, key=lambda p: p.overall_score, reverse=True)
            return [p.to_dict() for p in sorted_p[:n]]
    
    def get_projects_by_domain(self, domain: TechDomain) -> List[Dict]:
        with self._lock:
            return [p.to_dict() for p in self._projects if p.tech_domain == domain]
    
    def get_stats(self) -> Dict:
        with self._lock:
            total_value = sum(p.estimated_sale_price_min for p in self._projects)
            return {
                "version": self.VERSION,
                "total_cycles": self._cycle_count,
                "total_projects": len(self._projects),
                "total_gaps": len(self._gaps),
                "total_pipeline_value": total_value,
                "autonomous_running": self._running,
                "by_domain": {d.value: sum(1 for p in self._projects if p.tech_domain == d)
                              for d in TechDomain if any(p.tech_domain == d for p in self._projects)},
            }
    
    def to_dict(self) -> Dict:
        return self.get_stats()
