import requests
import json
import time
from datetime import datetime
import re

def get_tradingview_ohlc_tvdatafeed(symbol="BTC.D", exchange="CRYPTOCAP", interval="1D", days=365):
    """
    Get OHLC data from TradingView using tvdatafeed library
    
    Parameters:
    - symbol: Symbol to fetch (e.g., "BTC.D")
    - exchange: Exchange name (default: "CRYPTOCAP")
    - interval: Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1D, 1W, 1M)
    - days: Number of days (converted to bars based on interval)
    """
    
    try:
        print(f"\n📊 Fetching BTC.D OHLC from TradingView using tvdatafeed...")
        print(f"Symbol: {exchange}:{symbol}")
        print(f"Interval: {interval}")
        print(f"Days: {days}")
        print("=" * 80)
        
        from tvDatafeed import TvDatafeed, Interval
        
        # Map interval strings to TvDatafeed Interval enum
        interval_map = {
            '1m': Interval.in_1_minute,
            '3m': Interval.in_3_minute,
            '5m': Interval.in_5_minute,
            '15m': Interval.in_15_minute,
            '30m': Interval.in_30_minute,
            '45m': Interval.in_45_minute,
            '1h': Interval.in_1_hour,
            '2h': Interval.in_2_hour,
            '3h': Interval.in_3_hour,
            '4h': Interval.in_4_hour,
            '1D': Interval.in_daily,
            '1W': Interval.in_weekly,
            '1M': Interval.in_monthly,
        }
        
        if interval not in interval_map:
            print(f"❌ Invalid interval. Valid options: {list(interval_map.keys())}")
            return None
        
        # Calculate number of bars based on interval
        bars_per_day = {
            '1m': 1440, '3m': 480, '5m': 288, '15m': 96,
            '30m': 48, '45m': 32, '1h': 24, '2h': 12,
            '3h': 8, '4h': 6, '1D': 1, '1W': 1/7, '1M': 1/30
        }
        
        n_bars = int(days * bars_per_day.get(interval, 1))
        n_bars = min(n_bars, 5000)  # Max 5000 bars per request
        
        print(f"🔄 Requesting {n_bars} bars...")
        
        # Create TvDatafeed instance (no login required for most symbols)
        tv = TvDatafeed()
        
        # Get historical data
        df = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=interval_map[interval],
            n_bars=n_bars
        )
        
        if df is not None and not df.empty:
            print(f"✅ Successfully fetched {len(df)} bars")
            print("=" * 80)
            print(f"{'Date':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
            print("-" * 80)
            
            # Print all data
            for idx, row in df.iterrows():
                date_str = idx.strftime('%Y-%m-%d %H:%M:%S')
                print(f"{date_str:<20} {row['open']:>9.2f}% {row['high']:>9.2f}% {row['low']:>9.2f}% {row['close']:>9.2f}% {row['volume']:>14,.0f}")
            
            print("=" * 80)
            
            # Print statistics
            print(f"\n📈 Statistics ({len(df)} bars):")
            print(f"Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"Highest: {df['high'].max():.2f}%")
            print(f"Lowest: {df['low'].min():.2f}%")
            print(f"Range: {df['high'].max() - df['low'].min():.2f}%")
            print(f"First Close: {df['close'].iloc[0]:.2f}%")
            print(f"Last Close: {df['close'].iloc[-1]:.2f}%")
            print(f"Change: {df['close'].iloc[-1] - df['close'].iloc[0]:+.2f}%")
            print(f"Average Volume: {df['volume'].mean():,.0f}")
            print("=" * 80)
            
            return df
        else:
            print("❌ No data received from TradingView")
            return None
            
    except ImportError:
        print("\n❌ tvdatafeed library not installed")
        print("💡 Install it with: pip install tvdatafeed")
        
    except Exception as e:
        print(f"❌ Error fetching from TradingView: {e}")

if __name__ == "__main__":
    import sys
    days = 5
    interval = "1D"
    
    # Try TradingView first (with tvdatafeed)
    print("🔄 Attempting to fetch from TradingView...")
    data = get_tradingview_ohlc_tvdatafeed("BTC.D", "CRYPTOCAP", interval, days)
    
