# File: ./backend/app/external/binance.py
# Simple Binance API client for OHLCV data

import httpx
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timedelta, timezone


from app.core.rate_limiter import rate_limiter
from app.core.config import settings
from app.external.ohlcv_utils import convert_ohlcv_to_standardized
from app.utils.datetime_utils import normalize_candle_time

import pandas as pd

logger = logging.getLogger(__name__)


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors"""
    pass


class BinanceRateLimitError(BinanceAPIError):
    """Exception for rate limit errors"""
    pass


class BinanceClient:
    """
    Simple Binance API client for cryptocurrency OHLCV data
    
    Features:
    - Rate limiting integration
    - Simple retry logic
    - Circuit breaker pattern
    - Data validation
    - Error handling and logging
    
    Binance API Limits:
    - 1200 requests per minute
    - No API key required for public endpoints like klines
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.binance.com"):
        """
        Initialize Binance client
        
        Args:
            api_key: Optional API key (not needed for public endpoints)
            base_url: Binance API base URL
        """
        self.api_key = api_key or getattr(settings, 'BINANCE_API_KEY', None)
        self.base_url = base_url.rstrip("/")
        self.session: Optional[httpx.AsyncClient] = None
        
        # Default headers
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "CryptoPredict-BinanceClient/1.0"
        }
        
        # Add API key if available (for authenticated endpoints)
        if self.api_key:
            self.headers["X-MBX-APIKEY"] = self.api_key
    
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
    ) -> Any:
        """
        Make HTTP request to Binance API with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            validate_response: Whether to validate response format
            max_retries: Maximum number of retries
            
        Returns:
            API response data (list or dict)
            
        Raises:
            BinanceAPIError: For API errors
            BinanceRateLimitError: For rate limit errors
        """
        # Check circuit breaker
        if not await rate_limiter.check_circuit_breaker("binance"):
            raise BinanceAPIError("Binance API is temporarily unavailable (circuit breaker open)")
        
        # Wait for rate limit
        await rate_limiter.wait_for_rate_limit("binance")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making request to Binance (attempt {attempt + 1}): {url}")
                
                response = await session.get(url, params=params or {})
                
                # Handle rate limiting
                if response.status_code == 429:
                    await rate_limiter.record_api_failure("binance")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Binance rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise BinanceRateLimitError("Rate limit exceeded")
                
                # Handle other HTTP errors
                if response.status_code >= 400:
                    await rate_limiter.record_api_failure("binance")
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Binance API error: {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise BinanceAPIError(error_msg)
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    await rate_limiter.record_api_failure("binance")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise BinanceAPIError(f"Invalid JSON response: {e}")
                
                # Basic response validation
                if validate_response and not isinstance(data, (dict, list)):
                    await rate_limiter.record_api_failure("binance")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise BinanceAPIError("Invalid response format")
                
                # Record successful API call
                await rate_limiter.record_api_success("binance")
                
                logger.debug(f"Binance request successful: {url}")
                return data
                
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("binance")
                    raise BinanceAPIError("Request timeout after all retries")
                    
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("binance")
                    raise BinanceAPIError(f"Request failed after all retries: {e}")
        
        # Should not reach here
        raise BinanceAPIError("Request failed after all retries")
    
    async def get_price_data_by_timeframe(
        self,
        asset_id: int,
        crypto_id: str,
        timeframe: str = "1d",
        days: int = 100,
        vs_currency: str = "usd"
    ) -> Dict[str, List[List[float]]]:
        """
        Get price data with timeframe support optimized for our price_data_service
        
        Args:
            assset_id: int,
            crypto_id: Binance cryptocurrency ID 
            timeframe: Our timeframe format ('1h', '1d')
            days: Number of days to look back for price data
            vs_currency: VS currency (default: 'usd')
            
        Returns:
            dict: Market data
            
        Example:
            # Get last 24 1-hourly data points
            data = await client.get_price_data_by_timeframe('bitcoin', '1h', 24)
        """
        
        # Fetch market chart data (CoinGecko auto-selects interval based on days)
        data = await self._get_ohlcv(
            asset_id=asset_id,
            symbol=crypto_id,
            limit=days,
            interval=timeframe
        )
        
        return data


    async def _get_ohlcv(
        self,
        asset_id: int,
        symbol: str = 'BTCUSDT',
        interval: str = '1h',
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
    
        """
        Get OHLCV data (klines) from Binance
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDT')
            interval: Time interval ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M')
            limit: Number of candles (max 1000)
            start_time: Start time in milliseconds (optional)
            end_time: End time in milliseconds (optional)
            
        Returns:
            List of OHLCV dictionaries with keys:
            - timestamp: datetime object (UTC)
            - open: float
            - high: float  
            - low: float
            - close: float
            - volume: float
            - close_time: datetime object (UTC)
            - quote_volume: float
            - trades: int
            - taker_buy_base_volume: float
            - taker_buy_quote_volume: float
            
        Example:
            ohlcv = await client.get_price_data_by_timeframe('BTCUSDT', '1d', 30)
            for candle in ohlcv[:3]:
                print(f"{candle['timestamp']}: O:{candle['open']}, H:{candle['high']}, "
                      f"L:{candle['low']}, C:{candle['close']}, V:{candle['volume']}")
        """
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        
        valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")
        
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        data = await self._make_request("api/v3/klines", params)
        
        # Validate response structure
        if not isinstance(data, list):
            raise BinanceAPIError("Invalid klines data format - expected list")
        
        # Convert raw data to structured format
        binance_ohlcv = []
        for candle in data:
            if not isinstance(candle, list) or len(candle) < 6:
                logger.warning(f"Invalid candle format: {candle}")
                continue
            
            try:
                binance_ohlcv.append({
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'close_time': datetime.fromtimestamp(candle[6] / 1000, tz=timezone.utc) if len(candle) > 6 else None,
                    'quote_volume': float(candle[7]) if len(candle) > 7 else None,
                    'trades': int(candle[8]) if len(candle) > 8 else None,
                    'taker_buy_base_volume': float(candle[9]) if len(candle) > 9 else None,
                    'taker_buy_quote_volume': float(candle[10]) if len(candle) > 10 else None,
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing candle data: {e}")
                continue

            print(datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc))

        logger.info(f"Retrieved {len(binance_ohlcv)} OHLCV candles for {symbol} ({interval})")
        print(f"binance_ohlcv: {binance_ohlcv}")
        # Delegate conversion to shared utility for robustness across sources
        return convert_ohlcv_to_standardized(asset_id, interval, binance_ohlcv)

   
    async def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get exchange information and trading rules
        
        Args:
            symbol: Optional symbol to get info for specific pair
            
        Returns:
            Exchange information dictionary
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        data = await self._make_request("api/v3/exchangeInfo", params)
        
        if not isinstance(data, dict):
            raise BinanceAPIError("Invalid exchange info format")
        
        return data
    
    async def get_24hr_ticker(self, symbol: Optional[str] = None) -> Any:
        """
        Get 24hr ticker price change statistics
        
        Args:
            symbol: Optional symbol (if None, returns all symbols)
            
        Returns:
            Ticker data (dict for single symbol, list for all symbols)
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        data = await self._make_request("api/v3/ticker/24hr", params)
        return data
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None

    async def get_funding_rate_history(self, symbol='BTCUSDT', days=365):
        
        # Calculate start time (for example: one year ago)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        start_timestamp = int(start_time.timestamp() * 1000)
        
        all_data = []
        current_start = start_timestamp
              
        while True:
            params = {
                'symbol': symbol,
                'startTime': current_start,
                'limit': 1000  # Maximum
            }
            
            try:
                data = await self._make_request("fapi/v1/fundingRate", params)
                
                if not data:
                    break
                
                all_data.extend(data)

                # Last time for the next request
                last_time = data[-1]['fundingTime']
                current_start = last_time + 1
                
                # If we reached the current time, stop
                if last_time >= int(end_time.timestamp() * 1000):
                    break
                
                # Delay to avoid Rate Limit
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error: {e}")
                break
        
        interval = "1d"
        for item in all_data:
            try:
                ts = item.get('fundingTime') if isinstance(item, dict) else None
                funding_time = float(item.get('fundingRate'))
                fundingRate_percent = float(item.get('fundingRate')) * 100  # Convert to percent
                
            except Exception as e:
                logger.warning(f"Skipping funding rate item due to conversion error: {e}")
                continue                


        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms',utc=True)
        df['fundingRate'] = df['fundingRate'].astype(float)
        df['fundingRate_percent'] = df['fundingRate'] * 100  # Convert to percent
        
        # Sort by time
        df = df.sort_values('fundingTime').reset_index(drop=True)
        
        return df


