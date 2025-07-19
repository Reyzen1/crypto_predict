# File: ./backend/app/schemas/price_data.py
# Price data related Pydantic schemas

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from decimal import Decimal

from app.schemas.common import BaseSchema, DateRangeFilter


class PriceDataBase(BaseSchema):
    """Base price data schema with common fields"""
    
    timestamp: datetime = Field(description="Price data timestamp")
    open_price: Decimal = Field(gt=0, description="Opening price")
    high_price: Decimal = Field(gt=0, description="Highest price")
    low_price: Decimal = Field(gt=0, description="Lowest price")
    close_price: Decimal = Field(gt=0, description="Closing price")
    volume: Optional[Decimal] = Field(default=None, ge=0, description="Trading volume")
    market_cap: Optional[Decimal] = Field(default=None, ge=0, description="Market capitalization")
    
    @validator('high_price')
    def validate_high_price(cls, v, values):
        """Validate that high price is >= low, open, and close prices"""
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('High price must be >= low price')
        if 'open_price' in values and v < values['open_price']:
            raise ValueError('High price must be >= open price')
        if 'close_price' in values and v < values['close_price']:
            raise ValueError('High price must be >= close price')
        return v
    
    @validator('low_price')
    def validate_low_price(cls, v, values):
        """Validate that low price is <= open and close prices"""
        if 'open_price' in values and v > values['open_price']:
            raise ValueError('Low price must be <= open price')
        if 'close_price' in values and v > values['close_price']:
            raise ValueError('Low price must be <= close price')
        return v


class PriceDataCreate(PriceDataBase):
    """Schema for creating new price data"""
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")


class PriceDataUpdate(BaseModel):
    """Schema for updating price data"""
    
    open_price: Optional[Decimal] = Field(default=None, gt=0, description="Opening price")
    high_price: Optional[Decimal] = Field(default=None, gt=0, description="Highest price")
    low_price: Optional[Decimal] = Field(default=None, gt=0, description="Lowest price")
    close_price: Optional[Decimal] = Field(default=None, gt=0, description="Closing price")
    volume: Optional[Decimal] = Field(default=None, ge=0, description="Trading volume")
    market_cap: Optional[Decimal] = Field(default=None, ge=0, description="Market capitalization")


class PriceDataResponse(PriceDataBase):
    """Schema for price data in API responses"""
    
    id: int = Field(description="Unique identifier")
    crypto_id: int = Field(description="Cryptocurrency ID")
    created_at: datetime = Field(description="Creation timestamp")


class PriceDataWithCrypto(PriceDataResponse):
    """Schema for price data with cryptocurrency information"""
    
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    crypto_name: str = Field(description="Cryptocurrency name")


class OHLCV(BaseSchema):
    """Schema for OHLCV (Open, High, Low, Close, Volume) data"""
    
    timestamp: datetime = Field(description="Data timestamp")
    open: Decimal = Field(gt=0, description="Opening price")
    high: Decimal = Field(gt=0, description="Highest price")
    low: Decimal = Field(gt=0, description="Lowest price")
    close: Decimal = Field(gt=0, description="Closing price")
    volume: Decimal = Field(ge=0, description="Trading volume")


class PriceHistoryRequest(DateRangeFilter):
    """Schema for price history requests"""
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    interval: str = Field(
        default="1h", 
        description="Data interval (1m, 5m, 15m, 1h, 4h, 1d)"
    )
    limit: int = Field(default=1000, ge=1, le=10000, description="Maximum number of records")
    
    @validator('interval')
    def validate_interval(cls, v):
        """Validate interval format"""
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
        if v not in valid_intervals:
            raise ValueError(f'Interval must be one of: {", ".join(valid_intervals)}')
        return v


class PriceHistoryResponse(BaseModel):
    """Schema for price history responses"""
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    interval: str = Field(description="Data interval")
    data: List[OHLCV] = Field(description="Historical price data")
    count: int = Field(description="Number of data points")
    date_range: Dict[str, datetime] = Field(description="Date range of data")


class PriceStatistics(BaseSchema):
    """Schema for price statistics"""
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    period_days: int = Field(description="Analysis period in days")
    avg_price: Decimal = Field(description="Average price")
    min_price: Decimal = Field(description="Minimum price")
    max_price: Decimal = Field(description="Maximum price")
    total_volume: Decimal = Field(description="Total trading volume")
    price_volatility: float = Field(description="Price volatility (standard deviation)")
    price_change_percentage: float = Field(description="Total price change percentage")
    data_points: int = Field(description="Number of data points")
    latest_price: Decimal = Field(description="Latest price")


class MLDataRequest(BaseModel):
    """Schema for ML model data requests"""
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    days_back: int = Field(
        default=365, 
        ge=1, 
        le=3650, 
        description="Number of days of historical data"
    )
    features: List[str] = Field(
        default=["open", "high", "low", "close", "volume"], 
        description="List of features to include"
    )
    normalize: bool = Field(default=False, description="Whether to normalize the data")
    
    @validator('features')
    def validate_features(cls, v):
        """Validate feature list"""
        valid_features = ["open", "high", "low", "close", "volume", "market_cap"]
        invalid_features = [f for f in v if f not in valid_features]
        if invalid_features:
            raise ValueError(f'Invalid features: {", ".join(invalid_features)}')
        return v


class MLDataResponse(BaseModel):
    """Schema for ML model data responses"""
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    features: List[str] = Field(description="Included features")
    data: List[Dict[str, Any]] = Field(description="ML-ready data")
    count: int = Field(description="Number of data points")
    normalized: bool = Field(description="Whether data is normalized")
    date_range: Dict[str, datetime] = Field(description="Date range of data")


class PriceAlert(BaseSchema):
    """Schema for price alerts"""
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    alert_type: str = Field(description="Alert type (above, below, percentage_change)")
    threshold_value: Decimal = Field(description="Alert threshold value")
    is_active: bool = Field(default=True, description="Whether alert is active")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        """Validate alert type"""
        valid_types = ["above", "below", "percentage_change_up", "percentage_change_down"]
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v


class PriceDataBulkInsert(BaseModel):
    """Schema for bulk price data insertion"""
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    price_data: List[PriceDataBase] = Field(
        min_length=1, 
        max_length=10000, 
        description="List of price data entries"
    )
    
    @validator('price_data')
    def validate_chronological_order(cls, v):
        """Validate that price data is in chronological order"""
        if len(v) > 1:
            for i in range(1, len(v)):
                if v[i].timestamp <= v[i-1].timestamp:
                    raise ValueError('Price data must be in chronological order')
        return v


class PriceDataAnalytics(BaseSchema):
    """Schema for price data analytics"""
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    analysis_period: int = Field(description="Analysis period in days")
    moving_averages: Dict[str, Decimal] = Field(description="Moving averages (MA7, MA30, etc.)")
    support_levels: List[Decimal] = Field(description="Identified support levels")
    resistance_levels: List[Decimal] = Field(description="Identified resistance levels")
    trend_direction: str = Field(description="Overall trend direction")
    rsi: Optional[float] = Field(default=None, description="Relative Strength Index")
    bollinger_bands: Optional[Dict[str, Decimal]] = Field(
        default=None, 
        description="Bollinger Bands (upper, middle, lower)"
    )


class RealTimePriceUpdate(BaseSchema):
    """Schema for real-time price updates"""
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    current_price: Decimal = Field(description="Current price")
    change_24h: float = Field(description="24h change percentage")
    volume_24h: Decimal = Field(description="24h trading volume")
    market_cap: Optional[Decimal] = Field(default=None, description="Market cap")
    timestamp: datetime = Field(description="Update timestamp")
    source: str = Field(description="Data source (coingecko, binance, etc.)")
    
    @validator('source')
    def validate_source(cls, v):
        """Validate data source"""
        valid_sources = ["coingecko", "binance", "coinbase", "kraken"]
        if v.lower() not in valid_sources:
            raise ValueError(f'Source must be one of: {", ".join(valid_sources)}')
        return v.lower()