# File: ./backend/app/external/__init__.py
# External APIs package initialization - exports API clients

"""
External APIs package for CryptoPredict MVP

This package contains clients for external cryptocurrency APIs:
- CoinGecko: Price data, market information, historical data
- Binance: OHLCV trading data and market calculations
- Alternative.me: Fear & Greed Index sentiment data
- Google Trends: Search trends and sentiment analysis
- TradingView: OHLCV data and real market dominance

Usage:
    from app.external import CoinGeckoClient, TradingViewClient
    
    # Basic price data
    coingecko_client = CoinGeckoClient()
    prices = await coingecko_client.get_current_prices(['bitcoin'])
    
    # Real historical dominance data
    async with TradingViewClient() as tv_client:
        dominance = await tv_client.get_market_dominance_history(365)
        btc_prices = await tv_client.get_price_data_by_timeframe('BTC', 'USDT', '1d', 100)
"""

from app.external.coingecko import CoinGeckoClient
from app.external.binance import BinanceClient
from app.external.alternative_me import AlternativeMeClient
from app.external.google_trends import (
    SafeGoogleTrendsClient, 
    get_crypto_trends_safe, 
    get_crypto_sentiment_safe,
    get_historical_trends_score_safe
)
from app.external.tradingview import TradingViewClient

# Export main API clients
__all__ = [
    "CoinGeckoClient",
    "BinanceClient", 
    "AlternativeMeClient",
    "SafeGoogleTrendsClient",
    "TradingViewClient",
    "get_crypto_trends_safe",
    "get_crypto_sentiment_safe",
    "get_historical_trends_score_safe",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "CryptoPredict Team"
__description__ = "External API clients for cryptocurrency data"