# File: backend/app/schemas/common.py
# Common Pydantic schemas for shared data structures

from typing import Optional, Any, List, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Type variable for generic responses
DataT = TypeVar('DataT')


class BaseSchema(BaseModel):
    """Base schema with common configuration - FIXED for Pydantic V2"""
    
    model_config = ConfigDict(
        # Enable ORM mode for SQLAlchemy integration
        from_attributes=True,
        # Use enum values instead of names
        use_enum_values=True,
        # Validate assignment when updating fields
        validate_assignment=True
    )


class PaginationParams(BaseModel):
    """Schema for pagination parameters in API requests"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    order_by: str = Field(default="id", description="Field to order by")
    order_desc: bool = Field(default=False, description="Whether to order in descending order")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic schema for paginated API responses"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    items: List[DataT] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there are more items")
    
    @classmethod
    def create(
        cls,
        items: List[DataT],
        total: int,
        skip: int = 0,
        limit: int = 100
    ) -> "PaginatedResponse[DataT]":
        """Create paginated response"""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_next=(skip + limit) < total
        )


class SuccessResponse(BaseModel):
    """Standard success response schema"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(default="success", description="Response status")
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(default="error", description="Response status")
    message: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    error_code: Optional[str] = Field(default=None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthStatus(BaseModel):
    """Health check response schema"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(description="Health status")
    timestamp: datetime = Field(description="Check timestamp")
    version: Optional[str] = Field(default=None, description="Application version")
    components: Optional[dict] = Field(default=None, description="Component health status")


# Backward compatibility alias
HealthCheck = HealthStatus


class DateRangeFilter(BaseModel):
    """Date range filter for API queries"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    start_date: Optional[datetime] = Field(default=None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(default=None, description="End date for filtering")
    
    def validate_date_range(self) -> bool:
        """Validate that start_date is before end_date"""
        if self.start_date and self.end_date:
            return self.start_date <= self.end_date
        return True


class APIResponse(BaseModel, Generic[DataT]):
    """Generic API response wrapper"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: Optional[DataT] = Field(default=None, description="Response data")
    errors: Optional[List[str]] = Field(default=None, description="List of errors if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    @classmethod
    def success_response(
        cls,
        data: Optional[DataT] = None,
        message: str = "Operation successful"
    ) -> "APIResponse[DataT]":
        """Create success response"""
        return cls(
            success=True,
            message=message,
            data=data
        )
    
    @classmethod
    def error_response(
        cls,
        message: str,
        errors: Optional[List[str]] = None
    ) -> "APIResponse[DataT]":
        """Create error response"""
        return cls(
            success=False,
            message=message,
            errors=errors or []
        )


class SortOrder(BaseModel):
    """Schema for sorting parameters - FIXED: regex -> pattern"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    field: str = Field(description="Field to sort by")
    direction: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort direction")


class FilterParams(BaseModel):
    """Base schema for filtering parameters"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    search: Optional[str] = Field(default=None, max_length=255, description="Search term")
    active_only: Optional[bool] = Field(default=None, description="Filter for active items only")
    date_range: Optional[DateRangeFilter] = Field(default=None, description="Date range filter")


class BatchOperation(BaseModel):
    """Schema for batch operations"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    ids: List[int] = Field(description="List of IDs to operate on")
    operation: str = Field(description="Operation to perform")
    parameters: Optional[dict] = Field(default=None, description="Operation parameters")


class MetricsResponse(BaseModel):
    """Schema for metrics and statistics responses"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    period: str = Field(description="Time period for metrics")
    metrics: dict = Field(description="Metrics data")
    summary: Optional[dict] = Field(default=None, description="Summary statistics")


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    success_count: int = Field(description="Number of successful operations")
    error_count: int = Field(description="Number of failed operations")
    errors: List[dict] = Field(default=[], description="List of errors")
    
    @property
    def total_count(self) -> int:
        """Total number of operations attempted"""
        return self.success_count + self.error_count
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100


class SearchParams(BaseModel):
    """Schema for search parameters"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query: str = Field(min_length=1, max_length=255, description="Search query")
    fields: Optional[List[str]] = Field(default=None, description="Fields to search in")
    exact_match: bool = Field(default=False, description="Whether to use exact matching")
    case_sensitive: bool = Field(default=False, description="Whether search is case sensitive")


class TimeSeriesParams(BaseModel):
    """Schema for time series query parameters"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    start_time: datetime = Field(description="Start time for time series")
    end_time: datetime = Field(description="End time for time series")
    interval: str = Field(default="1h", description="Time interval (1m, 5m, 1h, 1d)")
    aggregation: str = Field(default="avg", description="Aggregation method (avg, sum, min, max)")


class ExportRequest(BaseModel):
    """Schema for data export requests"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    format: str = Field(description="Export format (csv, json, xlsx)")
    filters: Optional[FilterParams] = Field(default=None, description="Export filters")
    columns: Optional[List[str]] = Field(default=None, description="Columns to export")
    include_headers: bool = Field(default=True, description="Include headers in export")