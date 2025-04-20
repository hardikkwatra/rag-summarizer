import redis
import hashlib
import os
import logging
import json
from typing import Optional, Union, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Get Redis URL from environment variables with fallback
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Initialize Redis client with connection pooling and error handling
try:
    cache = redis.Redis.from_url(redis_url, decode_responses=False, socket_timeout=5)
    # Test connection
    cache.ping()
    logger.info(f"Successfully connected to Redis at {redis_url}")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    # Fallback to a dummy cache for development if Redis is not available
    class DummyCache:
        def __init__(self):
            self._cache = {}
            
        def get(self, key):
            return self._cache.get(key)
            
        def set(self, key, value, ex=None):
            self._cache[key] = value
            
        def delete(self, key):
            if key in self._cache:
                del self._cache[key]
    
    cache = DummyCache()
    logger.warning("Using in-memory dummy cache as Redis is not available")

def get_cache_key(text: str) -> str:
    """Generate a deterministic cache key for the given text."""
    return f"summary:{hashlib.sha256(text.encode()).hexdigest()}"

def get_cached_summary(text: str) -> Optional[bytes]:
    """Retrieve a cached summary for the given text if it exists."""
    key = get_cache_key(text)
    try:
        return cache.get(key)
    except Exception as e:
        logger.error(f"Error retrieving from cache: {e}")
        return None

def set_cached_summary(text: str, summary: str, expiry: int = 3600) -> bool:
    """
    Cache a summary with the given expiry time (default: 1 hour).
    
    Returns:
        bool: True if caching was successful, False otherwise
    """
    key = get_cache_key(text)
    try:
        cache.set(key, summary.encode('utf-8'), ex=expiry)
        logger.info(f"Cached summary for key {key[:10]}... with expiry {expiry}s")
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        return False

def invalidate_cache(text: str) -> bool:
    """
    Invalidate a cached summary.
    
    Returns:
        bool: True if invalidation was successful, False otherwise
    """
    key = get_cache_key(text)
    try:
        cache.delete(key)
        logger.info(f"Invalidated cache for key {key[:10]}...")
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return False
