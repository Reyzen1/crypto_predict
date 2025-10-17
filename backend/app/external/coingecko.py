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
        Get historical price data for a cryptocurrency (hourly-normalized)
        
        This is a wrapper around get_market_chart for backward compatibility.
        New code should use get_market_chart directly.
        
        Note: All data returned is hourly-normalized regardless of the interval parameter.
        
        Args:
            crypto_id: CoinGecko cryptocurrency ID (e.g., 'bitcoin')
            vs_currency: VS currency (default: 'usd')
            days: Number of days back (1-365)
            interval: Data interval ('daily', 'hourly') - note: output is always hourly-normalized
            
        Returns:
            dict: Historical data with hourly-normalized timestamps
            
        Example:
            data = await client.get_historical_data('bitcoin', days=7)
            # Returns: {'prices': [[hourly_timestamp, price], ...], 'market_caps': [...], 'total_volumes': [...]}
        """
        return await self.get_market_chart(
            crypto_id=crypto_id,
            vs_currency=vs_currency,
            days=days,
            interval=interval
        )
    
    async def get_market_chart(
        self,
        crypto_id: str,
        vs_currency: str = "usd",
        days: int = 30,
        interval: str = "daily"
    ) -> Dict[str, List[List[float]]]:
        """
        Get market chart data for a cryptocurrency (prices, market_caps, total_volumes)
        
        This is the core method that both get_historical_data and price_data_service use.
        All returned data is automatically normalized to hourly boundaries for consistency.
        
        Args:
            crypto_id: CoinGecko cryptocurrency ID (e.g., 'bitcoin')
            vs_currency: VS currency (default: 'usd')
            days: Number of days back (1-365 for free tier)
            interval: Data interval ('daily' for >90 days, 'hourly' for <=90 days, 'minutely' for <=1 day)
            
        Returns:
            dict: Market chart data with hourly-normalized timestamps
            Format: {
                'prices': [[hourly_timestamp_ms, price], ...],
                'market_caps': [[hourly_timestamp_ms, market_cap], ...], 
                'total_volumes': [[hourly_timestamp_ms, volume], ...]
            }
            
        Note:
            All timestamps are aligned to hourly boundaries (00:00, 01:00, 02:00, etc.)
            This ensures consistent behavior across all timeframe operations.
            
        Example:
            data = await client.get_market_chart('bitcoin', days=7, interval='hourly')
            # All timestamps will be aligned to exact hours
        """
        # Validate parameters
        if days < 1:
            raise ValueError("Days must be at least 1")
        
        if days > 365:
            logger.warning(f"Days ({days}) > 365 may not work with free tier")
        
        # Auto-select interval based on days if not specified appropriately
        if days <= 1 and interval == "daily":
            interval = "hourly"
            logger.info(f"Auto-switched to hourly interval for {days} day(s)")
        elif days > 90 and interval in ["hourly", "minutely"]:
            interval = "daily" 
            logger.info(f"Auto-switched to daily interval for {days} day(s)")
        
        params = {
            "vs_currency": vs_currency,
            "days": str(days)
        }
        
        # Add interval parameter (CoinGecko auto-selects if not provided)
        if interval in ["hourly", "daily"]:
            params["interval"] = interval
        
        endpoint = f"coins/{crypto_id}/market_chart"
        data = await self._make_request(endpoint, params)
        
        # Validate response structure
        required_keys = ["prices", "market_caps", "total_volumes"]
        if not all(key in data for key in required_keys):
            raise CoinGeckoAPIError(f"Invalid market chart data format. Expected keys: {required_keys}")
        
        # Validate data types and content
        for key in required_keys:
            if not isinstance(data[key], list):
                raise CoinGeckoAPIError(f"Invalid {key} data format - expected list")
            
            # Check each data point format
            for i, item in enumerate(data[key][:5]):  # Check first 5 items
                if not isinstance(item, list) or len(item) != 2:
                    raise CoinGeckoAPIError(f"Invalid {key} item format at index {i} - expected [timestamp, value]")
                
                timestamp, value = item
                if not isinstance(timestamp, (int, float)) or not isinstance(value, (int, float)):
                    raise CoinGeckoAPIError(f"Invalid {key} data types at index {i}")
                
                if value < 0:
                    logger.warning(f"Negative {key} value at index {i}: {value}")
        
        # Normalize all data to hourly boundaries for consistency
        original_count = len(data['prices'])
        data['prices'] = normalize_data_to_hourly(data['prices'])
        data['market_caps'] = normalize_data_to_hourly(data['market_caps'])
        data['total_volumes'] = normalize_data_to_hourly(data['total_volumes'])
        normalized_count = len(data['prices'])
        
        logger.info(f"Retrieved market chart for {crypto_id}: {original_count} -> {normalized_count} hourly-normalized data points")
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

    async def get_price_data_by_timeframe(
        self,
        crypto_id: str,
        timeframe: str = "1d",
        limit: int = 100,
        vs_currency: str = "usd"
    ) -> Dict[str, List[List[float]]]:
        """
        Get price data with timeframe support optimized for our price_data_service
        
        Args:
            crypto_id: CoinGecko cryptocurrency ID 
            timeframe: Our timeframe format ('1h', '4h', '1d')
            limit: Maximum number of data points to return
            vs_currency: VS currency (default: 'usd')
            
        Returns:
            dict: Market data filtered by timeframe
            
        Example:
            # Get last 24 4-hourly data points
            data = await client.get_price_data_by_timeframe('bitcoin', '4h', 24)
        """
        # Calculate days needed
        days = calculate_days_for_timeframe(timeframe, limit)
        
        # Get CoinGecko interval - optimize for timeframe
        interval = timeframe_to_coingecko_interval(timeframe)
        
        # For 1d timeframe with small limits, use hourly to get more precision
        if timeframe == '1d' and limit <= 7:
            interval = 'hourly'
            days = max(days, 7)  # Get at least a week of hourly data
        
        # Fetch market chart data (already normalized to hourly in get_market_chart)
        data = await self.get_market_chart(
            crypto_id=crypto_id,
            vs_currency=vs_currency,
            days=days,
            interval=interval
        )
        
        # Apply timeframe filtering to the already-normalized hourly data
        normalized_count = len(data['prices'])
        data['prices'] = filter_data_by_timeframe(data['prices'], timeframe)
        data['market_caps'] = filter_data_by_timeframe(data['market_caps'], timeframe) 
        data['total_volumes'] = filter_data_by_timeframe(data['total_volumes'], timeframe)
        filtered_count = len(data['prices'])
        
        logger.info(f"Filtered to {timeframe}: {normalized_count} -> {filtered_count} points")
        
        # Limit the results to requested number of points
        for key in ['prices', 'market_caps', 'total_volumes']:
            if len(data[key]) > limit:
                data[key] = data[key][-limit:]  # Take the most recent data points
        
        return data


# Utility functions for data conversion and validation

def timeframe_to_coingecko_interval(timeframe: str) -> str:
    """
    Convert our timeframe format to CoinGecko interval format
    
    Args:
        timeframe: Our timeframe format ('1h', '4h', '1d')
        
    Returns:
        str: CoinGecko interval format ('hourly', 'daily')
        
    Note:
        - For '1h': Use 'hourly' directly
        - For '4h': Use 'hourly' and filter every 4th point
        - For '1d': Use 'daily' when possible, 'hourly' for small ranges
    """
    timeframe_mapping = {
        '1h': 'hourly',
        '4h': 'hourly',  # Get hourly and filter every 4th
        '1d': 'daily'    # Prefer daily, but may use hourly for small ranges
    }
    
    return timeframe_mapping.get(timeframe, 'daily')


def calculate_days_for_timeframe(timeframe: str, limit: int) -> int:
    """
    Calculate number of days to request based on timeframe and desired data points
    
    Args:
        timeframe: Our timeframe format ('1h', '4h', '1d')
        limit: Number of data points desired
        
    Returns:
        int: Number of days to request from CoinGecko
    """
    if timeframe == '1h':
        # 1 day = 24 hourly points
        return max(1, (limit + 23) // 24)  # Round up
    elif timeframe == '4h':
        # 1 day = 6 four-hourly points  
        return max(1, (limit + 5) // 6)  # Round up
    elif timeframe == '1d':
        # 1 day = 1 daily point
        return limit
    else:
        return limit


def filter_data_by_timeframe(data: List[List[float]], timeframe: str) -> List[List[float]]:
    """
    Filter hourly-normalized data to match the specified timeframe
    
    This is much simpler now that all data is guaranteed to be hourly-aligned.
    
    Args:
        data: Hourly-normalized data [[timestamp_ms, value], ...]
        timeframe: Target timeframe ('1h', '4h', '1d')
        
    Returns:
        List: Filtered data for the specified timeframe
    """
    if not data or timeframe == '1h':
        return data
    
    if timeframe == '4h':
        return filter_to_4hourly(data)
    elif timeframe == '1d':
        return filter_to_daily(data)
    else:
        return data  # Unknown timeframe


def filter_to_4hourly(data: List[List[float]]) -> List[List[float]]:
    """
    Filter hourly data to 4-hourly intervals (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
    
    Args:
        data: Hourly-normalized data
        
    Returns:
        List: 4-hourly filtered data
    """
    filtered_data = []
    
    for timestamp_ms, value in data:
        # Convert to datetime to check hour
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
        
        # Keep only timestamps at 4-hour boundaries
        if dt.hour % 4 == 0:
            filtered_data.append([timestamp_ms, value])
    
    return filtered_data


def filter_to_daily(data: List[List[float]]) -> List[List[float]]:
    """
    Filter hourly data to daily intervals (00:00 UTC)
    
    Args:
        data: Hourly-normalized data
        
    Returns:
        List: Daily filtered data
    """
    filtered_data = []
    
    for timestamp_ms, value in data:
        # Convert to datetime to check hour
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
        
        # Keep only timestamps at midnight (00:00 UTC)
        if dt.hour == 0:
            filtered_data.append([timestamp_ms, value])
    
    return filtered_data


def align_timestamp_to_4h(timestamp_ms: int) -> int:
    """
    Align timestamp to 4-hour boundaries (0:00, 4:00, 8:00, 12:00, 16:00, 20:00 UTC)
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        int: Aligned timestamp in milliseconds
    """
    import datetime
    
    # Convert to datetime
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
    
    # Align to 4-hour boundary
    aligned_hour = (dt.hour // 4) * 4
    aligned_dt = dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)
    
    # Convert back to milliseconds
    return int(aligned_dt.timestamp() * 1000)


def align_timestamp_to_daily(timestamp_ms: int) -> int:
    """
    Align timestamp to daily boundaries (00:00 UTC)
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        int: Aligned timestamp in milliseconds
    """
    import datetime
    
    # Convert to datetime
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
    
    # Align to daily boundary (00:00 UTC)
    aligned_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert back to milliseconds
    return int(aligned_dt.timestamp() * 1000)


def align_timestamp_to_hourly(timestamp_ms: int) -> int:
    """
    Align timestamp to hourly boundaries (nearest hour)
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        int: Aligned timestamp in milliseconds
    """
    import datetime
    
    # Convert to datetime
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
    
    # Round to nearest hour
    if dt.minute >= 30:
        # Round up to next hour
        aligned_dt = dt.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    else:
        # Round down to current hour
        aligned_dt = dt.replace(minute=0, second=0, microsecond=0)
    
    # Convert back to milliseconds
    return int(aligned_dt.timestamp() * 1000)


def normalize_data_to_hourly(data: List[List[float]]) -> List[List[float]]:
    """
    Normalize all data points to hourly boundaries
    
    This function aligns all timestamps to the nearest hour and removes duplicates.
    This makes subsequent filtering operations much simpler and more reliable.
    
    Args:
        data: Raw data [[timestamp_ms, value], ...]
        
    Returns:
        List: Normalized hourly data
    """
    if not data:
        return data
    
    # Align all timestamps to hourly boundaries
    normalized_data = []
    seen_timestamps = set()
    
    for timestamp_ms, value in data:
        aligned_timestamp = align_timestamp_to_hourly(timestamp_ms)
        
        # Avoid duplicate timestamps (keep first occurrence)
        if aligned_timestamp not in seen_timestamps:
            normalized_data.append([aligned_timestamp, value])
            seen_timestamps.add(aligned_timestamp)
    
    # Sort by timestamp to ensure chronological order
    normalized_data.sort(key=lambda x: x[0])
    
    return normalized_data


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