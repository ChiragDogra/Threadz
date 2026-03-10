"""
Simple rate limiting implementation for Threadz API
"""
import time
from typing import Dict, Optional
from fastapi import HTTPException, Request
from collections import defaultdict, deque

class SimpleRateLimiter:
    def __init__(self):
        # Store request timestamps per IP
        self.requests: Dict[str, deque] = defaultdict(deque)
        
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if a request is allowed based on rate limit
        
        Args:
            key: Identifier (usually IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
        """
        now = time.time()
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] <= now - window:
            self.requests[key].popleft()
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False

# Global rate limiter instance
rate_limiter = SimpleRateLimiter()

def check_rate_limit(request: Request, limit: int = 100, window: int = 60):
    """
    Rate limiting middleware function
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip, limit, window):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
