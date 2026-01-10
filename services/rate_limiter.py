# services/rate_limiter.py
import asyncio
import time
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self, 
        requests_per_minute: int,
        burst_size: Optional[int] = None
    ):
        self.rpm = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.tokens = self.burst_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        # Track request timestamps for logging
        self.requests = deque(maxlen=100)
        
    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            await self._refill_tokens()
            
            while self.tokens < 1:
                # Wait until we have a token
                wait_time = (1 / self.rpm) * 60
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                await self._refill_tokens()
            
            self.tokens -= 1
            self.requests.append(time.time())
            
    async def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on time elapsed
        new_tokens = (elapsed / 60) * self.rpm
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now
        
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        now = time.time()
        recent_requests = [r for r in self.requests if now - r < 60]
        
        return {
            "available_tokens": self.tokens,
            "requests_last_minute": len(recent_requests),
            "rpm_limit": self.rpm,
        }

class PlatformRateLimiter:
    """Manages rate limiters for different platforms."""
    
    def __init__(self, settings):
        self.limiters = {
            "indeed": RateLimiter(settings.INDEED_RATE_LIMIT),
            "linkedin": RateLimiter(settings.LINKEDIN_RATE_LIMIT),
            "glassdoor": RateLimiter(settings.GLASSDOOR_RATE_LIMIT),
        }
        
    async def acquire(self, platform: str) -> None:
        """Acquire rate limit token for platform."""
        limiter = self.limiters.get(platform)
        if not limiter:
            raise ValueError(f"Unknown platform: {platform}")
        await limiter.acquire()
        
    def get_stats(self) -> dict:
        """Get stats for all platforms."""
        return {
            platform: limiter.get_stats() 
            for platform, limiter in self.limiters.items()
        }