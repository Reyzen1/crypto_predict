"""
Time utilities for cryptocurrency data processing

This module provides common time-related utility functions used across
the application for normalizing and processing cryptocurrency market data.
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def normalize_candle_time(candle_time: datetime, timeframe: str) -> datetime:
    """
    Normalize candle time based on timeframe to ensure consistent alignment
    
    This function aligns timestamps to timeframe boundaries to ensure:
    - Consistent data grouping across different sources
    - Proper aggregation alignment for higher timeframes
    - Elimination of sub-timeframe timestamp variations
    
    Args:
        candle_time: Original candle time (datetime object)
        timeframe: Target timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
        
    Returns:
        Normalized datetime aligned to timeframe boundaries
        
    Examples:
        - 1m: 14:37:25 -> 14:37:00 (zero seconds)
        - 5m: 14:37:25 -> 14:35:00 (5-minute boundaries: 00, 05, 10, ...)
        - 1h: 14:37:25 -> 14:00:00 (hour boundaries)
        - 4h: 14:37:25 -> 12:00:00 (4-hour boundaries: 00, 04, 08, 12, 16, 20)
        - 1d: 14:37:25 -> 00:00:00 (start of day UTC)
        - 1w: Mon 14:37:25 -> Mon 00:00:00 (start of week, Monday UTC)
        - 1M: 2024-01-15 14:37:25 -> 2024-01-01 00:00:00 (start of month UTC)
        
    Usage:
        from app.core.time_utils import normalize_candle_time
        
        # Normalize timestamp for 4-hour candle
        normalized_time = normalize_candle_time(
            datetime(2024, 1, 15, 14, 37, 25), 
            '4h'
        )
        # Result: 2024-01-15 12:00:00
    """
    # Handle millisecond timestamp conversion
    if isinstance(candle_time, (int, float)):
        candle_time = datetime.fromtimestamp(candle_time / 1000)
    
    if timeframe == '1m':
        # Align to minute boundaries (zero seconds)
        return candle_time.replace(second=0, microsecond=0)
    
    elif timeframe == '5m':
        # Align to 5-minute boundaries
        minutes = (candle_time.minute // 5) * 5
        return candle_time.replace(minute=minutes, second=0, microsecond=0)
    
    elif timeframe == '15m':
        # Align to 15-minute boundaries
        minutes = (candle_time.minute // 15) * 15
        return candle_time.replace(minute=minutes, second=0, microsecond=0)
    
    elif timeframe == '1h':
        # Align to hour boundaries
        return candle_time.replace(minute=0, second=0, microsecond=0)
    
    elif timeframe == '4h':
        # Align to 4-hour boundaries (0, 4, 8, 12, 16, 20)
        hour = (candle_time.hour // 4) * 4
        return candle_time.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    elif timeframe == '1d':
        # Align to day boundaries (start of day UTC)
        return candle_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    elif timeframe == '1w':
        # Align to week boundaries (Monday 00:00 UTC)
        days_since_monday = candle_time.weekday()
        week_start = candle_time - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    elif timeframe == '1M':
        # Align to month boundaries (first day of month 00:00 UTC)
        return candle_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    else:
        # Default: align to minute boundaries for unknown timeframes
        logger.warning(f"Unknown timeframe '{timeframe}', defaulting to minute alignment")
        return candle_time.replace(second=0, microsecond=0)


def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe string to minutes
    
    Args:
        timeframe: Timeframe string (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
        
    Returns:
        Number of minutes in the timeframe
        
    Examples:
        timeframe_to_minutes('1h')   # Returns 60
        timeframe_to_minutes('4h')   # Returns 240  
        timeframe_to_minutes('1d')   # Returns 1440
    """
    timeframe_map = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '1h': 60,
        '4h': 240,
        '1d': 1440,
        '1w': 10080,
        '1M': 43200  # Approximate 30 days
    }
    return timeframe_map.get(timeframe, 1440)  # Default to daily


def get_supported_timeframes() -> list:
    """
    Get list of supported timeframes
    
    Returns:
        List of supported timeframe strings
    """
    return ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']


def is_valid_timeframe(timeframe: str) -> bool:
    """
    Check if timeframe is valid
    
    Args:
        timeframe: Timeframe string to validate
        
    Returns:
        True if timeframe is supported, False otherwise
    """
    return timeframe in get_supported_timeframes()