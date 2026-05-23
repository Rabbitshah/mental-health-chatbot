import os
import time
import logging
import redis
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

# Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
# Set REDIS_ENABLED=false to disable Redis entirely (e.g. in test environments)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() not in ("false", "0", "no")

# Connection retry configuration
REDIS_MAX_RETRIES = int(os.getenv("REDIS_MAX_RETRIES", "3"))
REDIS_RETRY_DELAY = float(os.getenv("REDIS_RETRY_DELAY", "0.5"))  # seconds

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None
# Sentinel: set to True after all retries are exhausted so we skip future attempts
_redis_unavailable: bool = False
# Timestamp of last unavailability — retry after this many seconds
_REDIS_RETRY_AFTER: float = 30.0
_redis_unavailable_since: float = 0.0


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client with connection pooling, timeout, and retry logic.
    Returns None if Redis is unavailable (graceful degradation per Requirement 12.5).
    """
    global _redis_client, _redis_unavailable, _redis_unavailable_since

    # Fast-path: Redis disabled via environment variable
    if not REDIS_ENABLED:
        return None

    # Fast-path: skip retries if Redis was recently found unavailable
    if _redis_unavailable:
        if time.time() - _redis_unavailable_since < _REDIS_RETRY_AFTER:
            return None
        # Retry after cool-down period
        _redis_unavailable = False

    if _redis_client is not None:
        # Verify the existing connection is still alive
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis connection lost, attempting to reconnect...")
            _redis_client = None

    for attempt in range(1, REDIS_MAX_RETRIES + 1):
        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
                retry_on_timeout=False,
            )
            # Test connection
            client.ping()
            _redis_client = client
            _redis_unavailable = False
            logger.info(f"Redis connected successfully at {REDIS_HOST}:{REDIS_PORT}")
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection attempt {attempt}/{REDIS_MAX_RETRIES} failed: {e}")
            if attempt < REDIS_MAX_RETRIES:
                time.sleep(REDIS_RETRY_DELAY * attempt)  # exponential-ish back-off
        except Exception as e:
            logger.warning(f"Unexpected Redis error on attempt {attempt}: {e}")
            if attempt < REDIS_MAX_RETRIES:
                time.sleep(REDIS_RETRY_DELAY * attempt)

    logger.warning(
        "Redis unavailable after %d attempts. Continuing without caching (graceful degradation).",
        REDIS_MAX_RETRIES,
    )
    _redis_unavailable = True
    _redis_unavailable_since = time.time()
    return None


def close_redis_connection() -> None:
    """Close Redis connection on application shutdown."""
    global _redis_client, _redis_unavailable, _redis_unavailable_since
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None
    _redis_unavailable = False
    _redis_unavailable_since = 0.0


# ---------------------------------------------------------------------------
# Helper functions — all handle a None client gracefully (Requirement 12.5)
# ---------------------------------------------------------------------------

def cache_get(key: str) -> Optional[str]:
    """
    Retrieve a value from the cache.
    Returns None when the key is missing or Redis is unavailable.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.get(key)
    except (redis.RedisError, Exception) as e:
        logger.warning(f"Cache GET failed for key '{key}': {e}")
        return None


def cache_set(key: str, value: Any, ttl: int) -> bool:
    """
    Store a value in the cache with a TTL (seconds).
    Returns True on success, False when Redis is unavailable or an error occurs.
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.setex(key, ttl, value)
        return True
    except (redis.RedisError, Exception) as e:
        logger.warning(f"Cache SET failed for key '{key}': {e}")
        return False


def cache_delete(key: str) -> bool:
    """
    Delete a key from the cache.
    Returns True on success, False when Redis is unavailable or an error occurs.
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.delete(key)
        return True
    except (redis.RedisError, Exception) as e:
        logger.warning(f"Cache DELETE failed for key '{key}': {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob-style pattern.
    Returns the number of keys deleted, or 0 on failure.
    """
    client = get_redis_client()
    if client is None:
        return 0
    try:
        deleted_count = 0
        # Use scan_iter for production-safe iteration (O(N) vs blocking O(N))
        for key in client.scan_iter(match=pattern, count=100):
            if client.delete(key):
                deleted_count += 1
        return deleted_count
    except (redis.RedisError, Exception) as e:
        logger.warning(f"Cache DELETE pattern '{pattern}' failed: {e}")
        return 0


# ---------------------------------------------------------------------------
# Cache key patterns
# ---------------------------------------------------------------------------

class CacheKeys:
    """Redis cache key patterns (use .format() to fill placeholders)."""
    USER_PROFILE = "user:{user_id}:profile"
    SESSION_LIST = "user:{user_id}:sessions"
    SESSION_DATA = "session:{session_id}:data"
    SESSION_MESSAGES = "session:{session_id}:messages"
    MOOD_ANALYTICS = "user:{user_id}:mood:analytics:{days}"
    RATE_LIMIT = "ratelimit:{user_id}:{endpoint}"


# ---------------------------------------------------------------------------
# Cache TTL (Time To Live) in seconds
# ---------------------------------------------------------------------------

class CacheTTL:
    """Cache expiration times aligned with design document."""
    USER_PROFILE = 600   # 10 minutes  (Requirement 12.4)
    SESSION_LIST = 300   # 5 minutes   (Requirement 12.2)
    SESSION_DATA = 300   # 5 minutes   (Requirement 12.2)
    SESSION_MESSAGES = 300  # 5 minutes
    MOOD_ANALYTICS = 900  # 15 minutes (Requirement 12.6)


def invalidate_user_caches(user_id: int, session_id: int | None = None) -> None:
    """
    Invalidate all caches associated with a user (and optionally a session).
    Centralises cache invalidation so callers don't repeat key construction.
    """
    cache_delete(CacheKeys.SESSION_LIST.format(user_id=user_id))
    cache_delete(CacheKeys.USER_PROFILE.format(user_id=user_id))
    cache_delete_pattern(CacheKeys.MOOD_ANALYTICS.format(user_id=user_id, days="*"))
    if session_id is not None:
        cache_delete(CacheKeys.SESSION_DATA.format(session_id=session_id))
        cache_delete(CacheKeys.SESSION_MESSAGES.format(session_id=session_id))
