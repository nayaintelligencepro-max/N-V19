"""
NAYA V19 — Resilience Patterns
Circuit breaker, bulkhead isolation, retry logic, timeout management
"""
import logging
import time
import threading
from enum import Enum
from typing import Callable, Optional, Any, Dict
from functools import wraps
from datetime import datetime, timedelta
from collections import deque

log = logging.getLogger("NAYA.RESILIENCE")

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"          # Normal operation
    OPEN = "OPEN"              # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"    # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by:
    1. CLOSED: Requests pass through normally
    2. OPEN: Reject requests fast when failure threshold hit
    3. HALF_OPEN: Allow limited requests to test recovery
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: # of failures before OPEN
            recovery_timeout: Seconds before trying HALF_OPEN
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    log.info(f"🔄 Circuit breaker: HALF_OPEN → testing recovery")
                else:
                    raise Exception(f"Circuit breaker OPEN (failures: {self.failure_count})")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                log.info("✅ Circuit breaker: HALF_OPEN → CLOSED (recovered)")
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                log.warning(f"🔴 Circuit breaker: CLOSED → OPEN (threshold: {self.failure_threshold})")
    
    def _should_attempt_reset(self) -> bool:
        """Check if should try resetting."""
        if not self.last_failure_time:
            return False
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }

class BulkheadIsolation:
    """
    Bulkhead isolation pattern.
    
    Limits concurrent resource usage per operation to prevent
    resource exhaustion from affecting other operations.
    """
    
    def __init__(self, max_concurrent: int = 10):
        """
        Initialize bulkhead.
        
        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.current_count = 0
        self._lock = threading.Lock()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead isolation."""
        if not self.semaphore.acquire(blocking=False):
            raise Exception(f"Bulkhead limit reached ({self.max_concurrent} concurrent)")
        
        try:
            with self._lock:
                self.current_count += 1
            
            return func(*args, **kwargs)
        finally:
            with self._lock:
                self.current_count -= 1
            self.semaphore.release()
    
    def get_status(self) -> dict:
        """Get bulkhead status."""
        return {
            "max_concurrent": self.max_concurrent,
            "current_count": self.current_count,
            "available": self.max_concurrent - self.current_count,
            "utilization": round(self.current_count / self.max_concurrent * 100, 2),
        }

class RetryPolicy:
    """
    Intelligent retry policy.
    
    Implements exponential backoff with jitter to avoid
    thundering herd problems.
    """
    
    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 30.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry policy.
        
        Args:
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry policy."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    log.warning(f"⚠️ Retry {attempt + 1}/{self.max_attempts} in {delay:.2f}s: {str(e)[:50]}")
                    time.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay

class TimeoutManager:
    """
    Timeout management for operations.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        """Initialize timeout manager."""
        self.default_timeout = default_timeout
    
    def execute(self, func: Callable, timeout: Optional[float] = None, *args, **kwargs) -> Any:
        """
        Execute function with timeout.
        
        Note: Limited implementation without signal (Unix only)
        For production, use timeout libraries or asyncio.wait_for
        """
        timeout = timeout or self.default_timeout
        
        # Simple implementation - better to use concurrent.futures
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                log.error(f"❌ Function timeout: {timeout}s")
                raise TimeoutError(f"Operation exceeded {timeout}s timeout")

class ResilientFunction:
    """
    Decorator combining all resilience patterns.
    
    Usage:
        @ResilientFunction(
            circuit_breaker=True,
            bulkhead_limit=10,
            retry_attempts=3,
            timeout=30.0
        )
        def risky_operation():
            ...
    """
    
    def __init__(self,
                 circuit_breaker: bool = True,
                 bulkhead_limit: Optional[int] = None,
                 retry_attempts: int = 1,
                 timeout: Optional[float] = None):
        """Initialize resilient function decorator."""
        self.cb = CircuitBreaker() if circuit_breaker else None
        self.bulkhead = BulkheadIsolation(bulkhead_limit) if bulkhead_limit else None
        self.retry = RetryPolicy(max_attempts=retry_attempts) if retry_attempts > 1 else None
        self.timeout_mgr = TimeoutManager(timeout) if timeout else None
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Layer 1: Timeout
            if self.timeout_mgr:
                func_to_execute = lambda: self._execute_with_bulkhead(func, args, kwargs)
                return self.timeout_mgr.execute(func_to_execute)
            else:
                return self._execute_with_bulkhead(func, args, kwargs)
        
        return wrapper
    
    def _execute_with_bulkhead(self, func: Callable, args, kwargs) -> Any:
        """Execute with bulkhead."""
        if self.bulkhead:
            return self.bulkhead.execute(
                self._execute_with_retry, func, args, kwargs
            )
        else:
            return self._execute_with_retry(func, args, kwargs)
    
    def _execute_with_retry(self, func: Callable, args, kwargs) -> Any:
        """Execute with retry."""
        if self.retry:
            return self.retry.execute(
                self._execute_with_circuit_breaker, func, args, kwargs
            )
        else:
            return self._execute_with_circuit_breaker(func, args, kwargs)
    
    def _execute_with_circuit_breaker(self, func: Callable, args, kwargs) -> Any:
        """Execute with circuit breaker."""
        if self.cb:
            return self.cb.call(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def get_status(self) -> dict:
        """Get all resilience statuses."""
        return {
            "circuit_breaker": self.cb.get_status() if self.cb else None,
            "bulkhead": self.bulkhead.get_status() if self.bulkhead else None,
        }
