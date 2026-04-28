"""
NAYA — Anthropic Claude Provider (Production)
Cerveau stratégique principal — Claude 3.5 Sonnet.
"""
import os
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.LLM.ANTHROPIC")


class AnthropicProvider:
    """Provider Anthropic Claude — stratégie, analyse, décision."""

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    FAST_MODEL = "claude-3-haiku-20240307"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model or os.environ.get("LLM_STRATEGIC", self.DEFAULT_MODEL)
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        if not self._api_key or self._api_key.startswith("sk-ant-METS"):
            log.debug("Anthropic API key not configured")
            return
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
            self._available = True
            log.info(f"✅ Anthropic provider ready — model: {self._model}")
        except ImportError:
            log.debug("anthropic package not installed — pip install anthropic")
        except Exception as e:
            log.warning(f"Anthropic init error: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def execute(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self._available:
            return {"provider": "anthropic", "error": "Not available", "text": None}

        params = params or {}
        model = params.get("model", self._model)
        max_tokens = params.get("max_tokens", int(os.environ.get("LLM_MAX_TOKENS", 4096)))
        temperature = params.get("temperature", float(os.environ.get("LLM_TEMPERATURE_STRATEGIC", 0.3)))
        system = params.get("system", "Tu es NAYA, un système d'intelligence exécutive souverain. Tu crées et structures des business réels.")

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text if response.content else ""
            return {
                "provider": "anthropic",
                "model": model,
                "text": text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "stop_reason": response.stop_reason,
            }
        except Exception as e:
            log.error(f"Anthropic API error: {e}")
            return {"provider": "anthropic", "error": str(e), "text": None}

    def think(self, task: str, context: Dict = None) -> str:
        """Shortcut for strategic thinking."""
        system = (
            "Tu es NAYA, système exécutif souverain. "
            "Réponds avec précision, pragmatisme et orienté résultats business."
        )
        ctx_str = f"\nContexte: {context}" if context else ""
        result = self.execute(task + ctx_str, {"system": system, "temperature": 0.3})
        return result.get("text") or ""

    def create_business(self, brief: str) -> str:
        """Génère un plan business complet."""
        prompt = f"""Crée un business plan complet et actionnable pour:
{brief}

Structure ta réponse avec:
1. NOM & POSITIONNEMENT (1 phrase)
2. PROBLÈME RÉSOLU (douleur réelle et solvable)
3. SOLUTION & OFFRE (ce qu'on vend exactement)
4. PRIX (basé sur valeur, plancher 1000€)
5. CANAUX D'ACQUISITION (3 canaux concrets)
6. REVENUS PREMIER MOIS (objectif réaliste)
7. ACTIONS 72H (3 actions immédiates)

Sois précis, concret, sans vœux pieux."""
        result = self.execute(prompt, {"temperature": 0.4, "max_tokens": 2000})
        return result.get("text") or "Erreur génération business plan"

    def analyze_opportunity(self, opportunity: Dict) -> Dict:
        """Analyse profonde d'une opportunité business."""
        prompt = f"""Analyse cette opportunité business comme un investisseur expérimenté:

Opportunité: {opportunity.get('name', 'N/A')}
Marché: {opportunity.get('market', 'N/A')}
Valeur estimée: {opportunity.get('value', 0):,}€
Contexte: {opportunity.get('description', '')}

Donne:
- Score de viabilité (0-100)
- Risques principaux (top 3)
- Points forts (top 3)
- Recommandation: LAUNCH / DEFER / PIVOT
- Première action concrète

Format JSON uniquement."""
        result = self.execute(prompt, {"temperature": 0.2, "max_tokens": 1000})
        text = result.get("text", "")
        try:
            import json
            # Extract JSON from response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return {"raw_analysis": text, "recommendation": "ANALYZE"}
