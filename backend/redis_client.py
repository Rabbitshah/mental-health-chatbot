import os
import redis
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client with connection pooling and error handling.
    Returns None if Redis is unavailable (graceful degradation).
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            print(f"✓ Redis connected successfully at {REDIS_HOST}:{REDIS_PORT}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"⚠ Redis connection failed: {e}")
            print("  Application will continue without caching (graceful degradation)")
            _redis_client = None
        except Exception as e:
            print(f"⚠ Unexpected Redis error: {e}")
            _redis_client = None
    
    return _redis_client

def close_redis_connection():
    """Close Redis connection on application shutdown"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
            print("✓ Redis connection closed")
        except Exception as e:
            print(f"⚠ Error closing Redis connection: {e}")
        finally:
            _redis_client = None

# Cache key patterns
class CacheKeys:
    """Redis cache key patterns"""
    USER_PROFILE = "user:{user_id}:profile"
    SESSION_LIST = "user:{user_id}:sessions"
    SESSION_DATA = "session:{session_id}:data"
    SESSION_MESSAGES = "session:{session_id}:messages"
    MOOD_ANALYTICS = "user:{user_id}:mood:analytics:{days}"
    RATE_LIMIT = "ratelimit:{user_id}:{endpoint}"

# Cache TTL (Time To Live) in seconds
class CacheTTL:
    """Cache expiration times"""
    USER_PROFILE = 600  # 10 minutes
    SESSION_LIST = 300  # 5 minutes
    SESSION_DATA = 300  # 5 minutes
    SESSION_MESSAGES = 300  # 5 minutes
    MOOD_ANALYTICS = 900  # 15 minutes
