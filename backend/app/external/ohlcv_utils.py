from datetime import datetime, timezone
from typing import Any, Dict, List
import logging

from app.utils.datetime_utils import normalize_candle_time

logger = logging.getLogger(__name__)


def convert_ohlcv_to_standardized(asset_id: int, interval: str, raw_ohlcv: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert generic OHLCV-like dictionaries into the project's standardized OHLCV record.

    This supports input shape from both Binance (list-of-lists -> dicts) and TradingView
    (DataFrame iterrows -> dicts with datetime index), as long as each entry contains
    at least: 'timestamp' (datetime or ms int) and numeric open/high/low/close/volume.

    Returns list of dicts matching the repository expected schema.
    """
    records: List[Dict[str, Any]] = []
    if not raw_ohlcv:
        return records

    try:
        for candle in raw_ohlcv:
            try:
                # Accept several timestamp key names
                ts = candle.get('timestamp') if isinstance(candle, dict) else None
                if ts is None:
                    # try other common keys
                    ts = candle.get('candle_time', candle.get('time')) if isinstance(candle, dict) else None

                candle_time = normalize_candle_time(ts, interval)
                open_price = float(candle.get('open') or candle.get('open_price'))
                high_price = float(candle.get('high') or candle.get('high_price'))
                low_price = float(candle.get('low') or candle.get('low_price'))
                close_price = float(candle.get('close') or candle.get('close_price'))
                volume = float(candle.get('volume') or candle.get('quote_volume') or 0)

                rec: Dict[str, Any] = {
                    'asset_id': asset_id,
                    'timeframe': interval,
                    'candle_time': candle_time,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume,
                    'market_cap': candle.get('market_cap') if isinstance(candle, dict) else None,
                }

                # Optional fields
                if isinstance(candle, dict) and 'trades' in candle and candle.get('trades') is not None:
                    try:
                        rec['trade_count'] = int(candle.get('trades'))
                    except Exception:
                        pass

                # VWAP: quote_volume / volume when available and valid
                if isinstance(candle, dict) and candle.get('quote_volume') is not None and volume > 0:
                    try:
                        rec['vwap'] = float(candle.get('quote_volume')) / float(volume)
                    except Exception:
                        pass

                # Validation flag
                rec['is_validated'] = False

                records.append(rec)

            except Exception as e:
                logger.warning(f"Skipping candle due to conversion error: {e}")
                continue

    except Exception as e:
        logger.error(f"Error converting raw OHLCV to standardized format: {e}")

    return records
