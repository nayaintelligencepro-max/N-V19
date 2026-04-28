"""
NAYA — LLM Brain Router (Production)
Orchestre tous les LLM avec fallback automatique, cost-routing et cache.
Claude → GPT-4 → Mistral → Fallback local
"""
import os
import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.LLM.BRAIN")

def _gs(key: str, default: str = "") -> str:
    """Lit la clé LLM en temps réel depuis SECRETS/keys/llm.env."""
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__('os').environ.get(key, default)



class TaskType(Enum):
    STRATEGIC = "strategic"       # Analyse, décision, planification → Claude
    CREATIVE = "creative"         # Génération d'idées, copywriting → GPT-4o
    FAST = "fast"                 # Tâches simples, classification → Haiku/mini
    ANALYSIS = "analysis"         # Données, chiffres, patterns → Claude
    BUSINESS_CREATION = "business_creation"  # Créer un business → Claude
    HUNT = "hunt"                 # Détecter opportunités → Claude
    PRICING = "pricing"           # Calcul prix → Claude
    PROPOSAL = "proposal"         # Rédiger offre → GPT-4o


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


class LLMCache:
    """Cache simple en mémoire pour éviter les appels redondants."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self._store: Dict[str, Dict] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _key(self, prompt: str, model: str) -> str:
        return hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[str]:
        k = self._key(prompt, model)
        entry = self._store.get(k)
        if not entry:
            return None
        if time.time() - entry["ts"] > self._ttl:
            del self._store[k]
            return None
        return entry["text"]

    def set(self, prompt: str, model: str, text: str):
        if len(self._store) >= self._max_size:
            # Evict oldest
            oldest = min(self._store.items(), key=lambda x: x[1]["ts"])
            del self._store[oldest[0]]
        self._store[self._key(prompt, model)] = {"text": text, "ts": time.time()}

    def size(self) -> int:
        return len(self._store)


class NayaBrain:
    """
    Cerveau LLM central de NAYA.
    Routing intelligent, fallback automatique, cache, métriques.
    """

    TASK_MODEL_MAP = {
        TaskType.STRATEGIC:         lambda: os.environ.get("LLM_STRATEGIC", "claude-3-5-sonnet-20241022"),
        TaskType.CREATIVE:          lambda: os.environ.get("LLM_CREATIVE", "gpt-4o"),
        TaskType.FAST:              lambda: os.environ.get("LLM_FAST", "claude-3-haiku-20240307"),
        TaskType.ANALYSIS:          lambda: os.environ.get("LLM_ANALYSIS", "claude-3-5-sonnet-20241022"),
        TaskType.BUSINESS_CREATION: lambda: os.environ.get("LLM_STRATEGIC", "claude-3-5-sonnet-20241022"),
        TaskType.HUNT:              lambda: os.environ.get("LLM_STRATEGIC", "claude-3-5-sonnet-20241022"),
        TaskType.PRICING:           lambda: os.environ.get("LLM_ANALYSIS", "claude-3-5-sonnet-20241022"),
        TaskType.PROPOSAL:          lambda: os.environ.get("LLM_CREATIVE", "gpt-4o"),
    }

    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self._cache = LLMCache()
        self._stats = {"calls": 0, "cache_hits": 0, "errors": 0, "tokens_total": 0}
        self._init_providers()

    def _init_providers(self):
        # Anthropic
        try:
            from NAYA_CORE.execution.providers.anthropic_provider import AnthropicProvider
            p = AnthropicProvider()
            if p.available:
                self._providers["anthropic"] = p
                log.info("✅ LLM Brain: Anthropic Claude online")
        except Exception as e:
            log.debug(f"Anthropic provider: {e}")

        # OpenAI
        try:
            from NAYA_CORE.execution.providers.openai_provider import OpenAIProvider
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key and not api_key.startswith("sk-METS"):
                p = OpenAIProvider()
                self._providers["openai"] = p
                log.info("✅ LLM Brain: OpenAI online")
        except Exception as e:
            log.debug(f"OpenAI provider: {e}")

        if not self._providers:
            log.warning("⚠️ No LLM provider available — add API keys to .env")
        else:
            log.info(f"✅ LLM Brain ready — {len(self._providers)} provider(s): {list(self._providers.keys())}")

    @property
    def available(self) -> bool:
        return bool(self._providers)

    def think(
        self,
        prompt: str,
        task_type: TaskType = TaskType.STRATEGIC,
        system: str = None,
        use_cache: bool = True,
        temperature: float = None,
        max_tokens: int = None,
    ) -> LLMResponse:
        """Main entry point — route & execute."""
        self._stats["calls"] += 1
        target_model = self.TASK_MODEL_MAP[task_type]()

        # Cache check
        if use_cache:
            cached = self._cache.get(prompt, target_model)
            if cached:
                self._stats["cache_hits"] += 1
                return LLMResponse(text=cached, provider="cache", model=target_model, cached=True)

        # Provider selection
        provider_name = self._select_provider(target_model)
        if not provider_name:
            self._stats["errors"] += 1
            return LLMResponse(text="", provider="none", model="none",
                               error="No LLM provider available — configure API keys in .env")

        # Execute with fallback
        start = time.time()
        provider = self._providers[provider_name]
        params: Dict[str, Any] = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if system:
            params["system"] = system

        # Inject model hint
        if "claude" in target_model:
            params.setdefault("model", target_model)
        elif "gpt" in target_model:
            params["model"] = target_model

        result = provider.execute(prompt, params)
        latency = (time.time() - start) * 1000
        text = result.get("text") or ""
        tokens = result.get("tokens_used", 0)
        self._stats["tokens_total"] += tokens

        if text and use_cache:
            self._cache.set(prompt, target_model, text)

        resp = LLMResponse(
            text=text,
            provider=provider_name,
            model=result.get("model", target_model),
            tokens_used=tokens,
            latency_ms=round(latency, 1),
            error=result.get("error"),
        )

        if not resp.ok:
            self._stats["errors"] += 1
            log.warning(f"[BRAIN] {provider_name} failed: {resp.error} — trying fallback")
            return self._fallback(prompt, params, exclude=provider_name)

        return resp

    def _select_provider(self, model: str) -> Optional[str]:
        """Select best provider for requested model."""
        if "claude" in model and "anthropic" in self._providers:
            return "anthropic"
        if ("gpt" in model or "o1" in model) and "openai" in self._providers:
            return "openai"
        if "mistral" in model and "mistral" in self._providers:
            return "mistral"
        # Fallback: first available
        return next(iter(self._providers), None)

    def _fallback(self, prompt: str, params: Dict, exclude: str = "") -> LLMResponse:
        """Try next available provider."""
        for name, provider in self._providers.items():
            if name == exclude:
                continue
            try:
                result = provider.execute(prompt, params)
                text = result.get("text") or ""
                if text:
                    return LLMResponse(text=text, provider=name, model=name)
            except Exception:
                continue
        return LLMResponse(text="", provider="none", model="none",
                           error="All providers failed")

    # ── High-level shortcuts ───────────────────────────────────────────────────

    def create_business_plan(self, brief: str, context: Dict = None) -> str:
        """Generate complete business plan with LLM."""
        ctx = f"\nContexte additionnel: {context}" if context else ""
        prompt = f"""Tu es NAYA, système exécutif souverain spécialisé en création de business.

Crée un business plan complet, pragmatique et immédiatement actionnable pour:
{brief}{ctx}

Réponds EXACTEMENT dans ce format:

## NOM DU BUSINESS
[Nom court et mémorable]

## PROBLÈME RÉSOLU
[La douleur réelle, actuelle, solvable — en 2 phrases]

## SOLUTION & OFFRE PRINCIPALE
[Ce qu'on vend exactement — prix, format, livrable]

## PRIX STRATÉGIQUE
[Prix basé sur valeur créée — minimum 1000€ — justification]

## 3 CANAUX D'ACQUISITION IMMÉDIATS
1. [Canal 1 — action concrète]
2. [Canal 2 — action concrète]  
3. [Canal 3 — action concrète]

## OBJECTIF REVENUS J+30
[Montant réaliste en € — comment l'atteindre]

## ACTIONS 72H
1. [Action 1 — demain matin]
2. [Action 2 — dans 24h]
3. [Action 3 — dans 72h]

## RISQUES & MITIGATION
[Top 2 risques + comment les neutraliser]"""

        response = self.think(prompt, TaskType.BUSINESS_CREATION, temperature=0.4, max_tokens=2500)
        return response.text or "⚠️ LLM non disponible — configure ta clé Anthropic dans .env"

    def hunt_opportunities(self, sector: str, context: str = "") -> str:
        """Hunt for real business opportunities in a sector."""
        prompt = f"""Tu es NAYA en mode chasse d'opportunités.

Secteur ciblé: {sector}
{f'Contexte: {context}' if context else ''}

Identifie 5 opportunités business réelles, non saturées, avec douleurs solvables.

Pour chaque opportunité:
- NOM: [Nom de l'opportunité]
- DOULEUR: [Problème précis que les gens paient pour résoudre]
- CLIENTS: [Qui exactement — profil précis]
- VALEUR: [Montant estimé d'un deal — min 2000€]
- TEMPS JUSQU'AU PREMIER €: [24h / 48h / 72h / 1 semaine / 1 mois]
- PREMIÈRE ACTION: [Ce que je fais dès ce soir]

Priorise par: rapidité d'exécution × valeur × probabilité de succès."""

        response = self.think(prompt, TaskType.HUNT, temperature=0.5, max_tokens=2000)
        return response.text or "⚠️ Configure ta clé API pour activer la chasse intelligente"

    def write_proposal(self, pain: str, solution: str, price: float, client_name: str = "") -> str:
        """Write a premium sales proposal."""
        prompt = f"""Rédige une proposition commerciale premium, discrète et convaincante.

Client: {client_name or 'Prospect ciblé'}
Problème identifié: {pain}
Notre solution: {solution}
Investissement: {price:,.0f}€

La proposition doit:
- Commencer par valider la douleur du client (pas par nous vanter)
- Montrer le coût de l'INACTION (ce que ça lui coûte de ne rien faire)
- Présenter notre solution comme évidente
- Justifier le prix par le ROI
- Se terminer par un appel à l'action clair et urgent

Format: email professionnel, 300-400 mots maximum, ton direct et premium."""

        response = self.think(prompt, TaskType.PROPOSAL, temperature=0.6, max_tokens=800)
        return response.text or ""

    def score_opportunity(self, opp: Dict) -> Dict:
        """LLM-powered deep opportunity scoring."""
        prompt = f"""Analyse cette opportunité business en expert investisseur:

{json.dumps(opp, ensure_ascii=False, indent=2)}

Retourne un JSON avec exactement ces champs:
{{
  "viability_score": 0-100,
  "recommendation": "LAUNCH" | "DEFER" | "PIVOT" | "ABANDON",
  "reasoning": "2-3 phrases",
  "top_risk": "risque principal",
  "quick_win": "action rapide pour valider",
  "estimated_revenue_30d": 0
}}

JSON uniquement, aucun texte autour."""

        response = self.think(prompt, TaskType.ANALYSIS, use_cache=False, temperature=0.1)
        try:
            text = response.text or ""
            start = text.find("{"); end = text.rfind("}") + 1
            if start >= 0:
                return json.loads(text[start:end])
        except Exception:
            pass
        return {"viability_score": 50, "recommendation": "ANALYZE", "reasoning": response.text}

    def get_stats(self) -> Dict:
        return {
            **self._stats,
            "providers_online": list(self._providers.keys()),
            "cache_size": self._cache.size(),
            "available": self.available,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_brain: Optional[NayaBrain] = None


def get_brain() -> NayaBrain:
    global _brain
    if _brain is None:
        _brain = NayaBrain()
    return _brain
