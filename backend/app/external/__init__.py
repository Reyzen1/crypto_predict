# File: ./backend/app/external/__init__.py
# External APIs package initialization - exports API clients

"""
External APIs package for CryptoPredict MVP

This package contains clients for external cryptocurrency APIs:
- CoinGecko: Price data, market information, historical data
- Future: Binance, Alpha Vantage, etc.

Usage:
    from app.external import CoinGeckoClient
    
    client = CoinGeckoClient()
    prices = await client.get_current_prices(['bitcoin'])
"""

from app.external.coingecko import CoinGeckoClient

# Export main API clients
__all__ = [
    "CoinGeckoClient",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "CryptoPredict Team"
__description__ = "External API clients for cryptocurrency data"