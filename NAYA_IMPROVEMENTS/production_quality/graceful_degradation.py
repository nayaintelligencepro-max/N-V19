"""
QUALITÉ #6 — Système de dégradation gracieuse.

Quand un service tombe, le système continue de fonctionner en mode dégradé
plutôt que de crasher complètement. Chaque composant a un fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ServiceStatus:
    name: str
    healthy: bool
    fallback_active: bool
    degraded_since: Optional[str] = None
    fallback_calls: int = 0


FALLBACK_STRATEGIES: Dict[str, Dict[str, Any]] = {
    "llm_api": {
        "primary": "anthropic",
        "fallbacks": ["groq", "deepseek", "huggingface", "ollama", "template"],
        "description": "LLM chain multi-fournisseur avec template comme dernier recours",
    },
    "email_service": {
        "primary": "sendgrid",
        "fallbacks": ["smtp_direct", "queue_for_retry"],
        "description": "Email via SMTP direct si SendGrid tombe, sinon mise en queue",
    },
    "payment_gateway": {
        "primary": "deblock",
        "fallbacks": ["paypal", "revolut", "invoice_manual"],
        "description": "Cascade de paiement avec facturation manuelle en dernier recours",
    },
    "database": {
        "primary": "postgresql",
        "fallbacks": ["sqlite_local", "file_json"],
        "description": "Base locale SQLite si PG tombe, fichiers JSON en ultime recours",
    },
    "vector_store": {
        "primary": "qdrant",
        "fallbacks": ["pinecone", "in_memory"],
        "description": "Store vectoriel en mémoire si services externes indisponibles",
    },
    "scraping": {
        "primary": "selenium",
        "fallbacks": ["httpx", "cached_results"],
        "description": "HTTP direct si Selenium échoue, résultats cachés en dernier recours",
    },
}


class GracefulDegradationManager:
    """
    Gère la dégradation gracieuse de tous les services du système.

    Principe: le système ne doit JAMAIS s'arrêter complètement.
    Chaque service a au moins un fallback, et le système continue
    avec des capacités réduites plutôt que de crasher.
    """

    def __init__(self) -> None:
        self._services: Dict[str, ServiceStatus] = {}
        for name in FALLBACK_STRATEGIES:
            self._services[name] = ServiceStatus(name=name, healthy=True, fallback_active=False)
        logger.info(f"[GracefulDegradation] Initialisé — {len(self._services)} services protégés")

    def mark_degraded(self, service_name: str) -> None:
        """Marque un service comme dégradé et active le fallback."""
        if service_name in self._services:
            svc = self._services[service_name]
            svc.healthy = False
            svc.fallback_active = True
            svc.degraded_since = datetime.now(timezone.utc).isoformat()
            strategy = FALLBACK_STRATEGIES.get(service_name, {})
            logger.warning(
                f"[GracefulDegradation] {service_name} DÉGRADÉ — "
                f"fallback: {strategy.get('fallbacks', ['none'])[0]}"
            )

    def mark_recovered(self, service_name: str) -> None:
        """Marque un service comme récupéré."""
        if service_name in self._services:
            svc = self._services[service_name]
            svc.healthy = True
            svc.fallback_active = False
            svc.degraded_since = None
            logger.info(f"[GracefulDegradation] {service_name} RÉCUPÉRÉ")

    def get_fallback_chain(self, service_name: str) -> List[str]:
        """Retourne la chaîne de fallback d'un service."""
        strategy = FALLBACK_STRATEGIES.get(service_name, {})
        return [strategy.get("primary", "")] + strategy.get("fallbacks", [])

    def execute_with_fallback(
        self,
        service_name: str,
        primary_fn: Callable[..., T],
        fallback_fns: Optional[Dict[str, Callable[..., T]]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Exécute avec fallback automatique en cas d'échec."""
        try:
            result = primary_fn(*args, **kwargs)
            if service_name in self._services:
                self._services[service_name].healthy = True
            return result
        except Exception as primary_error:
            self.mark_degraded(service_name)
            logger.warning(f"[GracefulDegradation] {service_name} primary failed: {primary_error}")

            if fallback_fns:
                for fb_name, fb_fn in fallback_fns.items():
                    try:
                        result = fb_fn(*args, **kwargs)
                        if service_name in self._services:
                            self._services[service_name].fallback_calls += 1
                        logger.info(f"[GracefulDegradation] {service_name} → fallback '{fb_name}' OK")
                        return result
                    except Exception as fb_error:
                        logger.warning(f"[GracefulDegradation] fallback '{fb_name}' failed: {fb_error}")

            raise

    def system_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les services."""
        healthy_count = sum(1 for s in self._services.values() if s.healthy)
        degraded = [s.name for s in self._services.values() if not s.healthy]

        return {
            "overall": "healthy" if not degraded else "degraded",
            "services_total": len(self._services),
            "services_healthy": healthy_count,
            "services_degraded": degraded,
            "fallback_calls_total": sum(s.fallback_calls for s in self._services.values()),
        }


graceful_degradation_manager = GracefulDegradationManager()
