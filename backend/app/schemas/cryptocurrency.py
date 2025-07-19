# File: ./backend/app/schemas/cryptocurrency.py
# Cryptocurrency-related Pydantic schemas

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal

from app.schemas.common import BaseSchema


class CryptocurrencyBase(BaseSchema):
    """Base cryptocurrency schema with common fields"""
    
    symbol: str = Field(
        min_length=1, 
        max_length=10, 
        description="Cryptocurrency symbol (e.g., BTC, ETH)"
    )
    name: str = Field(
        min_length=1, 
        max_length=100, 
        description="Full cryptocurrency name"
    )
    coingecko_id: Optional[str] = Field(
        default=None, 
        max_length=50, 
        description="CoinGecko API identifier"
    )
    binance_symbol: Optional[str] = Field(
        default=None, 
        max_length=20, 
        description="Binance trading pair symbol"
    )
    
    @validator('symbol')
    def validate_symbol_format(cls, v):
        """Validate symbol format (uppercase, alphanumeric)"""
        if not v.isalnum():
            raise ValueError('Symbol must contain only alphanumeric characters')
        return v.upper()


class CryptocurrencyCreate(CryptocurrencyBase):
    """Schema for creating a new cryptocurrency"""
    
    is_active: bool = Field(default=True, description="Whether the cryptocurrency is active")


class CryptocurrencyUpdate(BaseModel):
    """Schema for updating cryptocurrency information"""
    
    name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=100, 
        description="Full cryptocurrency name"
    )
    coingecko_id: Optional[str] = Field(
        default=None, 
        max_length=50, 
        description="CoinGecko API identifier"
    )
    binance_symbol: Optional[str] = Field(
        default=None, 
        max_length=20, 
        description="Binance trading pair symbol"
    )
    is_active: Optional[bool] = Field(
        default=None, 
        description="Whether the cryptocurrency is active"
    )


class CryptocurrencyResponse(CryptocurrencyBase):
    """Schema for cryptocurrency data in API responses"""
    
    id: int = Field(description="Unique identifier")
    is_active: bool = Field(description="Whether the cryptocurrency is active")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class CryptocurrencyWithPrice(CryptocurrencyResponse):
    """Schema for cryptocurrency with latest price information"""
    
    latest_price: Optional[Decimal] = Field(
        default=None, 
        description="Latest price in USD"
    )
    price_change_24h: Optional[float] = Field(
        default=None, 
        description="24-hour price change percentage"
    )
    price_change_7d: Optional[float] = Field(
        default=None, 
        description="7-day price change percentage"
    )
    volume_24h: Optional[Decimal] = Field(
        default=None, 
        description="24-hour trading volume"
    )
    market_cap: Optional[Decimal] = Field(
        default=None, 
        description="Market capitalization"
    )
    last_updated: Optional[datetime] = Field(
        default=None, 
        description="Price data last update timestamp"
    )


class CryptocurrencyStats(BaseSchema):
    """Schema for cryptocurrency statistics"""
    
    symbol: str = Field(description="Cryptocurrency symbol")
    total_predictions: int = Field(default=0, description="Total number of predictions")
    total_price_data_points: int = Field(default=0, description="Total price data points")
    data_coverage_days: int = Field(default=0, description="Number of days with price data")
    avg_daily_volume: Optional[Decimal] = Field(
        default=None, 
        description="Average daily trading volume"
    )
    price_volatility: Optional[float] = Field(
        default=None, 
        description="Price volatility percentage"
    )
    first_price_date: Optional[datetime] = Field(
        default=None, 
        description="Date of first price data"
    )
    last_price_date: Optional[datetime] = Field(
        default=None, 
        description="Date of latest price data"
    )


class CryptocurrencyList(BaseModel):
    """Schema for cryptocurrency list responses"""
    
    cryptocurrencies: List[CryptocurrencyResponse] = Field(
        description="List of cryptocurrencies"
    )
    total_count: int = Field(description="Total number of cryptocurrencies")
    active_count: int = Field(description="Number of active cryptocurrencies")


class CryptocurrencySearch(BaseModel):
    """Schema for cryptocurrency search parameters"""
    
    query: str = Field(
        min_length=1, 
        max_length=50, 
        description="Search query (symbol or name)"
    )
    active_only: bool = Field(
        default=True, 
        description="Search only active cryptocurrencies"
    )
    include_price: bool = Field(
        default=False, 
        description="Include latest price information"
    )


class CryptocurrencyBulkUpdate(BaseModel):
    """Schema for bulk cryptocurrency operations"""
    
    cryptocurrency_ids: List[int] = Field(
        min_length=1, 
        max_length=50, 
        description="List of cryptocurrency IDs"
    )
    action: str = Field(description="Action to perform (activate, deactivate)")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate bulk action"""
        valid_actions = ["activate", "deactivate", "update_prices"]
        if v.lower() not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v.lower()


class MarketData(BaseSchema):
    """Schema for market data from external APIs"""
    
    symbol: str = Field(description="Cryptocurrency symbol")
    current_price: Decimal = Field(description="Current price in USD")
    market_cap: Optional[Decimal] = Field(default=None, description="Market capitalization")
    total_volume: Optional[Decimal] = Field(default=None, description="24h trading volume")
    price_change_percentage_24h: Optional[float] = Field(
        default=None, 
        description="24h price change percentage"
    )
    price_change_percentage_7d: Optional[float] = Field(
        default=None, 
        description="7d price change percentage"
    )
    price_change_percentage_30d: Optional[float] = Field(
        default=None, 
        description="30d price change percentage"
    )
    circulating_supply: Optional[Decimal] = Field(
        default=None, 
        description="Circulating supply"
    )
    total_supply: Optional[Decimal] = Field(
        default=None, 
        description="Total supply"
    )
    max_supply: Optional[Decimal] = Field(
        default=None, 
        description="Maximum supply"
    )
    last_updated: datetime = Field(description="Data last update timestamp")


class CryptocurrencyRanking(BaseSchema):
    """Schema for cryptocurrency ranking"""
    
    rank: int = Field(description="Market rank")
    symbol: str = Field(description="Cryptocurrency symbol")
    name: str = Field(description="Cryptocurrency name")
    market_cap: Decimal = Field(description="Market capitalization")
    current_price: Decimal = Field(description="Current price")
    change_24h: float = Field(description="24h price change percentage")


class SupportedCryptocurrencies(BaseModel):
    """Schema for supported cryptocurrencies list"""
    
    supported_symbols: List[str] = Field(description="List of supported symbols")
    coingecko_ids: List[str] = Field(description="List of CoinGecko IDs")
    binance_symbols: List[str] = Field(description="List of Binance symbols")
    total_supported: int = Field(description="Total number of supported cryptocurrencies")
    last_updated: datetime = Field(description="List last update timestamp")