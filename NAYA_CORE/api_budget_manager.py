"""
NAYA V19 — API Budget Manager Intelligent
══════════════════════════════════════════════════════════════════════════════
Gestion intelligente des budgets API pour éviter de cramer les crédits/tokens.
- Rate limiting par provider (Groq, Anthropic, Apollo, Serper, etc.)
- Tracking budget quotidien/mensuel
- Auto-fallback intelligent quand limite atteinte
- Métriques temps réel
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.API_BUDGET")

ROOT = Path(__file__).resolve().parent.parent
BUDGET_FILE = ROOT / "data" / "cache" / "api_budget.json"

# ── API Budget Limits (per day) ───────────────────────────────────────────────
API_LIMITS = {
    "groq": {
        "requests_per_day": 14_400,  # 10 req/min * 1440 min
        "tokens_per_day": 1_000_000,  # Conservative estimate
        "cost_per_1k_tokens": 0.0,  # Free tier
        "priority": 1,  # Highest priority (fast + free)
    },
    "anthropic": {
        "requests_per_day": 1_000,
        "tokens_per_day": 100_000,  # Claude Sonnet usage
        "cost_per_1k_tokens": 0.003,  # $3 per 1M input tokens
        "priority": 2,
    },
    "openai": {
        "requests_per_day": 3_000,
        "tokens_per_day": 200_000,
        "cost_per_1k_tokens": 0.0015,  # GPT-4o-mini
        "priority": 3,
    },
    "deepseek": {
        "requests_per_day": 5_000,
        "tokens_per_day": 500_000,
        "cost_per_1k_tokens": 0.0001,  # Ultra cheap
        "priority": 4,
    },
    "serper": {
        "requests_per_day": 2_500,  # Free tier 2500/month
        "tokens_per_day": 0,  # Not token-based
        "cost_per_request": 0.002,  # $2 per 1000 queries (paid)
        "priority": 1,
    },
    "apollo": {
        "requests_per_day": 100,  # Conservative free tier
        "tokens_per_day": 0,
        "cost_per_request": 0.01,  # Paid tier
        "priority": 2,
    },
    "sendgrid": {
        "requests_per_day": 100,  # Free tier 100/day
        "tokens_per_day": 0,
        "cost_per_request": 0.0,
        "priority": 1,
    },
}


@dataclass
class APIUsage:
    """Utilisation d'une API sur une période."""
    provider: str
    requests_count: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    errors: int = 0
    last_reset: float = field(default_factory=time.time)
    last_request: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "requests_count": self.requests_count,
            "tokens_used": self.tokens_used,
            "cost_usd": round(self.cost_usd, 4),
            "errors": self.errors,
            "last_reset": self.last_reset,
            "last_request": self.last_request,
        }


class APIBudgetManager:
    """
    Gestionnaire intelligent de budgets API.
    Thread-safe. Persistance JSON. Auto-reset quotidien.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._usage: Dict[str, APIUsage] = {}
        self._fallback_chains: Dict[str, List[str]] = {
            "llm": ["groq", "deepseek", "anthropic", "openai", "template"],
            "search": ["serper", "manual"],
            "enrichment": ["apollo", "hunter", "manual"],
        }
        BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        log.info("[API_BUDGET] Manager initialized")

    # ── Public API ──────────────────────────────────────────────────────────────

    def can_use(self, provider: str, tokens: int = 0) -> bool:
        """
        Vérifie si on peut utiliser l'API sans dépasser les limites.

        Args:
            provider: nom du provider (groq, anthropic, serper, etc.)
            tokens: nombre de tokens estimés pour cette requête

        Returns:
            True si sous les limites, False sinon
        """
        with self._lock:
            self._check_reset()
            usage = self._get_usage(provider)
            limits = API_LIMITS.get(provider, {})

            if not limits:
                # Unknown provider - allow but warn
                log.warning(f"[API_BUDGET] Unknown provider: {provider}")
                return True

            req_limit = limits.get("requests_per_day", float("inf"))
            token_limit = limits.get("tokens_per_day", float("inf"))

            if usage.requests_count >= req_limit:
                log.warning(f"[API_BUDGET] {provider} request limit reached: {usage.requests_count}/{req_limit}")
                return False

            if tokens > 0 and (usage.tokens_used + tokens) > token_limit:
                log.warning(f"[API_BUDGET] {provider} token limit would be exceeded: {usage.tokens_used + tokens}/{token_limit}")
                return False

            return True

    def record_usage(self, provider: str, tokens: int = 0, success: bool = True):
        """
        Enregistre l'utilisation d'une API.

        Args:
            provider: nom du provider
            tokens: tokens utilisés
            success: True si succès, False si erreur
        """
        with self._lock:
            usage = self._get_usage(provider)
            usage.requests_count += 1
            usage.tokens_used += tokens
            usage.last_request = time.time()

            if not success:
                usage.errors += 1

            # Calculate cost
            limits = API_LIMITS.get(provider, {})
            if "cost_per_1k_tokens" in limits and tokens > 0:
                usage.cost_usd += (tokens / 1000) * limits["cost_per_1k_tokens"]
            elif "cost_per_request" in limits:
                usage.cost_usd += limits["cost_per_request"]

            self._save()

    def get_best_provider(self, category: str = "llm") -> Optional[str]:
        """
        Retourne le meilleur provider disponible pour une catégorie.
        Suit la chaîne de fallback intelligemment.

        Args:
            category: "llm", "search", "enrichment"

        Returns:
            nom du provider ou None si tous saturés
        """
        with self._lock:
            chain = self._fallback_chains.get(category, [])
            for provider in chain:
                if provider == "template" or provider == "manual":
                    return provider
                if self.can_use(provider):
                    return provider

            log.warning(f"[API_BUDGET] All providers exhausted for {category}")
            return chain[-1] if chain else None  # Fallback to last option

    def get_usage_report(self) -> Dict:
        """Retourne un rapport complet d'utilisation."""
        with self._lock:
            total_requests = sum(u.requests_count for u in self._usage.values())
            total_tokens = sum(u.tokens_used for u in self._usage.values())
            total_cost = sum(u.cost_usd for u in self._usage.values())
            total_errors = sum(u.errors for u in self._usage.values())

            return {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "total_errors": total_errors,
                "error_rate": round(total_errors / max(total_requests, 1), 3),
                "providers": {
                    name: {
                        **usage.to_dict(),
                        "limit_requests": API_LIMITS.get(name, {}).get("requests_per_day", 0),
                        "limit_tokens": API_LIMITS.get(name, {}).get("tokens_per_day", 0),
                        "usage_pct_requests": round(usage.requests_count / max(API_LIMITS.get(name, {}).get("requests_per_day", 1), 1) * 100, 1),
                        "usage_pct_tokens": round(usage.tokens_used / max(API_LIMITS.get(name, {}).get("tokens_per_day", 1), 1) * 100, 1) if API_LIMITS.get(name, {}).get("tokens_per_day", 0) > 0 else 0,
                    }
                    for name, usage in self._usage.items()
                },
                "last_reset": min((u.last_reset for u in self._usage.values()), default=time.time()),
            }

    def reset_daily(self):
        """Reset manuel quotidien (appelé aussi automatiquement)."""
        with self._lock:
            for usage in self._usage.values():
                usage.requests_count = 0
                usage.tokens_used = 0
                usage.cost_usd = 0.0
                usage.errors = 0
                usage.last_reset = time.time()
            self._save()
            log.info("[API_BUDGET] Daily reset completed")

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _get_usage(self, provider: str) -> APIUsage:
        """Retourne ou crée un objet APIUsage."""
        if provider not in self._usage:
            self._usage[provider] = APIUsage(provider=provider)
        return self._usage[provider]

    def _check_reset(self):
        """Auto-reset si on a changé de jour."""
        now = time.time()
        for usage in list(self._usage.values()):
            # Reset if > 24h since last reset
            if (now - usage.last_reset) > (24 * 3600):
                log.info(f"[API_BUDGET] Auto-reset for {usage.provider} (24h elapsed)")
                usage.requests_count = 0
                usage.tokens_used = 0
                usage.cost_usd = 0.0
                usage.errors = 0
                usage.last_reset = now

    def _save(self):
        """Sauvegarde l'état."""
        try:
            data = {
                "usage": {name: usage.to_dict() for name, usage in self._usage.items()},
                "saved_at": time.time(),
            }
            tmp = BUDGET_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(BUDGET_FILE)
        except Exception as e:
            log.warning(f"[API_BUDGET] Save failed: {e}")

    def _load(self):
        """Charge l'état depuis le fichier."""
        try:
            if not BUDGET_FILE.exists():
                return
            data = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
            for name, u in data.get("usage", {}).items():
                self._usage[name] = APIUsage(
                    provider=name,
                    requests_count=u.get("requests_count", 0),
                    tokens_used=u.get("tokens_used", 0),
                    cost_usd=u.get("cost_usd", 0.0),
                    errors=u.get("errors", 0),
                    last_reset=u.get("last_reset", time.time()),
                    last_request=u.get("last_request", 0.0),
                )
        except Exception as e:
            log.warning(f"[API_BUDGET] Load failed: {e}")


# ── Singleton ────────────────────────────────────────────────────────────────────
_manager: Optional[APIBudgetManager] = None


def get_api_budget_manager() -> APIBudgetManager:
    global _manager
    if _manager is None:
        _manager = APIBudgetManager()
    return _manager
