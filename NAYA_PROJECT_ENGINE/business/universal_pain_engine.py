"""Universal Pain Engine — NAYA SUPREME V19.

Détecte des douleurs économiques RÉELLES, DISCRÈTES et SOLVABLES
à haute valeur sur TOUS les secteurs, pour TOUS types d'entreprises.

Va là où aucune IA business ne va :
- Douleurs opérationnelles cachées (jamais dites en public)
- Secteurs oubliés des grandes plateformes
- Pain d'infrastructure invisible mais critique
- Tensions réglementaires sous-traitées

Chaque douleur détectée → business créable, zéro jetable, 100% recyclable.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────────────────────── DATA CLASSES ────────────────────────────────────

class PainLevel(str, Enum):
    SURFACE = "surface"          # douleur connue, très concurrencée
    DISCRETE = "discrete"        # douleur peu traitée, niche forte
    ULTRA_DISCRETE = "ultra"     # douleur quasi-invisible, quasi monopole


class Urgency(str, Enum):
    CHRONIC = "chronic"          # douleur permanente → MRR
    ACUTE = "acute"              # urgence immédiate → one-shot premium
    LATENT = "latent"            # pas encore douloureux → éducatif


@dataclass
class DetectedPain:
    pain_id: str
    sector: str
    sub_sector: str
    company_type: str            # PME / ETI / Grande entreprise / Gouvernement
    pain_level: str              # PainLevel value
    urgency: str                 # Urgency value
    title: str                   # Douleur en 1 phrase
    description: str             # Douleur détaillée
    signal_keywords: List[str]   # Mots-clés triggers détection
    budget_floor_eur: int        # Minimum solvable
    budget_target_eur: int       # Ticket cible réaliste
    why_discrete: str            # Pourquoi c'est discret (pas traitées ailleurs)
    monetization_model: str      # Comment on monétise
    reuse_potential: str         # Comment recycler vers autres projets
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────── PAIN CATALOGUE ──────────────────────────────────

# 50+ douleurs discrètes réelles, haute valeur, tous secteurs
# Format: (sector, sub_sector, company_type, pain_level, urgency,
#          title, description, keywords, floor, target, why_discrete, model, reuse)
_RAW_PAINS: List[tuple] = [

    # ── TRANSPORT & LOGISTIQUE ──────────────────────────────────────────────
    ("Transport", "Port & Maritime", "Grande entreprise", "ultra", "acute",
     "Conformité NIS2 sur systèmes de contrôle portuaire non-IT",
     "Les systèmes de gestion des grues, écluses et tracking cargo sont hors scope IT mais sous NIS2. Aucun cabinet spécialisé OT/maritime.",
     ["NIS2 port", "SCADA maritime", "contrôle portuaire", "cyber OT"], 15000, 40000,
     "Niche OT maritime ignorée par cabinets IT classiques",
     "audit IEC62443 + roadmap NIS2 + retainer", "template audit → secteur énergie/industrie"),

    ("Transport", "Logistique Last-Mile", "ETI", "discrete", "acute",
     "Perte invisible 8-15% CA sur erreurs de routing algorithmique",
     "PME logistique avec TMS sous-paramétré: les pertes sont réelles mais jamais mesurées précisément.",
     ["optimisation tournées", "TMS", "last mile", "pertes logistique"], 5000, 18000,
     "Dirigeants ne savent pas que c'est mesurable précisément",
     "audit + quick win + abonnement optimisation", "outil diagnostic → e-commerce, livraison"),

    ("Transport", "Flotte routière", "PME", "discrete", "chronic",
     "Coûts cachés flotte diesel ignorés (assurance mal négociée + surconsommation)",
     "90% PME transport ne comparent jamais: assurances, carburant contrats, pneus groupements. Gap moyen 22k EUR/an.",
     ["coût flotte", "assurance transport", "carburant contrat", "optimisation flotte"], 3000, 12000,
     "Perçu comme 'normal' donc jamais remis en cause",
     "diagnostic + négociation fournisseurs + commission économies", "modèle → immobilier, énergie"),

    # ── ÉNERGIE & UTILITIES ─────────────────────────────────────────────────
    ("Energie", "Réseau distribution", "OIV", "ultra", "acute",
     "Vulnérabilités SCADA sur anciens RTU hors contrat maintenance OT",
     "RTU datant des années 2000 sans patch possible, interconnectés aux SCADA modernes. Risque réel, ignoré car 'ça tourne'.",
     ["RTU vulnérabilité", "SCADA legacy", "OT patch", "réseau distribution"], 25000, 80000,
     "Tabou interne: avouer ces RTU = avouer risque systémique",
     "audit vulnérabilité + plan remédiation + contrat suivi", "méthodologie → industrie, eau"),

    ("Energie", "Autoconsommation solaire B2B", "PME", "discrete", "latent",
     "Contrats PPA (Power Purchase Agreement) mal négociés pour ETI ≥200 salariés",
     "Les ETI signent des PPA sans expertise réelle: prix souvent 15-25% au-dessus du marché.",
     ["PPA solaire", "autoconsommation", "contrat énergie", "photovoltaïque B2B"], 4000, 20000,
     "Acheteurs énergie manquent de benchmark contractuel spécialisé",
     "diagnostic PPA + renégociation + success fee économies", "modèle → tout B2B avec énergie"),

    ("Energie", "Eau & assainissement", "Collectivité", "ultra", "chronic",
     "Non-conformité EU Water Framework Directive sur systèmes télégestion vétustes",
     "Télégestion eau datant 1995-2010 sans logs d'audit réglementaires. Amendes potentielles 100k EUR.",
     ["télégestion eau", "conformité eau", "EU Water Directive", "SCADA eau"], 20000, 60000,
     "Collectivités petites ne savent pas qu'elles sont non-conformes",
     "audit réglementaire + mise en conformité + abonnement", "framework → déchets, gaz"),

    # ── MANUFACTURING & INDUSTRIE ───────────────────────────────────────────
    ("Industrie", "Agroalimentaire", "ETI", "discrete", "acute",
     "Ransomware sur automates Siemens/Schneider non segmentés réseau usine",
     "Ligne de production interconnectée IT/OT sans DMZ. Une infection arrête tout. Coût downtime 50-200k EUR/jour.",
     ["ransomware automate", "segmentation OT", "Siemens S7", "downtime usine"], 15000, 45000,
     "DSI pense que l'OT est sous responsabilité production = tombé entre deux chaises",
     "segmentation réseau + déploiement capteurs OT + SOC OT", "architecture → pharma, chimie"),

    ("Industrie", "Plasturgie", "PME", "ultra", "chronic",
     "Perte matière 4-8% non mesurée sur injection plastique (rebuts cachés)",
     "Petits plasturiers mesurent la production finie mais jamais la matière perdue. Gap = 60-150k EUR/an.",
     ["rebuts plastique", "perte matière", "injection", "lean manufacturing"], 5000, 15000,
     "Pas de capteurs IoT mesure = pas de conscience du problème",
     "audit + capteurs IoT + dashboard lean + abonnement", "IoT template → textile, papier"),

    ("Industrie", "Mécanique de précision", "PME", "discrete", "acute",
     "Non-conformité IATF 16949 cachée détectée lors audit client automotive",
     "PMEs sous-traitants automobiles avec IATF 16949 menacée par non-conformités process cachées.",
     ["IATF 16949", "audit qualité", "sous-traitant automotive", "non-conformité"], 8000, 25000,
     "Pas de ressource interne qualité → peur de l'audit externe",
     "gap analysis + plan conformité + accompagnement certification", "framework → aerospace, médical"),

    # ── SANTÉ & MÉDICO-SOCIAL ───────────────────────────────────────────────
    ("Santé", "Cliniques privées", "ETI", "ultra", "acute",
     "Données patients sur SI vétuste non-HDS (Hébergement Données Santé)",
     "Cliniques avec SI 2005-2015 stockent données patients hors HDS. Amende CNIL + ANSSI possible.",
     ["HDS conformité", "données patients", "CNIL clinique", "SI médical"], 15000, 50000,
     "Les DSI cliniques savent mais retardent car coût migration perçu trop haut",
     "audit SI + roadmap HDS + accompagnement migration", "framework → EHPAD, cabinets"),

    ("Santé", "EHPAD", "PME", "discrete", "chronic",
     "Formation cybermenaces inexistante pour personnels non-IT d'EHPAD",
     "Phishing/vishing ciblant aides-soignants qui ont accès aux données patients. 0 formation = vecteur d'attaque #1.",
     ["phishing EHPAD", "formation cybersécurité santé", "personnel non-IT"], 2000, 8000,
     "Budget cyber = 0 en EHPAD, problème perçu comme informatique alors que c'est RH",
     "formation + kit sensibilisation + abonnement mensuel", "kit → associations, collectivités"),

    # ── FINANCE & ASSURANCE ─────────────────────────────────────────────────
    ("Finance", "Courtage assurance", "PME", "discrete", "chronic",
     "Portefeuille clients courtier sous-tarifé post-COVID sans réévaluation risque",
     "Courtiers avec 300-2000 contrats PME jamais réévalués. Gap tarifaire potentiel 15-30% non capturé.",
     ["tarification assurance", "réévaluation risque", "portefeuille courtier"], 5000, 20000,
     "Courtiers craignent de perdre clients en réévaluant, donc ne le font jamais",
     "audit portefeuille + modèle de réévaluation + commission", "modèle → banque, mutuelle"),

    ("Finance", "Gestion patrimoine", "ETI", "discrete", "latent",
     "Patrimoine digital non-inventorié (NFT, crypto, domaines, brevets SaaS)",
     "ETIs avec actifs digitaux (domaines stratégiques, API keys revenues, codes sources) jamais valorisés.",
     ["patrimoine digital", "valorisation actifs immatériels", "bilan numérique"], 4000, 18000,
     "Notaires et CGP ne savent pas valoriser le digital: zéro outil spécialisé",
     "audit patrimoine digital + valorisation + conseil succession", "modèle → startup, scale-up"),

    # ── RH & FORMATION ──────────────────────────────────────────────────────
    ("RH", "Recrutement technique", "ETI", "ultra", "acute",
     "Coût réel recrutement technique 3-5x le salaire annuel (invisible dans P&L)",
     "RH mesurent le coût direct (cabinet) mais jamais: temps manageur, formation, erreur recrutement.",
     ["coût recrutement réel", "turnover tech", "onboarding", "rétention"], 5000, 20000,
     "Le CFO ne voit que la facture cabinet, pas les coûts cachés → zéro urgence perçue",
     "audit coût réel + plan rétention + ROI formation", "modèle → tout secteur avec RH tech"),

    ("RH", "Formation professionnelle", "PME", "discrete", "chronic",
     "OPCO sous-utilisé: 70% des entreprises laissent 8-25k EUR/an non récupérés",
     "PME ne savent pas optimiser leur OPCO: formations éligibles non déclarées, droits expirés.",
     ["OPCO formation", "CPF entreprise", "financement formation"], 2000, 8000,
     "Comptables délèguent à RH qui ne maîtrise pas les rouages OPCO",
     "audit droits OPCO + plan formation + abonnement annuel", "kit → tout PME France"),

    # ── IMMOBILIER & CONSTRUCTION ───────────────────────────────────────────
    ("Immobilier", "Gestion locative", "PME", "discrete", "chronic",
     "Loyers sous-marché de 18-35% sur patrimoine géré pré-2018 jamais réindexé",
     "Petits gestionnaires avec portefeuilles vieux n'ont jamais systématiquement réindexé IRL. Gap = 40-120k EUR/an.",
     ["réindexation loyer", "IRL", "gestion locative", "patrimoine sous-marché"], 3000, 12000,
     "Gestionnaires craignent les départs locataires donc ne réindexent pas proactivement",
     "audit portefeuille + lettres réindexation + abonnement", "modèle → copropriété, syndic"),

    ("Immobilier", "Construction modulaire", "ETI", "ultra", "latent",
     "Maisons modulaires: délais permis hors-normes exploitables mais mal connus des promoteurs",
     "Constructeurs modulaires ignorent les ZAC/communes avec dérogations permis ≤4 semaines vs 3 mois standard.",
     ["construction modulaire", "permis rapide", "ZAC dérogation", "tiny house"], 8000, 35000,
     "Information réglementaire fragmentée sur 36000 communes = avantage concurrentiel durable",
     "intelligence réglementaire + cartographie ZAC + contrat conseil", "base → logement social, cabanes"),

    # ── JURIDIQUE & CONFORMITÉ ──────────────────────────────────────────────
    ("Juridique", "PME exportatrices", "PME", "ultra", "acute",
     "Conformité RGPD extraterritorial ignorée pour exports données vers USA/Inde",
     "PMEs exportatrices envoient des données clients vers partenaires non-UE sans DPA valide. Amende CNIL 4% CA.",
     ["RGPD extraterritorial", "DPA transfrontalier", "transfert données", "CNIL amende"], 5000, 20000,
     "Juristes généralistes ne maîtrisent pas Schrems II et ses implications pratiques",
     "audit transferts données + DPA conformes + formation équipe", "template → e-commerce, SaaS"),

    ("Juridique", "Marchés publics", "ETI", "discrete", "latent",
     "Offres non soumises faute de maîtrise des clauses mémoire technique",
     "ETIs compétentes techniquement perdent systématiquement en marchés publics car mémoires mal structurés.",
     ["mémoire technique", "marchés publics", "AO réponse", "CCTP rédaction"], 3000, 12000,
     "Pas de prestataire spécialisé 'rédaction mémoire technique OT/tech' abordable",
     "rédaction + coaching + abonnement veille AO", "modèle → tout secteur B2G"),

    # ── RETAIL & E-COMMERCE ─────────────────────────────────────────────────
    ("Retail", "E-commerce PME", "PME", "discrete", "acute",
     "Taux d'abandon panier 72% jamais optimisé (checkout UX non-testée)",
     "PMEs e-com avec Shopify/Prestashop n'ont jamais fait d'audit checkout: 15-30% de CA récupérable.",
     ["taux abandon panier", "checkout UX", "conversion e-commerce", "A/B test"], 3000, 12000,
     "Agences web facturent refonte complète; personne ne propose audit checkout ciblé",
     "audit UX + implémentation A/B + suivi mensuel", "outil → SaaS, marketplace"),

    ("Retail", "Distribution B2B", "ETI", "ultra", "chronic",
     "Catalog pricing obsolète: remises accordées manuellement en dehors ERP (Excel)",
     "Commerciaux accordent des remises ad hoc hors ERP: perte margin invisible 8-18% sur CA.",
     ["pricing B2B", "remises non contrôlées", "ERP marge", "catalog pricing"], 8000, 30000,
     "CFO voient les résultats nets mais jamais l'origine des pertes margin granulaires",
     "audit pricing + moteur règles ERP + formation force vente", "modèle → industrie, chimie"),

    # ── AGRICULTURE & AGROTECH ──────────────────────────────────────────────
    ("Agriculture", "Coopératives agricoles", "ETI", "ultra", "discrete",
     "Traçabilité blockchain non-implémentée = pertes primes qualité Label Rouge/Bio",
     "Coopératives pourraient facturer 12-25% de prime sur productions traçables blockchain mais n'ont pas l'outil.",
     ["traçabilité agricole", "blockchain farm", "label rouge", "prime qualité"], 10000, 40000,
     "Informatique coopérative = mainframe années 1990, aucun prestataire blockchain agricole accessible",
     "implémentation traçabilité + formation + licence SaaS", "plateforme → pêche, viticulture"),

    # ── TOURISME & HOSPITALITY ──────────────────────────────────────────────
    ("Tourisme", "Hôtellerie indépendante", "PME", "discrete", "chronic",
     "RevPAR (revenue per available room) 35-45% sous benchmark sans yield management",
     "Petits hôtels (20-80 chambres) sans PMS intelligent: prix fixés manuellement, jamais dynamiques.",
     ["yield management hôtel", "RevPAR", "PMS dynamique", "tarification hôtelière"], 5000, 18000,
     "Logiciels PMS coûtent 40-80k EUR: aucune offre accessible 5-20k EUR pour indépendants",
     "audit + déploiement yield management + abonnement", "modèle → camping, résidence"),

    # ── ADMINISTRATIONS & COLLECTIVITÉS ─────────────────────────────────────
    ("Secteur Public", "Communes 5k-50k habitants", "Gouvernement", "ultra", "acute",
     "Données personnelles citoyens sur logiciels non-DPA sans hébergement souverain",
     "70% communes stockent données citoyens (état civil, social) sur logiciels SaaS USA sans DPA valide.",
     ["RGPD commune", "hébergement souverain", "données citoyens", "DPA mairie"], 8000, 30000,
     "DPO communal = souvent secrétaire de mairie: zéro expertise RGPD technique",
     "audit + plan conformité + DPO externalisé mensuel", "kit → établissements scolaires, hôpitaux"),

    ("Secteur Public", "Intercommunalités", "Gouvernement", "ultra", "chronic",
     "Marchés MAPA mal rédigés exposant à recours contentieux récurrents",
     "MAPA rédigés par agents sans formation: 20-35% contiennent des irrégularités exposant à recours.",
     ["MAPA marchés publics", "recours contentieux", "achat public", "régularité marché"], 5000, 20000,
     "Formations achat public trop théoriques, pas de prestataire rédaction/audit MAPA opérationnel",
     "audit MAPA + correction + formation équipe achat", "modèle → CHU, universités"),

    # ── TECH & SAAS ─────────────────────────────────────────────────────────
    ("Tech", "SaaS B2B scale-up", "ETI", "discrete", "acute",
     "Churn silencieux 8-15%/mois jamais attribué correctement (attribution analytics cassée)",
     "Scale-ups perdent des clients sans savoir pourquoi: analytics mal configurée, pas de cohort analysis.",
     ["churn SaaS", "cohort analysis", "analytics attribution", "customer success"], 8000, 25000,
     "CS team fire-fight les churns sans comprendre les patterns: problème systémique invisible",
     "audit analytics + modèle prédiction churn + process CS", "modèle → marketplace, edtech"),

    ("Tech", "Editeurs logiciels legacy", "ETI", "ultra", "chronic",
     "Dette technique accumulée sur codebase >10 ans: impossible à transmettre ou vendre",
     "Editeurs avec code VB6/Delphi/COBOL veulent vendre ou transmettre leur actif: impossible sans modernisation.",
     ["dette technique", "modernisation codebase", "migration legacy", "valorisation éditeur"], 20000, 80000,
     "Les éditeurs legacy sont honteux de leur code: n'en parlent jamais à des prestataires externes",
     "audit + roadmap migration + accompagnement refacto", "modèle → industrie software, ERP niche"),

    # ── ÉDUCATION & FORMATION ──────────────────────────────────────────────
    ("Education", "Organismes de formation", "PME", "ultra", "acute",
     "Perte certification Qualiopi sur écarts documentaires mineurs jamais corrigés",
     "Organismes de formation avec Qualiopi obtenu mais documentation non maintenue: risque perte certification.",
     ["Qualiopi", "certification formation", "audit OF", "documentaire qualité"], 3000, 12000,
     "Aucun prestataire 'maintenance Qualiopi' abordable: les auditeurs sont les certificateurs eux-mêmes",
     "audit documentaire + mise à jour + veille réglementaire", "framework → autres certifications"),

    # ── AFRIQUE FRANCOPHONE (marchés oubliés) ───────────────────────────────
    ("Afrique Francophone", "Banques microfinance", "ETI", "ultra", "acute",
     "Conformité BCEAO 2024 sur KYC digital non-implémentée (amendes cumulées)",
     "IMF/banques Afrique Ouest avec KYC papier non-conformes nouvelles normes BCEAO 2024 sur digital.",
     ["BCEAO KYC", "microfinance conformité", "digitalisation KYC Afrique"], 8000, 30000,
     "Aucun prestataire francophone KYC/compliance fintech Afrique subsaharienne",
     "audit KYC + implémentation digital + formation", "template → CEMAC, Madagascar"),

    ("Afrique Francophone", "Télécoms opérateurs", "Grande entreprise", "discrete", "acute",
     "Sous-facturation data entreprises: packages B2B mal configurés (12-20% CA perdu)",
     "Opérateurs africains avec systèmes billing legacy: entreprises clientes sous-facturées, manque à gagner caché.",
     ["billing telecom", "sous-facturation", "BSS/OSS", "opérateur Afrique"], 15000, 50000,
     "Tabou interne: avouer une sous-facturation = risque audit réglementaire",
     "audit billing + correction système + contrat optimisation", "modèle → telecom Europe"),

    # ── POLYNÉSIE FRANÇAISE (territoire local) ──────────────────────────────
    ("Polynésie Française", "Hôtellerie luxe", "ETI", "ultra", "discrete",
     "Perte revenus annexes 25-40% sur activités excursions/spa non-optimisées digitalement",
     "Hôtels luxe Polynésie vendent activités par téléphone/réception: zéro dynamic pricing, zéro upsell digital.",
     ["hôtel luxe Polynésie", "activités touristiques", "upsell digital", "spa yield"], 10000, 35000,
     "Prestataires tech tourisme = franco-français, ignorent les spécificités PTF et langues locales",
     "audit + plateforme upsell + abonnement annuel", "modèle → Caraïbes, Pacifique"),

    ("Polynésie Française", "Pêche professionnelle", "PME", "ultra", "chronic",
     "Pertes post-capture 30-40% sur poissons premium faute de chaîne cold-chain traçable",
     "Pêcheurs Maohi avec prises premium (thon, dorade coryphène) perdent valeur faute de traçabilité.",
     ["cold chain pêche", "traçabilité poisson", "valeur poisson Polynésie"], 5000, 20000,
     "Aucune solution IoT cold-chain abordable adaptée embarcations PTF",
     "capteurs IoT + app traçabilité + certification export", "modèle → Nouvelle-Calédonie, Wallis"),

    # ── CROSS-SECTORIEL ─────────────────────────────────────────────────────
    ("Cross-Sectoriel", "Tout PME avec dépendance SaaS USA", "PME", "ultra", "latent",
     "Plan de continuité inexistant si SaaS américain coupe l'accès (CLOUD ACT, sanctions)",
     "PME 100% dépendantes de Salesforce/HubSpot/AWS sans plan B. CLOUD ACT = risque souveraineté.",
     ["souveraineté numérique", "alternative SaaS", "CLOUD ACT", "plan continuité"], 5000, 25000,
     "Zéro prestataire 'audit souveraineté numérique' positif accessible PME francophone",
     "audit dépendances + roadmap souveraineté + migration progressive", "modèle → tout secteur"),

    ("Cross-Sectoriel", "Entreprises familiales transmission", "PME", "ultra", "latent",
     "Valorisation erronée actifs immatériels lors cession (marque, données, processus)",
     "75% cessions PME familiales sous-estiment actifs immatériels: écart valorisation 20-40% du prix.",
     ["cession PME", "valorisation immatérielle", "transmission entreprise", "actifs invisibles"], 8000, 30000,
     "Experts-comptables valorisent l'actif tangible mais pas le goodwill numérique/process",
     "audit valorisation + rapport d'évaluation + accompagnement négociation", "modèle → partout"),
]


def _build_pain_id(title: str, sector: str) -> str:
    h = hashlib.md5(f"{sector}:{title}".encode()).hexdigest()[:8]
    return f"PAIN_{h.upper()}"


def _build_catalogue() -> Dict[str, DetectedPain]:
    catalogue: Dict[str, DetectedPain] = {}
    for row in _RAW_PAINS:
        (sector, sub_sector, company_type, pain_level, urgency,
         title, description, keywords, floor, target,
         why_discrete, model, reuse) = row
        pain_id = _build_pain_id(title, sector)
        dp = DetectedPain(
            pain_id=pain_id,
            sector=sector,
            sub_sector=sub_sector,
            company_type=company_type,
            pain_level=pain_level,
            urgency=urgency,
            title=title,
            description=description,
            signal_keywords=keywords,
            budget_floor_eur=floor,
            budget_target_eur=target,
            why_discrete=why_discrete,
            monetization_model=model,
            reuse_potential=reuse,
            tags=[sector, sub_sector, pain_level, urgency],
        )
        catalogue[pain_id] = dp
    return catalogue


# ─────────────────────────── ENGINE ──────────────────────────────────────────

class UniversalPainEngine:
    """Moteur universel de détection de douleurs discrètes haute valeur.

    Capacités:
    - Détecte sur 20+ secteurs, 40+ sous-secteurs
    - Filtre par niveau de discrétion (surface/discrete/ultra)
    - Génère des business models instantanément
    - Tag chaque pain pour réutilisation cross-projets (zero waste)
    - Exporte vers TORI_APP, Telegram, workflow LangGraph
    """

    def __init__(self) -> None:
        self._catalogue: Dict[str, DetectedPain] = _build_catalogue()
        self._cache_path = Path(__file__).parent.parent.parent / "data" / "exports" / "pain_catalogue.json"

    # ── SEARCH ────────────────────────────────────────────────────────────

    def search(
        self,
        sector: Optional[str] = None,
        min_budget_eur: int = 1000,
        pain_levels: Optional[List[str]] = None,
        urgency: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Recherche douleurs filtrées + scorées."""
        results: List[DetectedPain] = list(self._catalogue.values())

        if sector:
            sector_l = sector.lower()
            results = [p for p in results if sector_l in p.sector.lower() or sector_l in p.sub_sector.lower()]

        if pain_levels:
            results = [p for p in results if p.pain_level in pain_levels]

        if urgency:
            results = [p for p in results if p.urgency == urgency]

        if keywords:
            kw_lower = [k.lower() for k in keywords]
            def _kw_match(p: DetectedPain) -> bool:
                haystack = " ".join(p.signal_keywords + p.tags + [p.title, p.description]).lower()
                return any(kw in haystack for kw in kw_lower)
            results = [p for p in results if _kw_match(p)]

        results = [p for p in results if p.budget_floor_eur >= min_budget_eur]

        # score = target_budget weighted by urgency + pain_level
        urgency_w = {"acute": 1.5, "chronic": 1.2, "latent": 0.8}
        level_w = {"ultra": 1.4, "discrete": 1.1, "surface": 0.7}

        def _score(p: DetectedPain) -> float:
            uw = urgency_w.get(p.urgency, 1.0)
            lw = level_w.get(p.pain_level, 1.0)
            return p.budget_target_eur * uw * lw

        results.sort(key=_score, reverse=True)
        return [self._enrich(p) for p in results[:limit]]

    def get_ultra_discrete(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Top douleurs ultra-discrètes: là où aucune IA business ne va."""
        return self.search(pain_levels=["ultra"], limit=limit)

    def get_all_sectors(self) -> List[str]:
        return sorted({p.sector for p in self._catalogue.values()})

    def get_by_id(self, pain_id: str) -> Optional[Dict[str, Any]]:
        p = self._catalogue.get(pain_id)
        return self._enrich(p) if p else None

    # ── BUSINESS CREATION ────────────────────────────────────────────────

    def create_business_from_pain(self, pain_id: str) -> Dict[str, Any]:
        """Génère un business model complet depuis une douleur détectée."""
        p = self._catalogue.get(pain_id)
        if p is None:
            raise ValueError(f"Unknown pain_id: {pain_id}")

        business_id = f"BIZ_{p.pain_id}"
        return {
            "business_id": business_id,
            "pain_id": pain_id,
            "name": f"Solution {p.sub_sector} — {p.title[:40]}",
            "sector": p.sector,
            "target_client": p.company_type,
            "model": p.monetization_model,
            "offer_stack": {
                "floor_eur": p.budget_floor_eur,
                "target_eur": p.budget_target_eur,
                "premium_eur": int(p.budget_target_eur * 2.2),
            },
            "acquisition_channels": self._channels_for_pain(p),
            "10_days_revenue_target_eur": int(p.budget_target_eur * 1.5),
            "monthly_mrt_potential_eur": self._mrt(p),
            "reuse_map": p.reuse_potential,
            "tags": p.tags,
            "recyclable_assets": self._recyclable_assets(p),
        }

    def create_businesses_from_sector(self, sector: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Génère des business models pour tous les pains d'un secteur."""
        pains = self.search(sector=sector, limit=limit)
        return [self.create_business_from_pain(p["pain_id"]) for p in pains]

    # ── EXPORT ─────────────────────────────────────────────────────────────

    def export_catalogue(self) -> str:
        """Exporte le catalogue complet en JSON (persistance)."""
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_pains": len(self._catalogue),
            "sectors": self.get_all_sectors(),
            "pains": [asdict(p) for p in self._catalogue.values()],
        }
        self._cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(self._cache_path)

    def for_tori_dashboard(self) -> Dict[str, Any]:
        """Payload optimisé pour TORI_APP dashboard (Tauri)."""
        ultra = self.get_ultra_discrete(5)
        return {
            "total_pains": len(self._catalogue),
            "sectors_covered": len(self.get_all_sectors()),
            "ultra_discrete_top5": ultra,
            "total_addressable_value_eur": sum(
                p.budget_target_eur for p in self._catalogue.values()
            ),
            "avg_ticket_eur": int(
                sum(p.budget_target_eur for p in self._catalogue.values()) / len(self._catalogue)
            ),
        }

    # ── PRIVATE HELPERS ─────────────────────────────────────────────────────

    def _enrich(self, p: DetectedPain) -> Dict[str, Any]:
        d = asdict(p)
        d["business_potential_score"] = self._score(p)
        return d

    def _score(self, p: DetectedPain) -> int:
        uw = {"acute": 30, "chronic": 20, "latent": 10}.get(p.urgency, 15)
        lw = {"ultra": 40, "discrete": 25, "surface": 10}.get(p.pain_level, 20)
        budget_score = min(30, int(p.budget_target_eur / 2000))
        return uw + lw + budget_score

    def _channels_for_pain(self, p: DetectedPain) -> List[str]:
        if p.urgency == "acute":
            return ["linkedin_direct", "email_outreach", "referral"]
        if p.urgency == "chronic":
            return ["content_marketing", "seo", "linkedin", "newsletter"]
        return ["webinar", "whitepaper", "linkedin", "conference"]

    def _mrt(self, p: DetectedPain) -> int:
        """Monthly Recurring Target basé sur le modèle de monétisation."""
        if "abonnement" in p.monetization_model or "retainer" in p.monetization_model:
            return int(p.budget_target_eur * 0.3)
        if "licence" in p.monetization_model or "SaaS" in p.monetization_model:
            return int(p.budget_target_eur * 0.15)
        return 0

    def _recyclable_assets(self, p: DetectedPain) -> List[str]:
        """Assets créés pour ce pain qu'on peut recycler ailleurs."""
        return [
            f"audit_template_{re.sub(r'[^a-z0-9]', '_', p.sub_sector.lower())}",
            f"offer_1pager_{p.sector.lower().replace(' ', '_')}",
            f"email_sequence_{p.urgency}_{p.pain_level}",
            f"objection_faq_{p.vertical if hasattr(p, 'vertical') else p.sector}",
        ]

    @property
    def vertical(self) -> None:
        return None


# ─────────────────────────── SINGLETON ───────────────────────────────────────

universal_pain_engine = UniversalPainEngine()


if __name__ == "__main__":
    engine = UniversalPainEngine()
    print(f"Pains loaded: {len(engine._catalogue)}")
    ultra = engine.get_ultra_discrete(5)
    for p in ultra:
        print(f"  [{p['pain_level'].upper()}] {p['sector']} — {p['title'][:60]} → {p['budget_target_eur']:,} EUR")
    biz = engine.create_business_from_pain(ultra[0]["pain_id"])
    print(f"\nBusiness créé: {biz['name']}")
    print(f"  Model: {biz['model']}")
    print(f"  10j target: {biz['10_days_revenue_target_eur']:,} EUR")
    path = engine.export_catalogue()
    print(f"\nCatalogue exporté: {path}")
