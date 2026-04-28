"""
NAYA V19 — Free LLM Provider
Fournit un LLM sans clé via templates intelligents + Groq si disponible.
Jamais de crash — toujours une réponse.
"""
import os, logging, json
from typing import Optional

log = logging.getLogger("NAYA.LLM.FREE")


class FreeLLMProvider:
    """
    Provider LLM zéro-coût.
    Tente Groq (14 400 requêtes/j gratuites) en premier.
    Fallback sur templates intelligents contextuels.
    """

    TEMPLATES = {
        "pain_analysis": (
            "Analyse de douleur business détectée. Signal: {signal}. "
            "Estimation impact annuel: {cost}€. Catégorie: {category}. "
            "Action recommandée: Contacter décisionnaire dans 24h avec proposition chiffrée."
        ),
        "outreach_email": (
            "Objet: Réduction immédiate de {pain_type} — {company}\n\n"
            "Bonjour {name},\n\n"
            "Nous avons identifié que {company} fait face à {pain_type}, "
            "avec un impact estimé à {cost}€/an.\n\n"
            "Notre intervention spécialisée a permis à des acteurs comparables "
            "de réduire ce coût de 40 à 70% en moins de 90 jours.\n\n"
            "Seriez-vous disponible pour un échange de 15 minutes cette semaine ?\n\n"
            "Cordialement,\nNAYA Business Intelligence"
        ),
        "offer_generation": (
            "PROPOSITION COMMERCIALE\n\n"
            "Client: {company}\nDouleur identifiée: {pain}\n"
            "Valeur annuelle du problème: {cost}€\n\n"
            "NOTRE SOLUTION:\n"
            "- Intervention: {intervention}\n"
            "- Délai: {delay}\n"
            "- Investissement: {price}€\n"
            "- ROI attendu: {roi}x à 6 mois\n\n"
            "Paiement: PayPal.me ou Deblock.me — lien fourni à signature."
        ),
        "followup": (
            "Bonjour {name},\n\n"
            "Je reviens vers vous concernant notre proposition pour {company}.\n\n"
            "Avez-vous eu l'occasion d'en prendre connaissance ? "
            "Je reste disponible pour adapter le périmètre selon vos priorités.\n\n"
            "Lien de paiement sécurisé disponible dès validation.\n\n"
            "Cordialement"
        ),
        "default": "Analyse NAYA V19 en cours. Traitement du signal: {prompt}",
    }

    def generate(self, prompt: str, template_type: str = "default", **kwargs) -> str:
        # Tenter Groq d'abord
        result = self._try_groq(prompt)
        if result:
            return result
        # Fallback template
        tmpl = self.TEMPLATES.get(template_type, self.TEMPLATES["default"])
        try:
            return tmpl.format(prompt=prompt[:100], **kwargs)
        except Exception:
            return self.TEMPLATES["default"].format(prompt=prompt[:100])

    def _try_groq(self, prompt: str) -> Optional[str]:
        try:
            import urllib.request, json as _json
            key = os.environ.get("GROQ_API_KEY", "")
            if not key:
                return None
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
            }
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=_json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = _json.loads(r.read())
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None


_provider: Optional[FreeLLMProvider] = None

def get_free_llm() -> FreeLLMProvider:
    global _provider
    if _provider is None:
        _provider = FreeLLMProvider()
    return _provider
