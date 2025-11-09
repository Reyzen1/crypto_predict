

import sys
import asyncio
from pathlib import Path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))
from app.external.tradingview import TradingViewClient


if __name__ == "__main__":

    days = 5
    timeframe = "1D"
    tv = TradingViewClient()    
    # Try TradingView first (with tvdatafeed)
    print("🔄 Attempting to fetch from TradingView...")
    # Run the async method correctly using asyncio.run to avoid "coroutine was never awaited"
    data = asyncio.run(tv.get_price_data_by_timeframe(asset_id=1, crypto_id="BTC.D", timeframe=timeframe, days=days))
    print(data)
    tv.print_result(data)