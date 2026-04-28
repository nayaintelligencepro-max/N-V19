"""
NAYA — Autonomous Business Factory
Crée automatiquement tout type de business — de l'idée au premier client.
Mode autonome maximal : NAYA chasse, crée, price et lance sans intervention.
"""
import os
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

log = logging.getLogger("NAYA.BUSINESS_FACTORY")


class BusinessStatus(Enum):
    IDENTIFIED = "identified"
    DESIGNED = "designed"
    PRICED = "priced"
    READY_TO_LAUNCH = "ready_to_launch"
    LAUNCHED = "launched"
    GENERATING_REVENUE = "generating_revenue"
    SCALED = "scaled"
    PAUSED = "paused"


class BusinessCategory(Enum):
    # Services B2B
    CONSULTING = "consulting"
    AUDIT = "audit"
    IMPLEMENTATION = "implementation"
    TRAINING = "training"
    CHATBOT_AI = "chatbot_ai"
    AUTOMATION = "automation"
    # Produits
    SAAS = "saas"
    DIGITAL_PRODUCT = "digital_product"
    PHYSICAL_PRODUCT = "physical_product"
    # Commerce
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    DROPSHIPPING = "dropshipping"
    # Services locaux
    LOCAL_SERVICE = "local_service"
    FRANCHISE = "franchise"
    # Finance & Immobilier
    REAL_ESTATE = "real_estate"
    INVESTMENT = "investment"
    # Contenu & Influence
    CONTENT = "content"
    COACHING = "coaching"
    AGENCY = "agency"


@dataclass
class BusinessBlueprint:
    """Blueprint complet d'un business créé par NAYA."""
    id: str = field(default_factory=lambda: f"BIZ_{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    category: BusinessCategory = BusinessCategory.CONSULTING
    status: BusinessStatus = BusinessStatus.IDENTIFIED

    # Core
    problem_statement: str = ""
    solution: str = ""
    target_customer: str = ""
    unique_value_prop: str = ""

    # Financials
    price_floor: float = 1000.0
    price_recommended: float = 0.0
    price_anchor: float = 0.0
    mrr_target: float = 0.0
    first_deal_target: float = 0.0

    # Execution
    acquisition_channels: List[str] = field(default_factory=list)
    first_actions_72h: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    time_to_first_revenue_days: int = 7

    # Plan
    full_plan: str = ""
    proposal_template: str = ""

    # Metadata
    created_at: float = field(default_factory=time.time)
    launched_at: Optional[float] = None
    revenue_generated: float = 0.0
    source: str = "autonomous"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "problem": self.problem_statement,
            "solution": self.solution,
            "target": self.target_customer,
            "price_recommended": self.price_recommended,
            "price_anchor": self.price_anchor,
            "mrr_target": self.mrr_target,
            "channels": self.acquisition_channels,
            "actions_72h": self.first_actions_72h,
            "time_to_revenue_days": self.time_to_first_revenue_days,
            "revenue_generated": self.revenue_generated,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
        }


class BusinessFactory:
    """
    Usine à business autonome.
    Input: secteur ou brief.
    Output: business plan complet + proposition commerciale + actions.
    """

    SECTORS_CATALOG = [
        # B2B Services
        {"sector": "PME & artisans", "pain": "Gestion administrative chronophage", "category": BusinessCategory.AUTOMATION},
        {"sector": "Restaurants & food", "pain": "Commandes en ligne et fidélisation", "category": BusinessCategory.CONSULTING},
        {"sector": "BTP & construction", "pain": "Gestion chantier et devis", "category": BusinessCategory.SAAS},
        {"sector": "Cabinet comptable", "pain": "Automatisation rapprochements", "category": BusinessCategory.AUTOMATION},
        {"sector": "Agences immobilières", "pain": "Qualification leads et visites", "category": BusinessCategory.CHATBOT_AI},
        {"sector": "Cliniques & médecins", "pain": "Prise de RDV et suivi patients", "category": BusinessCategory.SAAS},
        {"sector": "E-commerce", "pain": "Panier abandonné et relance", "category": BusinessCategory.CHATBOT_AI},
        {"sector": "Avocats & notaires", "pain": "Gestion documents et clients", "category": BusinessCategory.AUTOMATION},
        {"sector": "Coaches & formateurs", "pain": "Scalabilité sans se démultiplier", "category": BusinessCategory.DIGITAL_PRODUCT},
        {"sector": "Hôtels & AirBnB", "pain": "Gestion multi-canaux et pricing", "category": BusinessCategory.CONSULTING},
        {"sector": "Startups tech", "pain": "MVP rapide et go-to-market", "category": BusinessCategory.CONSULTING},
        {"sector": "Retail & boutiques", "pain": "Trafic qualifié et conversion", "category": BusinessCategory.AGENCY},
        {"sector": "RH & recrutement", "pain": "Tri CV et entretiens", "category": BusinessCategory.CHATBOT_AI},
        {"sector": "Logistique & transport", "pain": "Optimisation tournées et coûts", "category": BusinessCategory.SAAS},
        {"sector": "Industrie & manufacturing", "pain": "Maintenance prédictive", "category": BusinessCategory.CONSULTING},
    ]

    def __init__(self):
        self._portfolio: Dict[str, BusinessBlueprint] = {}
        self._brain = None
        self._pricing = None
        self._stats = {
            "total_created": 0,
            "total_launched": 0,
            "total_revenue": 0.0,
        }
        self._init_engines()

    def _init_engines(self):
        try:
            from NAYA_CORE.execution.naya_brain import get_brain
            self._brain = get_brain()
        except Exception as e:
            log.debug(f"Brain not available: {e}")
        try:
            from BUSINESS_ENGINES.strategic_pricing_engine.pricing_engine import StrategicPricingEngine
            self._pricing = StrategicPricingEngine()
        except Exception as e:
            log.debug(f"Pricing not available: {e}")

    def create_from_brief(self, brief: str, category: str = "consulting") -> BusinessBlueprint:
        """Crée un business complet depuis un brief en langage naturel."""
        biz = BusinessBlueprint(
            category=self._parse_category(category),
            source="brief",
        )

        if self._brain and self._brain.available:
            # LLM-powered creation
            plan = self._brain.create_business_plan(brief)
            biz.full_plan = plan
            biz = self._parse_plan_into_blueprint(biz, plan, brief)
        else:
            # Rule-based fallback
            biz = self._rule_based_creation(biz, brief, category)

        biz.status = BusinessStatus.DESIGNED
        self._portfolio[biz.id] = biz
        self._stats["total_created"] += 1
        log.info(f"[FACTORY] Business created: {biz.name} ({biz.id}) — {biz.price_recommended:,.0f}€")
        return biz

    def create_from_sector(self, sector_index: int = None) -> BusinessBlueprint:
        """Crée un business depuis le catalogue de secteurs."""
        import random
        entry = self.SECTORS_CATALOG[sector_index % len(self.SECTORS_CATALOG)] \
            if sector_index is not None \
            else random.choice(self.SECTORS_CATALOG)

        brief = f"Business pour {entry['sector']}: résoudre '{entry['pain']}'"
        return self.create_from_brief(brief, entry["category"].value)

    def hunt_and_create(self, sector: str) -> List[BusinessBlueprint]:
        """Chasse des opportunités dans un secteur et crée les business."""
        blueprints = []

        if self._brain and self._brain.available:
            opportunities_text = self._brain.hunt_opportunities(sector)
            # Parse opportunities and create blueprints
            lines = opportunities_text.split("\n")
            current_opp = {}
            for line in lines:
                if line.strip().startswith("- NOM:") or "**NOM" in line:
                    if current_opp.get("name"):
                        bp = self.create_from_brief(
                            f"{current_opp['name']}: {current_opp.get('pain', '')}",
                            "consulting"
                        )
                        blueprints.append(bp)
                        if len(blueprints) >= 5: break
                    current_opp = {"name": line.split(":")[-1].strip()}
                elif "DOULEUR:" in line or "DOULEUR" in line:
                    current_opp["pain"] = line.split(":")[-1].strip()
            if current_opp.get("name") and len(blueprints) < 5:
                bp = self.create_from_brief(
                    f"{current_opp['name']}: {current_opp.get('pain', '')}",
                    "consulting"
                )
                blueprints.append(bp)
        else:
            # Fallback: create 3 from catalog
            for i in range(3):
                bp = self.create_from_sector(i)
                blueprints.append(bp)

        log.info(f"[FACTORY] Hunt in '{sector}': {len(blueprints)} businesses created")
        return blueprints

    def generate_proposal(self, blueprint_id: str, client_name: str = "") -> str:
        """Génère une proposition commerciale pour un business."""
        biz = self._portfolio.get(blueprint_id)
        if not biz:
            return "Business non trouvé"

        if self._brain and self._brain.available:
            proposal = self._brain.write_proposal(
                biz.problem_statement,
                biz.solution,
                biz.price_recommended,
                client_name,
            )
            biz.proposal_template = proposal
            return proposal

        return self._default_proposal(biz, client_name)

    def launch(self, blueprint_id: str) -> Dict:
        """Lance un business — marque comme actif."""
        biz = self._portfolio.get(blueprint_id)
        if not biz:
            return {"error": "Business not found"}
        biz.status = BusinessStatus.LAUNCHED
        biz.launched_at = time.time()
        self._stats["total_launched"] += 1
        log.info(f"[FACTORY] 🚀 LAUNCHED: {biz.name}")
        return {"status": "launched", "id": biz.id, "name": biz.name,
                "price": biz.price_recommended, "actions": biz.first_actions_72h}

    def get_portfolio(self) -> List[Dict]:
        return [b.to_dict() for b in self._portfolio.values()]

    def get_stats(self) -> Dict:
        active = sum(1 for b in self._portfolio.values()
                     if b.status in (BusinessStatus.LAUNCHED, BusinessStatus.GENERATING_REVENUE))
        return {**self._stats, "portfolio_size": len(self._portfolio), "active": active}

    # ── Private helpers ────────────────────────────────────────────────────────

    def _parse_category(self, cat: str) -> BusinessCategory:
        try:
            return BusinessCategory(cat.lower())
        except ValueError:
            return BusinessCategory.CONSULTING

    def _parse_plan_into_blueprint(self, biz: BusinessBlueprint, plan: str, brief: str) -> BusinessBlueprint:
        """Extract structured data from LLM plan."""
        lines = plan.split("\n")
        biz.name = brief.split(":")[0][:60] if ":" in brief else brief[:60]

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "## nom" in line_lower and i + 1 < len(lines):
                name = lines[i + 1].strip().lstrip("- ").strip()
                if name:
                    biz.name = name[:80]
            elif "problème" in line_lower and i + 1 < len(lines):
                biz.problem_statement = lines[i + 1].strip()
            elif "solution" in line_lower and i + 1 < len(lines):
                biz.solution = lines[i + 1].strip()
            elif "prix stratégique" in line_lower or "investissement" in line_lower:
                # Try to extract price
                for j in range(i, min(i + 4, len(lines))):
                    import re
                    prices = re.findall(r'(\d[\d\s]*)\s*[€$]', lines[j].replace(" ", ""))
                    if prices:
                        try:
                            p = float(prices[0].replace(" ", ""))
                            if p >= 500:
                                biz.price_recommended = p
                                break
                        except ValueError:
                            pass
            elif "canaux" in line_lower or "acquisition" in line_lower:
                for j in range(i + 1, min(i + 5, len(lines))):
                    ch = lines[j].strip().lstrip("123. -")
                    if ch and len(ch) > 5:
                        biz.acquisition_channels.append(ch)
            elif "actions 72h" in line_lower or "72h" in line_lower:
                for j in range(i + 1, min(i + 5, len(lines))):
                    act = lines[j].strip().lstrip("123. -")
                    if act and len(act) > 5:
                        biz.first_actions_72h.append(act)

        # Compute pricing if not extracted
        if biz.price_recommended < 1000 and self._pricing:
            biz.price_recommended = self._pricing.calculate_price(50000, 20000, "consulting", 0.6)
        biz.price_recommended = max(biz.price_recommended, 1000.0)
        biz.price_anchor = round(biz.price_recommended * 1.4 / 1000) * 1000
        biz.mrr_target = biz.price_recommended * 3
        biz.first_deal_target = biz.price_recommended

        if not biz.acquisition_channels:
            biz.acquisition_channels = ["LinkedIn Outreach", "Email direct", "Recommandations réseau"]
        if not biz.first_actions_72h:
            biz.first_actions_72h = [
                "Identifier 10 prospects qualifiés",
                "Envoyer 5 messages d'approche personnalisés",
                "Préparer une démo ou proof of concept"
            ]
        return biz

    def _rule_based_creation(self, biz: BusinessBlueprint, brief: str, category: str) -> BusinessBlueprint:
        """Fallback sans LLM."""
        biz.name = brief.split(":")[0][:60] if ":" in brief else brief[:60]
        biz.problem_statement = f"Problème identifié: {brief}"
        biz.solution = f"Solution experte pour: {brief}"
        biz.target_customer = "PME et entrepreneurs"
        biz.price_recommended = 3000.0
        biz.price_anchor = 4500.0
        biz.mrr_target = 9000.0
        biz.first_deal_target = 3000.0
        biz.acquisition_channels = ["LinkedIn direct", "Email cold outreach", "Réseau personnel"]
        biz.first_actions_72h = [
            "Définir 10 prospects cibles sur LinkedIn",
            "Rédiger et envoyer 5 messages personnalisés",
            "Créer une page de vente simple (Notion ou PDF)"
        ]
        biz.full_plan = f"Business plan généré en mode local (sans LLM):\n{brief}"
        return biz

    def _default_proposal(self, biz: BusinessBlueprint, client_name: str) -> str:
        name = client_name or "Cher prospect"
        return f"""Objet: Solution pour {biz.problem_statement[:50]}

{name},

Vous faites face à un défi bien réel : {biz.problem_statement}

Ce problème vous coûte du temps, de l'argent et de l'énergie chaque semaine.

Notre solution : {biz.solution}

Investissement : {biz.price_recommended:,.0f}€

Pour ce montant, vous obtenez un ROI direct dès le premier mois.

Êtes-vous disponible 20 minutes cette semaine pour en discuter ?

Cordialement,
NAYA Executive"""


# ── Singleton ──────────────────────────────────────────────────────────────────
_factory: Optional[BusinessFactory] = None


def get_factory() -> BusinessFactory:
    global _factory
    if _factory is None:
        _factory = BusinessFactory()
    return _factory
