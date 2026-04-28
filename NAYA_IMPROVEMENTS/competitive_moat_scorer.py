"""
NAYA SUPREME V19.3 — AMELIORATION #7
Competitive Moat Scorer
=======================
Scoring de l'avantage concurrentiel par prospect/secteur.
Evalue les barrieres a l'entree, les switching costs, et
l'avantage NAYA sur les solutions alternatives.

Unique a NAYA : scoring multidimensionnel de positionnement
concurrentiel integre au pipeline de vente.
"""
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

log = logging.getLogger("NAYA.MOAT")


@dataclass
class MoatScore:
    prospect_id: str
    company: str
    sector: str
    overall_score: float  # 0-100 : avantage NAYA
    dimensions: Dict[str, float]
    moat_level: str  # wide | narrow | none
    key_advantages: List[str]
    risks: List[str]
    pricing_recommendation: float  # EUR suggere
    competitive_position: str  # dominant | strong | even | weak


# Avantages NAYA par secteur
SECTOR_ADVANTAGES = {
    "transport_logistics": {
        "iec62443_expertise": 0.85,
        "nis2_deadline_urgency": 0.90,
        "ot_security_depth": 0.80,
        "automation_speed": 0.95,
        "local_presence": 0.60,
    },
    "energy_utilities": {
        "iec62443_expertise": 0.90,
        "nis2_deadline_urgency": 0.95,
        "ot_security_depth": 0.85,
        "automation_speed": 0.90,
        "local_presence": 0.55,
    },
    "manufacturing": {
        "iec62443_expertise": 0.80,
        "nis2_deadline_urgency": 0.85,
        "ot_security_depth": 0.75,
        "automation_speed": 0.90,
        "local_presence": 0.50,
    },
    "healthcare": {
        "iec62443_expertise": 0.70,
        "nis2_deadline_urgency": 0.80,
        "ot_security_depth": 0.65,
        "automation_speed": 0.85,
        "local_presence": 0.50,
    },
}

# Concurrents types par type de service
COMPETITOR_PROFILES = {
    "big4_consulting": {
        "name": "Big 4 (Deloitte, PwC, EY, KPMG)",
        "strengths": ["brand", "network", "scale"],
        "weaknesses": ["cost_10x", "slow_delivery", "generic_approach"],
        "price_multiplier": 10.0,
    },
    "boutique_cyber": {
        "name": "Boutiques Cybersecurite",
        "strengths": ["expertise_niche", "agility"],
        "weaknesses": ["limited_automation", "small_team", "no_ot_depth"],
        "price_multiplier": 3.0,
    },
    "internal_team": {
        "name": "Equipe interne du client",
        "strengths": ["context", "integration", "trust"],
        "weaknesses": ["bias", "capacity", "expertise_gap"],
        "price_multiplier": 0.0,
    },
    "no_action": {
        "name": "Status quo (ne rien faire)",
        "strengths": ["zero_cost_immediate"],
        "weaknesses": ["nis2_penalties", "breach_risk", "insurance_loss"],
        "price_multiplier": 0.0,
    },
}


class CompetitiveMoatScorer:
    """
    Evalue l'avantage concurrentiel de NAYA pour chaque prospect.

    Dimensions evaluees :
    1. Expertise IEC 62443 / NIS2 (unique NAYA)
    2. Vitesse d'execution (audit en 48h vs 3 mois Big 4)
    3. Prix competitif (5-20k vs 50-200k Big 4)
    4. Automatisation IA (unique NAYA)
    5. Conformite reglementaire (urgence deadline)
    6. Barriere de switching (lock-in client)
    """

    def __init__(self):
        self._scores: Dict[str, MoatScore] = {}
        self._total_scored: int = 0

    def score_prospect(self, prospect_id: str, company: str, sector: str,
                       company_size: str = "mid", urgency: str = "medium",
                       has_internal_team: bool = False,
                       budget_eur: float = 0) -> MoatScore:
        """Calcule le score d'avantage concurrentiel pour un prospect."""
        self._total_scored += 1

        sector_key = self._normalize_sector(sector)
        advantages = SECTOR_ADVANTAGES.get(sector_key, SECTOR_ADVANTAGES["manufacturing"])

        # Calculer chaque dimension
        dimensions = {}

        # 1. Expertise technique (IEC 62443 + OT)
        tech_score = (advantages["iec62443_expertise"] + advantages["ot_security_depth"]) / 2
        dimensions["expertise_technique"] = round(tech_score * 100, 1)

        # 2. Urgence reglementaire (boost si NIS2 deadline proche)
        urgency_multiplier = {"high": 1.3, "medium": 1.0, "low": 0.7}.get(urgency, 1.0)
        dimensions["urgence_reglementaire"] = round(advantages["nis2_deadline_urgency"] * 100 * urgency_multiplier, 1)
        dimensions["urgence_reglementaire"] = min(100, dimensions["urgence_reglementaire"])

        # 3. Avantage prix (NAYA vs alternatives)
        if budget_eur > 0:
            # Si budget connu, evaluer si NAYA est dans le budget
            naya_price = min(budget_eur * 0.8, 20000)
            price_advantage = min(1.0, budget_eur / max(naya_price, 1))
        else:
            price_advantage = 0.85  # NAYA est 5-10x moins cher que Big 4
        dimensions["avantage_prix"] = round(price_advantage * 100, 1)

        # 4. Vitesse d'execution
        dimensions["vitesse_execution"] = round(advantages["automation_speed"] * 100, 1)

        # 5. Automatisation IA (avantage unique NAYA)
        dimensions["automatisation_ia"] = 95.0  # Presque aucun concurrent offre ca

        # 6. Barriere de switching
        if has_internal_team:
            switching_barrier = 40.0  # Plus dur de deplacer une equipe interne
        else:
            switching_barrier = 75.0  # Client sans equipe = captif
        dimensions["barriere_switching"] = switching_barrier

        # Score global pondere
        weights = {
            "expertise_technique": 0.25,
            "urgence_reglementaire": 0.20,
            "avantage_prix": 0.15,
            "vitesse_execution": 0.15,
            "automatisation_ia": 0.15,
            "barriere_switching": 0.10,
        }
        overall = sum(dimensions[k] * weights[k] for k in weights)
        overall = round(min(100, overall), 1)

        # Determiner le niveau de moat
        if overall >= 75:
            moat_level = "wide"
            position = "dominant"
        elif overall >= 55:
            moat_level = "narrow"
            position = "strong"
        elif overall >= 40:
            moat_level = "narrow"
            position = "even"
        else:
            moat_level = "none"
            position = "weak"

        # Avantages cles
        key_advantages = []
        if dimensions["automatisation_ia"] >= 90:
            key_advantages.append("Automatisation IA unique (aucun concurrent)")
        if dimensions["vitesse_execution"] >= 85:
            key_advantages.append("Audit en 48h vs 3 mois (Big 4)")
        if dimensions["avantage_prix"] >= 80:
            key_advantages.append("Prix 5-10x inferieur aux Big 4")
        if dimensions["urgence_reglementaire"] >= 85:
            key_advantages.append("Expertise NIS2/IEC62443 de pointe")

        # Risques
        risks = []
        if dimensions["barriere_switching"] < 50:
            risks.append("Client a une equipe interne — risque de competition")
        if dimensions["urgence_reglementaire"] < 60:
            risks.append("Urgence reglementaire faible — cycle de vente long")
        if company_size == "enterprise":
            risks.append("Enterprise: processus d'achat complexe (6+ mois)")

        # Recommendation prix
        base_price = 5000
        if overall >= 75:
            pricing = base_price * 3  # Position dominante = prix premium
        elif overall >= 55:
            pricing = base_price * 2
        else:
            pricing = base_price * 1.2
        pricing = max(1000, round(pricing, -2))  # Minimum plancher 1000 EUR

        score = MoatScore(
            prospect_id=prospect_id, company=company, sector=sector,
            overall_score=overall, dimensions=dimensions,
            moat_level=moat_level, key_advantages=key_advantages,
            risks=risks, pricing_recommendation=pricing,
            competitive_position=position,
        )

        self._scores[prospect_id] = score
        log.info(f"[MOAT] {company}: score={overall}/100 moat={moat_level} price={pricing}EUR")
        return score

    def _normalize_sector(self, sector: str) -> str:
        sector = sector.lower().replace(" ", "_").replace("-", "_").replace("&", "")
        mappings = {
            "transport": "transport_logistics",
            "logistics": "transport_logistics",
            "energy": "energy_utilities",
            "utilities": "energy_utilities",
            "manufacturing": "manufacturing",
            "industry": "manufacturing",
            "health": "healthcare",
            "pharma": "healthcare",
        }
        for key, val in mappings.items():
            if key in sector:
                return val
        return "manufacturing"

    def get_top_opportunities(self, min_score: float = 60) -> List[Dict]:
        """Retourne les prospects avec le plus fort avantage concurrentiel."""
        results = []
        for score in self._scores.values():
            if score.overall_score >= min_score:
                results.append({
                    "prospect_id": score.prospect_id,
                    "company": score.company,
                    "score": score.overall_score,
                    "moat": score.moat_level,
                    "pricing": score.pricing_recommendation,
                    "advantages": score.key_advantages,
                })
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def get_stats(self) -> Dict:
        return {
            "total_scored": self._total_scored,
            "wide_moat": sum(1 for s in self._scores.values() if s.moat_level == "wide"),
            "narrow_moat": sum(1 for s in self._scores.values() if s.moat_level == "narrow"),
            "no_moat": sum(1 for s in self._scores.values() if s.moat_level == "none"),
        }


_scorer: Optional[CompetitiveMoatScorer] = None


def get_moat_scorer() -> CompetitiveMoatScorer:
    global _scorer
    if _scorer is None:
        _scorer = CompetitiveMoatScorer()
    return _scorer
