# File: ./backend/app/external/tradingview.py
# TradingView API client for OHLCV data and Market Dominance

import httpx
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timezone

from app.core.rate_limiter import rate_limiter
from app.core.config import settings
from app.utils.datetime_utils import normalize_candle_time

logger = logging.getLogger(__name__)


class TradingViewAPIError(Exception):
    """Custom exception for TradingView API errors"""
    pass


class TradingViewRateLimitError(TradingViewAPIError):
    """Exception for rate limit errors"""
    pass


class TradingViewClient:
    """
    TradingView API client for cryptocurrency OHLCV data and Market Dominance
    
    Features:
    - Rate limiting integration
    - Simple retry logic
    - Circuit breaker pattern
    - Data validation
    - Error handling and logging
    - Market dominance from CRYPTOCAP symbols
    
    TradingView API Endpoints:
    - Chart data: https://chartdata1.tradingview.com/
    - Symbol search: https://symbol-search.tradingview.com/
    - Scanner: https://scanner.tradingview.com/
    """
    
    def __init__(self, base_url: str = "https://chartdata1.tradingview.com"):
        """
        Initialize TradingView client
        
        Args:
            base_url: TradingView chart data API base URL
        """
        self.base_url = base_url.rstrip("/")
        self.session: Optional[httpx.AsyncClient] = None
        
        # Default headers to mimic browser requests
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Symbol mappings for crypto pairs
        self.symbol_mappings = {
            'bitcoin': 'BTCUSD',
            'ethereum': 'ETHUSD',
            'binancecoin': 'BNBUSD',
            'solana': 'SOLUSD',
            'cardano': 'ADAUSD',
            'dogecoin': 'DOGEUSD',
            'polkadot': 'DOTUSD',
            'polygon': 'MATICUSD',
            'chainlink': 'LINKUSD',
            'litecoin': 'LTCUSD'
        }
        
        # Market dominance symbols
        self.dominance_symbols = {
            'btc_dominance': 'CRYPTOCAP:BTC.D',
            'eth_dominance': 'CRYPTOCAP:ETH.D', 
            'total_market_cap': 'CRYPTOCAP:TOTAL',
            'total_market_cap_ex_btc': 'CRYPTOCAP:TOTAL2',
            'altcoin_dominance': 'CRYPTOCAP:OTHERS.D'
        }
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(30.0),  # 30 second timeout
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self.session
    
    def _map_crypto_id_to_symbol(self, crypto_id: str) -> str:
        """
        Map CoinGecko-style crypto ID to TradingView symbol
        
        Args:
            crypto_id: CoinGecko crypto ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            TradingView symbol (e.g., 'BTCUSD', 'ETHUSD')
        """
        # If the caller already supplied a full TradingView symbol (contains a
        # namespace like 'CRYPTOCAP:' or exchange prefix like 'BINANCE:'), return
        # it as-is (uppercase) so we don't accidentally append 'USD'.
        if crypto_id is None:
            raise ValueError("crypto_id cannot be None")

        cid = str(crypto_id).strip()
        if ':' in cid:
            # Already a fully-qualified TradingView symbol, return unchanged
            return cid.upper()

        # Try direct mapping first (CoinGecko id -> TradingView short symbol)
        if cid.lower() in self.symbol_mappings:
            return self.symbol_mappings[cid.lower()]

        # Try to construct symbol from common patterns
        up = cid.upper()
        if up in ['BTC', 'BITCOIN']:
            return 'BTCUSD'
        elif up in ['ETH', 'ETHEREUM']:
            return 'ETHUSD'
        elif up in ['BNB', 'BINANCECOIN']:
            return 'BNBUSD'

        # Default: try to use the ID directly + USD
        return f"{up}USD"
    
    def _map_timeframe_to_resolution(self, timeframe: str) -> str:
        """
        Map our timeframe format to TradingView resolution
        
        Args:
            timeframe: Our format ('1h', '1d', '1w')
            
        Returns:
            TradingView resolution ('60', 'D', 'W')
        """
        timeframe_map = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '4h': '240',
            '1d': 'D',
            '1w': 'W',
            '1M': 'M'
        }
        
        return timeframe_map.get(timeframe, 'D')  # Default to daily
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        validate_response: bool = True,
        max_retries: int = 3
    ) -> Any:
        """
        Make HTTP request to TradingView API with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            validate_response: Whether to validate response format
            max_retries: Maximum number of retries
            
        Returns:
            API response data (dict)
            
        Raises:
            TradingViewAPIError: For API errors
            TradingViewRateLimitError: For rate limit errors
        """
        print(f"Making request to TradingView API: {endpoint}, {params}")
        # Check circuit breaker
        if not await rate_limiter.check_circuit_breaker("tradingview"):
            raise TradingViewAPIError("TradingView API is temporarily unavailable (circuit breaker open)")
        
        # Wait for rate limit
        await rate_limiter.wait_for_rate_limit("tradingview")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making request to TradingView (attempt {attempt + 1}): {url}")
                
                response = await session.get(url, params=params or {})
                
                # Handle rate limiting
                if response.status_code == 429:
                    await rate_limiter.record_api_failure("tradingview")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"TradingView rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise TradingViewRateLimitError("Rate limit exceeded")
                
                # Handle other HTTP errors
                if response.status_code >= 400:
                    await rate_limiter.record_api_failure("tradingview")
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"TradingView API error: {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise TradingViewAPIError(error_msg)
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    await rate_limiter.record_api_failure("tradingview")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise TradingViewAPIError(f"Invalid JSON response: {e}")
                
                # Basic response validation
                if validate_response and not isinstance(data, dict):
                    await rate_limiter.record_api_failure("tradingview")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise TradingViewAPIError("Invalid response format")
                
                # Record successful API call
                await rate_limiter.record_api_success("tradingview")
                
                logger.debug(f"TradingView request successful: {url}")
                return data
                
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("tradingview")
                    raise TradingViewAPIError("Request timeout after all retries")
                    
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("tradingview")
                    raise TradingViewAPIError(f"Request failed after all retries: {e}")
        
        # Should not reach here
        raise TradingViewAPIError("Request failed after all retries")
    
    async def get_price_data_by_timeframe(
        self,
        asset_id: int,
        crypto_id: str,
        timeframe: str = "1d",
        days: int = 100,
        vs_currency: str = "usd"
    ) -> List[Dict[str, Any]]:
        """
        Get price data with timeframe support optimized for our price_data_service
        
        Args:
            asset_id: Asset ID from our database
            crypto_id: Cryptocurrency ID (CoinGecko format)
            timeframe: Our timeframe format ('1h', '1d')
            days: Number of days to look back for price data
            vs_currency: VS currency (default: 'usd')
            
        Returns:
            List of standardized OHLCV records
            
        Example:
            # Get last 24 1-hourly data points
            data = await client.get_price_data_by_timeframe(1, 'bitcoin', '1h', 24)
        """
        
        # Fetch OHLCV data from TradingView
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
        symbol: str = 'bitcoin',
        interval: str = '1d',
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV data from TradingView
        
        Args:
            asset_id: Asset ID from our database
            symbol: Crypto symbol (CoinGecko format)
            interval: Time interval ('1h', '1d', '1w')
            limit: Number of candles (max ~5000)
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            
        Returns:
            List of standardized OHLCV dictionaries
            
        Example:
            ohlcv = await client._get_ohlcv(1, 'bitcoin', '1d', 30)
        """
        # Validate parameters
        if limit < 1 or limit > 5000:
            raise ValueError("Limit must be between 1 and 5000")
        
        # Map symbol to TradingView format
        tv_symbol = symbol #self._map_crypto_id_to_symbol(symbol)
        
        # Map timeframe to TradingView resolution
        resolution = self._map_timeframe_to_resolution(interval)
        
        # Calculate time range
        if not end_time:
            end_time = int(datetime.now().timestamp())
        if not start_time:
            start_time = end_time - (limit * self._get_interval_seconds(interval))
        
        params = {
            'symbol': tv_symbol,
            'resolution': resolution,
            'from': start_time,
            'to': end_time,
            'countback': limit
        }
        
        try:
            data = await self._make_request("get", params)
            
            # Check for API errors
            if data.get('s') != 'ok':
                error_msg = data.get('errmsg', 'Unknown error')
                logger.warning(f"TradingView API returned error: {error_msg}")
                return []
            
            # Extract OHLCV data
            times = data.get('t', [])
            opens = data.get('o', [])
            highs = data.get('h', [])
            lows = data.get('l', [])
            closes = data.get('c', [])
            volumes = data.get('v', [])
            
            # Validate data consistency
            data_lengths = [len(times), len(opens), len(highs), len(lows), len(closes)]
            if not all(length == data_lengths[0] for length in data_lengths):
                logger.warning(f"Inconsistent data lengths: {data_lengths}")
                min_length = min(data_lengths)
                times = times[:min_length]
                opens = opens[:min_length]
                highs = highs[:min_length]
                lows = lows[:min_length]
                closes = closes[:min_length]
                volumes = volumes[:min_length] if volumes else [0] * min_length
            
            # Convert to structured format
            tradingview_ohlcv = []
            for i in range(len(times)):
                try:
                    tradingview_ohlcv.append({
                        'timestamp': datetime.fromtimestamp(times[i], tz=timezone.utc),
                        'open': float(opens[i]),
                        'high': float(highs[i]),
                        'low': float(lows[i]),
                        'close': float(closes[i]),
                        'volume': float(volumes[i]) if volumes and i < len(volumes) else 0.0,
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing TradingView candle data at index {i}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tradingview_ohlcv)} OHLCV candles for {tv_symbol} ({resolution})")
            
            # Convert to standardized format
            standardized_ohlcv = self._convert_tradingview_ohlcv_to_standardized_ohlcv(
                asset_id, interval, tradingview_ohlcv
            )
            
            return standardized_ohlcv
            
        except Exception as e:
            logger.error(f"Error fetching TradingView OHLCV data: {e}")
            return []
    
    def _get_interval_seconds(self, interval: str) -> int:
        """Get interval in seconds for time calculations"""
        interval_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
            '1w': 604800,
            '1M': 2592000  # ~30 days
        }
        return interval_map.get(interval, 86400)  # Default to 1 day
    
    def _convert_tradingview_ohlcv_to_standardized_ohlcv(
        self,
        asset_id: int,
        interval: str,
        raw_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert TradingView API data to standardized OHLCV format
        
        Args:
            asset_id: Asset ID from our database
            interval: Timeframe interval
            raw_data: Raw data from TradingView API
                Format: [{'timestamp': datetime, 'open': float, 'high': float, 'low': float, 
                        'close': float, 'volume': float}, ...]
        Returns:
            List of OHLCV records suitable for our price_data processing
                Format: [{'asset_id': int, 'timeframe': str, 'candle_time': datetime, 
                        'open_price': float, 'high_price': float, 'low_price': float, 
                        'close_price': float, 'volume': float, 'market_cap': None}, ...]
        """
        ohlcv_records = []
        
        try:
            if not raw_data or not isinstance(raw_data, list):
                logger.warning("Invalid raw_data format - expected non-empty list")
                return ohlcv_records
            
            for candle in raw_data:
                try:
                    # Validate required fields
                    required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    if not all(field in candle for field in required_fields):
                        logger.warning(f"Skipping invalid candle - missing fields: {candle}")
                        continue
                    
                    # Convert datetime to millisecond timestamp
                    if isinstance(candle['timestamp'], datetime):
                        timestamp_ms = int(candle['timestamp'].timestamp() * 1000)
                    else:
                        timestamp_ms = int(candle['timestamp'] * 1000)
                    
                    candle_time = normalize_candle_time(timestamp_ms, interval)
                    
                    # Create standardized OHLCV record
                    ohlcv_record = {
                        'asset_id': asset_id,
                        'timeframe': interval,
                        'candle_time': candle_time,
                        'open_price': float(candle['open']),
                        'high_price': float(candle['high']),
                        'low_price': float(candle['low']),
                        'close_price': float(candle['close']),
                        'volume': float(candle['volume']),
                        'market_cap': None,  # TradingView doesn't provide market cap in OHLCV
                        'is_validated': False  # Will be validated later
                    }
                    
                    ohlcv_records.append(ohlcv_record)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error processing TradingView candle {candle}: {e}")
                    continue
            
            logger.info(f"Successfully converted {len(ohlcv_records)} TradingView candles to OHLCV format")
            
        except Exception as e:
            logger.error(f"Error converting TradingView data to OHLCV format: {e}")
        
        return ohlcv_records
    
    # Market Dominance Methods
    async def get_market_dominance_history(self, days: int = 365) -> Dict[str, Any]:
        """
        Get historical market dominance data from TradingView
        This is REAL historical dominance data, not estimated!
        
        Args:
            days: Number of days to look back (max ~5000)
            
        Returns:
            Dict containing historical dominance data
            
        Example:
            dominance = await client.get_market_dominance_history(365)
        """
        try:
            # Get current time
            end_time = int(datetime.now().timestamp())
            start_time = end_time - (days * 86400)  # days * seconds_per_day
            
            # Fetch dominance data for different metrics
            results = {}
            
            for metric_name, symbol in self.dominance_symbols.items():
                try:
                    symbol_data = await self._get_symbol_history(
                        symbol, start_time, end_time, days
                    )
                    if symbol_data:
                        results[metric_name] = symbol_data
                except Exception as e:
                    logger.warning(f"Failed to fetch {metric_name} from {symbol}: {e}")
                    results[metric_name] = []
            
            # Process and combine data
            historical_dominance = self._process_dominance_data(results, days)
            
            return {
                'historical_dominance': historical_dominance,
                'data_source': 'tradingview',
                'symbols_used': list(self.dominance_symbols.values()),
                'accuracy': 'very_high',
                'real_historical_data': True,  # This is REAL data!
                'date_range': {
                    'start': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d'),
                    'end': datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')
                },
                'total_days': days,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting TradingView dominance history: {e}")
            return {'error': str(e), 'success': False}
    
    async def _get_symbol_history(
        self, 
        symbol: str, 
        start_time: int, 
        end_time: int, 
        days: int
    ) -> List[List[float]]:
        """
        Get historical data for a specific TradingView symbol
        
        Args:
            symbol: TradingView symbol (e.g., 'CRYPTOCAP:BTC.D')
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            days: Number of days
            
        Returns:
            List of [timestamp, value] pairs
        """
        try:
            params = {
                'symbol': symbol,
                'resolution': 'D',  # Daily resolution
                'from': start_time,
                'to': end_time,
                'countback': days
            }
            
            data = await self._make_request("get", params)
            
            if data.get('s') != 'ok':
                logger.warning(f"TradingView error for {symbol}: {data.get('errmsg', 'Unknown')}")
                return []
            
            # Extract times and close values
            times = data.get('t', [])
            closes = data.get('c', [])
            
            # Combine into [timestamp, value] pairs
            history = []
            for i in range(min(len(times), len(closes))):
                history.append([times[i], closes[i]])
            
            logger.debug(f"Retrieved {len(history)} data points for {symbol}")
            return history
            
        except Exception as e:
            logger.error(f"Error fetching symbol history for {symbol}: {e}")
            return []
    
    def _process_dominance_data(
        self, 
        raw_results: Dict[str, List], 
        days: int
    ) -> List[Dict[str, Any]]:
        """
        Process and combine dominance data from multiple symbols
        
        Args:
            raw_results: Raw dominance data from TradingView
            days: Number of days requested
            
        Returns:
            List of processed dominance records
        """
        processed_data = []
        
        try:
            # Get the longest dataset to use as reference
            reference_data = max(
                (data for data in raw_results.values() if data), 
                key=len, 
                default=[]
            )
            
            if not reference_data:
                logger.warning("No dominance data available")
                return processed_data
            
            # Process each day
            for i in range(len(reference_data)):
                timestamp, _ = reference_data[i]
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                # Extract values for this timestamp from all symbols
                record = {
                    'date': date_str,
                    'timestamp': timestamp
                }
                
                # BTC Dominance
                btc_data = raw_results.get('btc_dominance', [])
                if i < len(btc_data):
                    record['btc_dominance'] = btc_data[i][1]
                
                # ETH Dominance  
                eth_data = raw_results.get('eth_dominance', [])
                if i < len(eth_data):
                    record['eth_dominance'] = eth_data[i][1]
                
                # Total Market Cap
                total_data = raw_results.get('total_market_cap', [])
                if i < len(total_data):
                    record['total_market_cap'] = total_data[i][1]
                
                # Others/Altcoin Dominance
                others_data = raw_results.get('altcoin_dominance', [])
                if i < len(others_data):
                    record['altcoin_dominance'] = others_data[i][1]
                else:
                    # Calculate if we have BTC and ETH dominance
                    btc_dom = record.get('btc_dominance', 0)
                    eth_dom = record.get('eth_dominance', 0)
                    if btc_dom and eth_dom:
                        record['altcoin_dominance'] = max(0, 100 - btc_dom - eth_dom)
                
                # Add data quality indicators
                record['data_quality'] = 'high'
                record['source'] = 'tradingview'
                
                processed_data.append(record)
            
            logger.info(f"Processed {len(processed_data)} dominance records")
            
        except Exception as e:
            logger.error(f"Error processing dominance data: {e}")
        
        return processed_data
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    # Context manager support
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
