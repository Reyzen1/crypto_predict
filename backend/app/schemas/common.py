# File: ./backend/app/schemas/common.py
# Common Pydantic schemas for shared data structures

from typing import Optional, Any, List, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

# Type variable for generic responses
DataT = TypeVar('DataT')


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    class Config:
        # Enable ORM mode for SQLAlchemy integration
        from_attributes = True
        # Use enum values instead of names
        use_enum_values = True
        # Validate assignment when updating fields
        validate_assignment = True


class PaginationParams(BaseModel):
    """Schema for pagination parameters in API requests"""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    order_by: str = Field(default="id", description="Field to order by")
    order_desc: bool = Field(default=False, description="Whether to order in descending order")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic schema for paginated API responses"""
    
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
        """Create a paginated response"""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_next=skip + len(items) < total
        )


class SuccessResponse(BaseModel):
    """Schema for successful API responses"""
    
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")


class ErrorResponse(BaseModel):
    """Schema for error API responses"""
    
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Any] = Field(default=None, description="Additional error details")


class HealthCheck(BaseModel):
    """Schema for health check responses"""
    
    status: str = Field(description="Service status")
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="Application version")
    database: bool = Field(description="Database connection status")
    redis: bool = Field(description="Redis connection status")


class SearchParams(BaseModel):
    """Schema for search parameters"""
    
    query: str = Field(min_length=1, max_length=100, description="Search query")
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")


class DateRangeFilter(BaseModel):
    """Schema for date range filtering"""
    
    start_date: Optional[datetime] = Field(default=None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(default=None, description="End date for filtering")
    
    def validate_date_range(self) -> bool:
        """Validate that start_date is before end_date"""
        if self.start_date and self.end_date:
            return self.start_date <= self.end_date
        return True


class BulkOperation(BaseModel):
    """Schema for bulk operations"""
    
    ids: List[int] = Field(min_length=1, max_length=100, description="List of IDs to operate on")
    action: str = Field(description="Action to perform")


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results"""
    
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