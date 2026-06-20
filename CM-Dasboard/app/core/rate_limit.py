import time
import logging
import redis.asyncio as aioredis
from fastapi import Request, HTTPException, status
from app.core.config import settings

logger = logging.getLogger("cm_dashboard.core.rate_limit")

# In-memory sliding window fallback store
# Key: rate_limit:feedback:<ip> -> value: list of timestamps
_in_memory_limits = {}

async def check_rate_limit(request: Request, key_prefix: str, limit: int = 10, window_seconds: int = 60) -> None:
    """
    Rate limit checker enforcing maximum requests per time window per IP.
    Uses Redis ZSET (sliding window) if connected, otherwise falls back to in-memory sliding window.
    """
    # Fallback to "127.0.0.1" if request has no client info (e.g. during certain unit tests)
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"rate_limit:{key_prefix}:{client_ip}"
    
    # Try Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        now = time.time()
        # Pipeline execution to clean old items and add new one
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 5)
        _, _, current_count, _ = await pipe.execute()
        
        if current_count > limit:
            logger.warning(f"Rate limit exceeded (Redis) for {client_ip} on key {key}. Count: {current_count}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 10 submissions per minute are allowed."
            )
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Redis rate limiter access failed: {e}. Falling back to in-memory store.")

    # In-memory fallback
    now = time.time()
    if key not in _in_memory_limits:
        _in_memory_limits[key] = []
    
    # Filter old timestamps
    _in_memory_limits[key] = [t for t in _in_memory_limits[key] if t > now - window_seconds]
    
    if len(_in_memory_limits[key]) >= limit:
        logger.warning(f"Rate limit exceeded (In-Memory) for {client_ip} on key {key}. Count: {len(_in_memory_limits[key]) + 1}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 10 submissions per minute are allowed."
        )
    
    _in_memory_limits[key].append(now)
