# File: ./backend/app/external/coingecko.py
# Simple CoinGecko API client without problematic dependencies

import httpx
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging

from app.core.rate_limiter import rate_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)


class CoinGeckoAPIError(Exception):
    """Custom exception for CoinGecko API errors"""
    pass


class CoinGeckoRateLimitError(CoinGeckoAPIError):
    """Exception for rate limit errors"""
    pass


class CoinGeckoClient:
    """
    Simple CoinGecko API client for cryptocurrency data
    
    Features:
    - Rate limiting integration
    - Simple retry logic
    - Circuit breaker pattern
    - Data validation
    - Error handling and logging
    
    Free API Limits:
    - 50 calls/minute
    - No API key required for basic endpoints
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.coingecko.com/api/v3"):
        """
        Initialize CoinGecko client
        
        Args:
            api_key: Optional API key for higher rate limits
            base_url: CoinGecko API base URL
        """
        self.api_key = api_key or getattr(settings, 'COINGECKO_API_KEY', None)
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
        
        # Default headers
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "CryptoPredict-MVP/1.0"
        }
        
        # Add API key if available
        if self.api_key:
            self.headers["x-cg-demo-api-key"] = self.api_key
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(30.0),  # 30 second timeout
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self.session
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        validate_response: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request to CoinGecko API with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            validate_response: Whether to validate response format
            max_retries: Maximum number of retries
            
        Returns:
            dict: API response data
            
        Raises:
            CoinGeckoAPIError: For API errors
            CoinGeckoRateLimitError: For rate limit errors
        """
        # Check circuit breaker
        if not await rate_limiter.check_circuit_breaker("coingecko"):
            raise CoinGeckoAPIError("CoinGecko API is temporarily unavailable (circuit breaker open)")
        
        # Wait for rate limit
        await rate_limiter.wait_for_rate_limit("coingecko")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making request to CoinGecko (attempt {attempt + 1}): {url}")
                
                response = await session.get(url, params=params or {})
                
                # Handle rate limiting
                if response.status_code == 429:
                    await rate_limiter.record_api_failure("coingecko")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise CoinGeckoRateLimitError("Rate limit exceeded")
                
                # Handle other HTTP errors
                if response.status_code >= 400:
                    await rate_limiter.record_api_failure("coingecko")
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"CoinGecko API error: {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise CoinGeckoAPIError(error_msg)
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    await rate_limiter.record_api_failure("coingecko")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise CoinGeckoAPIError(f"Invalid JSON response: {e}")
                
                # Basic response validation
                if validate_response and not isinstance(data, (dict, list)):
                    await rate_limiter.record_api_failure("coingecko")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise CoinGeckoAPIError("Invalid response format")
                
                # Record successful API call
                await rate_limiter.record_api_success("coingecko")
                
                logger.debug(f"CoinGecko request successful: {url}")
                return data
                
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("coingecko")
                    raise CoinGeckoAPIError("Request timeout after all retries")
                    
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("coingecko")
                    raise CoinGeckoAPIError(f"Request failed after all retries: {e}")
        
        # Should not reach here
        raise CoinGeckoAPIError("Request failed after all retries")
    
    async def get_current_prices(
        self, 
        crypto_ids: List[str], 
        vs_currencies: List[str] = ["usd"],
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Get current prices for cryptocurrencies
        
        Args:
            crypto_ids: List of CoinGecko cryptocurrency IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currencies: List of vs currencies (default: ['usd'])
            include_market_cap: Include market cap data
            include_24hr_vol: Include 24h volume data  
            include_24hr_change: Include 24h change data
            
        Returns:
            dict: Price data in format {crypto_id: {currency: price, ...}}
            
        Example:
            prices = await client.get_current_prices(['bitcoin'])
            # Returns: {'bitcoin': {'usd': 50000.0, 'usd_market_cap': 1000000000, ...}}
        """
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24hr_vol).lower(),
            "include_24hr_change": str(include_24hr_change).lower(),
            "precision": "8"  # 8 decimal places
        }
        
        data = await self._make_request("simple/price", params)
        
        # Validate response structure
        if not isinstance(data, dict):
            raise CoinGeckoAPIError("Invalid price data format")
        
        # Ensure all requested cryptos are in response
        missing_cryptos = set(crypto_ids) - set(data.keys())
        if missing_cryptos:
            logger.warning(f"Missing price data for: {missing_cryptos}")
        
        return data
    
    async def get_historical_data(
        self,
        crypto_id: str,
        vs_currency: str = "usd",
        days: int = 30,
        interval: str = "daily"
    ) -> Dict[str, List[List[float]]]:
        """
        Get historical price data for a cryptocurrency
        
        Args:
            crypto_id: CoinGecko cryptocurrency ID (e.g., 'bitcoin')
            vs_currency: VS currency (default: 'usd')
            days: Number of days back (1-365, or 'max' for all data)
            interval: Data interval ('daily' for >90 days, 'hourly' for <=90 days)
            
        Returns:
            dict: Historical data with prices, market_caps, total_volumes
            
        Example:
            data = await client.get_historical_data('bitcoin', days=7)
            # Returns: {'prices': [[timestamp, price], ...], 'market_caps': [...], 'total_volumes': [...]}
        """
        # Validate parameters
        if days < 1 or days > 365:
            raise ValueError("Days must be between 1 and 365")
        
        params = {
            "vs_currency": vs_currency,
            "days": str(days),
            "interval": interval
        }
        
        endpoint = f"coins/{crypto_id}/market_chart"
        data = await self._make_request(endpoint, params)
        
        # Validate response structure
        required_keys = ["prices", "market_caps", "total_volumes"]
        if not all(key in data for key in required_keys):
            raise CoinGeckoAPIError(f"Invalid historical data format. Expected keys: {required_keys}")
        
        # Validate data types
        for key in required_keys:
            if not isinstance(data[key], list):
                raise CoinGeckoAPIError(f"Invalid {key} data format")
        
        return data
    
    async def search_cryptocurrencies(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies by name or symbol
        
        Args:
            query: Search query (name or symbol)
            
        Returns:
            list: List of matching cryptocurrencies
            
        Example:
            results = await client.search_cryptocurrencies('bitcoin')
            # Returns: [{'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', ...}, ...]
        """
        if not query or len(query.strip()) < 2:
            raise ValueError("Query must be at least 2 characters long")
        
        params = {"query": query.strip()}
        
        data = await self._make_request("search", params)
        
        # Extract coins from search results
        coins = data.get("coins", [])
        
        if not isinstance(coins, list):
            raise CoinGeckoAPIError("Invalid search results format")
        
        return coins
    
    async def ping(self) -> bool:
        """
        Test API connectivity
        
        Returns:
            bool: True if API is reachable, False otherwise
        """
        try:
            data = await self._make_request("ping", validate_response=False)
            return data.get("gecko_says") == "(V3) To the Moon!"
        except Exception as e:
            logger.error(f"CoinGecko ping failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Utility functions for data conversion and validation

def coingecko_id_to_symbol(coingecko_id: str) -> str:
    """
    Convert CoinGecko ID to common symbol
    
    Args:
        coingecko_id: CoinGecko cryptocurrency ID
        
    Returns:
        str: Common symbol (e.g., 'bitcoin' -> 'BTC')
    """
    # Common mappings
    id_to_symbol = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "binancecoin": "BNB",
        "cardano": "ADA",
        "solana": "SOL",
        "polkadot": "DOT",
        "dogecoin": "DOGE",
        "avalanche-2": "AVAX",
        "chainlink": "LINK",
        "polygon": "MATIC"
    }
    
    return id_to_symbol.get(coingecko_id, coingecko_id.upper())


def symbol_to_coingecko_id(symbol: str) -> str:
    """
    Convert symbol to CoinGecko ID
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC')
        
    Returns:
        str: CoinGecko ID (e.g., 'BTC' -> 'bitcoin')
    """
    # Common mappings
    symbol_to_id = {
        "BTC": "bitcoin",
        "ETH": "ethereum", 
        "BNB": "binancecoin",
        "ADA": "cardano",
        "SOL": "solana",
        "DOT": "polkadot",
        "DOGE": "dogecoin",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "MATIC": "polygon"
    }
    
    return symbol_to_id.get(symbol.upper(), symbol.lower())


def validate_price_data(data: Dict[str, Any]) -> bool:
    """
    Validate price data from CoinGecko API
    
    Args:
        data: Price data from API
        
    Returns:
        bool: True if data is valid
    """
    if not isinstance(data, dict):
        return False
    
    # Check for required price fields
    for crypto_id, price_data in data.items():
        if not isinstance(price_data, dict):
            return False
        
        # Must have at least USD price
        if "usd" not in price_data:
            return False
        
        # Price must be a positive number
        usd_price = price_data["usd"]
        if not isinstance(usd_price, (int, float)) or usd_price <= 0:
            return False
    
    return True


def validate_historical_data(data: Dict[str, List]) -> bool:
    """
    Validate historical data from CoinGecko API
    
    Args:
        data: Historical data from API
        
    Returns:
        bool: True if data is valid
    """
    required_keys = ["prices", "market_caps", "total_volumes"]
    
    # Check required keys
    if not all(key in data for key in required_keys):
        return False
    
    # Check data format
    for key in required_keys:
        if not isinstance(data[key], list):
            return False
        
        # Check each data point [timestamp, value]
        for item in data[key]:
            if not isinstance(item, list) or len(item) != 2:
                return False
            
            timestamp, value = item
            if not isinstance(timestamp, (int, float)) or not isinstance(value, (int, float)):
                return False
            
            if value < 0:  # Values shouldn't be negative
                return False
    
    return True