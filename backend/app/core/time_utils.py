"""
Time utilities for cryptocurrency data processing (DEPRECATED)

This module is deprecated. All datetime utilities have been moved to:
app.utils.datetime_utils

This file remains for backward compatibility only.
"""

# Backward compatibility imports - all functions moved to datetime_utils
from ..utils.datetime_utils import (
    normalize_candle_time,
    timeframe_to_minutes,
    get_supported_timeframes,
    is_valid_timeframe,
    serialize_datetime_objects,
)

# Deprecation warning
import warnings
warnings.warn(
    "app.core.time_utils is deprecated. Use app.utils.datetime_utils instead.",
    DeprecationWarning,
    stacklevel=2
)