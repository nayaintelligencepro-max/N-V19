"""
NAYA V19 — Storytelling Engine
Génère du contenu qui convertit — LinkedIn, TikTok, Instagram, Email.
LLM (Anthropic/Grok) pour personnalisation maximale.
Fonctionne 100% sans LLM avec templates haute conversion.
"""
import os, logging
from typing import Dict, List, Optional
from datetime import datetime

log = logging.getLogger("NAYA.STORY")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)

def _llm(prompt: str, max_tokens: int = 400) -> str:
    """Anthropic → Grok fallback pour génération de contenu."""
    # Anthropic
    try:
        import anthropic
        key = _gs("ANTHROPIC_API_KEY")
        if key:
            c = anthropic.Anthropic(api_key=key)
            r = c.messages.create(model="claude-3-haiku-20240307", max_tokens=max_tokens,
                messages=[{"role":"user","content":prompt}])
            return r.content[0].text
    except Exception as e:
        if "credit" not in str(e).lower() and "balance" not in str(e).lower():
            log.debug(f"[STORY] Anthropic: {e}")
    # Grok fallback
    try:
        import httpx
        gk = _gs("GROK_API_KEY") or _gs("XAI_API_KEY")
        if gk:
            r = httpx.post("https://api.x.ai/v1/chat/completions",
                headers={"Authorization":f"Bearer {gk}","Content-Type":"application/json"},
                json={"model":"grok-beta","messages":[{"role":"user","content":prompt}],
                      "max_tokens":max_tokens,"temperature":0.7}, timeout=30)
            if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
    except Exception as e: log.debug(f"[STORY] Grok: {e}")
    return ""

PAIN_HOOKS = {
    "CASH_TRAPPED":         "Votre trésorerie suffoque alors que vos clients vous doivent de l'argent.",
    "MARGIN_INVISIBLE_LOSS":"3 entreprises cette semaine ont découvert qu'elles perdaient des milliers€/mois sans le savoir.",
    "INVOICE_LEAK":         "Un artisan perd en moyenne 22 000€/an en oubliant de facturer. Pas de mauvaise volonté — juste du chaos.",
    "UNDERPRICED":          "Ce consultant facturait 500€/j. Ses concurrents: 900€. Même profil. Même résultat.",
    "GROWTH_BLOCK":         "Votre startup brûle de l'argent. La croissance attendue n'est pas venue.",
    "PROCESS_MANUAL_TAX":   "Votre équipe passe 20H/semaine sur des tâches qu'une machine ferait en 2 minutes.",
    "CLIENT_BLEED":         "Acquérir un client coûte 5× plus que fidéliser. Pourtant la plupart inversent le budget.",
    "default":              "J'ai analysé ce secteur cette semaine. Le même problème revient chez 3 entreprises sur 5.",
}

class StorytellingEngine:
    FORMULAS = {"PAS":"Problem→Agitation→Solution","AIDA":"Attention→Interest→Desire→Action"}

    def generate_linkedin_post(self, pain: str, solution: str, result: str,
                                sector: str = "", pain_cost: float = 0,
                                use_llm: bool = True) -> str:
        monthly = round(pain_cost/12) if pain_cost else 0
        # LLM en priorité
        if use_llm:
            prompt = (
                f"Post LinkedIn B2B COURT (150 mots max) — FORMAT PAS:\n"
                f"Secteur: {sector.replace('_',' ')} | Douleur: {pain}\n"
                f"Solution: {solution} | Résultat: {result}\n"
                f"Coût mensuel du problème: {monthly:,.0f}€/mois\n\n"
                f"Règles: direct, précis, pas de bullshit, UN seul CTA final, ton consultant-expert."
            )
            r = _llm(prompt, max_tokens=280)
            if r and len(r) > 60: return r
        # Fallback template
        pain_key = pain.upper().replace(" ","_").replace("-","_")
        hook = PAIN_HOOKS.get(next((k for k in PAIN_HOOKS if k in pain_key),
                                   next((k for k in PAIN_HOOKS if pain_key in k),"default")),
                               PAIN_HOOKS["default"])
        return (
            f"{hook}\n\n"
            f"Ce que j'ai vu chez 3 entreprises {sector.replace('_',' ')} cette semaine:\n"
            f"Le problème: {pain}\n\n"
            f"Ce qu'on a fait: {solution}\n\n"
            f"Résultat: {result}\n\n"
            f"Si vous vous reconnaissez → 20 min pour voir si c'est votre cas."
        )

    def generate_tiktok_script(self, pain: str, solution: str, result: str,
                                sector: str = "") -> Dict:
        prompt = (
            f"Script TikTok business 60 secondes:\n"
            f"[0-5s] HOOK choc | [5-20s] Problème+chiffre | [20-45s] Solution 3 étapes | [45-60s] CTA\n"
            f"Secteur: {sector.replace('_',' ')} | Problème: {pain} | Résultat: {result}\n"
            f"Ton: authentique, direct, pas de jargon."
        )
        r = _llm(prompt, max_tokens=350)
        if r and len(r) > 80:
            return {"script":r,"duration":"60s","platform":"tiktok","est_views":500,"est_leads":2}
        return {"script":(
            f"[HOOK] Tu perds combien par mois à cause de {pain}?\n"
            f"[PROB] Dans {sector.replace('_',' ')}: souvent des milliers€ sans le savoir.\n"
            f"[SOL] 3 étapes: 1) Diagnostic 2) Plan 3) Exécution en 48H\n"
            f"[CTA] Résultat: {result}. Lien en bio pour voir ton cas."
        ),"duration":"60s","platform":"tiktok","est_views":200,"est_leads":1}

    def generate_instagram_caption(self, pain: str, result: str, sector: str = "") -> Dict:
        prompt = (
            f"Caption Instagram business 120 mots max + 7 hashtags french business.\n"
            f"Secteur: {sector.replace('_',' ')} | Problème: {pain} | Résultat: {result}\n"
            f"Ton: inspirant mais concret."
        )
        r = _llm(prompt, max_tokens=220)
        if r and len(r) > 50: return {"caption":r,"platform":"instagram","est_reach":300}
        tags = f"#{sector.replace('_','')} #business #entrepreneur #pme #revenus #dirigeant #croissance"
        return {"caption":(f"💡 {pain} coûte des milliers€/an aux entreprises {sector.replace('_',' ')}.\n"
                f"Résultat client récent: {result}.\nLien en bio si tu veux voir les chiffres.\n\n{tags}"),
                "platform":"instagram","est_reach":150}

    def generate_content_series(self, sector: str, pain_category: str,
                                  pain_cost: float, weeks: int = 4) -> List[Dict]:
        """Série multi-canal 4 semaines: LinkedIn + TikTok + Instagram."""
        PAIN_LABELS = {"CASH_TRAPPED":"trésorerie bloquée","MARGIN_INVISIBLE_LOSS":"pertes de marges",
            "INVOICE_LEAK":"fuites de facturation","UNDERPRICED":"sous-facturation",
            "GROWTH_BLOCK":"croissance bloquée","PROCESS_MANUAL_TAX":"processus manuels coûteux",
            "CLIENT_BLEED":"churn silencieux"}
        pain  = PAIN_LABELS.get(pain_category, pain_category.replace("_"," "))
        result = f"{pain_cost:,.0f}€/an récupérés"
        posts = []
        for week in range(1, min(weeks+1,5)):
            posts.append({"week":week,"platform":"linkedin","type":"post",
                "content":self.generate_linkedin_post(pain, "méthode NAYA", result, sector, pain_cost, week==1),
                "timing":"mardi 9h30"})
            if week in (1,3):
                posts.append({"week":week,"platform":"tiktok","type":"video_script",
                    "content":self.generate_tiktok_script(pain,"48H",result,sector)["script"],
                    "timing":"jeudi 19h"})
        return posts

    def generate_premium_content(self, business_model: Dict) -> Dict:
        sector = business_model.get("sector","")
        pain   = business_model.get("problem","problème principal")
        result = business_model.get("result","résultat mesurable")
        pc     = float(business_model.get("pain_annual_cost",5000))
        lp     = self.generate_linkedin_post(pain,"méthode NAYA",result,sector,pc)
        return {"headline":f"Comment {sector.replace('_',' ')} résout {pain} en 48h",
                "hook":lp[:100]+"...","body":lp,"cta":"20 min sans engagement",
                "linkedin_post":lp,"estimated_reach":500,"estimated_leads":3}

    def generate_cold_email(self, company: str, pain: str, service: str, result: str) -> Dict:
        return {"subject":f"Question rapide sur {pain} chez {company}",
                "body":(f"Bonjour,\n\nJ'ai analysé {company} — problème identifié: {pain}.\n"
                        f"3 entreprises similaires résolues avec {service}.\nRésultat: {result}.\n"
                        f"15 minutes pour voir si c'est votre cas ?\n\nBien à vous,"),
                "expected_reply_rate":0.07}

    def generate_pitch(self, offer: Dict) -> str:
        return (f"Vous perdez de l'argent à cause de {offer.get('pain','?')}.\n"
                f"Résolu en 48h. Investissement: {offer.get('price',5000):,.0f}€. "
                f"Garantie: {offer.get('guarantee','remboursement intégral si pas de résultat')}.")


def get_storytelling_engine() -> StorytellingEngine:
    return StorytellingEngine()
