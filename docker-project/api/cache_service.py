#!/usr/bin/env python3
"""
Redis Cache Service for Crypto Backtest Results
Provides caching layer to speed up repeated queries by 50-100x
"""

import redis
import json
import hashlib
import logging
import os
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for backtest results"""
    
    def __init__(self, host=None, port=None, db=0, default_ttl=86400):
        """
        Initialize Redis cache connection
        
        Args:
            host: Redis host (default: from REDIS_HOST env or 'redis')
            port: Redis port (default: from REDIS_PORT env or 6379)
            db: Redis database number (default: 0)
            default_ttl: Default time-to-live in seconds (default: 86400 = 24 hours)
        """
        self.host = host or os.getenv('REDIS_HOST', 'redis')
        self.port = int(port or os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.default_ttl = default_ttl
        self.enabled = True
        
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis cache connected: {self.host}:{self.port} (TTL: {default_ttl}s)")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache unavailable: {e}. Running without cache.")
            self.enabled = False
            self.redis_client = None
    
    def generate_cache_key(self, prefix: str, **params) -> str:
        """
        Generate a unique cache key based on parameters
        
        Args:
            prefix: Key prefix (e.g., 'backtest', 'crypto_list')
            **params: Key-value pairs to include in hash
        
        Returns:
            Cache key string in format: prefix:hash
        
        Example:
            generate_cache_key('backtest', 
                              crypto_id=1, 
                              strategy_id=2, 
                              start_date='2024-01-01',
                              parameters={'rsi_period': 14})
            -> 'backtest:a3f5b2c8d9e1f4a7'
        """
        # Sort parameters for consistent hashing
        param_string = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()[:16]
        return f"{prefix}:{param_hash}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached value by key
        
        Args:
            key: Cache key
        
        Returns:
            Cached data as dictionary, or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.debug(f"🎯 Cache HIT: {key}")
                return json.loads(cached_data)
            else:
                logger.debug(f"❌ Cache MISS: {key}")
                return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set cached value with TTL
        
        Args:
            key: Cache key
            value: Data to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (default: self.default_ttl)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            json_data = json.dumps(value)
            self.redis_client.setex(key, ttl, json_data)
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"🗑️ Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., 'backtest:*')
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cache CLEAR: {deleted} keys matching '{pattern}'")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats (keys, memory, hits, misses)
        """
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Redis cache is disabled'
            }
        
        try:
            info = self.redis_client.info('stats')
            memory = self.redis_client.info('memory')
            keyspace = self.redis_client.info('keyspace')
            
            total_keys = 0
            if 'db0' in keyspace:
                total_keys = keyspace['db0'].get('keys', 0)
            
            return {
                'enabled': True,
                'host': self.host,
                'port': self.port,
                'total_keys': total_keys,
                'used_memory': memory.get('used_memory_human', 'N/A'),
                'used_memory_bytes': memory.get('used_memory', 0),
                'maxmemory': memory.get('maxmemory_human', 'N/A'),
                'maxmemory_bytes': memory.get('maxmemory', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {
                'enabled': False,
                'error': str(e)
            }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> str:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return "N/A"
        rate = (hits / total) * 100
        return f"{rate:.2f}%"
    
    def flush_all(self) -> bool:
        """
        Clear entire cache (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("⚠️ Cache FLUSH: All keys deleted!")
            return True
        except Exception as e:
            logger.warning(f"Cache flush error: {e}")
            return False
    
    def get_cached_or_compute(self, key: str, compute_func, ttl: Optional[int] = None, 
                             force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get cached value or compute and cache it
        
        This is a convenience method that combines get/set logic.
        
        Args:
            key: Cache key
            compute_func: Function to call if cache miss (should return dict)
            ttl: Time-to-live in seconds
            force_refresh: If True, ignore cache and recompute
        
        Returns:
            Cached or computed result
        
        Example:
            result = cache.get_cached_or_compute(
                'backtest:xyz',
                lambda: run_expensive_backtest(params),
                ttl=3600
            )
        """
        # Check if forced refresh
        if force_refresh:
            logger.info(f"🔄 Force refresh: {key}")
            result = compute_func()
            self.set(key, result, ttl)
            return result
        
        # Try to get from cache
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - compute and store
        result = compute_func()
        self.set(key, result, ttl)
        return result


# Global cache instance (singleton)
_cache_instance = None

def get_cache_service() -> CacheService:
    """
    Get global cache service instance (singleton pattern)
    
    Returns:
        CacheService instance
    
    Example:
        from cache_service import get_cache_service
        
        cache = get_cache_service()
        result = cache.get('my_key')
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
