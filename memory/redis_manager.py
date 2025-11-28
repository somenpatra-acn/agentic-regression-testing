"""
Redis Manager with Hybrid Deployment

Automatically detects Redis availability and falls back to fakeredis for development.
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import fakeredis
    FAKEREDIS_AVAILABLE = True
except ImportError:
    FAKEREDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis connection manager with automatic fallback

    Tries to connect to real Redis first, falls back to fakeredis if unavailable.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "ai_regression_test",
        use_fakeredis: bool = False
    ):
        """
        Initialize Redis manager

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            key_prefix: Prefix for all keys
            use_fakeredis: Force use of fakeredis (for testing)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.client = None
        self.is_fake = False

        if use_fakeredis or not REDIS_AVAILABLE:
            self._init_fakeredis()
        else:
            self._init_redis()

    def _init_redis(self):
        """Initialize real Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )

            # Test connection
            self.client.ping()
            self.is_fake = False
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")

        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            logger.info("Falling back to fakeredis...")
            self._init_fakeredis()

    def _init_fakeredis(self):
        """Initialize fakeredis fallback"""
        if FAKEREDIS_AVAILABLE:
            self.client = fakeredis.FakeRedis(decode_responses=True)
            self.is_fake = True
            logger.info("✅ Using fakeredis (in-memory mode)")
        else:
            raise RuntimeError(
                "Neither redis nor fakeredis is available. "
                "Install with: pip install redis fakeredis"
            )

    def _make_key(self, *parts: str) -> str:
        """Create namespaced key"""
        return f"{self.key_prefix}:{':'.join(parts)}"

    # ========== Basic Operations ==========

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        full_key = self._make_key(key)
        return self.client.get(full_key)

    def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value with optional TTL

        Args:
            key: Key name
            value: Value to store
            ttl: Time to live in seconds
        """
        full_key = self._make_key(key)
        return self.client.set(full_key, value, ex=ttl)

    def delete(self, key: str) -> int:
        """Delete key"""
        full_key = self._make_key(key)
        return self.client.delete(full_key)

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        full_key = self._make_key(key)
        return self.client.exists(full_key) > 0

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        full_key = self._make_key(key)
        return self.client.expire(full_key, ttl)

    # ========== JSON Operations ==========

    def get_json(self, key: str, default: Any = None) -> Any:
        """Get JSON value"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON for key: {key}")
            return default

    def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value"""
        try:
            json_str = json.dumps(value, default=str)
            return self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to encode JSON for key {key}: {e}")
            return False

    # ========== List Operations ==========

    def lpush(self, key: str, *values: str) -> int:
        """Push values to left of list"""
        full_key = self._make_key(key)
        return self.client.lpush(full_key, *values)

    def rpush(self, key: str, *values: str) -> int:
        """Push values to right of list"""
        full_key = self._make_key(key)
        return self.client.rpush(full_key, *values)

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get list range"""
        full_key = self._make_key(key)
        return self.client.lrange(full_key, start, end)

    def llen(self, key: str) -> int:
        """Get list length"""
        full_key = self._make_key(key)
        return self.client.llen(full_key)

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to range"""
        full_key = self._make_key(key)
        return self.client.ltrim(full_key, start, end)

    # ========== Hash Operations ==========

    def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field"""
        full_name = self._make_key(name)
        return self.client.hset(full_name, key, value)

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field"""
        full_name = self._make_key(name)
        return self.client.hget(full_name, key)

    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields"""
        full_name = self._make_key(name)
        return self.client.hgetall(full_name)

    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        full_name = self._make_key(name)
        return self.client.hdel(full_name, *keys)

    # ========== Set Operations ==========

    def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        full_key = self._make_key(key)
        return self.client.sadd(full_key, *members)

    def smembers(self, key: str) -> set:
        """Get all set members"""
        full_key = self._make_key(key)
        return self.client.smembers(full_key)

    def sismember(self, key: str, member: str) -> bool:
        """Check if member in set"""
        full_key = self._make_key(key)
        return self.client.sismember(full_key, member)

    # ========== Utility Operations ==========

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        full_pattern = self._make_key(pattern)
        keys = self.client.keys(full_pattern)
        # Remove prefix from returned keys
        prefix_len = len(self.key_prefix) + 1
        return [k[prefix_len:] for k in keys]

    def flush_all(self):
        """Delete all keys (use with caution!)"""
        if self.is_fake:
            self.client.flushall()
        else:
            # Only delete keys with our prefix for safety
            keys = self.keys("*")
            if keys:
                full_keys = [self._make_key(k) for k in keys]
                self.client.delete(*full_keys)

    def info(self) -> Dict[str, Any]:
        """Get Redis info"""
        return {
            "is_fake": self.is_fake,
            "host": self.host if not self.is_fake else "in-memory",
            "port": self.port if not self.is_fake else "N/A",
            "db": self.db,
            "key_prefix": self.key_prefix,
            "connected": self.client is not None
        }


# Global singleton instance
_redis_manager: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance"""
    global _redis_manager

    if _redis_manager is None:
        # Load from environment
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
        password = os.getenv("REDIS_PASSWORD")
        key_prefix = os.getenv("REDIS_KEY_PREFIX", "ai_regression_test")

        _redis_manager = RedisManager(
            host=host,
            port=port,
            db=db,
            password=password,
            key_prefix=key_prefix
        )

    return _redis_manager


def reset_redis_manager():
    """Reset global instance (for testing)"""
    global _redis_manager
    _redis_manager = None
