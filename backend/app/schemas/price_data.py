# File: ./backend/app/schemas/price_data.py
# Price data related Pydantic schemas - FIXED for Pydantic V2

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timedelta
from decimal import Decimal

from app.schemas.common import BaseSchema, DateRangeFilter


class PriceDataBase(BaseSchema):
    """Base price data schema with common fields"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    timestamp: datetime = Field(description="Price data timestamp")
    open_price: Decimal = Field(gt=0, description="Opening price")
    high_price: Decimal = Field(gt=0, description="Highest price")
    low_price: Decimal = Field(gt=0, description="Lowest price")
    close_price: Decimal = Field(gt=0, description="Closing price")
    volume: Optional[Decimal] = Field(default=None, ge=0, description="Trading volume")
    market_cap: Optional[Decimal] = Field(default=None, ge=0, description="Market capitalization")
    
    @field_validator('high_price')
    @classmethod
    def validate_high_price(cls, v, info):
        """Validate that high price is >= low, open, and close prices"""
        if 'low_price' in info.data and v < info.data['low_price']:
            raise ValueError('High price must be >= low price')
        if 'open_price' in info.data and v < info.data['open_price']:
            raise ValueError('High price must be >= open price')
        if 'close_price' in info.data and v < info.data['close_price']:
            raise ValueError('High price must be >= close price')
        return v
    
    @field_validator('low_price')
    @classmethod
    def validate_low_price(cls, v, info):
        """Validate that low price is <= open and close prices"""
        if 'open_price' in info.data and v > info.data['open_price']:
            raise ValueError('Low price must be <= open price')
        if 'close_price' in info.data and v > info.data['close_price']:
            raise ValueError('Low price must be <= close price')
        return v


class PriceDataCreate(PriceDataBase):
    """Schema for creating new price data"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")


class PriceDataUpdate(BaseModel):
    """Schema for updating price data"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    open_price: Optional[Decimal] = Field(default=None, gt=0, description="Opening price")
    high_price: Optional[Decimal] = Field(default=None, gt=0, description="Highest price")
    low_price: Optional[Decimal] = Field(default=None, gt=0, description="Lowest price")
    close_price: Optional[Decimal] = Field(default=None, gt=0, description="Closing price")
    volume: Optional[Decimal] = Field(default=None, ge=0, description="Trading volume")
    market_cap: Optional[Decimal] = Field(default=None, ge=0, description="Market capitalization")


class PriceDataResponse(PriceDataBase):
    """Schema for price data in API responses"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    id: int = Field(description="Unique identifier")
    crypto_id: int = Field(description="Cryptocurrency ID")
    created_at: datetime = Field(description="Creation timestamp")


class PriceDataWithCrypto(PriceDataResponse):
    """Schema for price data with cryptocurrency information"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    crypto_name: str = Field(description="Cryptocurrency name")


class OHLCV(BaseModel):
    """Schema for OHLCV (Open, High, Low, Close, Volume) data"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    timestamp: datetime = Field(description="Data timestamp")
    open: Decimal = Field(description="Opening price")
    high: Decimal = Field(description="Highest price")
    low: Decimal = Field(description="Lowest price")
    close: Decimal = Field(description="Closing price")
    volume: Decimal = Field(description="Trading volume")


class PriceHistoryRequest(BaseModel):
    """Schema for price history requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    days: int = Field(
        default=30, 
        ge=1, 
        le=3650, 
        description="Number of days of historical data"
    )
    timeframe: str = Field(
        default="1d", 
        description="Data timeframe (1h, 4h, 1d)"
    )
    
    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v):
        """Validate data timeframe"""
        valid_timeframes = ["1h", "4h", "1d"]
        if v not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of: {", ".join(valid_timeframes)}')
        return v


class PriceHistoryResponse(BaseModel):
    """Schema for price history responses - aligned with API endpoint"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    name: str = Field(description="Cryptocurrency name")
    start_date: datetime = Field(description="Start date of data")
    end_date: datetime = Field(description="End date of data")
    timeframe: str = Field(description="Data timeframe")
    data_points: int = Field(description="Number of data points")
    ohlcv_data: List[OHLCV] = Field(description="Historical OHLCV data")


class PriceStatistics(BaseSchema):
    """Schema for price statistics - aligned with API endpoint"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    name: str = Field(description="Cryptocurrency name")
    period_days: int = Field(description="Analysis period in days")
    data_points: int = Field(description="Number of data points")
    current_price: Decimal = Field(description="Current/latest price")
    min_price: Decimal = Field(description="Minimum price in period")
    max_price: Decimal = Field(description="Maximum price in period")
    avg_price: Decimal = Field(description="Average price in period")
    price_change: Decimal = Field(description="Absolute price change")
    price_change_percentage: float = Field(description="Price change percentage")
    volatility: float = Field(description="Price volatility (standard deviation)")
    avg_volume: Decimal = Field(description="Average trading volume")
    start_date: datetime = Field(description="Analysis start date")
    end_date: datetime = Field(description="Analysis end date")


class MLDataRequest(BaseModel):
    """Schema for ML model data requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
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
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v):
        """Validate feature list"""
        valid_features = ["open", "high", "low", "close", "volume", "market_cap"]
        invalid_features = [f for f in v if f not in valid_features]
        if invalid_features:
            raise ValueError(f'Invalid features: {", ".join(invalid_features)}')
        return v


class MLDataResponse(BaseModel):
    """Schema for ML model data responses - aligned with API endpoint"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    name: str = Field(description="Cryptocurrency name")
    start_date: datetime = Field(description="Data start date")
    end_date: datetime = Field(description="Data end date")
    features: List[str] = Field(description="Features included")
    data_points: int = Field(description="Number of data points")
    ml_data: List[Dict[str, Any]] = Field(description="ML-ready data")
    preprocessing_notes: List[str] = Field(description="Preprocessing information")


class PriceAlert(BaseSchema):
    """Schema for price alerts"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    user_id: int = Field(description="User ID")
    crypto_id: int = Field(description="Cryptocurrency ID")
    alert_type: str = Field(description="Alert type")
    threshold_price: Decimal = Field(description="Alert threshold price")
    is_active: bool = Field(default=True, description="Whether alert is active")
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        """Validate alert type"""
        valid_types = ["price_above", "price_below", "change_percentage"]
        if v.lower() not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v.lower()


class PriceDataBulkInsert(BaseModel):
    """Schema for bulk price data insertion - aligned with API endpoint"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID for all records")
    price_data: List[PriceDataBase] = Field(
        min_length=1, 
        max_length=1000, 
        description="List of price data to insert"
    )
    
    @field_validator('price_data')
    @classmethod
    def validate_price_data(cls, v):
        """Validate price data list"""
        if not v:
            raise ValueError('Price data list cannot be empty')
        return v


class PriceDataAnalytics(BaseSchema):
    """Schema for price data analytics"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    analysis_period: int = Field(description="Analysis period in days")


class AssetPriceDataFetchRequest(BaseSchema):
    """Schema for asset price data fetch request"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    asset_id: int = Field(gt=0, description="Asset ID")
    days: int = Field(default=30, ge=1, le=365, description="Number of days")
    timeframe: str = Field(default="1d", description="Data timeframe")
    vs_currency: str = Field(default="usd", description="Base currency")
    
    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v):
        """Validate timeframe - aligned with API endpoints"""
        valid_timeframes = ['1h', '4h', '1d']
        if v not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of: {", ".join(valid_timeframes)}')
        return v


class AssetPriceDataFetchResponse(BaseSchema):
    """Schema for asset price data fetch response"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    success: bool = Field(description="Operation success")
    asset_id: int = Field(description="Asset ID")
    records_inserted: int = Field(description="Number of records inserted")
    timeframe: str = Field(description="Data timeframe")
    period_days: int = Field(description="Period in days")
    message: str = Field(description="Operation message")


class BatchPriceDataFetchResponse(BaseSchema):
    """Schema for batch price data fetch response"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    success_count: int = Field(description="Successful operations")
    failed_count: int = Field(description="Failed operations")
    total_assets: int = Field(description="Total assets processed")
    timeframe: str = Field(description="Data timeframe")
    errors: List[str] = Field(description="Error messages")


class DataQualityReport(BaseSchema):
    """Schema for data quality report"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    asset_id: int = Field(description="Asset ID")
    timeframe: str = Field(description="Data timeframe")
    analysis_period_days: int = Field(description="Analysis period")
    total_records: int = Field(description="Total records")
    missing_price: int = Field(description="Missing price records")
    missing_volume: int = Field(description="Missing volume records")
    zero_prices: int = Field(description="Zero price records")
    data_gaps: int = Field(description="Number of data gaps")
    quality_score: float = Field(description="Quality score (0-100)")
    quality_grade: str = Field(description="Quality grade (A-F)")
    recommendations: List[str] = Field(description="Improvement recommendations")


class PriceDataGap(BaseSchema):
    """Schema for price data gap information"""
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True
    )
    
    start: str = Field(description="Gap start time")
    end: str = Field(description="Gap end time")
    duration_minutes: float = Field(description="Gap duration in minutes")
    expected_minutes: int = Field(description="Expected interval in minutes")
    trend_analysis: Dict[str, Any] = Field(description="Trend analysis results")
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
    
    model_config = ConfigDict(
        protected_namespaces=(),  
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    symbol: str = Field(description="Cryptocurrency symbol")
    current_price: Decimal = Field(description="Current price")
    change_24h: float = Field(description="24h change percentage")
    volume_24h: Decimal = Field(description="24h trading volume")
    market_cap: Optional[Decimal] = Field(default=None, description="Market cap")
    timestamp: datetime = Field(description="Update timestamp")
    source: str = Field(description="Data source (coingecko, binance, etc.)")
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        """Validate data source"""
        valid_sources = ["coingecko", "binance", "coinbase", "kraken"]
        if v.lower() not in valid_sources:
            raise ValueError(f'Source must be one of: {", ".join(valid_sources)}')
        return v.lower()