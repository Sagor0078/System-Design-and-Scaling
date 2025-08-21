from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import time
import uuid
from models import CreateUserRequest, ApiResponse
from cache import RedisCache, RateLimiter

# App configuration
app = FastAPI(title="Scalable API", version="1.0.0")
server_id = os.getenv("SERVER_ID", f"server-{uuid.uuid4().hex[:8]}")

# Initialize cache and rate limiter
cache = RedisCache()
rate_limiter = RateLimiter(cache.redis_client)

# In-memory database (for demo)
users_db = {}
user_counter = 0


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = request.client.host

    # Apply rate limiting (10 requests per minute)
    is_allowed, rate_info = rate_limiter.is_allowed(
        key=f"ip:{client_ip}", limit=10, window=60
    )

    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "reset_time": rate_info["reset_time"],
            },
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_info["reset_time"]),
            },
        )

    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Remaining"] = str(rate_info["tokens_remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
    response.headers["X-Server-ID"] = server_id

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return ApiResponse(success=True, message="Service healthy", server_id=server_id)


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user with caching"""
    cache_key = f"user:{user_id}"

    # Try cache first
    cached_user = cache.get(cache_key)
    if cached_user:
        return ApiResponse(
            success=True,
            data={**cached_user, "from_cache": True},
            message="User retrieved from cache",
            server_id=server_id,
        )

    # Check database
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = users_db[user_id]

    # Cache the result
    cache.set(cache_key, user_data, ttl=300)  # 5 minutes TTL

    return ApiResponse(
        success=True,
        data={**user_data, "from_cache": False},
        message="User retrieved from database",
        server_id=server_id,
    )


@app.post("/users")
async def create_user(user_request: CreateUserRequest):
    """Create new user"""
    global user_counter
    user_counter += 1

    user_data = {
        "id": user_counter,
        "name": user_request.name,
        "email": user_request.email,
        "created_at": time.time(),
    }

    # Save to database
    users_db[user_counter] = user_data

    # Cache the new user
    cache_key = f"user:{user_counter}"
    cache.set(cache_key, user_data, ttl=300)

    return ApiResponse(
        success=True,
        data=user_data,
        message="User created successfully",
        server_id=server_id,
    )


@app.get("/users")
async def list_users():
    """List all users (no caching for demo)"""
    return ApiResponse(
        success=True,
        data={"users": list(users_db.values()), "count": len(users_db)},
        message="Users retrieved",
        server_id=server_id,
    )


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user and clear cache"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove from database
    del users_db[user_id]

    # Clear cache
    cache_key = f"user:{user_id}"
    cache.delete(cache_key)

    return ApiResponse(
        success=True, message="User deleted successfully", server_id=server_id
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
