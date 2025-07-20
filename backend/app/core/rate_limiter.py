# File: ./backend/app/core/rate_limiter.py
# Simple rate limiter without aioredis to avoid conflicts

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int  # Maximum requests allowed
    time_window: int   # Time window in seconds
    retry_after: int   # Seconds to wait after hitting limit


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter for external API calls
    
    Features:
    - Per-API rate limiting
    - In-memory storage (no Redis dependency)
    - Circuit breaker pattern
    - Request counting and monitoring
    """
    
    def __init__(self):
        """Initialize simple rate limiter"""
        # In-memory storage for rate limiting
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}
        
        # Rate limit configurations for different APIs
        self.api_configs = {
            "coingecko": RateLimitConfig(
                max_requests=50,    # 50 requests per minute
                time_window=60,     # 60 seconds
                retry_after=60      # Wait 60 seconds after hitting limit
            ),
            "binance": RateLimitConfig(
                max_requests=1200,  # 1200 requests per minute
                time_window=60,     # 60 seconds  
                retry_after=60      # Wait 60 seconds after hitting limit
            )
        }
    
    def _get_rate_limit_key(self, api_name: str) -> str:
        """Generate key for rate limiting"""
        return f"rate_limit:{api_name}:{int(time.time() // 60)}"  # Per minute buckets
    
    def _clean_old_entries(self, api_name: str) -> None:
        """Clean old rate limit entries"""
        current_time = time.time()
        config = self.api_configs.get(api_name)
        if not config:
            return
        
        # Remove entries older than time window
        keys_to_remove = []
        for key in self.request_counts.keys():
            if key.startswith(f"rate_limit:{api_name}:"):
                timestamp = int(key.split(":")[-1]) * 60
                if current_time - timestamp > config.time_window:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]
    
    async def check_rate_limit(self, api_name: str) -> bool:
        """
        Check if API call is allowed within rate limits
        
        Args:
            api_name: Name of the API (e.g., 'coingecko')
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        config = self.api_configs.get(api_name)
        if not config:
            logger.warning(f"No rate limit config for API: {api_name}")
            return True
        
        try:
            # Clean old entries
            self._clean_old_entries(api_name)
            
            key = self._get_rate_limit_key(api_name)
            
            # Get current request count
            current_count = self.request_counts.get(key, {}).get("count", 0)
            
            # Check if within limits
            if current_count >= config.max_requests:
                logger.warning(
                    f"Rate limit exceeded for {api_name}: "
                    f"{current_count}/{config.max_requests}"
                )
                return False
            
            # Increment counter
            if key not in self.request_counts:
                self.request_counts[key] = {"count": 0, "timestamp": time.time()}
            
            self.request_counts[key]["count"] += 1
            
            logger.debug(
                f"Rate limit check passed for {api_name}: "
                f"{self.request_counts[key]['count']}/{config.max_requests}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {api_name}: {e}")
            # Allow request if check fails (fail open)
            return True
    
    async def wait_for_rate_limit(self, api_name: str) -> None:
        """
        Wait until rate limit allows the request
        
        Args:
            api_name: Name of the API
        """
        config = self.api_configs.get(api_name)
        if not config:
            return
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            if await self.check_rate_limit(api_name):
                return
            
            # Exponential backoff
            wait_time = min(config.retry_after * (2 ** retry_count), 300)  # Max 5 minutes
            logger.info(
                f"Rate limited for {api_name}. "
                f"Waiting {wait_time} seconds (attempt {retry_count + 1}/{max_retries})"
            )
            
            await asyncio.sleep(wait_time)
            retry_count += 1
        
        # If we reach here, we've exceeded max retries
        raise Exception(f"Rate limit exceeded for {api_name} after {max_retries} retries")
    
    async def check_circuit_breaker(self, api_name: str) -> bool:
        """
        Check circuit breaker state for API
        
        Args:
            api_name: Name of the API
            
        Returns:
            bool: True if API is available, False if circuit is open
        """
        try:
            circuit_state = self.circuit_breaker_state.get(api_name, {})
            
            # Check if circuit should be reset
            if circuit_state.get("state") == "open":
                timeout = circuit_state.get("timeout", 0)
                if time.time() > timeout:
                    # Reset circuit to half-open
                    circuit_state["state"] = "half-open"
                    self.circuit_breaker_state[api_name] = circuit_state
                    logger.info(f"Circuit breaker for {api_name} moved to half-open state")
                    return True
                else:
                    logger.warning(f"Circuit breaker open for {api_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Circuit breaker check failed for {api_name}: {e}")
            return True  # Fail open
    
    async def record_api_success(self, api_name: str) -> None:
        """
        Record successful API call
        
        Args:
            api_name: Name of the API
        """
        try:
            # Reset circuit breaker to closed state
            circuit_state = {
                "state": "closed",
                "failure_count": 0,
                "last_success": time.time()
            }
            
            self.circuit_breaker_state[api_name] = circuit_state
            
        except Exception as e:
            logger.error(f"Failed to record API success for {api_name}: {e}")
    
    async def record_api_failure(self, api_name: str) -> None:
        """
        Record failed API call and update circuit breaker
        
        Args:
            api_name: Name of the API
        """
        try:
            # Get current circuit state
            circuit_state = self.circuit_breaker_state.get(api_name, {
                "state": "closed",
                "failure_count": 0,
                "last_failure": 0
            })
            
            # Increment failure count
            circuit_state["failure_count"] = circuit_state.get("failure_count", 0) + 1
            circuit_state["last_failure"] = time.time()
            
            # Open circuit if too many failures
            if circuit_state["failure_count"] >= 5:  # Threshold: 5 failures
                circuit_state["state"] = "open"
                circuit_state["timeout"] = time.time() + 300  # Open for 5 minutes
                logger.warning(f"Circuit breaker opened for {api_name} due to failures")
            
            self.circuit_breaker_state[api_name] = circuit_state
            
        except Exception as e:
            logger.error(f"Failed to record API failure for {api_name}: {e}")
    
    async def get_api_stats(self, api_name: str) -> Dict[str, Any]:
        """
        Get rate limiting and circuit breaker stats for API
        
        Args:
            api_name: Name of the API
            
        Returns:
            dict: API statistics
        """
        try:
            # Rate limit stats
            key = self._get_rate_limit_key(api_name)
            current_requests = self.request_counts.get(key, {}).get("count", 0)
            
            # Circuit breaker stats
            circuit_state = self.circuit_breaker_state.get(api_name, {})
            
            config = self.api_configs.get(api_name, RateLimitConfig(0, 0, 0))
            
            return {
                "api_name": api_name,
                "rate_limit": {
                    "current_requests": current_requests,
                    "max_requests": config.max_requests,
                    "time_window": config.time_window,
                    "requests_remaining": max(0, config.max_requests - current_requests)
                },
                "circuit_breaker": {
                    "state": circuit_state.get("state", "closed"),
                    "failure_count": circuit_state.get("failure_count", 0),
                    "last_failure": circuit_state.get("last_failure"),
                    "last_success": circuit_state.get("last_success")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get API stats for {api_name}: {e}")
            return {"error": str(e)}


# Global rate limiter instance
rate_limiter = SimpleRateLimiter()