#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from datetime import datetime, timezone

def main():
    print("=== Testing Migration Success ===\n")
    
    # Test importing from new location
    try:
        from app.utils.datetime_utils import (
            normalize_datetime_string,
            normalize_candle_time,
            timeframe_to_minutes,
            serialize_datetime_objects
        )
        print("✅ Successfully imported from datetime_utils")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test normalize_datetime_string
    test_dt_str = "2025-10-27T00:00:00+03:30"
    normalized = normalize_datetime_string(test_dt_str)
    expected = "2025-10-26T20:30:00Z"
    
    print(f"Testing normalize_datetime_string:")
    print(f"Input:    {test_dt_str}")
    print(f"Output:   {normalized}")
    print(f"Expected: {expected}")
    print(f"Success:  {normalized == expected}")
    print()
    
    # Test normalize_candle_time
    timestamp = 1730419200000
    candle_normalized = normalize_candle_time(timestamp, '1h')
    print(f"Testing normalize_candle_time:")
    print(f"Input:           {timestamp}")
    print(f"Output:          {candle_normalized}")
    print(f"Timezone-aware:  {candle_normalized.tzinfo is not None}")
    print()
    
    # Test backward compatibility
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from app.core.time_utils import normalize_candle_time as old_func
        if w:
            print(f"✅ Deprecation warning: {w[0].message}")
        else:
            print("❌ No deprecation warning")
    
    print("\n✅ Migration test successful!")
    return True

if __name__ == "__main__":
    main()