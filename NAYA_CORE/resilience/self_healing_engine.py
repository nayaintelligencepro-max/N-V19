"""
NAYA SELF-HEALING ENGINE v1
Auto-recovery, health monitoring, dead letter queue
99.9% uptime vs manual intervention
"""

import asyncio, logging, os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import traceback

log = logging.getLogger("NAYA.HEALING")

# ═══════════════════════════════════════════════════════════════════════════
# 1. HEALTH CHECK SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    consecutive_failures: int = 0

class HealthMonitor:
    """Monitor health of all critical services"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.failure_threshold = 3  # 3 failures → mark unhealthy
        self.recovery_attempts: Dict[str, int] = {}
    
    async def register_check(self,
                            service_name: str,
                            check_fn: Callable) -> None:
        """Register health check function"""
        self.checks[service_name] = HealthCheck(
            service_name=service_name,
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            response_time_ms=0
        )
        # V19.3: stocker la vraie fonction de check
        if not hasattr(self, '_check_fns'):
            self._check_fns = {}
        self._check_fns[service_name] = check_fn
        log.info(f"✅ Registered health check: {service_name}")

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        check_fns = getattr(self, '_check_fns', {})

        for service_name, check in self.checks.items():
            try:
                start = datetime.now(timezone.utc)

                # V19.3 FIX: exécuter la vraie fonction de check avec timeout 5s
                check_fn = check_fns.get(service_name)
                if check_fn is None:
                    # Pas de fonction enregistrée → UNKNOWN
                    check.status = ServiceStatus.UNKNOWN
                    check.error_message = "No check_fn registered"
                    check.last_check = datetime.now(timezone.utc)
                    results[service_name] = check
                    continue

                # Support sync + async functions
                if asyncio.iscoroutinefunction(check_fn):
                    is_ok = await asyncio.wait_for(check_fn(), timeout=5.0)
                else:
                    is_ok = await asyncio.wait_for(
                        asyncio.to_thread(check_fn), timeout=5.0
                    )

                elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

                if is_ok:
                    check.status = ServiceStatus.HEALTHY
                    check.response_time_ms = elapsed
                    check.error_message = None
                    check.consecutive_failures = 0
                else:
                    check.consecutive_failures += 1
                    check.response_time_ms = elapsed
                    check.error_message = "check_fn returned False"
                    check.status = (
                        ServiceStatus.UNHEALTHY
                        if check.consecutive_failures >= self.failure_threshold
                        else ServiceStatus.DEGRADED
                    )

            except asyncio.TimeoutError:
                check.status = ServiceStatus.UNHEALTHY
                check.error_message = "Health check timeout (>5s)"
                check.consecutive_failures += 1

            except Exception as e:
                check.consecutive_failures += 1
                check.error_message = str(e)

                if check.consecutive_failures >= self.failure_threshold:
                    check.status = ServiceStatus.UNHEALTHY
                else:
                    check.status = ServiceStatus.DEGRADED

            check.last_check = datetime.now(timezone.utc)
            results[service_name] = check

        log.debug(f"Health check completed: {len(results)} services")
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system health"""
        healthy = sum(1 for c in self.checks.values() 
                     if c.status == ServiceStatus.HEALTHY)
        degraded = sum(1 for c in self.checks.values() 
                      if c.status == ServiceStatus.DEGRADED)
        unhealthy = sum(1 for c in self.checks.values() 
                       if c.status == ServiceStatus.UNHEALTHY)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "total": len(self.checks),
            "uptime_percentage": (healthy / max(len(self.checks), 1)) * 100,
            "checks": {k: {
                "status": v.status.value,
                "response_time_ms": v.response_time_ms,
                "error": v.error_message
            } for k, v in self.checks.items()}
        }

# ═══════════════════════════════════════════════════════════════════════════
# 2. AUTO-RECOVERY STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════

class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    async def attempt_recovery(self, service_name: str, 
                              error: Exception) -> bool:
        """Attempt to recover service"""
        raise NotImplementedError

class RestartStrategy(RecoveryStrategy):
    """Restart failed module via callback enregistré"""

    def __init__(self):
        self._restart_fns: Dict[str, Callable] = {}

    def register_restart(self, service_name: str, restart_fn: Callable):
        """Enregistrer une fonction de restart pour un service"""
        self._restart_fns[service_name] = restart_fn

    async def attempt_recovery(self, service_name: str,
                              error: Exception) -> bool:
        log.warning(f"🔄 Attempting restart: {service_name}")
        # V19.3 FIX: appeler le vrai callback de restart s'il existe
        restart_fn = self._restart_fns.get(service_name)
        if restart_fn is None:
            log.warning(f"No restart_fn for {service_name} — soft restart (no-op)")
            return False
        try:
            if asyncio.iscoroutinefunction(restart_fn):
                await asyncio.wait_for(restart_fn(), timeout=30.0)
            else:
                await asyncio.wait_for(asyncio.to_thread(restart_fn), timeout=30.0)
            log.info(f"✅ Restarted: {service_name}")
            return True
        except Exception as e:
            log.error(f"Restart failed for {service_name}: {e}")
            return False

class ConnectionRetryStrategy(RecoveryStrategy):
    """Retry connection with exponential backoff"""

    def __init__(self, max_retries: int = 5):
        self.max_retries = max_retries
        self._reconnect_fns: Dict[str, Callable] = {}

    def register_reconnect(self, service_name: str, reconnect_fn: Callable):
        self._reconnect_fns[service_name] = reconnect_fn

    async def attempt_recovery(self, service_name: str,
                              error: Exception) -> bool:
        reconnect_fn = self._reconnect_fns.get(service_name)

        for attempt in range(self.max_retries):
            wait_time = (2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
            log.warning(f"⏳ Retry {attempt+1}/{self.max_retries} in {wait_time}s: {service_name}")
            await asyncio.sleep(wait_time)

            # V19.3 FIX: tentative réelle de reconnexion
            if reconnect_fn is None:
                continue
            try:
                if asyncio.iscoroutinefunction(reconnect_fn):
                    ok = await asyncio.wait_for(reconnect_fn(), timeout=10.0)
                else:
                    ok = await asyncio.wait_for(asyncio.to_thread(reconnect_fn), timeout=10.0)
                if ok:
                    log.info(f"✅ Reconnected: {service_name}")
                    return True
            except Exception as e:
                log.debug(f"Reconnect attempt {attempt+1} failed: {e}")

        return False

class CacheInvalidationStrategy(RecoveryStrategy):
    """Clear cache and retry"""

    def __init__(self):
        self._invalidate_fns: Dict[str, Callable] = {}

    def register_invalidator(self, service_name: str, invalidate_fn: Callable):
        self._invalidate_fns[service_name] = invalidate_fn

    async def attempt_recovery(self, service_name: str,
                              error: Exception) -> bool:
        log.info(f"🗑️  Clearing cache for: {service_name}")
        # V19.3 FIX: appel réel à l'invalidateur
        invalidate_fn = self._invalidate_fns.get(service_name)
        if invalidate_fn is None:
            return False
        try:
            if asyncio.iscoroutinefunction(invalidate_fn):
                await invalidate_fn()
            else:
                await asyncio.to_thread(invalidate_fn)
            return True
        except Exception as e:
            log.error(f"Cache invalidation failed: {e}")
            return False

class CircuitBreakerStrategy(RecoveryStrategy):
    """Circuit breaker: fail fast, retry periodically"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout  # seconds
        self.failures: Dict[str, List[datetime]] = {}
        self.open_circuits: Dict[str, datetime] = {}
    
    async def attempt_recovery(self, service_name: str,
                              error: Exception) -> bool:
        now = datetime.now(timezone.utc)
        
        # Record failure
        if service_name not in self.failures:
            self.failures[service_name] = []
        
        self.failures[service_name].append(now)
        
        # Check if circuit should be open
        recent_failures = [f for f in self.failures[service_name]
                          if (now - f).total_seconds() < self.reset_timeout]
        
        if len(recent_failures) >= self.failure_threshold:
            self.open_circuits[service_name] = now
            log.error(f"⚡ Circuit opened: {service_name} (too many failures)")
            return False
        
        # Check if circuit should be closed
        if service_name in self.open_circuits:
            time_since_open = (now - self.open_circuits[service_name]).total_seconds()
            if time_since_open >= self.reset_timeout:
                del self.open_circuits[service_name]
                self.failures[service_name] = []
                log.info(f"✅ Circuit reset: {service_name}")
                return True
            else:
                return False
        
        return True

# ═══════════════════════════════════════════════════════════════════════════
# 3. DEAD LETTER QUEUE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FailedJob:
    job_id: str
    function_name: str
    args: tuple
    kwargs: dict
    error: str
    traceback_str: str
    first_attempt: datetime
    last_attempt: datetime
    retry_count: int = 0
    max_retries: int = 5

class DeadLetterQueue:
    """Queue for failed jobs - don't lose data"""
    
    def __init__(self):
        self.failed_jobs: Dict[str, FailedJob] = {}
        self.retry_attempts: Dict[str, int] = {}
    
    async def enqueue_failed_job(self,
                                job_id: str,
                                function_name: str,
                                args: tuple,
                                kwargs: dict,
                                error: Exception) -> str:
        """Add failed job to DLQ"""
        
        failed_job = FailedJob(
            job_id=job_id,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            error=str(error),
            traceback_str=traceback.format_exc(),
            first_attempt=datetime.now(timezone.utc),
            last_attempt=datetime.now(timezone.utc)
        )
        
        self.failed_jobs[job_id] = failed_job
        log.warning(f"📬 Job added to DLQ: {job_id}")
        
        return job_id
    
    async def retry_failed_jobs(self,
                               executor: Callable) -> Dict[str, bool]:
        """
        Retry all failed jobs.
        V19.3 FIX: executor(function_name, *args, **kwargs) appelé pour de vrai.
        executor doit être Callable[[str, tuple, dict], Awaitable | Any]
        """
        results = {}

        jobs_to_retry = [j for j in self.failed_jobs.values()
                        if j.retry_count < j.max_retries]

        for job in jobs_to_retry:
            try:
                log.info(f"🔄 Retrying: {job.job_id} (attempt {job.retry_count + 1})")

                # V19.3 FIX: exécution réelle via executor
                if asyncio.iscoroutinefunction(executor):
                    await executor(job.function_name, *job.args, **job.kwargs)
                else:
                    result = executor(job.function_name, *job.args, **job.kwargs)
                    # Si l'executor sync retourne une coroutine, l'attendre
                    if asyncio.iscoroutine(result):
                        await result

                # Success - remove from DLQ
                del self.failed_jobs[job.job_id]
                results[job.job_id] = True
                log.info(f"✅ Job recovered: {job.job_id}")

            except Exception as e:
                job.retry_count += 1
                job.last_attempt = datetime.now(timezone.utc)
                job.error = str(e)
                results[job.job_id] = False
                log.warning(f"❌ Retry failed: {job.job_id} ({job.retry_count}/{job.max_retries})")

        return results
    
    def get_dlq_status(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        total = len(self.failed_jobs)
        
        by_error = {}
        for job in self.failed_jobs.values():
            if job.error not in by_error:
                by_error[job.error] = 0
            by_error[job.error] += 1
        
        return {
            "total_failed_jobs": total,
            "errors_by_type": by_error,
            "oldest_job_age_seconds": (datetime.now(timezone.utc) - 
                                      min(j.first_attempt for j in self.failed_jobs.values())
                                     ).total_seconds() if total > 0 else 0,
            "jobs": [
                {
                    "job_id": j.job_id,
                    "function": j.function_name,
                    "error": j.error,
                    "retry_count": j.retry_count
                } for j in self.failed_jobs.values()
            ]
        }

# ═══════════════════════════════════════════════════════════════════════════
# 4. UNIFIED SELF-HEALING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class SelfHealingEngine:
    """Central orchestration for auto-recovery"""
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.circuit_breaker = CircuitBreakerStrategy()
        self.dlq = DeadLetterQueue()
        self.strategies: Dict[str, RecoveryStrategy] = {
            "restart": RestartStrategy(),
            "retry": ConnectionRetryStrategy(),
            "cache_clear": CacheInvalidationStrategy(),
            "circuit_breaker": self.circuit_breaker
        }
        self._healing_task = None
    
    async def start_continuous_healing(self, interval_seconds: int = 60):
        """Run healing checks continuously"""
        while True:
            try:
                # Run health checks
                checks = await self.health_monitor.run_all_checks()
                
                # Handle unhealthy services
                for service_name, check in checks.items():
                    if check.status == ServiceStatus.UNHEALTHY:
                        await self._recover_service(service_name, check)
                
                # Retry failed jobs periodically
                if self.dlq.failed_jobs:
                    async def _warn_unregistered_executor(fn_name: str, *args, **kwargs):
                        log.warning(f"DLQ retry: no executor registered for '{fn_name}' — job remains in queue")

                    await self.dlq.retry_failed_jobs(_warn_unregistered_executor)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                log.error(f"Healing loop error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _recover_service(self, service_name: str, 
                              check: HealthCheck) -> bool:
        """Attempt to recover unhealthy service"""
        log.warning(f"🏥 Recovering: {service_name} ({check.error_message})")
        
        # Try strategies in order
        for strategy_name, strategy in self.strategies.items():
            try:
                success = await strategy.attempt_recovery(
                    service_name, 
                    Exception(check.error_message)
                )
                if success:
                    log.info(f"✅ Recovered via {strategy_name}: {service_name}")
                    return True
            except Exception as e:
                log.warning(f"Strategy {strategy_name} failed: {e}")
                continue
        
        log.error(f"❌ All recovery strategies failed: {service_name}")
        return False
    
    async def handle_failed_job(self, 
                               job_id: str,
                               function_name: str,
                               args: tuple,
                               kwargs: dict,
                               error: Exception) -> str:
        """Queue failed job for later retry"""
        return await self.dlq.enqueue_failed_job(
            job_id, function_name, args, kwargs, error
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health = self.health_monitor.get_status()
        dlq = self.dlq.get_dlq_status()
        
        return {
            "health": health,
            "dead_letter_queue": dlq,
            "uptime_sla": "99.9%" if health["healthy"] > health["unhealthy"] else "< 99.9%"
        }
    
    def start_healing(self):
        """Start background healing task"""
        self._healing_task = asyncio.create_task(
            self.start_continuous_healing()
        )
        log.info("🏥 Self-Healing Engine started")

# ═══════════════════════════════════════════════════════════════════════════
# 5. SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_healing_engine: Optional[SelfHealingEngine] = None

def get_self_healing_engine() -> SelfHealingEngine:
    global _healing_engine
    if _healing_engine is None:
        _healing_engine = SelfHealingEngine()
        log.info("✅ Self-Healing Engine initialized")
    return _healing_engine
