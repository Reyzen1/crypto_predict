import requests
import json
import time
from datetime import datetime
import re



def get_tradingview_ohlc_tvdatafeed(symbol="BTC.D", exchange="CRYPTOCAP", interval="1D", days=365):
    """Fetch OHLC using the TradingViewClient wrapper.

    This replaces the previous direct tvDatafeed usage with the
    `TradingViewClient` class in `app.external.tradingview`.
    """
    try:
        print(f"\n📊 Fetching {symbol} OHLC from TradingView via TradingViewClient...")
        print(f"Symbol: {exchange}:{symbol}")
        print(f"Interval: {interval}")
        print(f"Days: {days}")
        print("=" * 80)

        from app.external.tradingview import TradingViewClient

        client = TradingViewClient()
        df = client.get_ohlc(symbol=symbol, exchange=exchange, interval=interval, days=days)

        if df is not None and not getattr(df, 'empty', False):
            print(f"✅ Successfully fetched {len(df)} bars")
            print("=" * 80)
            print(f"{'Date':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
            print("-" * 80)
            for idx, row in df.iterrows():
                date_str = idx.strftime('%Y-%m-%d %H:%M:%S')
                print(f"{date_str:<20} {row['open']:>9.2f}% {row['high']:>9.2f}% {row['low']:>9.2f}% {row['close']:>9.2f}% {row['volume']:>14,.0f}")

            print("=" * 80)
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
        print("\n❌ tvdatafeed (or TradingViewClient dependency) not installed")
        print("💡 Install tvdatafeed with: pip install tvdatafeed")
        print("\nAlternatively, use CoinGecko for OHLC data...")
        return None
    except Exception as e:
        print(f"❌ Error fetching from TradingView: {e}")
        print("\n💡 Falling back to CoinGecko...")
        return None



if __name__ == "__main__":
    import sys
    days = 5
    interval = "1D"
    
    # Try TradingView first (with tvdatafeed)
    print("🔄 Attempting to fetch from TradingView...")
    data = get_tradingview_ohlc_tvdatafeed("BTC.D", "CRYPTOCAP", interval, days)
    
