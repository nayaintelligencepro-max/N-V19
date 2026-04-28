"""
NAYA V19 — LLM Router Production
Route intelligente Groq → DeepSeek → Anthropic → Fallback.
Rotation quotidienne, budget par provider, cache local.
"""
import os, time, json, logging, threading, hashlib
from typing import Dict, Optional, Any
from pathlib import Path

log = logging.getLogger("NAYA.LLM.ROUTER")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class LLMRouter:
    """
    NAYA V19 — Router LLM intelligent production-ready.
    Priorité: Groq (gratuit) → DeepSeek (cheap) → Anthropic → Fallback templates.
    """

    DAILY_LIMITS = {
        "groq": 14400,
        "deepseek": 50000,
        "anthropic": 500,
        "openai": 500,
        "internal": 999999,
    }

    GROQ_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]

    def __init__(self):
        self._lock = threading.RLock()
        self._usage: Dict[str, int] = {k: 0 for k in self.DAILY_LIMITS}
        self._last_reset = time.time()
        self._cache: Dict[str, str] = {}
        self._history = []
        self._operation_count = 0
        self._error_count = 0
        self._active = True
        self._initialized_at = time.time()

    def _reset_if_needed(self):
        if time.time() - self._last_reset > 86400:
            with self._lock:
                self._usage = {k: 0 for k in self.DAILY_LIMITS}
                self._last_reset = time.time()

    def _cache_key(self, prompt: str, provider: str) -> str:
        return hashlib.md5(f"{provider}:{prompt[:200]}".encode()).hexdigest()

    def _pick_provider(self, task_type: str = "default") -> str:
        """Pick cheapest available provider with capacity."""
        self._reset_if_needed()
        order = ["groq", "deepseek", "anthropic", "openai", "internal"]
        for p in order:
            if self._usage.get(p, 0) < self.DAILY_LIMITS.get(p, 0):
                key_map = {
                    "groq": "GROQ_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY",
                }
                if p == "internal":
                    return "internal"
                if _gs(key_map.get(p, "")):
                    return p
        return "internal"

    def route(self, prompt: str, task_type: str = "default",
              system: str = "", max_tokens: int = 1000) -> str:
        """Route un prompt vers le meilleur LLM disponible."""
        with self._lock:
            self._operation_count += 1

        ck = self._cache_key(prompt, task_type)
        if ck in self._cache:
            return self._cache[ck]

        provider = self._pick_provider(task_type)
        result = ""

        try:
            if provider == "groq":
                result = self._call_groq(prompt, system, max_tokens)
            elif provider == "deepseek":
                result = self._call_deepseek(prompt, system, max_tokens)
            elif provider == "anthropic":
                result = self._call_anthropic(prompt, system, max_tokens)
            elif provider == "openai":
                result = self._call_openai(prompt, system, max_tokens)
            else:
                result = self._fallback_template(prompt, task_type)

            if result:
                with self._lock:
                    self._usage[provider] = self._usage.get(provider, 0) + 1
                    self._cache[ck] = result
                    if len(self._cache) > 200:
                        oldest = list(self._cache.keys())[:50]
                        for k in oldest:
                            self._cache.pop(k, None)
        except Exception as e:
            log.warning(f"[LLMRouter] {provider} failed: {e}")
            with self._lock:
                self._error_count += 1
            result = self._fallback_template(prompt, task_type)

        self._history.append({"provider": provider, "ts": time.time(), "ok": bool(result)})
        if len(self._history) > 500:
            self._history = self._history[-500:]
        return result

    def _call_groq(self, prompt: str, system: str, max_tokens: int) -> str:
        import urllib.request, json as _json
        key = _gs("GROQ_API_KEY")
        if not key:
            raise ValueError("No GROQ_API_KEY")
        payload = {
            "model": self.GROQ_MODELS[0],
            "messages": [
                {"role": "system", "content": system or "Tu es NAYA, assistant business autonome."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=_json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read())
        return data["choices"][0]["message"]["content"]

    def _call_deepseek(self, prompt: str, system: str, max_tokens: int) -> str:
        import urllib.request, json as _json
        key = _gs("DEEPSEEK_API_KEY")
        base = _gs("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        if not key:
            raise ValueError("No DEEPSEEK_API_KEY")
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system or "Tu es NAYA."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{base}/v1/chat/completions",
            data=_json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read())
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str, system: str, max_tokens: int) -> str:
        import urllib.request, json as _json
        key = _gs("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("No ANTHROPIC_API_KEY")
        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "system": system or "Tu es NAYA.",
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=_json.dumps(payload).encode(),
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read())
        return data["content"][0]["text"]

    def _call_openai(self, prompt: str, system: str, max_tokens: int) -> str:
        import urllib.request, json as _json
        key = _gs("OPENAI_API_KEY")
        if not key:
            raise ValueError("No OPENAI_API_KEY")
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system or "Tu es NAYA."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=_json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read())
        return data["choices"][0]["message"]["content"]

    def _fallback_template(self, prompt: str, task_type: str) -> str:
        """Réponse template quand aucun LLM disponible."""
        templates = {
            "outreach": "Bonjour, je vous contacte suite à l'identification d'une opportunité stratégique pour votre organisation. Notre approche a généré des résultats mesurables pour des acteurs comparables. Seriez-vous disponible pour un échange de 15 minutes cette semaine ?",
            "offer": "Suite à notre analyse, nous proposons une intervention sur mesure valorisée entre 5 000€ et 50 000€ selon le périmètre défini. ROI estimé : 3x à 6 mois.",
            "followup": "Je reviens vers vous concernant notre échange précédent. Avez-vous eu l'occasion d'étudier notre proposition ? Je reste disponible pour ajuster selon vos contraintes.",
            "default": f"[NAYA V19 — Réponse autonome] Analyse en cours pour: {prompt[:100]}...",
        }
        return templates.get(task_type, templates["default"])

    def stats(self) -> Dict:
        return {
            "operations": self._operation_count,
            "errors": self._error_count,
            "cache_size": len(self._cache),
            "daily_usage": dict(self._usage),
            "uptime_h": round((time.time() - self._initialized_at) / 3600, 2),
        }

    # Legacy compatibility
    def _execute_route(self, *args, **kwargs) -> Any:
        prompt = str(args[0]) if args else kwargs.get("prompt", "")
        return self.route(prompt)
