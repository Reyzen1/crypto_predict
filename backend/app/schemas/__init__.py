# File: backend/app/schemas/__init__.py
# Schemas package initialization - exports all schema classes

# Common schemas
from app.schemas.common import (
    BaseSchema,
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    HealthStatus,
    HealthCheck,  # Backward compatibility alias
    DateRangeFilter,
    APIResponse,
    SortOrder,
    FilterParams,
    BatchOperation,
    MetricsResponse,
    BulkOperationResult,
    SearchParams,
    TimeSeriesParams,
    ExportRequest
)

# User schemas
from app.schemas.user import (
    UserBase,
    UserRegister,
    UserLogin,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    UserProfile,
    UserStats,
    UserListResponse,
    TokenResponse,
    AuthResponse,
    TokenRefresh
)

# Cryptocurrency schemas
from app.schemas.cryptocurrency import (
    CryptocurrencyBase,
    CryptocurrencyCreate,
    CryptocurrencyUpdate,
    CryptocurrencyResponse,
    CryptocurrencyWithPrice,
    CryptocurrencyStats,
    CryptocurrencyList,
    CryptocurrencySearch,
    CryptocurrencyBulkUpdate
)

# Price data schemas
from app.schemas.price_data import (
    PriceDataBase,
    PriceDataCreate,
    PriceDataUpdate,
    PriceDataResponse,
    PriceDataWithCrypto,
    OHLCV,
    PriceHistoryRequest,
    PriceHistoryResponse,
    PriceStatistics,
    MLDataRequest,
    MLDataResponse,
    PriceDataBulkInsert,
    PriceDataAnalytics,
    RealTimePriceUpdate
)

# Prediction schemas
from app.schemas.ml_prediction import (
    PredictionBase,
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse,
    PredictionRequest,
    PredictionResult,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelPerformance,
    PredictionAnalytics,
    PredictionComparison
)

# Export all schema classes for easy importing
__all__ = [
    # Common schemas
    "BaseSchema",
    "PaginationParams", 
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse", 
    "HealthStatus",
    "HealthCheck",  # Backward compatibility
    "DateRangeFilter",
    "APIResponse",
    "SortOrder",
    "FilterParams",
    "BatchOperation",
    "MetricsResponse",
    "BulkOperationResult",
    "SearchParams",
    "TimeSeriesParams",
    "ExportRequest",
    
    # User schemas
    "UserBase",
    "UserRegister",
    "UserLogin", 
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "UserProfile",
    "UserStats",
    "UserListResponse",
    "TokenResponse",
    "AuthResponse",
    "TokenRefresh",
    
    # Cryptocurrency schemas
    "CryptocurrencyBase",
    "CryptocurrencyCreate",
    "CryptocurrencyUpdate",
    "CryptocurrencyResponse", 
    "CryptocurrencyWithPrice",
    "CryptocurrencyStats",
    "CryptocurrencyList",
    "CryptocurrencySearch",
    "CryptocurrencyBulkUpdate",
    
    # Price data schemas
    "PriceDataBase",
    "PriceDataCreate",
    "PriceDataUpdate",
    "PriceDataResponse",
    "PriceDataWithCrypto",
    "OHLCV",
    "PriceHistoryRequest", 
    "PriceHistoryResponse",
    "PriceStatistics",
    "MLDataRequest",
    "MLDataResponse", 
    "PriceDataBulkInsert",
    "PriceDataAnalytics",
    "RealTimePriceUpdate",
    
    # Prediction schemas
    "PredictionBase", 
    "PredictionCreate",
    "PredictionUpdate",
    "PredictionResponse",
    "PredictionRequest",
    "PredictionResult",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "ModelPerformance",
    "PredictionAnalytics", 
    "PredictionComparison"
]