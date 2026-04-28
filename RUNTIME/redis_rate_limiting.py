"""
NAYA SUPREME - Distributed Rate Limiting
═════════════════════════════════════════════════════════════════════════════════

Rate limiting distribué avec Redis pour scalabilité.
Support de multiples stratégies: sliding window, token bucket, etc.
"""

import redis
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import logging

log = logging.getLogger("naya.rate_limiting")

# ════════════════════════════════════════════════════════════════════════════════
# REDIS CONNECTION
# ════════════════════════════════════════════════════════════════════════════════

class RedisRateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis rate limiter
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.redis.ping()  # Verify connection
        log.info("✅ Redis rate limiter initialized")
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limit (sliding window)
        
        Args:
            key: Rate limit key (e.g., "user:123" or "api_key:abc")
            limit: Max requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Dict with rate limit info
        """
        
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = self.redis.zcard(key)
        
        # Check if limit exceeded
        allowed = current_count < limit
        
        if allowed:
            # Add new request
            self.redis.zadd(key, {str(now): now})
            # Set expiration
            self.redis.expire(key, window_seconds + 1)
        
        return {
            "allowed": allowed,
            "current": current_count,
            "limit": limit,
            "window_seconds": window_seconds,
            "reset_in_seconds": window_seconds if not allowed else None
        }
    
    def token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: int,
        refill_interval: int = 60
    ) -> Dict[str, Any]:
        """
        Token bucket rate limiting
        
        Args:
            key: Bucket key
            capacity: Max tokens in bucket
            refill_rate: Tokens to add per interval
            refill_interval: Seconds between refills
        
        Returns:
            Dict with token bucket info
        """
        
        now = time.time()
        bucket_key = f"{key}:bucket"
        refill_key = f"{key}:refill"
        
        # Get current tokens and last refill time
        bucket_data = self.redis.hgetall(bucket_key)
        tokens = float(bucket_data.get('tokens', capacity))
        last_refill = float(bucket_data.get('last_refill', now))
        
        # Calculate refill
        elapsed = now - last_refill
        refills = int(elapsed / refill_interval)
        
        if refills > 0:
            tokens = min(capacity, tokens + (refills * refill_rate))
            last_refill = now
        
        # Check if token available
        allowed = tokens >= 1.0
        
        if allowed:
            tokens -= 1.0
        
        # Update bucket
        self.redis.hset(
            bucket_key,
            mapping={
                'tokens': str(tokens),
                'last_refill': str(last_refill)
            }
        )
        self.redis.expire(bucket_key, refill_interval * 10)
        
        return {
            "allowed": allowed,
            "tokens_available": tokens,
            "capacity": capacity,
            "reset_in_seconds": refill_interval if not allowed else None
        }
    
    def get_quota(self, key: str) -> Dict[str, Any]:
        """Get current quota status"""
        data = self.redis.hgetall(key)
        return data if data else None
    
    def reset_limit(self, key: str) -> bool:
        """Reset rate limit for key"""
        return bool(self.redis.delete(key))
    
    def set_custom_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """Set custom rate limit"""
        self.redis.hset(
            f"{key}:config",
            mapping={
                'limit': str(limit),
                'window': str(window_seconds)
            }
        )
        return True


# ════════════════════════════════════════════════════════════════════════════════
# ENDPOINT RATE LIMIT DECORATOR
# ════════════════════════════════════════════════════════════════════════════════

def rate_limit(
    limit: int = 100,
    window: int = 60,
    key_func=None
):
    """
    Decorator pour rate limiter les endpoints FastAPI
    
    Args:
        limit: Max requests
        window: Time window in seconds
        key_func: Function to extract rate limit key from request
    """
    def decorator(func):
        async def async_wrapper(request, *args, **kwargs):
            # Default key function: use client IP
            if key_func is None:
                rate_key = f"api:{request.client.host}"
            else:
                rate_key = key_func(request)
            
            limiter = RedisRateLimiter()
            result = limiter.check_rate_limit(rate_key, limit, window)
            
            if not result["allowed"]:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(result["reset_in_seconds"])}
                )
            
            return await func(request, *args, **kwargs)
        
        return async_wrapper
    
    return decorator


# ════════════════════════════════════════════════════════════════════════════════
# BUSINESS RATE LIMITS
# ════════════════════════════════════════════════════════════════════════════════

class BusinessRateLimiter:
    """Rate limiter pour les opérations métier"""
    
    # Limites par tier
    RATE_LIMITS = {
        'free': {
            'leads_per_day': 10,
            'publications_per_day': 5,
            'api_calls_per_minute': 60,
        },
        'pro': {
            'leads_per_day': 100,
            'publications_per_day': 50,
            'api_calls_per_minute': 600,
        },
        'enterprise': {
            'leads_per_day': 10000,
            'publications_per_day': 1000,
            'api_calls_per_minute': 10000,
        },
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.limiter = RedisRateLimiter(redis_url)
    
    def check_operation(
        self,
        business_id: str,
        operation: str,
        tier: str = 'free'
    ) -> Dict[str, Any]:
        """
        Check if operation is allowed for business
        
        Args:
            business_id: Business ID
            operation: Operation name (e.g., 'leads', 'publications')
            tier: Subscription tier
        
        Returns:
            Rate limit check result
        """
        
        if tier not in self.RATE_LIMITS:
            tier = 'free'
        
        limits = self.RATE_LIMITS[tier]
        
        # Determine time window based on operation
        if operation.endswith('_per_day'):
            window = 86400  # 24 hours
        elif operation.endswith('_per_minute'):
            window = 60
        else:
            window = 3600  # 1 hour default
        
        limit = limits.get(f"{operation}_per_day", 100)
        if operation.endswith('_per_minute'):
            limit = limits.get(f"{operation}_per_minute", 600)
        
        key = f"business:{business_id}:{operation}"
        
        return self.limiter.check_rate_limit(key, limit, window)
    
    def get_business_quotas(self, business_id: str, tier: str = 'free') -> Dict[str, Any]:
        """Get all quotas for a business"""
        if tier not in self.RATE_LIMITS:
            tier = 'free'
        
        limits = self.RATE_LIMITS[tier]
        quotas = {}
        
        for operation, limit in limits.items():
            key = f"business:{business_id}:{operation}"
            quota = self.limiter.check_rate_limit(
                key,
                limit,
                86400 if 'day' in operation else 60
            )
            quotas[operation] = quota
        
        return quotas
    
    def reset_business_quotas(self, business_id: str) -> bool:
        """Reset all quotas for a business"""
        for tier_limits in self.RATE_LIMITS.values():
            for operation in tier_limits.keys():
                key = f"business:{business_id}:{operation}"
                self.limiter.reset_limit(key)
        return True
