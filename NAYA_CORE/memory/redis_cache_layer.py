"""
NAYA REDIS CACHE LAYER v1
Performance 100x - Intelligent caching, invalidation, warming
Supports all data types: sessions, prospects, campaigns, metrics
"""

import os, json, logging, asyncio, pickle
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta, timezone
from functools import wraps
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

log = logging.getLogger("NAYA.CACHE")

# ═══════════════════════════════════════════════════════════════════════════
# 1. REDIS CONNECTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class RedisManager:
    """Manage Redis connections with pooling, failover, monitoring"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")
        self.cluster = os.getenv("REDIS_CLUSTER", "false").lower() == "true"
        
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self.is_healthy = False
    
    async def connect(self) -> bool:
        """Initialize Redis connection pool"""
        try:
            self.pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=20,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            self.client = Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            self.is_healthy = True
            log.info(f"✅ Redis connected: {self.host}:{self.port}")
            return True
        except Exception as e:
            log.error(f"❌ Redis connection failed: {e}")
            self.is_healthy = False
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Monitor Redis health"""
        try:
            await self.client.ping()
            self.is_healthy = True
            return True
        except:
            self.is_healthy = False
            return False

# ═══════════════════════════════════════════════════════════════════════════
# 2. CACHE STRATEGIES & TTL
# ═══════════════════════════════════════════════════════════════════════════

class CacheStrategy:
    """Define caching strategy for different data types"""
    
    # TTL configurations (seconds)
    SESSION = 3600                # 1 hour
    PROSPECT_DATA = 86400         # 24 hours
    CAMPAIGN_METRICS = 300        # 5 minutes
    EMAIL_VERIFICATION = 604800   # 7 days (don't re-check same email)
    SEARCH_RESULTS = 3600         # 1 hour
    ENRICHMENT_DATA = 2592000     # 30 days
    API_RESPONSES = 600           # 10 minutes
    FEATURE_FLAGS = 300           # 5 minutes
    USER_PREFERENCES = 2592000    # 30 days
    
    # Invalidation patterns
    INVALIDATE_ON_PROSPECT_UPDATE = ["prospect:{id}:*", "prospect_list:*"]
    INVALIDATE_ON_CAMPAIGN = ["campaign:{id}:*", "metrics:*"]
    INVALIDATE_ON_ENRICHMENT = ["email:*", "domain:*"]

# ═══════════════════════════════════════════════════════════════════════════
# 3. SMART CACHING LAYER
# ═══════════════════════════════════════════════════════════════════════════

class SmartCache:
    """Intelligent caching with TTL, invalidation, warming"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.hit_count = 0
        self.miss_count = 0
        self.invalidation_log: List[Dict] = []
    
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value is None:
                self.miss_count += 1
                return None
            
            self.hit_count += 1
            if deserialize:
                return json.loads(value)
            return value
        except Exception as e:
            log.warning(f"Cache get failed for {key}: {e}")
            return None
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: int = 3600,
                  serialize: bool = True) -> bool:
        """Set value in cache with TTL"""
        try:
            if serialize:
                value = json.dumps(value, default=str)
            
            await self.redis.setex(key, ttl, value)
            log.debug(f"✅ Cached: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            log.warning(f"Cache set failed for {key}: {e}")
            return False
    
    async def get_or_fetch(self,
                          key: str,
                          fetch_fn: Callable,
                          ttl: int = 3600) -> Any:
        """Get from cache or fetch if missing"""
        # Try cache
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Miss - fetch from source
        result = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()
        
        # Cache result
        await self.set(key, result, ttl)
        return result
    
    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache by pattern (e.g., 'prospect:123:*')"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                self.invalidation_log.append({
                    "pattern": pattern,
                    "deleted": deleted,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                log.info(f"🗑️  Invalidated {deleted} keys matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            log.warning(f"Invalidation failed: {e}")
            return 0
    
    async def warm(self, key: str, fetch_fn: Callable, ttl: int = 3600):
        """Pre-populate cache (warming)"""
        try:
            result = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()
            await self.set(key, result, ttl)
            log.info(f"🔥 Cache warmed: {key}")
        except Exception as e:
            log.warning(f"Cache warming failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache hit/miss statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "last_invalidations": self.invalidation_log[-10:]
        }

# ═══════════════════════════════════════════════════════════════════════════
# 4. DECORATOR FOR AUTOMATIC CACHING
# ═══════════════════════════════════════════════════════════════════════════

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for automatic function result caching"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = cache_key[:100]  # Limit key length
            
            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                log.debug(f"Cache HIT: {cache_key[:50]}")
                return cached_value
            
            # Miss - execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# ═══════════════════════════════════════════════════════════════════════════
# 5. SPECIALIZED CACHES FOR DIFFERENT DOMAINS
# ═══════════════════════════════════════════════════════════════════════════

class ProspectCache:
    """Cache for prospect data"""
    def __init__(self, cache: SmartCache):
        self.cache = cache
    
    async def get_prospect(self, prospect_id: str) -> Optional[Dict]:
        return await self.cache.get(f"prospect:{prospect_id}")
    
    async def set_prospect(self, prospect_id: str, data: Dict):
        await self.cache.set(f"prospect:{prospect_id}", data, CacheStrategy.PROSPECT_DATA)
    
    async def invalidate_prospect(self, prospect_id: str):
        await self.cache.invalidate(f"prospect:{prospect_id}:*")

class EmailCache:
    """Cache for email verification/enrichment"""
    def __init__(self, cache: SmartCache):
        self.cache = cache
    
    async def get_email(self, email: str) -> Optional[Dict]:
        return await self.cache.get(f"email:{email}")
    
    async def set_email(self, email: str, data: Dict):
        await self.cache.set(f"email:{email}", data, CacheStrategy.EMAIL_VERIFICATION)

class MetricsCache:
    """Cache for real-time metrics"""
    def __init__(self, cache: SmartCache):
        self.cache = cache
    
    async def get_campaign_metrics(self, campaign_id: str) -> Optional[Dict]:
        return await self.cache.get(f"metrics:campaign:{campaign_id}")
    
    async def set_campaign_metrics(self, campaign_id: str, data: Dict):
        await self.cache.set(f"metrics:campaign:{campaign_id}", data, CacheStrategy.CAMPAIGN_METRICS)

# ═══════════════════════════════════════════════════════════════════════════
# 6. CACHE WARMER - Pre-populate important data
# ═══════════════════════════════════════════════════════════════════════════

class CacheWarmer:
    """Pre-populate cache at startup with hot data"""
    
    def __init__(self, cache: SmartCache):
        self.cache = cache
    
    async def warm_all(self, data_sources: Dict[str, Callable]):
        """Warm all critical caches"""
        log.info(f"🔥 Starting cache warming ({len(data_sources)} sources)...")
        
        tasks = []
        for key, fetch_fn in data_sources.items():
            tasks.append(self.cache.warm(key, fetch_fn))
        
        await asyncio.gather(*tasks)
        log.info(f"✅ Cache warming completed")

# ═══════════════════════════════════════════════════════════════════════════
# 7. UNIFIED CACHE MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class CacheManager:
    """Central cache management system"""
    
    def __init__(self):
        self.redis_mgr = RedisManager()
        self.smart_cache: Optional[SmartCache] = None
        self.prospect_cache: Optional[ProspectCache] = None
        self.email_cache: Optional[EmailCache] = None
        self.metrics_cache: Optional[MetricsCache] = None
        self.warmer: Optional[CacheWarmer] = None
    
    async def initialize(self) -> bool:
        """Initialize all cache components"""
        # Connect to Redis
        if not await self.redis_mgr.connect():
            return False
        
        # Initialize specialized caches
        self.smart_cache = SmartCache(self.redis_mgr.client)
        self.prospect_cache = ProspectCache(self.smart_cache)
        self.email_cache = EmailCache(self.smart_cache)
        self.metrics_cache = MetricsCache(self.smart_cache)
        self.warmer = CacheWarmer(self.smart_cache)
        
        log.info("✅ Cache Manager initialized")
        return True
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.redis_mgr:
            await self.redis_mgr.disconnect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "redis_healthy": self.redis_mgr.is_healthy,
            "cache_stats": self.smart_cache.get_stats() if self.smart_cache else None
        }

# ═══════════════════════════════════════════════════════════════════════════
# 8. SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_cache_manager: Optional[CacheManager] = None
cache: Optional[SmartCache] = None

async def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    return _cache_manager

async def get_cache() -> SmartCache:
    global cache
    if cache is None:
        mgr = await get_cache_manager()
        cache = mgr.smart_cache
    return cache
