import redis
import json
import os
import time
from typing import Optional, Any


class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        try:
            return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return bool(self.redis_client.exists(key))


# Rate limiting using Redis
class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """
        Token bucket rate limiter
        Returns (is_allowed, info_dict)
        """
        current_time = int(time.time())
        pipe = self.redis_client.pipeline()

        # Get current bucket state
        bucket_key = f"rate_limit:{key}"
        bucket_data = self.redis_client.hgetall(bucket_key)

        if not bucket_data:
            # Initialize bucket
            tokens = limit - 1
            last_refill = current_time
        else:
            tokens = int(bucket_data.get("tokens", 0))
            last_refill = int(bucket_data.get("last_refill", current_time))

        # Calculate tokens to add (refill rate: 1 token per second)
        time_passed = current_time - last_refill
        tokens_to_add = min(time_passed, limit - tokens)
        tokens = min(limit, tokens + tokens_to_add)

        if tokens > 0:
            # Allow request
            tokens -= 1
            pipe.hset(
                bucket_key, mapping={"tokens": tokens, "last_refill": current_time}
            )
            pipe.expire(bucket_key, window)
            pipe.execute()

            return True, {
                "allowed": True,
                "tokens_remaining": tokens,
                "reset_time": current_time + (limit - tokens),
            }
        else:
            # Deny request
            return False, {
                "allowed": False,
                "tokens_remaining": 0,
                "reset_time": current_time + (limit - tokens),
            }
