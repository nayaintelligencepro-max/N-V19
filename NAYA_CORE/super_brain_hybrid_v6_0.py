"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NAYA — SUPER BRAIN V6.1 — DOCTRINE FONDAMENTALE                          ║
║                                                                              ║
║  UNE SEULE RÈGLE:                                                           ║
║  Si la douleur est réelle + discrète + solvable → l'offre n'est pas        ║
║  refusable, car elle coûte MOINS CHER que la douleur elle-même.            ║
║                                                                              ║
║  CE QUI CHANGE PAR RAPPORT À V6.0:                                         ║
║  ✗ Plus de module ZeroWasteLoopV2 (recyclage de refus)                    ║
║  ✗ Plus de filtre MINIMUM_PAIN_SCORE arbitraire                            ║
║  ✗ Plus de templates d'offres génériques                                   ║
║  ✗ Plus de RecycleMode — l'offre juste ne se recycle pas                  ║
║                                                                              ║
║  ✓ NoiseFilter strict — filtre le bruit AVANT la détection                ║
║  ✓ RealCostVerifier — la douleur doit COÛTER plus que la solution         ║
║  ✓ DiscretenesGate — la douleur doit être non-verbalisée par le marché    ║
║  ✓ SolvabilityGate — on doit pouvoir la résoudre en 24/48/72H RÉELLEMENT  ║
║  ✓ PriceFromPain — le prix SORT de la douleur, pas d'une grille           ║
║  ✓ IrrefutableOffer — construite pour ne pas être refusable               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time, uuid, logging, math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

log = logging.getLogger("NAYA.BRAIN.V6")


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 0 — FILTRE DE BRUIT
# Élimine tout ce qui n'est pas une vraie douleur discrète
# ══════════════════════════════════════════════════════════════════════════════

class NoiseSignal(Enum):
    """Signaux de bruit à éliminer — ce ne sont PAS des douleurs solvables."""
    VAGUE_COMPLAINT    = "vague"       # "on aimerait mieux faire"
    ASPIRATIONAL       = "aspiration"  # "on veut grandir"
    ALREADY_SOLVED     = "solved"      # solution déjà en place
    NOT_DECISION_MAKER = "no_dm"       # contact pas décisionnaire
    NO_BUDGET_CAPACITY = "no_capacity" # aucune capacité à payer
    PUBLICLY_KNOWN     = "public"      # tout le monde le sait déjà
    COMPETITOR_ACTIVE  = "competed"    # concurrent résout déjà ça


# Signaux qui ÉLIMINENT une douleur (bruit certain)
NOISE_ELIMINATORS = [
    # L'entreprise a déjà une solution en cours
    "en cours", "on y travaille", "on a engagé", "déjà prestataire",
    "notre équipe gère", "on a une solution", "c'est prévu",
    # Pas de capacité de décision ou de paiement
    "faut demander au siège", "pas mon budget", "groupe décide",
    "on n'a pas les moyens", "zéro budget pour ça",
    # Aspiration sans douleur réelle
    "ce serait bien", "on aimerait un jour", "idéalement",
    "dans un monde idéal", "objectif long terme",
]

# Signaux de VRAIE douleur discrète (non-bruit)
REAL_PAIN_CONFIRMERS = [
    # Douleur financière concrète
    "on perd", "ça nous coûte", "on saigne", "on n'arrive pas à",
    "le cash manque", "les marges baissent", "impayés", "tréso tendue",
    "marges baissent", "marge en baisse", "rentabilité", "food cost",
    "trésorerie tendue", "cash flow", "chiffre d'affaires", "découvert",
    "dette fournisseur", "burn rate", "sous-tarifé", "impayé",
    # Douleur opérationnelle concrète
    "ça prend trop de temps", "on fait tout à la main", "c'est le chaos",
    "on compense", "on bricole", "erreurs récurrentes",
    "paperasse", "admin", "manuellement", "relances", "chronophage",
    "facturation", "recouvrement", "tâches répétitives",
    # Douleur humaine concrète
    "j'en peux plus", "seul face à", "personne ne comprend", "j'hésite à",
    "j'ose pas augmenter", "peur de perdre", "on sait pas pourquoi",
    "débordé", "surchargé", "stressé", "épuisé", "tout repose sur",
    # Douleur de marché concrète
    "clients partent", "on perd des contrats", "concurrent nous prend",
    "on sous-facture", "nos actifs dorment", "réseau non-activé",
    "churn", "attrition", "on stagne", "croissance bloquée",
    "incontrôlable", "incompréhensible", "inexpliqué", "sans savoir",
    # Expressions 2 mots courantes du scraper
    "relances manuelles", "impayés clients", "facturation chronophage",
    "marges baissent", "cash manque", "clients partent", "admin lourde",
    "trésorerie tendue", "coûts cachés", "temps perdu", "erreurs récurrentes",
    "sous-facturé", "mal facturé", "prix bas", "concurrence forte",
]


class NoiseFilter:
    """
    Filtre le bruit AVANT tout traitement.
    Principe: mieux vaut éliminer 10 vraies opportunités que traiter 1 fausse.
    """

    def is_noise(self, signal: str, context: Dict = None) -> Tuple[bool, str]:
        """
        Retourne (True, raison) si le signal est du bruit.
        Retourne (False, "") si le signal mérite d'être analysé.
        """
        s = signal.lower().strip()
        ctx = {k: str(v).lower() for k, v in (context or {}).items()}

        # Élimination directe par mots-clés de bruit
        for eliminator in NOISE_ELIMINATORS:
            if eliminator in s:
                return True, f"BRUIT_ELIMINATOR: '{eliminator}' → solution déjà en cours ou aspiration vague"

        # Signal trop court pour être une vraie douleur
        if len(s.split()) < 2:
            return True, "BRUIT_TROP_VAGUE: signal trop court, pas assez concret"

        # Vérifier présence d'un confirmateur de vraie douleur
        has_real_pain = any(confirmer in s for confirmer in REAL_PAIN_CONFIRMERS)
        
        # Si pas de confirmateur ET signal vague → bruit
        if not has_real_pain and not any(char.isdigit() for char in s):
            # Pas de chiffre, pas de confirmateur = probablement vague
            if len(s.split()) < 6:
                return True, "BRUIT_ASPIRATION: aucun indicateur de douleur concrète"

        return False, ""

    def filter_signals(self, signals: List[str], context: Dict = None) -> Tuple[List[str], List[str]]:
        """
        Trie les signaux en vrais signaux et bruits.
        Returns: (real_signals, noise_signals)
        """
        real, noise = [], []
        for sig in signals:
            is_n, _ = self.is_noise(sig, context)
            (noise if is_n else real).append(sig)
        return real, noise

    def filter(self, signals, context=None):
        """Alias de filter_signals — compatibilite avec les appels nf.filter()."""
        if not isinstance(signals, list):
            return {"real": [], "noise": []}
        real, noise = self.filter_signals(signals, context or {})
        return {"real": real, "noise": noise}

    def filter_profile(self, profile: Dict) -> Dict:
        """
        Filtre un profil complet — retourne profil nettoyé + rapport de bruit.
        """
        raw_signals = profile.get("signals", [])
        real_signals, noise_signals = self.filter_signals(raw_signals, profile)
        
        return {
            **profile,
            "signals": real_signals,           # Signaux nets
            "noise_removed": noise_signals,    # Ce qui a été éliminé
            "signal_quality": round(len(real_signals) / max(len(raw_signals), 1), 2),
            "qualifies": len(real_signals) >= 1,  # Au moins 1 signal réel
        }


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 1 — DOULEUR RÉELLE ET DISCRÈTE
# ══════════════════════════════════════════════════════════════════════════════

class DiscretenessLevel(Enum):
    """Niveau de discrétion de la douleur — plus c'est caché, plus c'est précieux."""
    VISIBLE    = 0   # Tout le monde le sait — peu de valeur différentielle
    SEMI_DISC  = 1   # Secteur averti le voit — opportunité moyenne
    DISCRETE   = 2   # Spécialiste détecte — bonne opportunité
    HIDDEN     = 3   # Seule une analyse fine révèle — excellente opportunité
    INVISIBLE  = 4   # Personne d'autre ne cherche ici — opportunité unique


class PainCategory(Enum):
    # ── Financier ────────────────────────────────────────────────────────────
    CASH_TRAPPED          = "cash_trapped"          # Cash bloqué dans mauvais postes
    MARGIN_INVISIBLE_LOSS = "margin_invisible_loss" # Marge perdue sans que ça se voit
    INVOICE_LEAK          = "invoice_leak"           # Argent non-facturé ou perdu en admin
    HIDDEN_COST           = "hidden_cost"            # Coûts cachés non-identifiés
    UNDERPRICED           = "underpriced"            # Prix trop bas vs valeur réelle
    # ── Opérationnel ─────────────────────────────────────────────────────────
    PROCESS_MANUAL_TAX    = "process_manual_tax"    # Temps perdu en tâches manuelles répétitives
    TALENT_FRAGILITY      = "talent_fragility"      # Dépendance critique à 1 personne
    COMPLIANCE_SILENT     = "compliance_silent"     # Non-conformité silencieuse (RGPD, etc.)
    # ── Marché ───────────────────────────────────────────────────────────────
    CLIENT_BLEED          = "client_bleed"          # Clients qui partent sans se plaindre
    COMPETITOR_BLIND      = "competitor_blind"      # Menace concurrentielle non-perçue
    DORMANT_ASSET         = "dormant_asset"         # Actif existant non-monétisé
    UNSEEN_SEGMENT        = "unseen_segment"        # Segment client non-adressé
    # ── Humain / Dirigeant ───────────────────────────────────────────────────
    FOUNDER_BOTTLENECK    = "founder_bottleneck"   # Tout passe par le fondateur
    GROWTH_BLOCK          = "growth_block"          # Frein interne à la croissance
    PRICING_PARALYSIS     = "pricing_paralysis"     # Incapacité à augmenter les prix


# Profil de chaque douleur : coût réel, discrétion, solvabilité
PAIN_PROFILES: Dict[PainCategory, Dict] = {
    PainCategory.CASH_TRAPPED: {
        "cost_ratio": 0.18,      # % du CA que cette douleur coûte par an
        "discreteness": DiscretenessLevel.DISCRETE,
        "solvable_hours": 24,
        "solution_cost_ratio": 0.02,   # Solution coûte 2% du CA
        "proof_template": "Libère {gain}€ de cash dans les 30 premiers jours",
        "industries": ["artisan_trades", "pme_b2b", "liberal_professions", "restaurant_food"],
        "verbal_triggers": ["tréso tendue", "le cash manque", "carnet plein mais", "trésorerie tendue", "impayés", "cash flow", "on n'a plus de cash", "dette fournisseur", "découvert", "liquidités"],
        "behavioral_triggers": ["impayés > 45j", "acompte < 20%", "paiement fin de chantier"],
    },
    PainCategory.MARGIN_INVISIBLE_LOSS: {
        "cost_ratio": 0.12,
        "discreteness": DiscretenessLevel.HIDDEN,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.025,
        "proof_template": "+{gain_pts} points de marge récupérés = {gain}€/an récurrents",
        "industries": ["restaurant_food", "pme_b2b", "ecommerce", "artisan_trades"],
        "verbal_triggers": ["marges baissent", "ça coûte plus cher", "inflation matières", "on perd de la marge", "marge en baisse", "moins rentable", "rentabilité baisse", "marges s'érodent", "on saigne sur", "pertes de marge"],
        "behavioral_triggers": ["EBE < 8%", "CA croît marge stagne", "prix stables > 18 mois"],
    },
    PainCategory.INVOICE_LEAK: {
        "cost_ratio": 0.09,
        "discreteness": DiscretenessLevel.SEMI_DISC,
        "solvable_hours": 24,
        "solution_cost_ratio": 0.015,
        "proof_template": "Récupère {gain}€ d'impayés + stoppe la fuite administrative",
        "industries": ["artisan_trades", "liberal_professions", "pme_b2b"],
        "verbal_triggers": ["on perd", "pas facturé", "oublié de facturer", "impayés", "relances manuelles", "factures en retard", "impayés clients", "paiements tardifs", "créances clients", "on n'arrive pas à se faire payer"],
        "behavioral_triggers": ["devis manuscrits", "facturation retardée", "relances manuelles"],
    },
    PainCategory.HIDDEN_COST: {
        "cost_ratio": 0.10,
        "discreteness": DiscretenessLevel.HIDDEN,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.02,
        "proof_template": "Identifie {gain}€ de coûts cachés — économies immédiates visibles en 72H",
        "industries": ["pme_b2b", "ecommerce", "startup_scaleup", "restaurant_food"],
        "verbal_triggers": ["ça nous coûte trop", "on sait pas pourquoi", "marges baissent", "coûts cachés", "food cost", "charges augmentent", "dépenses incontrôlables", "budget qui dérape", "frais incompréhensibles", "EBE en baisse"],
        "behavioral_triggers": ["abonnements non-audités", "fournisseurs jamais renégociés", "logiciels inutilisés"],
    },
    PainCategory.UNDERPRICED: {
        "cost_ratio": 0.25,     # Manque à gagner massif
        "discreteness": DiscretenessLevel.INVISIBLE,
        "solvable_hours": 24,
        "solution_cost_ratio": 0.02,
        "proof_template": "+{gain_pct}% de revenu sans changer 1 client ni 1 produit",
        "industries": ["liberal_professions", "artisan_trades", "startup_scaleup", "pme_b2b"],
        "verbal_triggers": ["j'ose pas augmenter", "clients négocient toujours", "concurrent plus cher", "sous-tarifé", "prix trop bas", "on sous-facture", "peur d'augmenter", "j'hésite à monter les prix"],
        "behavioral_triggers": ["TJM inférieur marché", "prix jamais remontés > 2 ans", "toujours disponible"],
    },
    PainCategory.PROCESS_MANUAL_TAX: {
        "cost_ratio": 0.08,
        "discreteness": DiscretenessLevel.DISCRETE,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.018,
        "proof_template": "{hours}H/semaine récupérées dès la première semaine = {gain}€/an de productivité",
        "industries": ["pme_b2b", "ecommerce", "artisan_trades", "healthcare_wellness"],
        "verbal_triggers": ["tout à la main", "ça prend trop de temps", "on bricole", "on compense", "tâches répétitives", "paperasse", "trop d'admin", "chronophage", "on fait tout manuellement", "perte de temps"],
        "behavioral_triggers": ["Excel pour tout", "copier-coller récurrent", "double saisie", "pas d'automatisation", "manuellement", "admin", "cabinet", "saisie manuelle", "tout en papier", "facturation lourde"],
    },
    PainCategory.CLIENT_BLEED: {
        "cost_ratio": 0.20,
        "discreteness": DiscretenessLevel.HIDDEN,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.025,
        "proof_template": "Stop l'hémorragie — {gain}€/an récupérés sur churn évité",
        "industries": ["startup_scaleup", "pme_b2b", "ecommerce", "liberal_professions"],
        "verbal_triggers": ["clients partent", "on perd des contrats", "renouvellements difficiles", "churn", "on perd des clients", "fidélisation difficile", "clients qui ne reviennent pas", "résiliations"],
        "behavioral_triggers": ["NPS jamais mesuré", "aucun entretien sortant", "churn non-monitoré"],
    },
    PainCategory.DORMANT_ASSET: {
        "cost_ratio": 0.20,
        "discreteness": DiscretenessLevel.INVISIBLE,
        "solvable_hours": 72,
        "solution_cost_ratio": 0.03,
        "proof_template": "Activation = {gain}€ de revenus nouveaux sans coût de structure additionnel",
        "industries": ["liberal_professions", "pme_b2b", "real_estate_investors", "diaspora_markets"],
        "verbal_triggers": ["réseau non-activé", "données qui dorment", "locaux vides", "expertise non-vendue", "actifs sous-utilisés", "capacités inutilisées", "potentiel inexploité", "stock dormant"],
        "behavioral_triggers": ["IP non-exploitée", "réseau LinkedIn inactif", "locaux sous-utilisés"],
    },
    PainCategory.FOUNDER_BOTTLENECK: {
        "cost_ratio": 0.12,
        "discreteness": DiscretenessLevel.INVISIBLE,
        "solvable_hours": 24,
        "solution_cost_ratio": 0.015,
        "proof_template": "Libère {hours}H/semaine du dirigeant = croissance débloquée",
        "industries": ["pme_b2b", "artisan_trades", "liberal_professions", "startup_scaleup"],
        "verbal_triggers": ["je fais tout moi-même", "seul face à", "personne d'autre peut", "tout repose sur moi", "j'en peux plus", "surchargé", "débordé", "je gère tout"],
        "behavioral_triggers": ["fondateur = commercial + ops + technique", "pas de délégation", "aucun copil"],
    },
    PainCategory.PRICING_PARALYSIS: {
        "cost_ratio": 0.22,
        "discreteness": DiscretenessLevel.INVISIBLE,
        "solvable_hours": 24,
        "solution_cost_ratio": 0.02,
        "proof_template": "+{gain_pct}% revenu sans perdre aucun client — prouvé en 30 jours",
        "industries": ["liberal_professions", "artisan_trades", "startup_scaleup", "pme_b2b"],
        "verbal_triggers": ["j'hésite à augmenter", "peur de perdre clients", "concurrent moins cher", "j'ose pas augmenter les prix", "on sous-facture", "marge insuffisante", "prix trop bas vs valeur"],
        "behavioral_triggers": ["prix stables > 2 ans", "marge en baisse", "jamais refusé une mission"],
    },
    PainCategory.COMPLIANCE_SILENT: {
        "cost_ratio": 0.08,
        "discreteness": DiscretenessLevel.DISCRETE,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.015,
        "proof_template": "Mise en conformité évite {gain}€ de risque amende + préserve contrats clients",
        "industries": ["healthcare_wellness", "pme_b2b", "startup_scaleup"],
        "verbal_triggers": ["on n'est pas encore conforme", "rgpd pas fait", "contrats à risque"],
        "behavioral_triggers": ["données clients non-chiffrées", "contrats anciens", "CGV absentes"],
    },
    PainCategory.TALENT_FRAGILITY: {
        "cost_ratio": 0.15,
        "discreteness": DiscretenessLevel.HIDDEN,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.025,
        "proof_template": "Sécurise {risk_eur}€ de CA qui dépend d'une seule personne",
        "industries": ["pme_b2b", "startup_scaleup", "liberal_professions"],
        "verbal_triggers": ["si untel part", "tout repose sur lui", "personne d'autre sait"],
        "behavioral_triggers": ["CTO seul à maîtriser le code", "1 commercial = 70% du CA", "pas de documentation"],
    },
    PainCategory.UNSEEN_SEGMENT: {
        "cost_ratio": 0.30,  # Opportunité manquée massive
        "discreteness": DiscretenessLevel.INVISIBLE,
        "solvable_hours": 72,
        "solution_cost_ratio": 0.03,
        "proof_template": "Nouveau segment = {gain}€ de CA additionnel sans toucher à l'existant",
        "industries": ["diaspora_markets", "urban_neglected", "pme_b2b", "ecommerce"],
        "verbal_triggers": ["on a jamais essayé ce marché", "on sait pas si ça marche"],
        "behavioral_triggers": ["mono-marché", "0 diversification", "base clients homogène"],
    },
    PainCategory.GROWTH_BLOCK: {
        "cost_ratio": 0.18,
        "discreteness": DiscretenessLevel.HIDDEN,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.02,
        "proof_template": "Déblocage = ×{multiplier} sur revenus en 12 mois — premières métriques J+30",
        "industries": ["startup_scaleup", "pme_b2b", "ecommerce"],
        "verbal_triggers": ["on stagne", "on sait pas pourquoi ça bloque", "ça devrait décoller", "croissance bloquée", "on n'arrive pas à scaler", "le burn rate monte", "pas de traction", "CAC trop élevé"],
        "behavioral_triggers": ["MRR plat > 3 mois", "pipeline vide", "aucun test growth"],
    },
    PainCategory.COMPETITOR_BLIND: {
        "cost_ratio": 0.15,
        "discreteness": DiscretenessLevel.DISCRETE,
        "solvable_hours": 48,
        "solution_cost_ratio": 0.02,
        "proof_template": "Veille concurrentielle = anticipation = {gain}€ de CA défendu",
        "industries": ["pme_b2b", "ecommerce", "startup_scaleup", "restaurant_food"],
        "verbal_triggers": ["la concurrence est dure", "on perd des clients sans savoir"],
        "behavioral_triggers": ["aucune veille concurrentielle", "surprise par entrants", "prix copiés"],
    },
}

# Industries et leurs profils de signaux comportementaux observables
INDUSTRY_BEHAVIORAL_SIGNALS: Dict[str, Dict] = {
    "restaurant_food": {
        "pains": [PainCategory.MARGIN_INVISIBLE_LOSS, PainCategory.HIDDEN_COST, PainCategory.CASH_TRAPPED, PainCategory.PRICING_PARALYSIS],
        "behavioral_markers": ["food cost > 32%", "turnover > 80%/an", "prix figés > 18 mois", "stock Excel"],
    },
    "artisan_trades": {
        "pains": [PainCategory.INVOICE_LEAK, PainCategory.CASH_TRAPPED, PainCategory.UNDERPRICED, PainCategory.FOUNDER_BOTTLENECK],
        "behavioral_markers": ["devis papier", "impayés > 15%", "acompte < 30%", "carnet plein sans cash"],
    },
    "pme_b2b": {
        "pains": [PainCategory.CASH_TRAPPED, PainCategory.MARGIN_INVISIBLE_LOSS, PainCategory.INVOICE_LEAK, PainCategory.CLIENT_BLEED, PainCategory.PROCESS_MANUAL_TAX, PainCategory.FOUNDER_BOTTLENECK, PainCategory.HIDDEN_COST],
        "behavioral_markers": ["EBE < 10%", "NPS jamais mesuré", "Excel pour tout", "fondateur = tout"],
    },
    "liberal_professions": {
        "pains": [PainCategory.UNDERPRICED, PainCategory.DORMANT_ASSET, PainCategory.PRICING_PARALYSIS, PainCategory.FOUNDER_BOTTLENECK],
        "behavioral_markers": ["TJM inférieur marché", "réseau non-activé", "toujours disponible", "méthodes non-vendues"],
    },
    "ecommerce": {
        "pains": [PainCategory.HIDDEN_COST, PainCategory.CLIENT_BLEED, PainCategory.MARGIN_INVISIBLE_LOSS, PainCategory.PROCESS_MANUAL_TAX],
        "behavioral_markers": ["ACOS > 35%", "retours > 12%", "stock Excel", "SAV email sans ticket"],
    },
    "startup_scaleup": {
        "pains": [PainCategory.CASH_TRAPPED, PainCategory.CLIENT_BLEED, PainCategory.MARGIN_INVISIBLE_LOSS, PainCategory.PRICING_PARALYSIS, PainCategory.TALENT_FRAGILITY, PainCategory.GROWTH_BLOCK],
        "behavioral_markers": ["churn > 8%/mois", "prix jamais remontés", "CTO seul", "MRR plat"],
    },
    "real_estate_investors": {
        "pains": [PainCategory.CASH_TRAPPED, PainCategory.DORMANT_ASSET, PainCategory.HIDDEN_COST],
        "behavioral_markers": ["impayés locataires", "locaux vides > 3 mois", "frais non-audités"],
    },
    "healthcare_wellness": {
        "pains": [PainCategory.COMPLIANCE_SILENT, PainCategory.INVOICE_LEAK, PainCategory.PROCESS_MANUAL_TAX, PainCategory.DORMANT_ASSET],
        "behavioral_markers": ["rgpd non-conforme", "rejets sécu > 8%", "feuilles papier", "réseau confrères inactif"],
    },
    "diaspora_markets": {
        "pains": [PainCategory.UNSEEN_SEGMENT, PainCategory.UNDERPRICED, PainCategory.DORMANT_ASSET, PainCategory.CASH_TRAPPED, PainCategory.INVOICE_LEAK],
        "behavioral_markers": ["transfert 5%+ frais", "services absents", "réseau communauté inexploité"],
    },
    "urban_neglected": {
        "pains": [PainCategory.UNSEEN_SEGMENT, PainCategory.DORMANT_ASSET],
        "behavioral_markers": ["désert commercial", "locaux vides", "pouvoir d'achat ignoré"],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 2 — DÉTECTEUR DE DOULEUR DISCRÈTE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RawPain:
    """
    Douleur brute détectée — avant qualification complète.
    Chaque champ est fondé sur du concret, pas du probable.
    """
    category: PainCategory
    industry: str
    evidence: List[str]           # Signaux observés qui prouvent la douleur
    revenue_eur: float            # CA de l'entreprise (base de calcul)
    discreteness: DiscretenessLevel
    annual_cost_eur: float        # Ce que cette douleur coûte réellement par an
    solution_cost_eur: float      # Ce que la solution coûte
    hours_to_solve: int           # 24, 48 ou 72H
    cost_to_value_ratio: float    # annual_cost / solution_cost — doit être > 3
    proof: str                    # Preuve concrète du ROI pour le client

    @property
    def is_irrefutable(self) -> bool:
        """
        Une offre est irréfutable si la douleur coûte au moins 3x la solution.
        Refuser = payer 3x plus pour ne rien changer.
        """
        return self.cost_to_value_ratio >= 3.0

    @property
    def discreteness_score(self) -> int:
        return self.discreteness.value  # 0-4

    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "industry": self.industry,
            "evidence": self.evidence,
            "annual_cost_eur": self.annual_cost_eur,
            "solution_cost_eur": self.solution_cost_eur,
            "cost_to_value_ratio": round(self.cost_to_value_ratio, 1),
            "hours_to_solve": self.hours_to_solve,
            "irrefutable": self.is_irrefutable,
            "discreteness": self.discreteness.name,
            "proof": self.proof,
        }


class DiscretePainDetector:
    """
    Détecte uniquement les douleurs discrètes réelles et solvables.
    Principe: ne détecte QUE ce qu'il peut prouver avec des chiffres.
    """

    MINIMUM_COST_TO_VALUE_RATIO = 3.0   # La douleur doit coûter 3x la solution
    MINIMUM_DISCRETENESS = DiscretenessLevel.SEMI_DISC  # Pas trop visible

    def __init__(self):
        self._noise_filter = NoiseFilter()
        self._detected_count = 0
        self._filtered_count = 0

    def detect(self, industry: str, signals: List[str], revenue_eur: float) -> List[RawPain]:
        """
        Détecte les douleurs discrètes à partir de signaux concrets.
        Retourne seulement les douleurs irréfutables.
        """
        # 1. Filtrer le bruit d'abord
        real_signals, noise = self._noise_filter.filter_signals(signals)
        self._filtered_count += len(noise)

        if not real_signals:
            return []

        # 2. Matcher signaux → douleurs
        industry_config = INDUSTRY_BEHAVIORAL_SIGNALS.get(industry, {})
        candidate_categories = industry_config.get("pains", list(PainCategory))
        raw_signals_lower = [s.lower() for s in real_signals]

        detected = []
        for category in candidate_categories:
            profile = PAIN_PROFILES.get(category)
            if not profile:
                continue

            # Compter les matches de signaux
            matches = self._count_matches(raw_signals_lower, profile)
            if matches == 0:
                continue

            # Calculer les coûts réels
            annual_cost = revenue_eur * profile["cost_ratio"]
            solution_cost = revenue_eur * profile["solution_cost_ratio"]
            ratio = annual_cost / max(solution_cost, 1)

            # Gate: le ratio doit être suffisant
            if ratio < self.MINIMUM_COST_TO_VALUE_RATIO:
                continue

            # Gate: la discrétion doit être suffisante
            if profile["discreteness"].value < self.MINIMUM_DISCRETENESS.value:
                continue

            proof = self._build_proof(profile, annual_cost, solution_cost, revenue_eur)

            pain = RawPain(
                category=category,
                industry=industry,
                evidence=[s for s in real_signals if self._signal_matches_profile(s.lower(), profile)],
                revenue_eur=revenue_eur,
                discreteness=profile["discreteness"],
                annual_cost_eur=round(annual_cost),
                solution_cost_eur=round(solution_cost),
                hours_to_solve=profile["solvable_hours"],
                cost_to_value_ratio=round(ratio, 1),
                proof=proof,
            )

            if pain.is_irrefutable:
                detected.append(pain)
                self._detected_count += 1

        # Trier par ratio coût/valeur décroissant — les plus irréfutables en premier
        return sorted(detected, key=lambda p: p.cost_to_value_ratio, reverse=True)

    def detect_from_text(self, text: str, industry: str, revenue_eur: float) -> List[RawPain]:
        """Détecte depuis un texte libre — conversation, email, entretien."""
        text_lower = text.lower()
        matched_signals = []

        for category, profile in PAIN_PROFILES.items():
            for trigger in profile.get("verbal_triggers", []):
                if trigger in text_lower:
                    matched_signals.append(trigger)

        return self.detect(industry, matched_signals, revenue_eur) if matched_signals else []

    def _count_matches(self, signals_lower: List[str], profile: Dict) -> int:
        count = 0
        for sig in signals_lower:
            if self._signal_matches_profile(sig, profile):
                count += 1
        return count

    def _signal_matches_profile(self, signal: str, profile: Dict) -> bool:
        all_triggers = (
            profile.get("verbal_triggers", []) +
            profile.get("behavioral_triggers", [])
        )
        return any(t.lower() in signal or signal in t.lower() for t in all_triggers)

    def _build_proof(self, profile: Dict, annual_cost: float, solution_cost: float, revenue: float) -> str:
        template = profile.get("proof_template", "ROI = {gain}€ en {hours}H")
        gain = annual_cost - solution_cost
        return (template
            .replace("{gain}", f"{int(gain):,}")
            .replace("{gain_pts}", f"{int(profile.get('cost_ratio',0.1)*100/3)}")
            .replace("{gain_pct}", f"{int(profile.get('cost_ratio',0.1)*100)}")
            .replace("{hours}", f"{profile['solvable_hours']}")
            .replace("{hours}", f"{int(gain/50)}")
            .replace("{risk_eur}", f"{int(revenue*0.3):,}")
            .replace("{multiplier}", "2-3")
        )

    @property
    def stats(self) -> Dict:
        return {"detected": self._detected_count, "noise_filtered": self._filtered_count}


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 3 — PRIX ISSU DE LA DOULEUR (pas d'une grille)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class IrrefutableOffer:
    """
    Offre construite pour être irréfutable.
    Le prix sort du coût de la douleur, pas d'un catalogue.
    Le refus = payer 3x plus pour garder le problème.
    """
    id: str = field(default_factory=lambda: f"OFF_{uuid.uuid4().hex[:8].upper()}")
    pain: Optional[RawPain] = None

    # Prix — calculé depuis la douleur
    price_eur: float = 0.0
    price_anchor_eur: float = 0.0   # Coût de la douleur annuelle (anchor)
    cost_to_client_if_no_action: float = 0.0
    roi_ratio: float = 0.0          # Combien rapporte chaque euro investi

    # Offre
    title: str = ""
    problem_in_euros: str = ""      # "Cette douleur vous coûte X€/an"
    solution_statement: str = ""    # Ce qu'on fait exactement
    deliverables: List[str] = field(default_factory=list)
    proof: str = ""                 # La preuve concrète
    guarantee: str = ""             # Garantie résultat — jamais de process
    first_action_hours: int = 4     # Ce qui se passe dans les 4 premières heures
    delivery_hours: int = 24

    # Irréfutabilité
    irrefutable_logic: str = ""     # La phrase qui rend le refus impossible
    assets_created: List[str] = field(default_factory=list)  # Ce qui reste après

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "price": self.price_eur, "anchor": self.price_anchor_eur,
            "title": self.title, "problem_in_euros": self.problem_in_euros,
            "solution": self.solution_statement, "deliverables": self.deliverables,
            "proof": self.proof, "guarantee": self.guarantee,
            "delivery_hours": self.delivery_hours, "roi_ratio": self.roi_ratio,
            "irrefutable_logic": self.irrefutable_logic,
            "assets_created": self.assets_created,
            "pain": self.pain.to_dict() if self.pain else {},
        }


class PriceFromPain:
    """
    Le prix sort du coût de la douleur.
    Principe: on prend entre 10% et 25% du coût annuel de la douleur.
    C'est mathématiquement irréfutable.
    """

    # On facture entre 10% et 25% du coût annuel de la douleur
    # Selon la discrétion (plus c'est caché, plus on peut prendre)
    TAKE_RATE_BY_DISCRETENESS = {
        DiscretenessLevel.VISIBLE:    0.10,
        DiscretenessLevel.SEMI_DISC:  0.14,
        DiscretenessLevel.DISCRETE:   0.18,
        DiscretenessLevel.HIDDEN:     0.22,
        DiscretenessLevel.INVISIBLE:  0.25,
    }

    # Planchers par délai — inviolables
    FLOORS = {24: 5_000, 48: 10_000, 72: 20_000}
    # Pas de plafond — le prix est illimité vers le haut, seul le plancher est absolu.

    def price(self, pain: RawPain) -> float:
        """Calcule le prix exact depuis la douleur — sans plafond."""
        take_rate = self.TAKE_RATE_BY_DISCRETENESS[pain.discreteness]
        raw_price = pain.annual_cost_eur * take_rate

        floor = self.FLOORS[pain.hours_to_solve]
        # Appliquer seulement le plancher, jamais de plafond
        priced = max(floor, raw_price)

        # Arrondir au palier symbolique le plus proche
        return self._round_to_tier(priced)

    def _round_to_tier(self, price: float) -> float:
        """Arrondit au palier symbolique le plus proche (illimité vers le haut)."""
        tiers = [5000, 7500, 10000, 12500, 15000, 20000, 25000, 30000, 40000, 50000,
                 60000, 75000, 100000, 150000, 200000, 300000, 500000, 750000, 1000000]
        return min(tiers, key=lambda t: abs(t - price))

    def build_irrefutable_offer(self, pain: RawPain) -> IrrefutableOffer:
        """Construit l'offre complète et irréfutable depuis la douleur."""
        price = self.price(pain)
        roi = pain.annual_cost_eur / max(price, 1)

        offer = IrrefutableOffer(
            pain=pain,
            price_eur=price,
            price_anchor_eur=pain.annual_cost_eur,
            cost_to_client_if_no_action=pain.annual_cost_eur,
            roi_ratio=round(roi, 1),
            delivery_hours=pain.hours_to_solve,
            proof=pain.proof,
        )

        offer.title = self._build_title(pain)
        offer.problem_in_euros = (
            f"Cette situation vous coûte actuellement {pain.annual_cost_eur:,.0f}€/an. "
            f"Notre intervention à {price:,.0f}€ vous rend {pain.annual_cost_eur - price:,.0f}€ dès la première année."
        )
        offer.solution_statement = self._build_solution(pain)
        offer.deliverables = self._build_deliverables(pain)
        offer.guarantee = self._build_guarantee(pain, price)
        offer.irrefutable_logic = self._irrefutable_logic(pain, price)
        offer.first_action_hours = 4
        offer.assets_created = self._assets_created(pain)

        return offer

    def _build_title(self, pain: RawPain) -> str:
        TITLES = {
            PainCategory.CASH_TRAPPED:          f"Libération Trésorerie — {pain.annual_cost_eur:,.0f}€ récupérés en 30 jours",
            PainCategory.MARGIN_INVISIBLE_LOSS: f"Restauration Marges — +{int(pain.annual_cost_eur/pain.revenue_eur*100)}pts récupérés",
            PainCategory.INVOICE_LEAK:          f"Arrêt Fuite Facturation — {pain.annual_cost_eur:,.0f}€/an stoppés",
            PainCategory.HIDDEN_COST:           f"Audit Coûts Cachés — {pain.annual_cost_eur:,.0f}€ identifiés en 72H",
            PainCategory.UNDERPRICED:           f"Repositionnement Prix — +{int(pain.annual_cost_eur/pain.revenue_eur*100)}% revenu sans perdre 1 client",
            PainCategory.PROCESS_MANUAL_TAX:    f"Automatisation Processus — {int(pain.annual_cost_eur/50)}H/an récupérées",
            PainCategory.CLIENT_BLEED:          f"Stop Churn Silencieux — {pain.annual_cost_eur:,.0f}€/an de CA défendu",
            PainCategory.DORMANT_ASSET:         f"Activation Actifs — {pain.annual_cost_eur:,.0f}€ de valeur dormante réveillée",
            PainCategory.FOUNDER_BOTTLENECK:    f"Délégation Dirigeant — {int(pain.annual_cost_eur/250)}H/an libérées",
            PainCategory.PRICING_PARALYSIS:     f"Hausse Prix — +{int(pain.annual_cost_eur/pain.revenue_eur*100)}% sans friction client",
            PainCategory.COMPLIANCE_SILENT:     f"Mise en Conformité — {pain.annual_cost_eur:,.0f}€ de risque éliminé",
            PainCategory.TALENT_FRAGILITY:      f"Sécurisation Talent Clé — {int(pain.annual_cost_eur):,}€ de risque couvert",
            PainCategory.UNSEEN_SEGMENT:        f"Ouverture Segment — {pain.annual_cost_eur:,.0f}€ de CA nouveau identifié",
            PainCategory.GROWTH_BLOCK:          f"Déblocage Croissance — ×2-3 revenus en 12 mois",
            PainCategory.COMPETITOR_BLIND:      f"Veille Concurrentielle — {pain.annual_cost_eur:,.0f}€ de CA défendu",
        }
        return TITLES.get(pain.category, f"Résolution {pain.category.value} — ROI ×{pain.cost_to_value_ratio}")

    def _build_solution(self, pain: RawPain) -> str:
        SOLUTIONS = {
            PainCategory.CASH_TRAPPED:          f"Diagnostic trésorerie ligne par ligne + plan libération immédiate + 30j suivi",
            PainCategory.MARGIN_INVISIBLE_LOSS: f"Analyse P&L complète + benchmark marges secteur + plan restoration 60j",
            PainCategory.INVOICE_LEAK:          f"Audit facturation + élimination fuites + système pro opérationnel en 24H",
            PainCategory.HIDDEN_COST:           f"Audit coûts ligne par ligne + identification top 5 + plan réduction immédiate",
            PainCategory.UNDERPRICED:           f"Benchmark marché + nouvelle grille + script hausse + clients pilotes J+15",
            PainCategory.PROCESS_MANUAL_TAX:    f"Cartographie processus + automatisation des 3 plus coûteux + formation équipe",
            PainCategory.CLIENT_BLEED:          f"Analyse cohortes + entretiens clients à risque + playbook rétention 90j",
            PainCategory.DORMANT_ASSET:         f"Audit actifs dormants + 3 scénarios monétisation + plan activation premier actif",
            PainCategory.FOUNDER_BOTTLENECK:    f"Diagnostic délégation + framework priorisation + plan libération dirigeant",
            PainCategory.PRICING_PARALYSIS:     f"Benchmark + test prix + script communication + migration clients sans friction",
            PainCategory.COMPLIANCE_SILENT:     f"Audit conformité + plan mise en conformité + documentation + certification",
            PainCategory.TALENT_FRAGILITY:      f"Cartographie savoirs clés + plan documentation + backup opérationnel",
            PainCategory.UNSEEN_SEGMENT:        f"Étude segment + 5 entretiens clients + business case + plan go-to-market",
            PainCategory.GROWTH_BLOCK:          f"Diagnostic blocages + roadmap croissance + quick wins J+30 + accompagnement",
            PainCategory.COMPETITOR_BLIND:      f"Veille concurrentielle complète + matrix de positionnement + plan réponse",
        }
        return SOLUTIONS.get(pain.category, f"Résolution complète {pain.category.value} en {pain.hours_to_solve}H")

    def _build_deliverables(self, pain: RawPain) -> List[str]:
        BASE_DELIVERABLES = {
            PainCategory.CASH_TRAPPED:          ["Rapport trésorerie", "Modèle prévisionnel 90j", "Plan actions prioritisé", "30j support"],
            PainCategory.MARGIN_INVISIBLE_LOSS: ["Analyse P&L détaillée", "Benchmark marges secteur", "Plan restoration", "KPIs dashboard"],
            PainCategory.INVOICE_LEAK:          ["Audit facturation", "Système devis/facture pro", "SOP processus", "Formation 2H"],
            PainCategory.HIDDEN_COST:           ["Audit ligne par ligne", "Top 5 coûts éliminables", "Plan réduction 90j", "Suivi mensuel"],
            PainCategory.UNDERPRICED:           ["Benchmark prix marché", "Nouvelle grille tarifaire", "Script hausse clients", "Suivi 60j"],
            PainCategory.PROCESS_MANUAL_TAX:    ["Cartographie processus", "3 automatisations déployées", "Documentation", "Formation équipe"],
            PainCategory.CLIENT_BLEED:          ["Analyse churn", "Segmentation risque", "Playbook rétention", "Dashboard KPIs"],
            PainCategory.DORMANT_ASSET:         ["Audit actifs", "3 business cases", "Plan activation J+1", "Accompagnement lancement"],
            PainCategory.FOUNDER_BOTTLENECK:    ["Diagnostic délégation", "Framework décision", "Plan délégation", "Suivi mensuel"],
            PainCategory.PRICING_PARALYSIS:     ["Benchmark concurrentiel", "Grille prix optimisée", "Script communication", "Suivi 60j"],
            PainCategory.COMPLIANCE_SILENT:     ["Audit conformité", "Plan mise en conformité", "Documentation légale", "Formation équipe"],
            PainCategory.TALENT_FRAGILITY:      ["Cartographie savoirs", "Plan documentation", "Backup processus", "Formation remplaçant"],
            PainCategory.UNSEEN_SEGMENT:        ["Étude segment", "5 entretiens clients", "Business case", "Plan go-to-market"],
            PainCategory.GROWTH_BLOCK:          ["Diagnostic blocages", "Roadmap 12 mois", "Plan Q1 détaillé", "3 sessions accompagnement"],
            PainCategory.COMPETITOR_BLIND:      ["Veille complète", "Matrix positionnement", "Opportunités différenciation", "Plan réponse"],
        }
        return BASE_DELIVERABLES.get(pain.category, ["Rapport complet", "Plan d'action", "Suivi 30j"])

    def _build_guarantee(self, pain: RawPain, price: float) -> str:
        """Garantie résultat — jamais de garantie process."""
        gain = int(pain.annual_cost_eur - price)
        GUARANTEES = {
            PainCategory.CASH_TRAPPED:          f"Vous identifiez {int(pain.annual_cost_eur*0.3):,}€ de cash libérable en 30j — ou remboursement intégral",
            PainCategory.MARGIN_INVISIBLE_LOSS: f"+{int(pain.annual_cost_eur/pain.revenue_eur*100*0.5)}pts de marge en 90j — ou nous continuons gratuitement",
            PainCategory.INVOICE_LEAK:          f"Impayés réduits de 50% en 60j — ou remboursement",
            PainCategory.HIDDEN_COST:           f"Économies identifiées = minimum 3x la facture — ou remboursement",
            PainCategory.UNDERPRICED:           f"+{int(pain.cost_to_value_ratio*5)}% revenu en 90j sans perdre 1 client — ou remboursement",
            PainCategory.PROCESS_MANUAL_TAX:    f"10H/semaine récupérées dès J+7 — ou remboursement",
            PainCategory.CLIENT_BLEED:          f"Churn réduit de 30% en 90j — ou travail supplémentaire gratuit",
            PainCategory.DORMANT_ASSET:         f"1 actif en cours de monétisation en 90j — ou remboursement partiel",
            PainCategory.FOUNDER_BOTTLENECK:    f"5H/semaine libérées dès J+30 — ou remboursement",
            PainCategory.PRICING_PARALYSIS:     f"+{int(pain.cost_to_value_ratio*4)}% revenu en 60j — ou remboursement",
            PainCategory.COMPLIANCE_SILENT:     f"Conformité atteinte en 30j — ou nous finissons gratuitement",
            PainCategory.TALENT_FRAGILITY:      f"Plan backup opérationnel en 48H — sinon remboursement intégral",
        }
        return GUARANTEES.get(pain.category,
            f"Vous récupérez au minimum {gain:,}€ sur 12 mois ou remboursement intégral")

    def _irrefutable_logic(self, pain: RawPain, price: float) -> str:
        """La phrase qui rend le refus logiquement impossible."""
        cost = int(pain.annual_cost_eur)
        return (
            f"Cette situation vous coûte déjà {cost:,}€/an — soit {int(cost/12):,}€/mois. "
            f"Notre intervention à {int(price):,}€ s'amortit en {int(price/(cost/12)):.0f} mois. "
            f"Refuser = choisir de payer {cost:,}€/an pour garder le problème."
        )

    def _assets_created(self, pain: RawPain) -> List[str]:
        ASSETS = {
            PainCategory.CASH_TRAPPED:          ["Modèle prévisionnel réutilisable", "Process trésorerie documenté"],
            PainCategory.MARGIN_INVISIBLE_LOSS: ["Dashboard marges sectoriel", "Framework analyse P&L"],
            PainCategory.INVOICE_LEAK:          ["Template devis/factures", "SOP facturation"],
            PainCategory.HIDDEN_COST:           ["Grille audit coûts secteur", "Process review mensuel"],
            PainCategory.UNDERPRICED:           ["Base benchmark prix secteur", "Script hausse prix"],
            PainCategory.PROCESS_MANUAL_TAX:    ["Automatisations N8N réutilisables", "Cartographie processus type"],
            PainCategory.CLIENT_BLEED:          ["Framework analyse churn sectoriel", "Playbook rétention"],
            PainCategory.DORMANT_ASSET:         ["Méthodologie audit actifs", "Template business case"],
            PainCategory.FOUNDER_BOTTLENECK:    ["Framework délégation", "Template OKR équipe"],
            PainCategory.PRICING_PARALYSIS:     ["Base données prix secteur", "Playbook hausse prix"],
        }
        return ASSETS.get(pain.category, ["Méthodologie d'intervention documentée"])


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 4 — ESCALIER NATUREL (pas une grille, une progression logique)
# ══════════════════════════════════════════════════════════════════════════════

class NaturalLadder:
    """
    L'escalier de valeur sort de la douleur elle-même.
    On ne force pas — chaque niveau règle un aspect de la même douleur.
    """

    def __init__(self, pricer: PriceFromPain):
        self._pricer = pricer

    def build(self, pain: RawPain) -> List[IrrefutableOffer]:
        """Construit l'escalier naturel 24H → 48H → 72H pour la même douleur."""
        steps = []

        # Step 1 — 24H: Diagnostic + Quick Win + Plan
        pain_24 = self._clone_pain(pain, hours=24, cost_ratio=0.40)
        step1 = self._pricer.build_irrefutable_offer(pain_24)
        step1.title = f"[24H] Diagnostic + Plan — {int(pain_24.annual_cost_eur*0.4):,}€ identifiés"
        step1.deliverables = step1.deliverables[:2] + ["Quick win immédiat J+1"]
        steps.append(step1)

        # Step 2 — 48H: Diagnostic + Implémentation partielle
        pain_48 = self._clone_pain(pain, hours=48, cost_ratio=0.70)
        step2 = self._pricer.build_irrefutable_offer(pain_48)
        step2.title = f"[48H] Diagnostic + Implémentation — {int(pain_48.annual_cost_eur*0.6):,}€ récupérés"
        steps.append(step2)

        # Step 3 — 72H: Solution complète
        step3 = self._pricer.build_irrefutable_offer(pain)
        step3.title = f"[72H] Solution Complète — {int(pain.annual_cost_eur):,}€/an stoppés"
        steps.append(step3)

        return steps

    def _clone_pain(self, pain: RawPain, hours: int, cost_ratio: float) -> RawPain:
        adjusted_cost = pain.annual_cost_eur * cost_ratio
        adjusted_solution = pain.solution_cost_eur * cost_ratio
        return RawPain(
            category=pain.category, industry=pain.industry, evidence=pain.evidence,
            revenue_eur=pain.revenue_eur, discreteness=pain.discreteness,
            annual_cost_eur=round(adjusted_cost),
            solution_cost_eur=round(adjusted_solution),
            hours_to_solve=hours,
            cost_to_value_ratio=round(adjusted_cost / max(adjusted_solution, 1), 1),
            proof=pain.proof,
        )


# ══════════════════════════════════════════════════════════════════════════════
# COUCHE 5 — SUPER BRAIN V6.1 — ORCHESTRATEUR
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BrainOutput:
    """Sortie complète du Super Brain — prête à être utilisée."""
    company_id: str
    pains_detected: List[RawPain]
    top_pain: Optional[RawPain]
    offer: Optional[IrrefutableOffer]
    full_ladder: List[IrrefutableOffer]
    noise_removed: List[str]
    signal_quality: float
    is_qualified: bool
    qualification_reason: str
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "company_id": self.company_id,
            "qualified": self.is_qualified,
            "qualification_reason": self.qualification_reason,
            "signal_quality": self.signal_quality,
            "noise_removed": self.noise_removed,
            "pains_count": len(self.pains_detected),
            "top_pain": self.top_pain.to_dict() if self.top_pain else None,
            "offer": self.offer.to_dict() if self.offer else None,
            "ladder": [o.to_dict() for o in self.full_ladder],
        }


class SuperBrainV6:
    """
    Super Brain V6.1 — le cerveau qui ne s'occupe que de douleurs irréfutables.
    """
    VERSION = "6.1.0"

    def __init__(self):
        self._noise_filter = NoiseFilter()
        self._detector = DiscretePainDetector()
        self._pricer = PriceFromPain()
        self._ladder = NaturalLadder(self._pricer)
        self._outputs: List[BrainOutput] = []

    def process(self, industry: str, signals: List[str], revenue_eur: float,
                company_id: str = None) -> BrainOutput:
        """
        Traitement complet d'un profil entreprise.
        Filtre le bruit → détecte la douleur → construit l'offre irréfutable.
        """
        cid = company_id or f"CO_{uuid.uuid4().hex[:8].upper()}"

        # 1. Filtrer le bruit
        real_signals, noise = self._noise_filter.filter_signals(signals)
        signal_quality = round(len(real_signals) / max(len(signals), 1), 2)

        if not real_signals:
            return BrainOutput(
                company_id=cid, pains_detected=[], top_pain=None,
                offer=None, full_ladder=[], noise_removed=noise,
                signal_quality=0.0, is_qualified=False,
                qualification_reason="DISQUALIFIED: 100% bruit — aucun signal de douleur réelle"
            )

        # 2. Détecter les douleurs discrètes
        pains = self._detector.detect(industry, real_signals, revenue_eur)

        if not pains:
            return BrainOutput(
                company_id=cid, pains_detected=[], top_pain=None,
                offer=None, full_ladder=[], noise_removed=noise,
                signal_quality=signal_quality, is_qualified=False,
                qualification_reason=f"DISQUALIFIED: signaux présents mais douleur pas assez discrète/solvable (ratio < {DiscretePainDetector.MINIMUM_COST_TO_VALUE_RATIO}x)"
            )

        # 3. Prendre la douleur la plus irréfutable
        top = pains[0]

        # 4. Construire l'offre depuis la douleur
        offer = self._pricer.build_irrefutable_offer(top)

        # 5. Construire l'escalier naturel
        ladder = self._ladder.build(top)

        output = BrainOutput(
            company_id=cid, pains_detected=pains, top_pain=top,
            offer=offer, full_ladder=ladder, noise_removed=noise,
            signal_quality=signal_quality, is_qualified=True,
            qualification_reason=f"QUALIFIED: douleur {top.category.value} coûte {top.annual_cost_eur:,}€/an → offre {offer.price_eur:,}€ = ratio {top.cost_to_value_ratio}x"
        )
        self._outputs.append(output)
        return output

    def process_text(self, text: str, industry: str, revenue_eur: float) -> BrainOutput:
        """Traite un texte libre — conversation, email, notes entretien."""
        pains = self._detector.detect_from_text(text, industry, revenue_eur)
        if not pains:
            # Extraire les signaux du texte et les passer au process standard
            signals = [s for s in text.split(".") if len(s.strip()) > 10]
            return self.process(industry, signals, revenue_eur)
        top = pains[0]
        offer = self._pricer.build_irrefutable_offer(top)
        ladder = self._ladder.build(top)
        return BrainOutput(
            company_id=f"CO_{uuid.uuid4().hex[:8].upper()}",
            pains_detected=pains, top_pain=top, offer=offer, full_ladder=ladder,
            noise_removed=[], signal_quality=1.0, is_qualified=True,
            qualification_reason=f"QUALIFIED (text): {top.category.value} | ratio {top.cost_to_value_ratio}x"
        )

    def get_stats(self) -> Dict:
        qualified = [o for o in self._outputs if o.is_qualified]
        return {
            "version": self.VERSION,
            "total_processed": len(self._outputs),
            "qualified": len(qualified),
            "disqualified": len(self._outputs) - len(qualified),
            "qualification_rate": round(len(qualified) / max(len(self._outputs), 1) * 100, 1),
            "revenue_pipeline": sum(o.offer.price_eur for o in qualified if o.offer),
            "detector": self._detector.stats,
        }


# ══════════════════════════════════════════════════════════════════════════════
# API PUBLIQUE
# ══════════════════════════════════════════════════════════════════════════════

_BRAIN: Optional[SuperBrainV6] = None

def get_super_brain() -> SuperBrainV6:
    global _BRAIN
    if _BRAIN is None:
        _BRAIN = SuperBrainV6()
    return _BRAIN

get_brain = get_super_brain  # alias


def hunt_and_create(industry: str, signals: List[str], revenue_eur: float = 500000) -> Dict:
    """
    API principale — filtre le bruit, détecte la douleur, crée l'offre irréfutable.
    """
    brain = get_super_brain()
    output = brain.process(industry, signals, revenue_eur)
    return output.to_dict()


def create_cash_ladder(industry: str, signals: List[str], revenue_eur: float = 500000) -> List[Dict]:
    """Crée l'escalier naturel 24H/48H/72H pour la douleur détectée."""
    brain = get_super_brain()
    output = brain.process(industry, signals, revenue_eur)
    return [o.to_dict() for o in output.full_ladder]


def analyze_text(text: str, industry: str, revenue_eur: float = 300000) -> Dict:
    """Analyse un texte libre pour détecter les douleurs discrètes."""
    brain = get_super_brain()
    output = brain.process_text(text, industry, revenue_eur)
    return output.to_dict()


def noise_check(signals: List[str]) -> Dict:
    """Vérifie quels signaux sont du bruit — utile pour calibrer."""
    f = NoiseFilter()
    real, noise = f.filter_signals(signals)
    return {"real_signals": real, "noise": noise,
            "quality": round(len(real) / max(len(signals), 1), 2)}


# Compatibilité ascendante V5/V6.0
async def process_with_super_brain(opportunity_data: Dict) -> Dict:
    return hunt_and_create(
        opportunity_data.get("target_segment", "pme_b2b"),
        [opportunity_data.get("description", "")],
        float(opportunity_data.get("estimated_value", 500000))
    )

# Stubs V6.0 supprimés (ZeroWasteLoopV2 n'existe plus — pas de refus possible)
def recycle_rejection(*args, **kwargs) -> Dict:
    return {"message": "Doctrine V6.1: une offre irréfutable n'a pas de refus à recycler. Requalifier la douleur."}
