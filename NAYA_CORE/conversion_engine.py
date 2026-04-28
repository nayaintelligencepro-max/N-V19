"""
NAYA — CONVERSION ENGINE V8
════════════════════════════════════════════════════════════════════════════════
L'argent ne vient pas de la détection — il vient du CLOSING.

Ce module gère les 4 leviers de conversion:
  1. VITESSE — contacter dans les 24H augmente le taux de conv. ×7
  2. PREUVE — ROI calculé, pas estimé — chiffres réels
  3. GARANTIE — réduction du risque perçu à zéro
  4. URGENCE — pourquoi agir maintenant plutôt que jamais

Chaque offre NAYA est optimisée sur ces 4 axes simultanément.
════════════════════════════════════════════════════════════════════════════════
"""
import time, logging, os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

log = logging.getLogger("NAYA.CONVERSION")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__('os').environ.get(key, default)



class ConversionTactic(Enum):
    """Tactiques de conversion éprouvées — classées par efficacité."""
    ROI_ANCHOR          = "roi_anchor"       # Ancrage sur coût de la douleur
    RISK_REVERSAL       = "risk_reversal"    # Garantie totale — zéro risque client
    SOCIAL_PROOF        = "social_proof"     # Preuves clients similaires
    URGENCY_REAL        = "urgency_real"     # Urgence basée sur coût du délai
    AUTHORITY_DEMO      = "authority_demo"   # Démo valeur avant achat
    FRAMING_COST_OF_NO  = "cost_of_no"       # Coût de ne rien faire > coût de l'offre
    SIMPLE_NEXT_STEP    = "simple_next_step" # Une seule action demandée


@dataclass
class ConversionScript:
    """Script de conversion complet pour un deal."""
    deal_id: str = ""
    pain_category: str = ""
    sector: str = ""
    price: float = 0.0
    annual_pain_cost: float = 0.0

    # 4 messages clés par canal
    linkedin_hook: str = ""      # Les 2 premières lignes — seul ce qui compte
    email_subject: str = ""      # Le taux d'ouverture dépend de ça
    email_opening: str = ""      # Les 3 premières lignes
    call_opener: str = ""        # Les 15 premières secondes

    # Arguments closing
    roi_statement: str = ""      # "Votre ROI est X en Y"
    risk_reversal: str = ""      # "Si pas de résultat, on rembourse intégralement"
    urgency_frame: str = ""      # "Chaque mois sans action = X€ perdus"
    objection_price: str = ""    # Réponse à "c'est trop cher"
    objection_time: str = ""     # Réponse à "pas le temps maintenant"
    objection_competitor: str = ""  # Réponse à "on a déjà quelqu'un"

    # CTA optimal
    primary_cta: str = ""        # Une seule action demandée


class ConversionEngine:
    """
    Génère les scripts de conversion optimaux pour chaque deal.
    Basé sur 4 leviers psychologiques éprouvés.
    """

    # Prix des garanties selon le secteur (ce que le client risque)
    GUARANTEE_TEMPLATES = {
        "cash_trapped":      "Vous récupérez le montant identifié en 30 jours — sinon remboursement intégral",
        "margin_invisible_loss": "Marges restaurées de X points en 60 jours — ou on continue gratuitement",
        "invoice_leak":      "Système opérationnel en 24H — sinon remboursement intégral",
        "underpriced":       "Première hausse testée sans perdre un seul client — sinon on annule sans frais",
        "client_bleed":      "Taux de churn réduit de 30% en 90 jours — sinon remboursement partiel",
        "dormant_asset":     "3 scénarios de monétisation livrés — ou on rembourse la moitié",
        "process_manual_tax":"Automatisation des 3 processus les plus lourds — ou on retravaille gratuit",
        "default":           "Résultats mesurables en 30 jours — ou remboursement intégral",
    }

    # Coût du délai (argent perdu chaque mois sans action)
    def _monthly_cost_of_delay(self, annual_pain: float) -> float:
        return round(annual_pain / 12)

    def build_conversion_script(self, deal_dict: Dict) -> ConversionScript:
        """Construit le script de conversion complet depuis un deal."""
        pain = deal_dict.get("pain", "").replace("_", " ")
        sector = deal_dict.get("sector", "votre secteur").replace("_", " ")
        price = float(deal_dict.get("price", 5000))
        annual = float(deal_dict.get("pain_annual_cost", 30000))
        roi = round(annual / max(price, 1), 1)
        monthly_loss = self._monthly_cost_of_delay(annual)
        title = deal_dict.get("title", f"Solution {pain}")
        guarantee = self.GUARANTEE_TEMPLATES.get(
            deal_dict.get("pain", "default"),
            self.GUARANTEE_TEMPLATES["default"]
        ).replace("X", str(int(annual * 0.03)))

        script = ConversionScript(
            deal_id=deal_dict.get("id", ""),
            pain_category=pain,
            sector=sector,
            price=price,
            annual_pain_cost=annual,
        )

        # ── LinkedIn hook — 2 lignes max ─────────────────────────────────────
        script.linkedin_hook = (
            f"Cette semaine j'ai vu 3 PME {sector} perdre {annual/3:,.0f}€ chacune à cause de {pain}.\n"
            f"La plupart ne le savaient pas. Voilà comment on le détecte en 20 minutes."
        )

        # ── Email subject ─────────────────────────────────────────────────────
        script.email_subject = f"{annual/12:,.0f}€/mois perdus — {pain} dans votre secteur"

        # ── Email opening (3 lignes — taux de réponse ×3 vs email générique) ─
        script.email_opening = (
            f"Bonjour,\n\n"
            f"J'analyse les entreprises {sector} depuis 3 ans. "
            f"Le problème #{1}: {pain}. "
            f"Il coûte {annual:,.0f}€/an en moyenne — sans que le dirigeant s'en rende compte.\n\n"
            f"On vient de le résoudre pour une PME similaire. ROI ×{roi} en 90 jours.\n"
            f"15 minutes pour voir si c'est votre cas ?"
        )

        # ── Call opener — 15 secondes ─────────────────────────────────────────
        script.call_opener = (
            f"'Bonjour [Prénom], je vous appelle car j'ai identifié que "
            f"les entreprises {sector} perdent en moyenne {monthly_loss:,.0f}€/mois "
            f"à cause de {pain}. Est-ce que ça vous parle? "
            f"J'ai 5 minutes pour vous montrer les chiffres.'"
        )

        # ── Arguments closing ─────────────────────────────────────────────────
        script.roi_statement = (
            f"Pour {price:,.0f}€ investis aujourd'hui, vous récupérez {annual:,.0f}€/an. "
            f"ROI ×{roi}. Payback en {round(price/annual*12, 1)} mois."
        )

        script.risk_reversal = (
            f"Garantie résultat: {guarantee}. "
            f"Vous ne payez que si vous voyez les résultats. "
            f"Le risque est nul de votre côté."
        )

        script.urgency_frame = (
            f"Chaque mois sans action = {monthly_loss:,.0f}€ supplémentaires perdus. "
            f"Sur 6 mois: {monthly_loss*6:,.0f}€. Sur 12 mois: {annual:,.0f}€. "
            f"L'offre ne change pas. Le coût de l'inaction, si."
        )

        script.objection_price = (
            f"Je comprends. {price:,.0f}€ c'est un investissement. "
            f"Mais regardons le calcul: vous perdez {annual:,.0f}€/an aujourd'hui. "
            f"L'intervention coûte {price:,.0f}€ une fois. "
            f"Le ROI est ×{roi} dès la première année. "
            f"Continuer comme ça coûte {annual-price:,.0f}€ de plus que d'agir."
        )

        script.objection_time = (
            f"Je comprends. C'est justement pour ça qu'on livre en {deal_dict.get('delivery_hours', 48)}H. "
            f"Votre équipe n'est pas mobilisée plus de 2H. "
            f"Et pendant qu'on travaille, vous gagnez du temps — pas l'inverse."
        )

        script.objection_competitor = (
            f"Excellent. Quelle est leur approche sur {pain}? "
            f"(écouter la réponse) "
            f"Ce que vous décrivez s'attaque aux symptômes. "
            f"Notre méthode s'attaque à la cause: {title}. "
            f"C'est pour ça que le ROI est ×{roi} et pas ×1.2."
        )

        script.primary_cta = (
            f"Une seule action: un appel de 20 minutes pour voir les chiffres sur votre cas. "
            f"Pas d'engagement. Pas de pitch. Juste les données."
        )

        return script

    def score_deal_conversion_potential(self, deal_dict: Dict) -> Dict:
        """Score la probabilité de conversion d'un deal (0-100)."""
        score = 0
        factors = []

        # ROI — plus c'est élevé, plus c'est irréfutable
        roi = float(deal_dict.get("pain_annual_cost", 0)) / max(float(deal_dict.get("price", 1)), 1)
        if roi >= 5: score += 30; factors.append(f"ROI ×{roi:.1f} exceptionnel (+30)")
        elif roi >= 3: score += 20; factors.append(f"ROI ×{roi:.1f} fort (+20)")
        elif roi >= 2: score += 10; factors.append(f"ROI ×{roi:.1f} acceptable (+10)")

        # Prix — zone de confort décisionnel
        price = float(deal_dict.get("price", 0))
        if 3000 <= price <= 15000: score += 25; factors.append("Prix zone décision autonome (+25)")
        elif 15000 <= price <= 40000: score += 15; factors.append("Prix décision conseil (+15)")
        elif price > 40000: score += 5; factors.append("Prix hors zone autonome (+5)")

        # Urgence douleur
        annual = float(deal_dict.get("pain_annual_cost", 0))
        monthly = annual / 12
        if monthly > 5000: score += 20; factors.append(f"{monthly:,.0f}€/mois perdu — urgence forte (+20)")
        elif monthly > 2000: score += 12; factors.append(f"{monthly:,.0f}€/mois — urgence moyenne (+12)")

        # Discrétion
        pain = deal_dict.get("pain", "")
        hidden_pains = ["underpriced", "pricing_paralysis", "dormant_asset", "founder_bottleneck"]
        if any(h in pain for h in hidden_pains):
            score += 15; factors.append("Douleur invisible — personne d'autre ne la détecte (+15)")

        # Secteur
        sector = deal_dict.get("sector", "")
        hot_sectors = ["pme_b2b", "startup_scaleup", "liberal_professions"]
        if any(s in sector for s in hot_sectors):
            score += 10; factors.append("Secteur haute conversion (+10)")

        return {
            "score": min(score, 100),
            "tier": "HOT" if score >= 70 else "WARM" if score >= 45 else "COLD",
            "factors": factors,
            "recommended_channel": "phone_outbound" if score >= 70 else "email + linkedin",
            "estimated_close_days": 7 if score >= 70 else 21 if score >= 45 else 45,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_conv_engine: Optional[ConversionEngine] = None

def get_conversion_engine() -> ConversionEngine:
    global _conv_engine
    if _conv_engine is None:
        _conv_engine = ConversionEngine()
    return _conv_engine
