"""
Redis Caching Service
"""
import redis.asyncio as redis
from typing import Optional, Any, Callable
import json
import pickle
from datetime import timedelta
from loguru import logger
from functools import wraps


class CacheService:
    """
    Advanced caching service using Redis

    Features:
    - Get/Set/Delete operations
    - Pattern-based deletion
    - TTL support
    - Decorator for automatic caching
    - Support for complex Python objects using pickle
    """

    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False  # To handle pickle
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            data = await self.redis_client.get(key)
            if data:
                # Try to unpickle first
                try:
                    return pickle.loads(data)
                except:
                    # If fails, try JSON
                    return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Save value to cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use pickle for complex types
            serialized = pickle.dumps(value)

            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)

            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted

        Example:
            await cache.delete_pattern("user:*")
        """
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {str(e)}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value
        """
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False

    def cached(self, ttl: int = 3600, key_prefix: str = ""):
        """
        Decorator for automatic caching

        Args:
            ttl: Time to live in seconds
            key_prefix: Prefix for cache key

        Usage:
            @cache_service.cached(ttl=3600, key_prefix="user")
            async def get_user(user_id: int):
                # Function implementation
                pass
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_result

                # Execute function
                result = await func(*args, **kwargs)

                # Save to cache
                await self.set(cache_key, result, ttl)
                logger.debug(f"Cache miss: {cache_key}")

                return result

            return wrapper
        return decorator

    async def close(self):
        """Close Redis connection"""
        await self.redis_client.close()
