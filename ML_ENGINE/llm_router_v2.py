"""
NAYA V21 — LLM Router V2
Routage intelligent vers le bon modèle selon la tâche.
- Offres      : Groq Llama 3.3 70B (< 3s, ultra-rapide)
- Closing     : Claude Sonnet (raisonnement complexe)
- Généraliste : GPT-4o / DeepSeek
- Fallback    : Templates statiques (0 API)

RAG intégré : avant chaque offre, récupérer les 3 cas similaires gagnants.
"""
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.LLM_ROUTER_V2")

# ── Modèle par tâche ──────────────────────────────────────────────────────────
TASK_MODELS: Dict[str, List[str]] = {
    "offer_generation": [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-70b-versatile",
        "anthropic/claude-sonnet-4-6",
        "openai/gpt-4o",
        "template",
    ],
    "closing_negotiation": [
        "anthropic/claude-sonnet-4-6",
        "openai/gpt-4o",
        "groq/llama-3.3-70b-versatile",
        "deepseek/deepseek-chat",
        "template",
    ],
    "pain_detection": [
        "groq/llama-3.3-70b-versatile",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
        "template",
    ],
    "audit_analysis": [
        "anthropic/claude-sonnet-4-6",
        "openai/gpt-4o",
        "groq/llama-3.3-70b-versatile",
        "template",
    ],
    "content_generation": [
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4-6",
        "groq/llama-3.3-70b-versatile",
        "template",
    ],
}

# Prompt templates par secteur (V21)
SECTOR_PROMPT_TEMPLATES: Dict[str, str] = {
    "transport_logistique": """Tu es un expert cybersécurité OT spécialisé Transport & Logistique (SNCF, RATP, ADP, ports).
Cible : DSI/RSSI opérationnel avec contraintes réseau ferroviaire/maritime.
Douleurs : conformité NIS2 obligatoire, SCADA vulnérables, incidents ransom sur automates.
Style : direct, chiffré, ROI en premier. Ticket cible : 15-40k EUR.
Contexte prospect : {context}
Douleur détectée : {pain}
Génère une offre commerciale en 3 paragraphes (accroche, valeur, appel action).""",

    "energie_utilities": """Tu es un expert cybersécurité OT Énergie & Utilities (EDF, Enedis, RTE, GRTgaz).
Cible : Responsable SCADA, Directeur Sécurité OIV.
Douleurs : vulnérabilités infrastructure critique, conformité NIS2 + NIS1 ANSSI, cyberattaques centrales.
Style : institutionnel mais urgent, référence réglementaire systématique. Ticket : 40-80k EUR.
Contexte prospect : {context}
Douleur détectée : {pain}
Génère une offre commerciale IEC 62443 en 3 paragraphes (accroche réglementaire, valeur, appel action).""",

    "manufacturing": """Tu es un expert cybersécurité OT Manufacturing (Airbus, Michelin, Renault, Alstom).
Cible : Directeur Usine, Responsable MES/SCADA.
Douleurs : downtime coûteux, ransomware sur automates, mise à niveau OT.
Style : pragmatique, ROI calculé sur base temps d'arrêt évité. Ticket : 15-40k EUR.
Contexte prospect : {context}
Douleur détectée : {pain}
Génère une offre commerciale en 3 paragraphes (impact production, valeur, appel action).""",

    "iec62443": """Tu es un expert certification IEC 62443 (seul sur le marché francophone).
Cible : RSSI, Auditeur interne, bureau de certification.
Douleurs : gaps IEC 62443 avant audit, deadline certification, renouvellement ISO 27001.
Style : technique et précis, référence standards. Ticket : 15-80k EUR.
Contexte prospect : {context}
Douleur détectée : {pain}
Génère une offre de mise en conformité IEC 62443 en 3 paragraphes (gap identifié, roadmap, appel action).""",
}


@dataclass
class LLMResponse:
    """Réponse du routeur LLM."""
    text: str
    model_used: str
    task: str
    latency_ms: float
    tokens_used: int = 0
    rag_contexts: List[str] = field(default_factory=list)
    from_cache: bool = False


class LLMRouterV2:
    """
    Routeur LLM V2 — modèle dédié par tâche + RAG + fallback automatique.
    Basculement automatique si quota/erreur/latence > 10s.
    """

    LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "10"))
    CACHE_SIZE = 100

    def __init__(self):
        self._cache: Dict[str, LLMResponse] = {}
        self._stats: Dict[str, Dict] = {
            "calls": {}, "errors": {}, "latency_ms": {},
        }
        log.info("✅ LLMRouterV2 initialisé")

    # ── Public API ────────────────────────────────────────────────────────────
    def generate(
        self,
        task: str,
        prompt: str,
        sector: Optional[str] = None,
        context: Optional[str] = None,
        pain: Optional[str] = None,
        rag_results: Optional[List[str]] = None,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        """
        Génère du texte via le modèle optimal pour la tâche.
        """
        t0 = time.time()

        # Construire le prompt enrichi
        full_prompt = self._build_prompt(task, prompt, sector, context, pain, rag_results)

        # Déterminer l'ordre des modèles
        model_list = (
            [model_override] + TASK_MODELS.get(task, TASK_MODELS["content_generation"])
            if model_override
            else TASK_MODELS.get(task, TASK_MODELS["content_generation"])
        )

        # Cache check
        cache_key = f"{task}:{full_prompt[:100]}"
        if cache_key in self._cache:
            resp = self._cache[cache_key]
            resp.from_cache = True
            return resp

        # Tentative sur chaque modèle
        for model in model_list:
            try:
                if model == "template":
                    text = self._fallback_template(task, sector, context, pain)
                else:
                    text = self._call_model(model, full_prompt)
                latency = (time.time() - t0) * 1000
                resp = LLMResponse(
                    text=text,
                    model_used=model,
                    task=task,
                    latency_ms=round(latency, 1),
                    rag_contexts=rag_results or [],
                )
                # Cache
                if len(self._cache) >= self.CACHE_SIZE:
                    self._cache.pop(next(iter(self._cache)))
                self._cache[cache_key] = resp
                self._record_stat(model, latency, success=True)
                log.info("LLM %s/%s latency=%.0fms", task, model, latency)
                return resp
            except Exception as exc:
                log.warning("LLM %s/%s failed: %s — trying next", task, model, exc)
                self._record_stat(model, 0, success=False)

        # Ne devrait jamais arriver (template est le dernier fallback)
        return LLMResponse(
            text="Service temporairement indisponible. Veuillez réessayer.",
            model_used="error",
            task=task,
            latency_ms=(time.time() - t0) * 1000,
        )

    def generate_offer(
        self,
        company: str,
        sector: str,
        pain: str,
        contact_name: str = "",
        rag_results: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Génère une offre commerciale ultra-personnalisée < 3s."""
        context = f"Entreprise: {company}"
        if contact_name:
            context += f", Contact: {contact_name}"
        return self.generate(
            task="offer_generation",
            prompt=f"Offre pour {company} dans le secteur {sector}",
            sector=sector,
            context=context,
            pain=pain,
            rag_results=rag_results,
        )

    def generate_closing_response(
        self,
        objection: str,
        context: str,
        sector: str,
    ) -> LLMResponse:
        """Génère une réponse de closing pour une objection détectée."""
        prompt = f"Objection reçue: {objection}\nContexte: {context}\nGénère une réponse de closing persuasive."
        return self.generate(
            task="closing_negotiation",
            prompt=prompt,
            sector=sector,
        )

    # ── Internals ─────────────────────────────────────────────────────────────
    def _build_prompt(
        self,
        task: str,
        base_prompt: str,
        sector: Optional[str],
        context: Optional[str],
        pain: Optional[str],
        rag_results: Optional[List[str]],
    ) -> str:
        parts = []
        # System prompt sectoriel
        if sector and sector in SECTOR_PROMPT_TEMPLATES:
            system = SECTOR_PROMPT_TEMPLATES[sector].format(
                context=context or "",
                pain=pain or base_prompt,
            )
            parts.append(system)
        else:
            parts.append(base_prompt)
        # RAG context
        if rag_results:
            parts.append("\n\n--- EXEMPLES GAGNANTS (RAG) ---")
            for i, r in enumerate(rag_results[:3], 1):
                parts.append(f"Cas {i}: {r}")
            parts.append("--- FIN EXEMPLES ---\n")
        return "\n".join(parts)

    def _call_model(self, model: str, prompt: str) -> str:
        """Appelle un modèle LLM externe. Fallback sur template si pas de clé."""
        provider, model_name = model.split("/", 1)
        if provider == "groq":
            return self._call_groq(model_name, prompt)
        if provider == "anthropic":
            return self._call_anthropic(model_name, prompt)
        if provider == "openai":
            return self._call_openai(model_name, prompt)
        if provider == "deepseek":
            return self._call_deepseek(model_name, prompt)
        raise ValueError(f"Provider inconnu: {provider}")

    def _call_groq(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY non défini")
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                timeout=self.LLM_TIMEOUT_S,
            )
            return resp.choices[0].message.content or ""
        except ImportError:
            raise RuntimeError("groq package non installé")

    def _call_anthropic(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY non défini")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model_name,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text if resp.content else ""
        except ImportError:
            raise RuntimeError("anthropic package non installé")

    def _call_openai(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY non défini")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                timeout=self.LLM_TIMEOUT_S,
            )
            return resp.choices[0].message.content or ""
        except ImportError:
            raise RuntimeError("openai package non installé")

    def _call_deepseek(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY non défini")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                timeout=self.LLM_TIMEOUT_S,
            )
            return resp.choices[0].message.content or ""
        except ImportError:
            raise RuntimeError("openai package non installé")

    def _fallback_template(
        self,
        task: str,
        sector: Optional[str],
        context: Optional[str],
        pain: Optional[str],
    ) -> str:
        """Template statique — zéro API, toujours disponible."""
        templates = {
            "offer_generation": (
                f"Bonjour,\n\nSuite à l'analyse de votre situation ({pain or 'besoin identifié'}), "
                f"nous proposons un audit de sécurité OT sur mesure pour {context or 'votre organisation'}.\n\n"
                f"Notre intervention couvre : cartographie OT, gap analysis IEC 62443, roadmap correctivve.\n\n"
                f"Tarif : à partir de 15 000 EUR. Retour sur investissement dès la première année.\n\n"
                f"Disponible pour un appel de 30 min cette semaine ?"
            ),
            "closing_negotiation": (
                f"Je comprends votre préoccupation. Permettez-moi de vous montrer le ROI concret : "
                f"un incident OT coûte en moyenne 500 000 EUR. Notre audit à 15 000 EUR représente "
                f"3% de ce risque. Quelle date vous conviendrait pour valider ensemble ?"
            ),
            "content_generation": (
                f"Les cyberattaques sur les systèmes OT industriels ont augmenté de 300% en 2024. "
                f"La conformité NIS2 est obligatoire pour les entités essentielles dès janvier 2025. "
                f"NAYA vous aide à atteindre la conformité en 90 jours."
            ),
        }
        return templates.get(task, f"Réponse automatique NAYA pour {task}.")

    def _record_stat(self, model: str, latency_ms: float, success: bool) -> None:
        self._stats["calls"][model] = self._stats["calls"].get(model, 0) + 1
        if not success:
            self._stats["errors"][model] = self._stats["errors"].get(model, 0) + 1
        if latency_ms > 0:
            prev = self._stats["latency_ms"].get(model, [])
            prev.append(latency_ms)
            self._stats["latency_ms"][model] = prev[-50:]  # Keep last 50

    def get_stats(self) -> Dict:
        result: Dict[str, Any] = {}
        for model, calls in self._stats["calls"].items():
            errors = self._stats["errors"].get(model, 0)
            latencies = self._stats["latency_ms"].get(model, [])
            result[model] = {
                "calls": calls,
                "errors": errors,
                "success_rate": round((calls - errors) * 100 / calls, 1) if calls > 0 else 0,
                "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            }
        return result


# ── Singleton ─────────────────────────────────────────────────────────────────
_router: Optional[LLMRouterV2] = None


def get_llm_router_v2() -> LLMRouterV2:
    global _router
    if _router is None:
        _router = LLMRouterV2()
    return _router
