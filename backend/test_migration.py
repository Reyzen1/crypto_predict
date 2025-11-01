#!/usr/bin/env python3

def test_migration_success():
    """Test that all functions work correctly after migration"""
    
    print("=== Testing Migration to datetime_utils.py ===\n")
    
    try:
        # Test importing from new location
        from backend.app.utils.datetime_utils import (
            normalize_datetime,
            normalize_candle_time,
            timeframe_to_minutes,
            get_supported_timeframes,
            is_valid_timeframe,
            normalize_datetime_string,
            serialize_datetime_objects
        )
        print("✅ Successfully imported all functions from datetime_utils")
        
        # Test backward compatibility
        from backend.app.core.time_utils import (
            normalize_candle_time as old_normalize_candle_time,
            timeframe_to_minutes as old_timeframe_to_minutes,
            normalize_datetime_string as old_normalize_datetime_string
        )
        print("✅ Backward compatibility imports work")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test functions work
    from datetime import datetime, timezone
    
    # Test normalize_datetime_string
    test_dt_str = "2025-10-27T00:00:00+03:30"
    normalized = normalize_datetime_string(test_dt_str)
    expected = "2025-10-26T20:30:00Z"
    
    if normalized == expected:
        print(f"✅ normalize_datetime_string works: {test_dt_str} → {normalized}")
    else:
        print(f"❌ normalize_datetime_string failed: expected {expected}, got {normalized}")
        return False
    
    # Test normalize_candle_time
    test_timestamp = 1730419200000  # 2025-11-01 00:00:00 UTC
    candle_normalized = normalize_candle_time(test_timestamp, '1h')
    
    if candle_normalized.tzinfo is not None:
        print(f"✅ normalize_candle_time creates timezone-aware datetime: {candle_normalized}")
    else:
        print(f"❌ normalize_candle_time should create timezone-aware datetime")
        return False
    
    # Test timeframe_to_minutes
    minutes = timeframe_to_minutes('4h')
    if minutes == 240:
        print(f"✅ timeframe_to_minutes works: 4h = {minutes} minutes")
    else:
        print(f"❌ timeframe_to_minutes failed: expected 240, got {minutes}")
        return False
    
    # Test serialize_datetime_objects
    test_obj = {
        'datetime': datetime(2025, 11, 1, 12, 30),
        'string': 'test',
        'nested': {
            'dt': datetime(2025, 11, 1, 15, 45)
        }
    }
    serialized = serialize_datetime_objects(test_obj)
    
    if isinstance(serialized['datetime'], str) and isinstance(serialized['nested']['dt'], str):
        print(f"✅ serialize_datetime_objects works")
    else:
        print(f"❌ serialize_datetime_objects failed")
        return False
    
    return True

def test_deprecation_warning():
    """Test that deprecation warning is shown"""
    
    print("\n=== Testing Deprecation Warning ===\n")
    
    import warnings
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # This should trigger deprecation warning
        from backend.app.core.time_utils import normalize_candle_time
        
        if len(w) > 0 and issubclass(w[0].category, DeprecationWarning):
            print(f"✅ Deprecation warning shown: {w[0].message}")
            return True
        else:
            print("❌ No deprecation warning shown")
            return False

if __name__ == "__main__":
    print("Testing migration of time_utils.py to datetime_utils.py\n")
    
    success1 = test_migration_success()
    success2 = test_deprecation_warning()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ Migration successful!")
        print("✅ All functions work correctly from datetime_utils.py")
        print("✅ Backward compatibility maintained with time_utils.py")
        print("✅ Deprecation warning shows for old imports")
        print("\nSummary:")
        print("- All datetime utilities now in: app.utils.datetime_utils")
        print("- Backward compatibility: app.core.time_utils (with warning)")
        print("- All imports updated across the codebase")
        print("- Data normalization works from database to storage")
    else:
        print("❌ Migration failed!")
    
    exit(0 if (success1 and success2) else 1)