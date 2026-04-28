"""
NAYA SUPREME - Prometheus Metrics Module
═════════════════════════════════════════════════════════════════════════════════

Instrumentation complète pour monitoring en production.
Métriques: requêtes, latency, erreurs, business metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from functools import wraps
import time
import logging
from typing import Callable, Any
from contextlib import contextmanager

log = logging.getLogger("naya.metrics")

# ════════════════════════════════════════════════════════════════════════════════
# REGISTRY
# ════════════════════════════════════════════════════════════════════════════════

registry = CollectorRegistry()

# ════════════════════════════════════════════════════════════════════════════════
# API METRICS
# ════════════════════════════════════════════════════════════════════════════════

http_requests_total = Counter(
    'naya_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'naya_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry
)

http_exceptions_total = Counter(
    'naya_http_exceptions_total',
    'Total HTTP exceptions',
    ['endpoint', 'exception_type'],
    registry=registry
)

# ════════════════════════════════════════════════════════════════════════════════
# BUSINESS METRICS
# ════════════════════════════════════════════════════════════════════════════════

pain_signals_detected = Counter(
    'naya_pain_signals_detected_total',
    'Total pain signals detected',
    ['industry', 'pain_type'],
    registry=registry
)

service_offers_generated = Counter(
    'naya_service_offers_generated_total',
    'Total service offers generated',
    ['tier', 'industry'],
    registry=registry
)

publications_sent = Counter(
    'naya_publications_sent_total',
    'Total publications sent',
    ['channel', 'status'],
    registry=registry
)

leads_generated = Counter(
    'naya_leads_generated_total',
    'Total leads generated',
    ['source', 'quality'],
    registry=registry
)

conversion_rate = Gauge(
    'naya_conversion_rate',
    'Current conversion rate',
    ['funnel_stage'],
    registry=registry
)

revenue_total = Gauge(
    'naya_revenue_total',
    'Total revenue generated',
    ['currency', 'source'],
    registry=registry
)

# ════════════════════════════════════════════════════════════════════════════════
# SYSTEM METRICS
# ════════════════════════════════════════════════════════════════════════════════

cache_hits = Counter(
    'naya_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses = Counter(
    'naya_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

database_queries = Counter(
    'naya_database_queries_total',
    'Total database queries',
    ['operation', 'table'],
    registry=registry
)

database_query_duration = Histogram(
    'naya_database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry
)

external_api_calls = Counter(
    'naya_external_api_calls_total',
    'Total external API calls',
    ['provider', 'status'],
    registry=registry
)

external_api_duration = Histogram(
    'naya_external_api_duration_seconds',
    'External API call duration',
    ['provider'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry
)

active_sessions = Gauge(
    'naya_active_sessions',
    'Number of active sessions',
    registry=registry
)

# ════════════════════════════════════════════════════════════════════════════════
# DECORATOR POUR HTTP REQUESTS
# ════════════════════════════════════════════════════════════════════════════════

def track_http_request(endpoint: str):
    """Decorator pour tracker les requêtes HTTP"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            method = kwargs.get('request', {}).method if 'request' in kwargs else 'UNKNOWN'
            
            start_time = time.time()
            status = 500
            
            try:
                result = await func(*args, **kwargs)
                status = result.status_code if hasattr(result, 'status_code') else 200
                return result
            except Exception as e:
                http_exceptions_total.labels(
                    endpoint=endpoint,
                    exception_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            method = kwargs.get('request', {}).method if 'request' in kwargs else 'UNKNOWN'
            
            start_time = time.time()
            status = 500
            
            try:
                result = func(*args, **kwargs)
                status = result.status_code if hasattr(result, 'status_code') else 200
                return result
            except Exception as e:
                http_exceptions_total.labels(
                    endpoint=endpoint,
                    exception_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    
    return decorator


# ════════════════════════════════════════════════════════════════════════════════
# CONTEXT MANAGERS POUR DATABASE
# ════════════════════════════════════════════════════════════════════════════════

@contextmanager
def track_database_query(operation: str, table: str):
    """Context manager pour tracker les requêtes database"""
    start_time = time.time()
    
    try:
        database_queries.labels(operation=operation, table=table).inc()
        yield
    finally:
        duration = time.time() - start_time
        database_query_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)


# ════════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE TRACKING
# ════════════════════════════════════════════════════════════════════════════════

def track_cache_hit(cache_type: str):
    """Record cache hit"""
    cache_hits.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Record cache miss"""
    cache_misses.labels(cache_type=cache_type).inc()


def track_pain_signal(industry: str, pain_type: str):
    """Record pain signal detection"""
    pain_signals_detected.labels(industry=industry, pain_type=pain_type).inc()


def track_service_offer(tier: str, industry: str):
    """Record service offer generation"""
    service_offers_generated.labels(tier=tier, industry=industry).inc()


def track_publication(channel: str, status: str):
    """Record publication"""
    publications_sent.labels(channel=channel, status=status).inc()


def track_lead(source: str, quality: str):
    """Record lead generation"""
    leads_generated.labels(source=source, quality=quality).inc()


def track_external_api_call(provider: str, status: str, duration: float = 0.0):
    """Record external API call"""
    external_api_calls.labels(provider=provider, status=status).inc()
    if duration > 0:
        external_api_duration.labels(provider=provider).observe(duration)


def set_active_sessions(count: int):
    """Set active sessions gauge"""
    active_sessions.set(count)


def set_conversion_rate(stage: str, rate: float):
    """Set conversion rate"""
    conversion_rate.labels(funnel_stage=stage).set(rate)


def set_revenue(currency: str, source: str, amount: float):
    """Set total revenue"""
    revenue_total.labels(currency=currency, source=source).set(amount)


# ════════════════════════════════════════════════════════════════════════════════
# EXPORT METRICS
# ════════════════════════════════════════════════════════════════════════════════

def get_metrics_text() -> str:
    """Get Prometheus metrics in text format"""
    return generate_latest(registry).decode('utf-8')
