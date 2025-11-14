

import sys
import asyncio
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))
from app.external.tradingview import TradingViewClient
from app.external.binance import BinanceClient


if __name__ == "__main__":
    days = 5
    timeframe = "1d"
    # Try TradingView first (with tvdatafeed)
    print("🔄 Attempting to fetch from TradingView...")
    # Run the async method correctly using asyncio.run to avoid "coroutine was never awaited"
    #client = TradingViewClient()    
    #data = asyncio.run(client.get_price_data_by_timeframe(asset_id=1, crypto_id="BTC.D", timeframe=timeframe, days=days))
    client = BinanceClient()    
    data = asyncio.run(client.get_price_data_by_timeframe(asset_id=1, crypto_id="BTCUSDT", timeframe=timeframe, days=days))

    from datetime import datetime, timezone
    print(f"datetime.fromtimestamp(1762646400000 / 1000, tz=timezone.utc): {datetime.fromtimestamp(1762646400000 / 1000, tz=timezone.utc)}")

