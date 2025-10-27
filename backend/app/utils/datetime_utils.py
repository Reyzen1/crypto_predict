# backend/app/utils/datetime_utils.py
# Timezone normalization utilities

from datetime import datetime
from typing import Union, Optional
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
    
    # Remove timezone info to create naive datetime
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    
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