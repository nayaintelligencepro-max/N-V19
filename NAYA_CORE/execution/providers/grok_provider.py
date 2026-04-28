"""
NAYA V19 — GROK / xAI PROVIDER
Grok-beta : LLM ultra-rapide de xAI (Elon Musk).
Compatible OpenAI API format → intégration simple.

Modèles disponibles:
  - grok-beta        : le plus capable (stratégie, analyse)
  - grok-vision-beta : avec vision (analyse images/docs)

Clé: GROK_API_KEY ou XAI_API_KEY dans SECRETS/keys/llm.env
"""

import os
import json
import time
import logging
import hashlib
import urllib.request
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.LLM.GROK")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class GrokProvider:
    """
    Grok / xAI Provider — LLM haute performance.
    API compatible OpenAI → mêmes patterns d'appel.
    Excellent pour: analyse, stratégie, génération d'offres, copywriting.
    """

    BASE_URL = "https://api.x.ai/v1/chat/completions"
    DEFAULT_MODEL = "grok-beta"
    MODELS = {
        "strategic": "grok-beta",
        "creative":  "grok-beta",
        "fast":      "grok-beta",
    }

    def __init__(self):
        self._key = _gs("GROK_API_KEY") or _gs("XAI_API_KEY") or _gs("GROK_API_KEY")
        self._model = os.environ.get("GROK_MODEL", self.DEFAULT_MODEL)
        self._available = bool(self._key and len(self._key) > 20)
        self._calls = 0
        self._errors = 0

        if self._available:
            log.info(f"✅ Grok provider ready — modèle: {self._model}")
        else:
            log.debug("Grok: GROK_API_KEY non configurée")

    @property
    def available(self) -> bool:
        return self._available

    def execute(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self._available:
            return {"provider": "grok", "error": "Not configured", "text": None}

        params = params or {}
        model = params.get("model", self._model)
        max_tokens = params.get("max_tokens", 4096)
        temperature = params.get("temperature", 0.3)
        system = params.get(
            "system",
            "Tu es NAYA SUPREME, un système d'intelligence exécutive souverain. "
            "Tu crées et structures des business réels qui génèrent des revenus immédiats. "
            "Tu analyses avec précision, tu décides vite, tu proposes du concret."
        )

        self._calls += 1

        try:
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.BASE_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return {
                "provider": "grok",
                "model": model,
                "text": text,
                "tokens_used": usage.get("total_tokens", 0),
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "stop_reason": data["choices"][0].get("finish_reason", "stop"),
            }

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            log.warning(f"[Grok] HTTP {e.code}: {body}")
            self._errors += 1
            return {"provider": "grok", "error": f"HTTP {e.code}: {body}", "text": None}

        except Exception as e:
            log.warning(f"[Grok] Error: {e}")
            self._errors += 1
            return {"provider": "grok", "error": str(e), "text": None}

    def think(self, task: str, context: Dict = None) -> str:
        """Pensée stratégique."""
        ctx = f"\nContexte: {json.dumps(context, ensure_ascii=False)}" if context else ""
        result = self.execute(task + ctx, {"temperature": 0.25})
        return result.get("text") or ""

    def create_business(self, brief: str) -> str:
        """Génère un business plan complet et actionnable."""
        prompt = f"""Tu es NAYA SUPREME, expert en création de business rapide qui génère du cash.

Brief: {brief}

Génère un business plan ultra-concret en 7 points:

1. 🎯 NOM & POSITIONNEMENT (1 phrase percutante)
2. 💔 DOULEUR RÉELLE (quantifiée en €/an, spécifique)
3. 💡 OFFRE EXACTE (ce qu'on vend, livrable précis en 48h)
4. 💰 PRIX (basé sur ROI, minimum 1000€ — justification)
5. 📣 3 CANAUX D'ACQUISITION (actions concrètes avec scripts)
6. 📈 REVENUS 72H / 30J / 90J (objectifs réalistes chiffrés)
7. ⚡ ACTIONS IMMÉDIATES (3 actions à faire dans les 4 heures)

Sois TRÈS précis. Donne des chiffres réels. Pas de généralités."""

        result = self.execute(prompt, {
            "temperature": 0.4,
            "max_tokens": 3000,
            "system": "Tu es un expert en création de business à cash rapide. Tu donnes du concret, des chiffres, des actions."
        })
        return result.get("text") or ""

    def analyze_opportunity(self, opportunity: Dict) -> Dict:
        """Analyse une opportunité business avec scoring."""
        prompt = f"""Analyse cette opportunité comme un investisseur avec 20 ans d'expérience:

Opportunité: {opportunity.get('name', 'N/A')}
Marché: {opportunity.get('market', 'N/A')}
Valeur douleur estimée: {opportunity.get('value', 0):,}€/an
Description: {opportunity.get('description', '')}

Réponds UNIQUEMENT en JSON valide (pas de markdown):
{{
  "viability_score": <0-100>,
  "urgency_score": <0-100>,
  "risks": ["risque1", "risque2", "risque3"],
  "strengths": ["force1", "force2", "force3"],
  "recommendation": "LAUNCH|DEFER|PIVOT",
  "first_action": "action concrète dans les 24h",
  "revenue_potential_30d": <montant en euros>,
  "revenue_potential_90d": <montant en euros>,
  "ideal_price": <prix recommandé en euros>,
  "confidence": <0-100>
}}"""

        result = self.execute(prompt, {
            "temperature": 0.15,
            "max_tokens": 800,
            "system": "Tu es un analyste business expert. Réponds UNIQUEMENT en JSON valide, sans markdown ni backticks."
        })
        text = result.get("text", "")
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return {
            "viability_score": 65,
            "recommendation": "LAUNCH",
            "first_action": "Contacter 10 prospects qualifiés",
            "revenue_potential_30d": int(opportunity.get("value", 30000) * 0.15),
            "confidence": 60,
            "raw": text,
        }

    def generate_cold_email(self, company: str, contact: str, pain: str,
                            pain_cost: float, price: float, offer_title: str) -> Dict:
        """Génère un email cold personnalisé et percutant."""
        monthly_cost = pain_cost / 12
        roi = round(pain_cost / max(price, 1), 1)

        prompt = f"""Génère un email cold B2B court et percutant (150 mots max).

Destinataire: {contact or 'le dirigeant'} de {company}
Problème identifié: {pain.replace('_', ' ')} coûte {pain_cost:,.0f}€/an (soit {monthly_cost:,.0f}€/mois)
Notre offre: {offer_title}
Prix: {price:,.0f}€
ROI client: ×{roi} sur 12 mois

RÈGLES ABSOLUES:
- Commencer par la DOULEUR, pas par "Bonjour je m'appelle"
- Mentionner le coût mensuel exact ({monthly_cost:,.0f}€/mois qui part)
- Preuve sociale (on l'a fait pour d'autres)
- UNE seule question en CTA (pas un lien)
- Ton humain, pas vendeur, pas générique

Format exact:
OBJET: [ligne d'objet percutante]

[Corps de l'email]"""

        result = self.execute(prompt, {
            "temperature": 0.65,
            "max_tokens": 500,
            "system": "Tu es un expert en cold email B2B avec +80% de taux de réponse. Chaque email est unique et personnel."
        })

        text = result.get("text", "")
        lines = text.strip().split("\n")

        subject = ""
        body_lines = []
        skip_next_blank = False

        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("OBJET:") or stripped.upper().startswith("SUBJECT:"):
                subject = stripped.split(":", 1)[-1].strip().strip('"').strip("'")
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()
        # Nettoyer les lignes vides en début
        body = body.lstrip("\n")

        return {
            "subject": subject or f"Question sur {pain.replace('_', ' ')} chez {company}",
            "body": body or text,
            "provider": "grok",
            "model": self._model,
        }

    def get_stats(self) -> Dict:
        return {
            "provider": "grok",
            "available": self._available,
            "model": self._model,
            "calls": self._calls,
            "errors": self._errors,
            "success_rate": round((1 - self._errors / max(self._calls, 1)) * 100, 1),
        }
