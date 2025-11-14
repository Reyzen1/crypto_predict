# backend/app/utils/datetime_utils.py
# Comprehensive datetime utilities for cryptocurrency data processing

from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def normalize_datetime(dt: Union[datetime, None]) -> Optional[datetime]:
    """
    Normalize datetime object by removing timezone information for consistent comparison
    
    Strategy: Convert all datetime objects to naive datetime for consistent comparison.
    This eliminates timezone mismatch issues between database records (+03:30) 
    and input data (naive datetime).
    
    Args:
        dt: Datetime object (timezone-aware or naive)
        
    Returns:
        Naive datetime object or None if input is None
    """
    if dt is None:
        return None
    
    if not isinstance(dt, datetime):
        try:
            # Try to convert string to datetime if needed
            if isinstance(dt, str):
                # Handle ISO format strings
                if 'T' in dt:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                else:
                    return None
            else:
                return None
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse datetime: {dt}")
            return None
    
    # Convert to UTC and then remove timezone info for consistent naive datetime
    if dt.tzinfo is not None:
        # First convert to UTC to preserve actual time, then make naive
        dt_utc = dt  #.astimezone(timezone.utc)
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc
    
    return dt


def compare_datetimes(dt1: Union[datetime, None], dt2: Union[datetime, None]) -> bool:
    """
    Compare two datetime objects after normalizing them to naive datetime
    
    Args:
        dt1: First datetime object
        dt2: Second datetime object
        
    Returns:
        True if datetimes are equal after normalization
    """
    normalized_dt1 = normalize_datetime(dt1)
    normalized_dt2 = normalize_datetime(dt2)
    
    # Handle None cases
    if normalized_dt1 is None and normalized_dt2 is None:
        return True
    if normalized_dt1 is None or normalized_dt2 is None:
        return False
    
    return normalized_dt1 == normalized_dt2


def normalize_datetime_list(datetime_list: list) -> list:
    """
    Normalize a list of datetime objects
    
    Args:
        datetime_list: List of datetime objects
        
    Returns:
        List of normalized naive datetime objects
    """
    return [normalize_datetime(dt) for dt in datetime_list if dt is not None]


def normalize_datetime_dict_keys(datetime_dict: dict) -> dict:
    """
    Normalize datetime keys in a dictionary
    
    Args:
        datetime_dict: Dictionary with datetime keys
        
    Returns:
        Dictionary with normalized datetime keys
    """
    normalized_dict = {}
    for key, value in datetime_dict.items():
        if isinstance(key, datetime):
            normalized_key = normalize_datetime(key)
            if normalized_key is not None:
                normalized_dict[normalized_key] = value
        else:
            normalized_dict[key] = value
    
    return normalized_dict


# Legacy support functions for backward compatibility
def remove_timezone(dt: Union[datetime, None]) -> Optional[datetime]:
    """
    Legacy function - use normalize_datetime instead
    Remove timezone information from datetime object
    """
    return normalize_datetime(dt)


def make_timezone_aware(dt: Union[datetime, None], tzinfo=None) -> Optional[datetime]:
    """
    Make datetime timezone-aware (NOT RECOMMENDED for new code)
    
    Note: This function is provided for completeness but we recommend
    using normalize_datetime() for consistent naive datetime handling
    """
    if dt is None:
        return None
    
    if not isinstance(dt, datetime):
        return None
    
    if dt.tzinfo is None:
        from datetime import timezone
        tzinfo = tzinfo or timezone.utc
        return dt.replace(tzinfo=tzinfo)
    
    return dt


def to_aware_utc(dt: Union[datetime, int, float, str, None]) -> Optional[datetime]:
    """
    Ensure the input is a timezone-aware datetime in UTC.

    - If input is numeric (assumed milliseconds), converts to UTC datetime.
    - If input is a naive datetime, assumes UTC and attaches tzinfo=UTC.
    - If input is timezone-aware, converts to UTC.
    - If input is an ISO8601 string, attempts to parse it.
    Returns None for invalid input.
    """
    if dt is None:
        return None

    # Millisecond timestamp
    if isinstance(dt, (int, float)):
        try:
            return datetime.fromtimestamp(dt / 1000.0, tz=timezone.utc)
        except Exception:
            return None

    # String input
    if isinstance(dt, str):
        try:
            dt_parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            if dt_parsed.tzinfo is None:
                return dt_parsed.replace(tzinfo=timezone.utc)
            return dt_parsed.astimezone(timezone.utc)
        except Exception:
            return None

    # Datetime input
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return None


def canonical_datetime_key(dt: Union[datetime, int, float, str, None]) -> Optional[str]:
    """
    Return a canonical string key for a datetime suitable for dictionary lookups.

    The canonical form is the ISO8601 string of the datetime converted to UTC
    (e.g. '2025-11-06T00:00:00+00:00'). Returns None if dt is invalid.
    """
    aw = to_aware_utc(dt)
    if aw is None:
        return None
    return aw.isoformat()


# ============================================================================
# Candle Time and Timeframe Utilities (moved from time_utils.py)
# ============================================================================

def normalize_candle_time(candle_time: Union[datetime, int, float], timeframe: str) -> datetime:
    """
    Normalize candle time based on timeframe to ensure consistent alignment
    
    This function aligns timestamps to timeframe boundaries to ensure:
    - Consistent data grouping across different sources
    - Proper aggregation alignment for higher timeframes
    - Elimination of sub-timeframe timestamp variations
    
    Args:
        candle_time: Original candle time (datetime object, timestamp int/float)
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
    """
    # Handle millisecond timestamp conversion
    if isinstance(candle_time, (int, float)):
        # Always create timezone-aware datetime in UTC for consistency
        candle_time = datetime.fromtimestamp(candle_time / 1000, tz=timezone.utc)
    
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


def serialize_datetime_objects(obj: Any) -> Any:
    """
    Convert datetime objects to ISO format strings in nested data structures
    
    Args:
        obj: Any object that may contain datetime objects
        
    Returns:
        Object with datetime objects converted to ISO strings
        
    Examples:
        # Simple datetime
        serialize_datetime_objects(datetime(2025, 11, 1, 12, 30))
        # Returns: '2025-11-01T12:30:00'
        
        # Dictionary with datetime
        serialize_datetime_objects({
            'created_at': datetime(2025, 11, 1, 12, 30),
            'name': 'BTC'
        })
        # Returns: {'created_at': '2025-11-01T12:30:00', 'name': 'BTC'}
        
        # Nested structures
        serialize_datetime_objects({
            'data': [
                {'timestamp': datetime(2025, 11, 1), 'value': 100},
                {'timestamp': datetime(2025, 11, 2), 'value': 200}
            ]
        })
        # Returns nested structure with datetime strings
    """
    if isinstance(obj, dict):
        return {k: serialize_datetime_objects(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_objects(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj