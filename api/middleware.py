"""
NAYA V19 — Rate Limiter Middleware
Protection des endpoints LLM coûteux et de l'API publique.

Stratégie par tier :
  - Endpoints LLM (brain, hunt, cognition) : 20 req/min par IP
  - Endpoints Revenue (scan, prospects)     : 10 req/min par IP
  - Endpoints lecture (status, pipeline)    : 120 req/min par IP
  - Webhooks entrants                       : illimités (PayPal/Deblock/Telegram trustés)
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

log = logging.getLogger("NAYA.ratelimit")


# ── Configuration des limites par préfixe d'URL ───────────────────────────────
RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    # (max_requests, window_seconds)
    "/brain":        (20, 60),    # LLM — coûteux
    "/cognition":    (20, 60),    # LLM — coûteux
    "/hunt":         (15, 60),    # LLM + scraping
    "/sovereign":    (10, 60),    # cycle complet
    "/revenue/scan": (5,  60),    # scraping web intensif
    "/revenue/prospects": (10, 60),
    "/accelerator":  (5,  60),    # blitz — très coûteux
    "/llm":          (20, 60),    # voting engine
    "/revenue":      (30, 60),    # endpoints revenue généraux
    "/pipeline":     (60, 60),    # lectures pipeline
    "/autonomous":   (20, 60),
    "/integrations": (30, 60),
    "/webhooks":     (1000, 60),  # PayPal/Deblock/Telegram — pas de limite réelle
    "/":             (120, 60),   # tout le reste
}

# IPs exemptées (localhost toujours exempt)
EXEMPT_IPS = {"127.0.0.1", "::1", "0.0.0.0"}

# Stockage en mémoire : {(ip, prefix): [(timestamp, ...)]}
_windows: Dict[Tuple[str, str], list] = defaultdict(list)


def _get_limit(path: str) -> Tuple[int, int]:
    """Retourne (max_req, window_sec) pour un path donné."""
    for prefix, limit in RATE_LIMITS.items():
        if path.startswith(prefix) and prefix != "/":
            return limit
    return RATE_LIMITS["/"]


def _get_client_ip(request: Request) -> str:
    """Extrait l'IP réelle même derrière un proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class NayaRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting par IP et par catégorie d'endpoint.
    Utilise une fenêtre glissante en mémoire (pas de Redis requis).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        ip = _get_client_ip(request)

        # Toujours laisser passer les IPs locales et les health checks
        if ip in EXEMPT_IPS or path in ("/health", "/heartbeat", "/"):
            return await call_next(request)

        max_req, window = _get_limit(path)
        key = (ip, path.split("/")[1] if "/" in path else path)
        now = time.time()

        # Nettoyer les entrées hors fenêtre
        _windows[key] = [t for t in _windows[key] if now - t < window]

        if len(_windows[key]) >= max_req:
            retry_after = int(window - (now - _windows[key][0])) + 1
            log.warning(
                f"[RATELIMIT] {ip} bloqué sur {path} "
                f"({len(_windows[key])}/{max_req} req/{window}s)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Trop de requêtes. Limite: {max_req} req/{window}s.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        _windows[key].append(now)

        # Ajouter les headers de rate limit dans la réponse
        response = await call_next(request)
        remaining = max_req - len(_windows[key])
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Window"] = str(window)
        return response


def get_rate_limit_stats() -> dict:
    """Statistiques du rate limiter — exposé via /system/rate-limits."""
    now = time.time()
    active = {}
    for (ip, prefix), timestamps in _windows.items():
        recent = [t for t in timestamps if now - t < 60]
        if recent:
            key = f"{ip}/{prefix}"
            active[key] = len(recent)
    return {
        "active_windows": len(active),
        "top_consumers": sorted(active.items(), key=lambda x: -x[1])[:10],
        "total_tracked_ips": len({k[0] for k in _windows}),
    }

# Alias for backward compatibility
RateLimiterMiddleware = NayaRateLimitMiddleware
