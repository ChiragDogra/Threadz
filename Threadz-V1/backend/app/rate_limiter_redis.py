"""
Redis-based Rate Limiting for Threadz Application
"""
import time
import json
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request
import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .sentry_config import sentry_manager

# Initialize Redis rate limiter
redis_client = None

class RedisRateLimiter:
    """Redis-based rate limiter with advanced features"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=50
            )
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis rate limiter initialized")
        except Exception as e:
            print(f"❌ Redis rate limiter failed: {e}")
            self.redis_client = None
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int,
        identifier: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Check if a request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., "auth", "upload", "api")
            limit: Maximum requests allowed
            window: Time window in seconds
            identifier: Unique identifier (defaults to IP)
        
        Returns:
            Tuple[bool, Dict]: (is_allowed, rate_limit_info)
        """
        if not self.redis_client:
            # Fallback to in-memory limiting if Redis not available
            return self._fallback_in_memory(key, limit, window, identifier)
        
        try:
            # Create rate limit key
            rate_key = f"rate_limit:{key}:{identifier or 'default'}"
            
            # Get current count and expiry
            pipe = self.redis_client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, window)
            results = await pipe.execute()
            
            current_count = results[0]
            
            # Calculate remaining requests and reset time
            remaining = max(0, limit - current_count)
            reset_time = int(time.time()) + window
            
            is_allowed = current_count <= limit
            
            rate_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "current": current_count,
                "key": key
            }
            
            return is_allowed, rate_info
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "rate_limit_check",
                "key": key,
                "limit": limit
            })
            # Fallback to in-memory limiting
            return self._fallback_in_memory(key, limit, window, identifier)
    
    def _fallback_in_memory(
        self, 
        key: str, 
        limit: int, 
        window: int,
        identifier: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """Fallback in-memory rate limiting"""
        # Simple in-memory fallback (not distributed)
        if not hasattr(self, '_memory_store'):
            self._memory_store = {}
        
        memory_key = f"{key}:{identifier or 'default'}"
        now = time.time()
        
        if memory_key not in self._memory_store:
            self._memory_store[memory_key] = {"count": 0, "reset_time": now + window}
        
        memory_data = self._memory_store[memory_key]
        
        # Reset if window expired
        if now > memory_data["reset_time"]:
            memory_data["count"] = 0
            memory_data["reset_time"] = now + window
        
        memory_data["count"] += 1
        
        current_count = memory_data["count"]
        remaining = max(0, limit - current_count)
        is_allowed = current_count <= limit
        
        rate_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": memory_data["reset_time"],
            "current": current_count,
            "key": key
        }
        
        return is_allowed, rate_info
    
    async def get_rate_limit_status(self, key: str, identifier: Optional[str] = None) -> Optional[Dict]:
        """Get current rate limit status without incrementing"""
        if not self.redis_client:
            return None
        
        try:
            rate_key = f"rate_limit:{key}:{identifier or 'default'}"
            
            # Get current count and TTL
            pipe = self.redis_client.pipeline()
            pipe.get(rate_key)
            pipe.ttl(rate_key)
            results = await pipe.execute()
            
            current_count = int(results[0] or 0)
            ttl = results[1]
            
            if ttl == -1:  # No expiry set
                ttl = 3600  # Default to 1 hour
            
            return {
                "current": current_count,
                "ttl": ttl,
                "key": key
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_rate_limit_status",
                "key": key
            })
            return None
    
    async def reset_rate_limit(self, key: str, identifier: Optional[str] = None) -> bool:
        """Reset rate limit for a specific key"""
        if not self.redis_client:
            return False
        
        try:
            rate_key = f"rate_limit:{key}:{identifier or 'default'}"
            await self.redis_client.delete(rate_key)
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "reset_rate_limit",
                "key": key
            })
            return False

# Global rate limiter instance
redis_rate_limiter = RedisRateLimiter()

# Rate limiting configurations
RATE_LIMITS = {
    "auth": {"limit": 5, "window": 60},        # 5 requests per minute
    "upload": {"limit": 10, "window": 3600},    # 10 uploads per hour
    "ai_generation": {"limit": 5, "window": 300}, # 5 generations per 5 minutes
    "api": {"limit": 100, "window": 3600},      # 100 requests per hour
    "payment": {"limit": 10, "window": 300},     # 10 payment attempts per 5 minutes
    "email": {"limit": 3, "window": 300},        # 3 emails per 5 minutes
}

async def check_rate_limit(
    request: Request, 
    limit_key: str, 
    identifier: Optional[str] = None
):
    """Check rate limit and raise exception if exceeded"""
    if not redis_rate_limiter.redis_client:
        # Try to initialize if not already done
        await redis_rate_limiter.initialize()
    
    config = RATE_LIMITS.get(limit_key, {"limit": 100, "window": 3600})
    
    # Get identifier (IP address or custom)
    if not identifier:
        identifier = get_remote_address(request)
    
    is_allowed, rate_info = await redis_rate_limiter.is_allowed(
        key=limit_key,
        limit=config["limit"],
        window=config["window"],
        identifier=identifier
    )
    
    if not is_allowed:
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset"]),
            "Retry-After": str(rate_info["reset"] - int(time.time()))
        }
        
        sentry_manager.add_tag("rate_limit_exceeded", limit_key)
        sentry_manager.add_extra("rate_limit_info", rate_info)
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {limit_key}. Try again later.",
            headers=headers
        )
    
    # Add rate limit headers to response (will be handled by middleware)
    request.state.rate_limit_info = rate_info

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to add rate limit headers to responses"""
    response = await call_next(request)
    
    # Add rate limit headers if available
    if hasattr(request.state, 'rate_limit_info'):
        rate_info = request.state.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
    
    return response

# Initialize rate limiter
async def initialize_rate_limiter():
    """Initialize the Redis rate limiter"""
    await redis_rate_limiter.initialize()
