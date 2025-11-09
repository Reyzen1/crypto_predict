"""
TradingView client wrapper using tvDatafeed

This module provides a small `TradingViewClient` class that wraps the
`tvDatafeed.TvDatafeed` usage from `scripts/test_btc_d.py` into a reusable
client. The class avoids importing tvDatafeed at module import time so the
package can be imported even when tvDatafeed isn't installed.

Usage:
    client = TradingViewClient()  # or TradingViewClient(username, password)
    df = client.get_ohlc(symbol="BTC.D", exchange="CRYPTOCAP", interval="1D", days=365)

If tvDatafeed is not installed, the client will raise ImportError with a
helpful message when you call `get_ohlc`.
"""
from datetime import datetime, timezone
from typing import Any, List, Dict
import logging
import asyncio

# use a real logger instead of importing from fastapi
logger = logging.getLogger(__name__)

class TradingViewClient:
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
            crypto_id: TradingView cryptocurrency ID
            timeframe: Our timeframe format ('1h', '1d')
            days: Number of days to look back for price data
            vs_currency: VS currency (default: 'usd')
            
        Returns:
            dict: Market data
            
        Example:
            # Get last 24 1-hourly data points
            data = await client.get_price_data_by_timeframe('bitcoin', '1h', 24)
        """
        data = await self._get_ohlcv(
            asset_id=asset_id,
            symbol=crypto_id,
            days=days,
            interval=timeframe
        )
                
        return data


    async def _get_ohlcv(
        self, 
        asset_id: int, 
        symbol: str = "BTC.D", 
        exchange: str = "CRYPTOCAP", 
        interval: str = "1D", 
        days: int = 365
    )-> List[Dict[str, Any]]:
        """Fetch OHLC data for a symbol.

        Args:
            symbol: TradingView symbol (e.g., "BTC.D")
            exchange: Exchange / dataset name (e.g., "CRYPTOCAP")
            interval: Timeframe string (same keys as the original script)
            days: Number of days to fetch; translated to bars according to interval
        Returns:
            pandas.DataFrame or None
        """
        try:
            # Import tvdatafeed lazily so the module can run in environments
            # where tvdatafeed is not installed (we provide a fallback demo).
            from tvDatafeed import TvDatafeed, Interval
            tv = TvDatafeed()

            interval_map = {
                '1m': 'in_1_minute',
                '3m': 'in_3_minute',
                '5m': 'in_5_minute',
                '15m': 'in_15_minute',
                '30m': 'in_30_minute',
                '45m': 'in_45_minute',
                '1h': 'in_1_hour',
                '2h': 'in_2_hour',
                '3h': 'in_3_hour',
                '4h': 'in_4_hour',
                '1D': 'in_daily',
                '1W': 'in_weekly',
                '1M': 'in_monthly',
            }

            if interval not in interval_map:
                raise ValueError(f"Invalid interval: {interval}. Valid: {list(interval_map.keys())}")

            # Map string to Interval attribute
            interval_attr = getattr(Interval, interval_map[interval])
            print(f"Using TradingView interval: {interval_attr}")

            # Calculate number of bars to request
            bars_per_day = {
                '1m': 1440, '3m': 480, '5m': 288, '15m': 96,
                '30m': 48, '45m': 32, '1h': 24, '2h': 12,
                '3h': 8, '4h': 6, '1D': 1, '1W': 1/7, '1M': 1/30
            }
            n_bars = int(days * bars_per_day.get(interval, 1))
            n_bars = min(n_bars, 5000)

            print(f"symbol={symbol}, exchange={exchange}, interval={interval_attr}, n_bars={n_bars}")
            df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_attr, n_bars=n_bars)

            # Convert raw data to structured format
            ohlcv = []


            # Use datetime-like index as timestamp
            for idx, row in df.iterrows():
                try:
                    # idx is often a pandas.Timestamp or datetime
                    if isinstance(idx, (datetime,)):
                        ts_dt = idx
                    else:
                        ts_dt = datetime.fromtimestamp(idx / 1000, tz=timezone.utc)

                        #ts_dt = _parse_timestamp(idx)

                    # Extract OHLCV from named columns if available
                    open_v = float(row['open']) if 'open' in row.index else float(row[1])
                    high_v = float(row['high']) if 'high' in row.index else float(row[2])
                    low_v = float(row['low']) if 'low' in row.index else float(row[3])
                    close_v = float(row['close']) if 'close' in row.index else float(row[4])
                    vol_v = float(row['volume']) if 'volume' in row.index else float(row[5])

                    ohlcv.append({
                        'timestamp': ts_dt,
                        'open': open_v,
                        'high': high_v,
                        'low': low_v,
                        'close': close_v,
                        'volume': vol_v,
                    })
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Error parsing candle row: {e}")
                    continue
            logger.info(f"Retrieved {len(ohlcv)} OHLCV candles for {symbol} ({interval})")

            # pass the parsed ohlcv list to the converter (was using undefined name before)
            standardized_ohlcv = self._convert_tradingview_ohlcv_to_standardized_ohlcv(asset_id, interval, ohlcv)
            return standardized_ohlcv

        except ImportError:
            print("\n❌ tvdatafeed library not installed")
            print("💡 Install it with: pip install tradingview-datafeed")
            return None
        except Exception as e:
            print(f"❌ Error fetching from TradingView: {e}")
            return None

    def _convert_tradingview_ohlcv_to_standardized_ohlcv(
        self, 
        asset_id: int, 
        interval: str, 
        ohlcv: list
    ) -> List[Dict[str, Any]]:
        """Convert TradingView OHLCV format to standardized format.

        Args:
            asset_id: Internal asset ID
            interval: Timeframe string
            ohlcv: List of OHLCV dictionaries from TradingView

        Returns:
            pd.DataFrame with standardized OHLCV data
        """
        import pandas as pd

        records = []
        try:
            for entry in ohlcv:
                ohlcv_record = {
                    'asset_id': asset_id,
                    'timeframe': interval,
                    'candle_time': entry['timestamp'],
                    'open_price': float(entry['open']),
                    'high_price': float(entry['high']),
                    'low_price': float(entry['low']),
                    'close_price': float(entry['close']),
                    'volume': float(entry['volume']),
                    'market_cap': None  # TradingView doesn't provide market cap in OHLCV data
                }

                records.append(ohlcv_record)
        except Exception as e:
            logger.error(f"Error converting tradingview data to OHLCV format: {e}")

        return records

    def print_result(self, data: List[Dict[str, Any]]):
        if data is not None and len(data) > 0:
            print(f"✅ Successfully fetched {len(data)} bars")
            print("=" * 80)
            print(f"{'Date':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
            print("-" * 80)
            for row in data:
                date_str = row['candle_time'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{date_str:<20} {row['open_price']:>9.2f}% {row['high_price']:>9.2f}% {row['low_price']:>9.2f}% {row['close_price']:>9.2f}% {row['volume']:>14,.0f}")

            print("=" * 80)
            print(f"\n📈 Statistics ({len(data)} bars):")
            print(f"Period: {data[0]['candle_time'].strftime('%Y-%m-%d')} to {data[-1]['candle_time'].strftime('%Y-%m-%d')}")
            print(f"Highest: {max(row['high_price'] for row in data):.2f}%")
            print(f"Lowest: {min(row['low_price'] for row in data):.2f}%")
            print(f"Range: {max(row['high_price'] for row in data) - min(row['low_price'] for row in data):.2f}%")
            print(f"First Close: {data[0]['close_price']:.2f}%")
            print(f"Last Close: {data[-1]['close_price']:.2f}%")
            print(f"Change: {data[-1]['close_price'] - data[0]['close_price']:+.2f}%")
            print(f"Average Volume: {sum(row['volume'] for row in data) / len(data):,.0f}")
            print("=" * 80)
        else:
            print("❌ No data received from TradingView")
