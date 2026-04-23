"""
NAYA V19 — OpenTelemetry Core
Instrumentation complète avec Jaeger tracing distribué
"""
import logging
import time
from typing import Optional, Callable, Any
from functools import wraps
from datetime import datetime

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

log = logging.getLogger("NAYA.TELEMETRY")

class NAYATelemetryCore:
    """
    Cœur d'instrumentation OpenTelemetry pour NAYA V19.
    
    Features:
    - Distributed tracing (Jaeger)
    - Metrics export (Prometheus)
    - Custom span decorators
    - Latency tracking
    - Error tracking
    - Revenue/Conversion metrics
    """
    
    def __init__(self, 
                 service_name: str = "naya-v19",
                 jaeger_host: str = "localhost",
                 jaeger_port: int = 6831):
        """Initialize telemetry system."""
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        
        self._tracer_provider: Optional[TracerProvider] = None
        self._tracer: Optional[trace.Tracer] = None
        self._metrics: dict = {}
        self._initialized = False
    
    def initialize(self) -> dict:
        """Initialize all telemetry components."""
        if not OTEL_AVAILABLE:
            log.warning("⚠️ OpenTelemetry not installed, using fallback")
            return {"initialized": False, "reason": "OpenTelemetry not available"}
        
        try:
            # Setup Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )
            
            # Create tracer provider
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                "version": "19.0.0",
                "environment": "production",
            })
            
            self._tracer_provider = TracerProvider(resource=resource)
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            trace.set_tracer_provider(self._tracer_provider)
            
            # Get tracer
            self._tracer = trace.get_tracer(__name__)
            
            # Initialize metrics dictionaries
            self._metrics = {
                "requests": 0,
                "errors": 0,
                "revenue": 0.0,
                "conversions": 0,
                "latencies": [],
            }
            
            self._initialized = True
            log.info(f"✅ Telemetry initialized: {self.service_name}")
            
            return {
                "initialized": True,
                "jaeger": f"{self.jaeger_host}:{self.jaeger_port}",
                "service": self.service_name,
            }
        
        except Exception as e:
            log.error(f"❌ Telemetry init failed: {e}", exc_info=True)
            return {"initialized": False, "error": str(e)}
    
    def trace_function(self, 
                      operation_name: Optional[str] = None,
                      track_latency: bool = True,
                      track_errors: bool = True):
        """
        Decorator for automatic span creation and tracking.
        
        Usage:
            @telemetry.trace_function("process_lead")
            def process_lead(lead_id):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self._initialized:
                    return func(*args, **kwargs)
                
                span_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                try:
                    with self._tracer.start_as_current_span(span_name) as span:
                        start_time = time.time()
                        
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                        
                        result = func(*args, **kwargs)
                        
                        if track_latency:
                            latency_ms = (time.time() - start_time) * 1000
                            self._metrics["latencies"].append(latency_ms)
                            span.set_attribute("latency_ms", latency_ms)
                        
                        self._metrics["requests"] += 1
                        span.set_attribute("status", "success")
                        
                        return result
                
                except Exception as e:
                    if track_errors:
                        self._metrics["errors"] += 1
                        if self._tracer:
                            current_span = trace.get_current_span()
                            current_span.record_exception(e)
                            current_span.set_attribute("error", True)
                    raise
            
            return wrapper
        return decorator
    
    def record_revenue(self, amount: float, currency: str = "EUR", 
                       source: str = "unknown", deal_id: Optional[str] = None):
        """Record revenue event with tracing."""
        if self._initialized and self._tracer:
            with self._tracer.start_as_current_span("record_revenue") as span:
                span.set_attribute("amount", amount)
                span.set_attribute("currency", currency)
                span.set_attribute("source", source)
                if deal_id:
                    span.set_attribute("deal_id", deal_id)
        
        self._metrics["revenue"] += amount
        log.info(f"💰 Revenue: {amount} {currency} from {source}")
    
    def record_conversion(self, 
                         lead_id: str,
                         lead_score: float,
                         offer_id: str):
        """Record conversion with metrics."""
        if self._initialized and self._tracer:
            with self._tracer.start_as_current_span("record_conversion") as span:
                span.set_attribute("lead_id", lead_id)
                span.set_attribute("lead_score", lead_score)
                span.set_attribute("offer_id", offer_id)
        
        self._metrics["conversions"] += 1
        log.info(f"✅ Conversion: Lead {lead_id[:8]}... score={lead_score:.2f}")
    
    def get_status(self) -> dict:
        """Get telemetry status."""
        avg_latency = 0.0
        if self._metrics["latencies"]:
            avg_latency = sum(self._metrics["latencies"]) / len(self._metrics["latencies"])
        
        return {
            "initialized": self._initialized,
            "service_name": self.service_name,
            "requests": self._metrics["requests"],
            "errors": self._metrics["errors"],
            "conversions": self._metrics["conversions"],
            "revenue": self._metrics["revenue"],
            "avg_latency_ms": round(avg_latency, 2),
        }

# Global singleton
_telemetry_instance: Optional[NAYATelemetryCore] = None

def get_telemetry() -> NAYATelemetryCore:
    """Get or create global telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = NAYATelemetryCore()
        _telemetry_instance.initialize()
    return _telemetry_instance
