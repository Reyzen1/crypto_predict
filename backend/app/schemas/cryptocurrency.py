# File: ./backend/app/schemas/cryptocurrency.py
# Cryptocurrency-related Pydantic schemas - FIXED for Pydantic V2

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from decimal import Decimal

from app.schemas.common import BaseSchema


class CryptocurrencyBase(BaseSchema):
    """Base cryptocurrency schema with common fields"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
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
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol_format(cls, v):
        """Validate symbol format (uppercase, alphanumeric)"""
        if not v.isalnum():
            raise ValueError('Symbol must contain only alphanumeric characters')
        return v.upper()


class CryptocurrencyCreate(CryptocurrencyBase):
    """Schema for creating a new cryptocurrency"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    is_active: bool = Field(default=True, description="Whether the cryptocurrency is active")


class CryptocurrencyUpdate(BaseModel):
    """Schema for updating cryptocurrency information"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
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
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    id: int = Field(description="Unique identifier")
    is_active: bool = Field(description="Whether the cryptocurrency is active")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class CryptocurrencyWithPrice(CryptocurrencyResponse):
    """Schema for cryptocurrency with latest price information"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    latest_price: Optional[Decimal] = Field(
        default=None, 
        description="Latest price in USD"
    )
    latest_price_date: Optional[datetime] = Field(
        default=None, 
        description="Date of latest price"
    )
    price_change_24h: Optional[float] = Field(
        default=None, 
        description="24h price change percentage"
    )
    market_cap: Optional[Decimal] = Field(
        default=None, 
        description="Current market capitalization"
    )


class CryptocurrencyStats(BaseSchema):
    """Schema for cryptocurrency statistics"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    total_data_points: int = Field(description="Total price data points")
    date_range_days: int = Field(description="Date range in days")
    avg_daily_volume: Decimal = Field(description="Average daily volume")
    highest_price: Decimal = Field(description="Highest recorded price")
    lowest_price: Decimal = Field(description="Lowest recorded price")
    volatility_score: float = Field(
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
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    cryptocurrencies: List[CryptocurrencyResponse] = Field(
        description="List of cryptocurrencies"
    )
    total_count: int = Field(description="Total number of cryptocurrencies")
    active_count: int = Field(description="Number of active cryptocurrencies")


class CryptocurrencySearch(BaseModel):
    """Schema for cryptocurrency search parameters"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
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
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    cryptocurrency_ids: List[int] = Field(
        min_length=1, 
        max_length=50, 
        description="List of cryptocurrency IDs"
    )
    action: str = Field(description="Action to perform (activate, deactivate)")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate bulk action"""
        valid_actions = ["activate", "deactivate", "update_prices"]
        if v.lower() not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v.lower()


class MarketData(BaseSchema):
    """Schema for market data from external APIs"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    symbol: str = Field(description="Cryptocurrency symbol")
    current_price: Decimal = Field(description="Current price in USD")
    market_cap: Optional[Decimal] = Field(
        default=None, 
        description="Market capitalization"
    )
    total_volume: Optional[Decimal] = Field(
        default=None, 
        description="24h trading volume"
    )
    price_change_24h: Optional[float] = Field(
        default=None, 
        description="24h price change percentage"
    )
    market_cap_rank: Optional[int] = Field(
        default=None, 
        description="Market cap ranking"
    )
    last_updated: datetime = Field(description="Last update timestamp")


class CryptocurrencyRanking(BaseModel):
    """Schema for cryptocurrency rankings"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    rank: int = Field(description="Market cap rank")
    cryptocurrency: CryptocurrencyWithPrice = Field(description="Cryptocurrency details")
    market_data: MarketData = Field(description="Current market data")


class SupportedCryptocurrencies(BaseModel):
    """Schema for supported cryptocurrencies list"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    total_supported: int = Field(description="Total supported cryptocurrencies")
    active_trading: int = Field(description="Active trading pairs")
    prediction_enabled: List[str] = Field(
        description="Cryptocurrencies with ML prediction enabled"
    )
    recently_added: List[CryptocurrencyResponse] = Field(
        description="Recently added cryptocurrencies"
    )
    top_volume: List[CryptocurrencyWithPrice] = Field(
        description="Top volume cryptocurrencies"
    )