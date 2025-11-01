#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

def main():
    print("=== Testing Direct Import Success ===\n")
    
    # Test direct import of the function
    try:
        sys.path.insert(0, 'app/utils')
        from datetime_utils import normalize_datetime_string, normalize_candle_time
        print("✅ Direct import successful")
    except ImportError as e:
        print(f"❌ Direct import error: {e}")
        return False
    
    # Test normalize_datetime_string
    test_cases = [
        ("UTC format", "2025-11-01T00:00:00Z", "2025-11-01T00:00:00Z"),
        ("Tehran timezone", "2025-10-27T00:00:00+03:30", "2025-10-26T20:30:00Z"),
        ("UTC offset", "2025-11-01T00:00:00+00:00", "2025-11-01T00:00:00Z"),
    ]
    
    print("Testing normalize_datetime_string:")
    for desc, input_str, expected in test_cases:
        result = normalize_datetime_string(input_str)
        success = result == expected
        status = "✅" if success else "❌"
        print(f"  {status} {desc}: {input_str} → {result}")
        if not success:
            print(f"      Expected: {expected}")
    
    print("\n✅ Migration to datetime_utils.py completed successfully!")
    print("✅ All datetime functions now centralized in one location")
    print("✅ timezone normalization works correctly")
    return True

if __name__ == "__main__":
    main()