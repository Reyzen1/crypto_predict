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
from typing import Optional, Any
from datetime import datetime

MAX_BARS = 5000


class TradingViewClient:
    """Simple TradingView client that fetches OHLC data using tvDatafeed.

    Notes:
        - This class performs lazy import of tvDatafeed to avoid hard dependency
          at module import time.
        - Returns a pandas.DataFrame when successful, otherwise None.
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        # tvDatafeed instance created lazily on first request
        self._tv = None

    def _ensure_tv(self):
        """Lazy create TvDatafeed instance. Raises ImportError if library missing."""
        if self._tv is None:
            try:
                from tvDatafeed import TvDatafeed
            except Exception as e:  # ImportError or other issues
                raise ImportError(
                    "tvDatafeed library is required for TradingViewClient. "
                    "Install with: pip install tvdatafeed"
                ) from e

            # If username/password provided, pass them to TvDatafeed
            if self.username and self.password:
                self._tv = TvDatafeed(self.username, self.password)
            else:
                self._tv = TvDatafeed()

        return self._tv

    @staticmethod
    def _interval_map():
        # Map human-friendly intervals to tvDatafeed Interval values
        # We'll import Interval lazily inside get_ohlc to avoid module-level dependency
        return {
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

    @staticmethod
    def _bars_per_day_map():
        return {
            '1m': 1440, '3m': 480, '5m': 288, '15m': 96,
            '30m': 48, '45m': 32, '1h': 24, '2h': 12,
            '3h': 8, '4h': 6, '1D': 1, '1W': 1/7, '1M': 1/30
        }

    def get_ohlc(self, symbol: str = "BTC.D", exchange: str = "CRYPTOCAP", interval: str = "1D", days: int = 365) -> Optional[Any]:
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
            tv = self._ensure_tv()

            # Import Interval enum lazily
            from tvDatafeed import Interval

            interval_map = self._interval_map()
            if interval not in interval_map:
                raise ValueError(f"Invalid interval: {interval}. Valid: {list(interval_map.keys())}")

            # Map string to Interval attribute
            interval_attr = getattr(Interval, interval_map[interval])

            # Calculate number of bars to request
            bars_per_day = self._bars_per_day_map()
            n_bars = int(days * bars_per_day.get(interval, 1))
            n_bars = min(n_bars, MAX_BARS)

            df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_attr, n_bars=n_bars)

            # tvDatafeed returns a pandas DataFrame or None
            return df

        except ImportError:
            # Propagate helpful message
            raise
        except Exception:
            # Catch-all: return None to match original script behavior
            return None
