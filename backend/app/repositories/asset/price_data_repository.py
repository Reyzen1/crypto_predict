# backend/app/repositories/asset/price_data.py
# Repository for price data management

from typing import List, Optional, Dict, Any, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from ..base_repository import BaseRepository
from app.models.asset.price_data import PriceData
from app.models.asset import Asset
from app.utils.datetime_utils import normalize_datetime, compare_datetimes, normalize_datetime_dict_keys, serialize_datetime_objects


class PriceDataRepository(BaseRepository):
    """
    Repository for cryptocurrency price data management
    """
    
    def __init__(self, db: Session):
        super().__init__(PriceData, db)
    
    def get_by_asset(self, asset_id: int, limit: int = 100) -> List[PriceData]:
        """Get recent price data for an asset"""
        print(f"Debug: return self.db.query(PriceData).filter(")
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.candle_time.desc()).limit(limit).all()
    
    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[PriceData]:
        """Get recent price data by symbol"""
        print(f"Debug: return self.db.query(PriceData).join(Asset).filter(")
        return self.db.query(PriceData).join(Asset).filter(
            Asset.symbol == symbol
        ).order_by(PriceData.candle_time.desc()).limit(limit).all()
    

    def get_price_statistics(self, asset_id: int, days: int = 30) -> Dict[str, Any]:
        """Get price statistics for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        print(f"Debug: stats = self.db.query(")
        stats = self.db.query(
            func.max(PriceData.high_price).label('max_price'),
            func.min(PriceData.low_price).label('min_price'),
            func.avg(PriceData.close_price).label('avg_price'),
            func.sum(PriceData.volume).label('total_volume'),
            func.count(PriceData.id).label('data_points')
        ).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).first()
        
        if not stats:
            return {}
        
        return {
            'max_price': float(stats.max_price) if stats.max_price else 0,
            'min_price': float(stats.min_price) if stats.min_price else 0,
            'avg_price': float(stats.avg_price) if stats.avg_price else 0,
            'total_volume': float(stats.total_volume) if stats.total_volume else 0,
            'data_points': stats.data_points or 0,
            'price_volatility': self._calculate_volatility(asset_id, days)
        }
    
    def _calculate_volatility(self, asset_id: int, days: int) -> float:
        """
        Calculate price volatility using percentage returns
        
        Uses close_price for volatility calculation based on daily returns
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        print(f"Debug: prices = self.db.query(PriceData.close_price).filter(")
        prices = self.db.query(PriceData.close_price).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).order_by(PriceData.candle_time.asc()).all()
        
        if len(prices) < 2:
            return 0.0
        
        price_list = [float(p.close_price) for p in prices]
        returns = [(price_list[i] - price_list[i-1]) / price_list[i-1] for i in range(1, len(price_list))]
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def get_missing_data_gaps(self, asset_id: int, expected_interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """Identify gaps in price data"""
        print("**********get_missing_data_gaps->recent_data = self.db.query(PriceData.candle_time).filter(")
        recent_data = self.db.query(PriceData.candle_time).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.candle_time.desc()).limit(1000).all()
        
        if len(recent_data) < 2:
            return []
        
        gaps = []
        timestamps = [d.candle_time for d in reversed(recent_data)]
        expected_delta = timedelta(minutes=expected_interval_minutes)
        
        for i in range(1, len(timestamps)):
            actual_gap = timestamps[i] - timestamps[i-1]
            if actual_gap > expected_delta * 1.5:  # Allow 50% tolerance
                gaps.append({
                    'start': timestamps[i-1].isoformat(),
                    'end': timestamps[i].isoformat(),
                    'duration_minutes': actual_gap.total_seconds() / 60,
                    'expected_minutes': expected_interval_minutes
                })
        
        return gaps

    def _get_existing_records(self, asset_id: int, timeframe: str, candle_times: List) -> Dict:
        """Get existing records for bulk comparison with timezone normalization"""
        if not candle_times:
            return {}

        existing_query = self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timeframe == timeframe,
            PriceData.candle_time.in_(candle_times)
        ).all()
        
        # Create lookup dictionary with consistent timezone normalization
        existing_records = {}
        for record in existing_query:
            normalized_time = normalize_datetime(record.candle_time)
            if normalized_time is not None:
                existing_records[normalized_time] = record
        
        return existing_records

    def _get_existing_record(self, existing_records: Dict, candle_time) -> Optional[PriceData]:
        """Get existing record with timezone normalization"""
        normalized_time = normalize_datetime(candle_time)
        return existing_records.get(normalized_time) if normalized_time is not None else None

    # --- Technical indicator helpers (used by bulk insert) ---
    def _compute_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Simple moving average of last `period` values. Returns None if insufficient data."""
        if not prices or len(prices) < period:
            return None
        window = prices[-period:]
        return sum(window) / float(period)

    def _compute_ema_last(self, prices: List[float], period: int) -> Optional[float]:
        """Compute the EMA for the last value in prices using period. Returns None if insufficient history."""
        if not prices or len(prices) < period:
            return None
        alpha = 2.0 / (period + 1)
        # initial EMA = SMA of first `period` values
        ema = sum(prices[:period]) / float(period)
        for price in prices[period:]:
            ema = (price - ema) * alpha + ema
        return ema

    def _compute_rsi_last(self, prices: List[float], period: int) -> Optional[float]:
        """Compute RSI (Wilder smoothing) and return last RSI value. Returns None if insufficient data."""
        if not prices or len(prices) < period + 1:
            return None
        gains = []
        losses = []
        # first window
        for i in range(1, period + 1):
            delta = prices[i] - prices[i - 1]
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Wilder smoothing for remainder of series
        for i in range(period + 1, len(prices)):
            delta = prices[i] - prices[i - 1]
            gain = max(delta, 0.0)
            loss = abs(min(delta, 0.0))
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi


    def _should_update_existing_record(self, existing: PriceData, new_data: Dict) -> bool:
        """Check if existing record should be updated based on price changes"""
        def safe_compare(existing_val, new_val, tolerance=1e-8):
            if existing_val is None and new_val is None:
                return True
            if existing_val is None or new_val is None:
                return False
            try:
                existing_float = float(existing_val)
                new_float = float(new_val)
                return abs(existing_float - new_float) < tolerance
            except (ValueError, TypeError):
                return existing_val == new_val
        
        # Check if key price fields have changed
        price_unchanged = (
            safe_compare(existing.close_price, new_data.get('close_price')) and
            safe_compare(existing.low_price, new_data.get('low_price')) and
            safe_compare(existing.high_price, new_data.get('high_price'))
        )
        print(f"existing:close_price={existing.close_price}, low_price={existing.low_price}, , high_price={existing.high_price}")
        print(f"new_data:close_price={new_data.get('close_price')}, low_price={new_data.get('low_price')}, , high_price={new_data.get('high_price')}")
        
        return not price_unchanged

    def _update_existing_record(self, existing: PriceData, new_data: Dict) -> None:
        """Update existing record with new data"""
        for key, value in new_data.items():
            if key not in ['asset_id', 'timeframe', 'candle_time'] and hasattr(existing, key):
                setattr(existing, key, value)
    
    def bulk_insert(self, asset: Asset, price_data_list: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]], 
                   timeframe: Union[str, List[str]] = '1h', enable_auto_aggregation: bool = True) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        True bulk insert with unified multi-timeframe support for maximum performance
        
        Processes all timeframes in a single transaction with batch operations:
        - Single timeframe: Maintains backward compatibility 
        - Multiple timeframes: True bulk processing with single database operations
        - Auto-aggregation: Automatically creates higher timeframe data (4h, 1d, etc.)
        
        Args:
            asset: Asset object (already loaded with cache data)
            price_data_list: 
                - For single timeframe: List of price data dictionaries
                - For multiple timeframes: Dict with timeframe as key, List[Dict] as value
            timeframe: 
                - Single timeframe: str (e.g., '1h')
                - Multiple timeframes: List[str] (e.g., ['4h', '1d', '1w'])
            enable_auto_aggregation: If True, automatically aggregate to higher timeframes
                
        Returns:
            - For single timeframe: Dict with operation statistics (includes aggregation stats)
            - For multiple timeframes: Dict[timeframe, Dict[statistics]] (includes aggregation stats)
        """
        # Normalize inputs for unified processing
        if isinstance(timeframe, str):
            # Single timeframe: convert to multi-timeframe format for unified processing
            timeframes = [timeframe]
            if isinstance(price_data_list, dict):
                # If dict provided for single timeframe, extract the data
                price_data_dict = price_data_list
            else:
                # Convert list to dict format
                price_data_dict = {timeframe: price_data_list}
        else:
            # Multiple timeframes: validate input format
            timeframes = timeframe
            if isinstance(price_data_list, dict):
                price_data_dict = price_data_list
            else:
                # Invalid: list provided for multi-timeframe
                return {tf: {'status': 'error', 'error': 'Invalid input: expected dict for multi-timeframe mode', 'success': False} for tf in timeframes}
        
        return self._unified_bulk_insert(asset, price_data_dict, timeframes, enable_auto_aggregation)
    
    def _unified_bulk_insert(self, asset: Asset, price_data_dict: Dict[str, List[Dict[str, Any]]], 
                           timeframes: List[str], enable_auto_aggregation: bool = True) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        True unified bulk insert processing all timeframes in single transaction
        
        This is the core implementation that processes multiple timeframes efficiently:
        - Single database transaction for all timeframes
        - Batch queries for existing record checks
        - Bulk insert operations across all timeframes
        - Unified error handling and cache updates
        - Auto-aggregation to higher timeframes with complete statistics
        
        Args:
            enable_auto_aggregation: If True, automatically creates higher timeframe data
        """
        try:
            # Initialize results tracking
            results = {}
            total_inserted = 0
            total_updated = 0 
            total_skipped = 0
            
            # Validate input consistency
            if not isinstance(price_data_dict, dict):
                error_result = {'status': 'error', 'error': 'Invalid input format', 'success': False}
                return error_result if len(timeframes) == 1 else {tf: error_result for tf in timeframes}
            
            # Early return for empty data
            if not any(price_data_dict.get(tf, []) for tf in timeframes):
                empty_result = {
                    'status': 'success', 'total_processed': 0, 'inserted_records': 0,
                    'updated_records': 0, 'skipped_records': 0, 'data_range': {'start': None, 'end': None}, 'success': True
                }
                return empty_result if len(timeframes) == 1 else {tf: empty_result for tf in timeframes}
            
            # === PHASE 1: Process each timeframe and collect operations ===
            timeframe_stats, all_records_to_insert, all_records_to_update, all_records_to_skip = self._process_all_timeframes(
                asset, price_data_dict, timeframes
            )
            
            # === PHASE 2: Execute bulk operations ===
            total_inserted, total_updated, total_skipped = self._execute_bulk_operations(
                all_records_to_insert, all_records_to_update, all_records_to_skip, asset
            )
            
            # === PHASE 3: Update asset caches ===
            if total_inserted > 0 or total_updated > 0:
                self._update_asset_caches(asset, timeframes, timeframe_stats)
            
            # === PHASE 4: Auto-aggregation to higher timeframes ===
            aggregation_stats = {}
            if enable_auto_aggregation and (total_inserted > 0 or total_updated > 0):
                aggregation_stats = self._perform_auto_aggregation(asset, timeframes, timeframe_stats)
            
            # === PHASE 5: Build and return results with aggregation stats ===
            return self._build_final_results_with_aggregation(timeframes, timeframe_stats, aggregation_stats)
                
        except Exception as e:
            print(f"********unified_bulk_insert--> error: {str(e)}")
            self.db.rollback()
            error_result = {
                'status': 'error',
                'error': str(e),
                'total_processed': 0,
                'inserted_records': 0,
                'updated_records': 0,
                'skipped_records': 0,
                'data_range': {'start': None, 'end': None},
                'success': False
            }
            return error_result if len(timeframes) == 1 else {tf: error_result for tf in timeframes}

       
    def get_data_quality_report(self, asset_id: int, days: int = 7) -> Dict[str, Any]:
        """Generate data quality report for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Combined query for all quality metrics in one database call
        from sqlalchemy import case
        print("********get_data_quality_report->quality_stats = self.db.query")
        quality_stats = self.db.query(
            func.count(PriceData.id).label('total_records'),
            func.sum(case((PriceData.close_price.is_(None), 1), else_=0)).label('missing_price'),
            func.sum(case((PriceData.volume.is_(None), 1), else_=0)).label('missing_volume'),
            func.sum(case((PriceData.close_price <= 0, 1), else_=0)).label('zero_prices')
        ).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).first()
        
        # Extract results from the combined query
        total_records = quality_stats.total_records or 0
        missing_price = quality_stats.missing_price or 0
        missing_volume = quality_stats.missing_volume or 0
        zero_prices = quality_stats.zero_prices or 0
        
        # Check data gaps
        print("********get_data_quality_report->get_missing_data_gaps")
        gaps = self.get_missing_data_gaps(asset_id, 5)
        # Calculate quality score           
        quality_score = 100
        if total_records > 0:
            quality_score -= (missing_price / total_records * 30)  # 30% penalty for missing prices
            quality_score -= (missing_volume / total_records * 20)  # 20% penalty for missing volume
            quality_score -= (zero_prices / total_records * 25)     # 25% penalty for zero prices
            quality_score -= min(len(gaps), 5) * 5                  # 5% penalty per gap (max 25%)
        
        result = {
            'asset_id': asset_id,
            'period_days': days,
            'total_records': total_records or 0,
            'missing_price': missing_price or 0,
            'missing_volume': missing_volume or 0,
            'zero_prices': zero_prices or 0,
            'data_gaps': len(gaps),
            'quality_score': max(0, round(quality_score, 1)),
            'quality_grade': 'A' if quality_score >= 90 else 'B' if quality_score >= 80 else 'C' if quality_score >= 70 else 'D' if quality_score >= 60 else 'F'
        }

        return result

    def get_timeframe_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Get timeframe hierarchy and aggregation rules"""
        return {
            '1m': {'minutes': 1, 'base_timeframe': None},
            '5m': {'minutes': 5, 'base_timeframe': '1m'},
            '15m': {'minutes': 15, 'base_timeframe': '5m'},
            '1h': {'minutes': 60, 'base_timeframe': '15m'},
            '4h': {'minutes': 240, 'base_timeframe': '1h'},
            '1d': {'minutes': 1440, 'base_timeframe': '4h'},
            '1w': {'minutes': 10080, 'base_timeframe': '1d'},
            '1M': {'minutes': 43200, 'base_timeframe': '1w'}  # Approximate 30 days
        }

    def get_aggregatable_timeframes(self, source_timeframe: str) -> List[str]:
        """Get list of timeframes that can be aggregated from source timeframe"""
        hierarchy = self.get_timeframe_hierarchy()
        source_minutes = hierarchy.get(source_timeframe, {}).get('minutes', 0)
        
        if not source_minutes:
            return []
        
        aggregatable = []
        for tf, info in hierarchy.items():
            tf_minutes = info['minutes']
            if tf_minutes > source_minutes and tf_minutes % source_minutes == 0:
                aggregatable.append(tf)
        
        return sorted(aggregatable, key=lambda x: hierarchy[x]['minutes'])

    def aggregate_to_higher_timeframe(self, asset_id: int, source_timeframe: str, 
                                    target_timeframe: Union[str, List[str]], start_time: datetime = None, 
                                    end_time: datetime = None) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Aggregate price data from source timeframe to higher target timeframe(s) using SQL
        
        Args:
            asset_id: Asset ID to aggregate data for
            source_timeframe: Source timeframe (e.g., '1h')
            target_timeframe: Target timeframe (e.g., '4h', '1d') or list of target timeframes
            start_time: Start time for aggregation (optional)
            end_time: End time for aggregation (optional)
            
        Returns:
            - If target_timeframe is string: List of aggregated OHLCV data
            - If target_timeframe is list: Dict with timeframe as key and List[Dict] as value
        """
        # Handle both single timeframe and multiple timeframes
        if isinstance(target_timeframe, str):
            target_timeframes = [target_timeframe]
            return_single = True
        else:
            target_timeframes = target_timeframe
            return_single = False
        
        hierarchy = self.get_timeframe_hierarchy()
        
        # Validate source timeframe
        if source_timeframe not in hierarchy:
            raise ValueError(f"Invalid source timeframe: {source_timeframe}")
        
        source_minutes = hierarchy[source_timeframe]['minutes']
        
        # Validate all target timeframes
        for tf in target_timeframes:
            if tf not in hierarchy:
                raise ValueError(f"Invalid target timeframe: {tf}")
            
            target_minutes = hierarchy[tf]['minutes']
            
            if target_minutes <= source_minutes:
                raise ValueError(f"Target timeframe {tf} must be higher than source {source_timeframe}")
            
            if target_minutes % source_minutes != 0:
                raise ValueError(f"Target timeframe {tf} must be divisible by source {source_timeframe}")
        
        # Process all timeframes in a single query
        result = self._aggregate_multiple_timeframes_single_query(
            asset_id=asset_id,
            source_timeframe=source_timeframe,
            target_timeframes=target_timeframes,
            start_time=start_time,
            end_time=end_time
        )
        
        # Return format based on input
        if return_single:
            return result[target_timeframes[0]]
        else:
            return result
    
    def _aggregate_multiple_timeframes_single_query(self, asset_id: int, source_timeframe: str,
                                                   target_timeframes: List[str], start_time: datetime = None,
                                                   end_time: datetime = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate data for multiple target timeframes in a single optimized query
        
        This method uses a single SQL query with multiple CTEs to process all target timeframes
        at once, dramatically improving performance compared to running separate queries.
        
        Args:
            asset_id: Asset ID to aggregate data for
            source_timeframe: Source timeframe (e.g., '1h')
            target_timeframes: List of target timeframes (e.g., ['4h', '1d', '1w'])
            start_time: Start time for aggregation (optional)
            end_time: End time for aggregation (optional)
            
        Returns:
            Dict with timeframe as key and aggregated data list as value
        """
        from sqlalchemy import text
        
        # Build dynamic query for all timeframes
        timeframe_ctes = []
        union_selects = []
        
        for tf in target_timeframes:
            interval_expression = self._get_time_grouping_expression(tf)
            cte_name = f"tf_{tf.replace('h', 'h').replace('d', 'd').replace('w', 'w').replace('M', 'm')}"
            
            # Create CTE for each timeframe
            timeframe_ctes.append(f"""
            {cte_name}_agg AS (
                SELECT 
                    '{tf}' as timeframe,
                    DATE_TRUNC('{interval_expression}', candle_time) as period_start,
                    MAX(high_price) as high_price,
                    MIN(low_price) as low_price,
                    SUM(volume) as volume,
                    AVG(market_cap) as avg_market_cap,
                    SUM(trade_count) as total_trades,
                    SUM(close_price * volume) / NULLIF(SUM(volume), 0) as vwap,
                    COUNT(id) as source_records
                FROM price_data 
                WHERE asset_id = :asset_id 
                    AND timeframe = :source_timeframe
                    {' AND candle_time >= :start_time' if start_time else ''}
                    {' AND candle_time <= :end_time' if end_time else ''}
                GROUP BY DATE_TRUNC('{interval_expression}', candle_time)
            ),
            {cte_name}_open_close AS (
                SELECT 
                    '{tf}' as timeframe,
                    DATE_TRUNC('{interval_expression}', candle_time) as period,
                    FIRST_VALUE(open_price) OVER (
                        PARTITION BY DATE_TRUNC('{interval_expression}', candle_time) 
                        ORDER BY candle_time ASC 
                        ROWS UNBOUNDED PRECEDING
                    ) as first_open,
                    FIRST_VALUE(close_price) OVER (
                        PARTITION BY DATE_TRUNC('{interval_expression}', candle_time) 
                        ORDER BY candle_time DESC 
                        ROWS UNBOUNDED PRECEDING
                    ) as last_close,
                    ROW_NUMBER() OVER (
                        PARTITION BY DATE_TRUNC('{interval_expression}', candle_time) 
                        ORDER BY candle_time ASC
                    ) as rn
                FROM price_data 
                WHERE asset_id = :asset_id 
                    AND timeframe = :source_timeframe
                    {' AND candle_time >= :start_time' if start_time else ''}
                    {' AND candle_time <= :end_time' if end_time else ''}
            )""")
            
            # Create UNION SELECT for each timeframe
            union_selects.append(f"""
                SELECT 
                    agg.timeframe,
                    agg.period_start,
                    oc.first_open as open_price,
                    agg.high_price,
                    agg.low_price,
                    oc.last_close as close_price,
                    agg.volume,
                    agg.avg_market_cap,
                    agg.total_trades,
                    agg.vwap,
                    agg.source_records
                FROM {cte_name}_agg agg
                JOIN (
                    SELECT DISTINCT timeframe, period, first_open, last_close
                    FROM {cte_name}_open_close 
                    WHERE rn = 1
                ) oc ON agg.period_start = oc.period AND agg.timeframe = oc.timeframe
            """)
        
        # Combine all CTEs and UNIONs into a single query
        comprehensive_query = text(f"""
            WITH {', '.join(timeframe_ctes)}
            {' UNION ALL '.join(union_selects)}
            ORDER BY timeframe, period_start ASC
        """)
        
        # Execute the comprehensive query
        query_params = {
            'asset_id': asset_id,
            'source_timeframe': source_timeframe
        }
        if start_time:
            query_params['start_time'] = start_time
        if end_time:
            query_params['end_time'] = end_time
        
        results = self.db.execute(comprehensive_query, query_params).fetchall()
        
        # Group results by timeframe
        timeframe_results = {tf: [] for tf in target_timeframes}
        
        for row in results:
            timeframe_data = {
                'asset_id': asset_id,
                'timeframe': row.timeframe,
                'candle_time': row.period_start,
                'open_price': float(row.open_price) if row.open_price else 0,
                'high_price': float(row.high_price) if row.high_price else 0,
                'low_price': float(row.low_price) if row.low_price else 0,
                'close_price': float(row.close_price) if row.close_price else 0,
                'volume': float(row.volume) if row.volume else 0,
                'market_cap': float(row.avg_market_cap) if row.avg_market_cap else None,
                'trade_count': int(row.total_trades) if row.total_trades else None,
                'vwap': float(row.vwap) if row.vwap else None,
                'is_validated': False
            }
            timeframe_results[row.timeframe].append(timeframe_data)
        
        return timeframe_results
    
    def _get_time_grouping_expression(self, timeframe: str) -> str:
        """
        Get the PostgreSQL time grouping expression for a given timeframe
        
        Args:
            timeframe: Target timeframe (e.g., '1h', '4h', '1d', '1w', '1M')
            
        Returns:
            PostgreSQL compatible interval expression
        """
        if timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            return f'{hours} hours'
        elif timeframe.endswith('d'):
            days = int(timeframe[:-1])
            return f'{days} days'
        elif timeframe.endswith('w'):
            weeks = int(timeframe[:-1])
            days = weeks * 7
            return f'{days} days'
        elif timeframe.endswith('M'):
            months = int(timeframe[:-1])
            return f'{months} months'
        else:
            raise ValueError(f"Unsupported timeframe format: {timeframe}")
    

    def _get_time_grouping_expression(self, timeframe: str) -> str:
        """Get PostgreSQL date_trunc expression for timeframe"""
        grouping_map = {
            '5m': '5 minutes',
            '15m': '15 minutes', 
            '1h': 'hour',
            '4h': '4 hours',
            '1d': 'day',
            '1w': 'week',
            '1M': 'month'
        }
        
        if timeframe not in grouping_map:
            raise ValueError(f"Unsupported timeframe for grouping: {timeframe}")
        
        return grouping_map[timeframe]

    def bulk_aggregate_and_store(self, asset: Asset, source_timeframe: str, 
                                target_timeframes: List[str] = None,
                                start_time: datetime = None, 
                                end_time: datetime = None) -> Dict[str, Any]:
        """
        Bulk aggregate from source timeframe to multiple target timeframes and store results
        
        Now uses the enhanced multi-timeframe aggregation for optimal performance:
        - Single database query for all timeframes (instead of N separate queries)
        - ~75% performance improvement for multiple timeframes
        - Maintains backward compatibility
        
        Returns:
            Dictionary with timeframe -> bulk_insert result dict
                Each result contains: {success, inserted_records, updated_records, skipped_records, ...}
        """
        if target_timeframes is None:
            target_timeframes = self.get_aggregatable_timeframes(source_timeframe)
        
        if not target_timeframes:
            return {}
        
        results = {}
        
        try:
            # 🚀 NEW: Get aggregated data for ALL timeframes in a SINGLE optimized query!
            # This replaces the previous loop that made N separate database calls
            print("******bulk_aggregate_and_store-->multi_timeframe_aggregate start")
            all_aggregated_data = self.aggregate_to_higher_timeframe(
                asset_id=asset.id,
                source_timeframe=source_timeframe,
                target_timeframe=target_timeframes,  # ✨ Pass ALL timeframes at once!
                start_time=start_time,
                end_time=end_time
            )
            print("******bulk_aggregate_and_store-->multi_timeframe_aggregate end")
            
            # 🚀 ENHANCED: Store ALL timeframes in a SINGLE optimized bulk_insert operation!
            # This replaces the previous loop that made N separate bulk_insert calls
            print("******bulk_aggregate_and_store-->multi_timeframe_bulk_insert start")
            bulk_results = self.bulk_insert(
                asset=asset, 
                price_data_list=all_aggregated_data,  # ✨ Pass ALL timeframes data at once!
                timeframe=target_timeframes  # ✨ Pass ALL timeframes at once!
            )
            print("******bulk_aggregate_and_store-->multi_timeframe_bulk_insert end")
            
            # Extract results for each timeframe
            for target_tf in target_timeframes:
                tf_result = bulk_results.get(target_tf, {})
                if tf_result.get('success', False):
                    # Return the complete bulk_insert result for detailed statistics
                    results[target_tf] = tf_result
                else:
                    results[target_tf] = {
                        'success': False,
                        'error': tf_result.get('error', 'Unknown error'),
                        'inserted_records': 0,
                        'updated_records': 0,
                        'skipped_records': 0
                    }
            
        except Exception as e:
            self.db.rollback()
            # If the multi-timeframe query fails, mark all as failed
            for target_tf in target_timeframes:
                results[target_tf] = {
                    'success': False,
                    'error': f"Error in multi-timeframe aggregation: {str(e)}",
                    'inserted_records': 0,
                    'updated_records': 0,
                    'skipped_records': 0
                }
        
        return results

    def get_aggregation_status(self, asset: Asset) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregation status showing available data for each timeframe
        
        Uses cached timeframe_data from asset table for optimal performance
        Falls back to price_data query if cache is empty
        
        Returns:
            Dictionary with timeframe -> {count, latest_time, earliest_time}
        """
        
        if not asset:
            return {}

        status = {} 
        # Use cached data if available
        if asset.timeframe_data:
            status = asset.get_all_timeframe_data()
        return status

    def get_bulk_aggregation_status(self, asset_ids: List[int]) -> Dict[int, Dict[str, Dict[str, Any]]]:
        """
        Get aggregation status for multiple assets efficiently in one query
        
        Args:
            asset_ids: List of asset IDs to get status for
            
        Returns:
            Dictionary with asset_id -> timeframe -> {count, latest_time, earliest_time}
        """
        if not asset_ids:
            return {}
        
        try:
            from ...models.asset import Asset
            
            # Get all assets with cached data first
            assets = self.db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
            
            results = {}
            assets_needing_query = []
            
            # Check cached data first
            for asset in assets:
                if asset.timeframe_data:
                    # Use cached data
                    results[asset.id] = asset.get_all_timeframe_data()
                else:
                    # Need to query database
                    assets_needing_query.append(asset.id)
                    results[asset.id] = {}
            
            # For assets without cached data, do bulk query
            if assets_needing_query:
                hierarchy = self.get_timeframe_hierarchy()
                all_timeframes = list(hierarchy.keys())
                
                bulk_stats = self.db.query(
                    PriceData.asset_id,
                    PriceData.timeframe,
                    func.count(PriceData.id).label('count'),
                    func.max(PriceData.candle_time).label('latest_time'),
                    func.min(PriceData.candle_time).label('earliest_time')
                ).filter(
                    PriceData.asset_id.in_(assets_needing_query),
                    PriceData.timeframe.in_(all_timeframes)
                ).group_by(
                    PriceData.asset_id,
                    PriceData.timeframe
                ).all()
                
                # Initialize empty data for assets needing query
                for asset_id in assets_needing_query:
                    for timeframe in all_timeframes:
                        results[asset_id][timeframe] = {
                            'count': 0,
                            'latest_time': None,
                            'earliest_time': None,
                            'can_aggregate_to': self.get_aggregatable_timeframes(timeframe)
                        }
                
                # Fill in actual data from query results
                for stat in bulk_stats:
                    asset_id = stat.asset_id
                    timeframe = stat.timeframe
                    count = stat.count if stat.count else 0
                    latest = stat.latest_time.isoformat() if stat.latest_time else None
                    earliest = stat.earliest_time.isoformat() if stat.earliest_time else None
                    
                    if asset_id in results:
                        results[asset_id][timeframe] = {
                            'count': count,
                            'latest_time': latest,
                            'earliest_time': earliest,
                            'can_aggregate_to': self.get_aggregatable_timeframes(timeframe)
                        }
            
            return results
            
        except Exception as e:
            # Return empty structure for all requested assets
            return {asset_id: {} for asset_id in asset_ids}

    def _process_all_timeframes(self, asset: Asset, price_data_dict: Dict[str, List[Dict[str, Any]]], 
                               timeframes: List[str]) -> Tuple[Dict, List, List, List]:
        """
        Process all timeframes and collect operations for bulk processing.
        
        Args:
            asset (Asset): Asset object containing metadata and cache information
            price_data_dict (Dict[str, List[Dict[str, Any]]]): Dictionary mapping timeframe strings 
                to lists of OHLCV price data records
            timeframes (List[str]): List of timeframe strings to process (e.g., ['1m', '5m', '1h'])
        
        Returns:
            Tuple[Dict, List, List, List]: A 4-tuple containing:
                - timeframe_stats (Dict): Statistics per timeframe with keys:
                    - 'inserted': number of new records
                    - 'updated': number of updated records  
                    - 'skipped': number of skipped records
                    - 'data_range': {'start': datetime, 'end': datetime}
                - all_records_to_insert (List[Dict]): Aggregated list of all new records to insert
                - all_records_to_update (List[Tuple]): Aggregated list of update operations
                - all_records_to_skip (List[Tuple]): Aggregated list of skipped records
        """
        all_records_to_insert = []
        all_records_to_update = []
        all_records_to_skip = []
        timeframe_stats = {}
        
        # Get latest candle times for all timeframes at once
        latest_candle_times = {}
        for tf in timeframes:
            latest_candle_times[tf] = asset.get_latest_candle_time(tf) if asset else None
        
        # Process each timeframe
        for tf in timeframes:
            tf_stats, tf_inserts, tf_updates, tf_skips = self._process_single_timeframe(
                asset, tf, price_data_dict.get(tf, []), latest_candle_times[tf]
            )
            
            timeframe_stats[tf] = tf_stats
            all_records_to_insert.extend(tf_inserts)
            all_records_to_update.extend(tf_updates)
            all_records_to_skip.extend(tf_skips)
        
        return timeframe_stats, all_records_to_insert, all_records_to_update, all_records_to_skip

    def _process_single_timeframe(self, asset: Asset, tf: str, price_records: List[Dict[str, Any]], 
                                 latest_candle_time) -> Tuple[Dict, List, List, List]:
        """
        Process a single timeframe and categorize records for insert/update/skip operations.
        
        Args:
            asset (Asset): Asset object for database queries and metadata
            tf (str): Timeframe string (e.g., '1m', '5m', '1h', '1d')
            price_records (List[Dict[str, Any]]): List of OHLCV price data dictionaries containing:
                - 'candle_time': datetime of the candle
                - 'open_price', 'high_price', 'low_price', 'close_price': OHLC values
                - 'volume': trading volume
            latest_candle_time (datetime or None): Latest existing candle time from asset cache
        
        Returns:
            Tuple[Dict, List, List, List]: A 4-tuple containing:
                - tf_stats (Dict): Timeframe statistics with counts and data range
                - tf_inserts (List[Dict]): Records ready for database insertion
                - tf_updates (List[Tuple]): (existing_record, new_data, timeframe) tuples for updates
                - tf_skips (List[Tuple]): (data, timeframe) tuples for skipped records
        """
        if not price_records:
            return {'inserted': 0, 'updated': 0, 'skipped': 0, 'data_range': {'start': None, 'end': None}}, [], [], []

        # Filter and sort records
        price_records = self._prepare_price_records(price_records, tf)
        
        # Setup historical data and indicators context
        prev_closes, all_batch_closes = self._setup_indicator_context(asset, tf, price_records)
        
        # Get existing records
        candle_times = [data['candle_time'] for data in price_records if 'candle_time' in data]
        existing_records = self._get_existing_records(asset.id, tf, candle_times)
        
        # Process each record
        tf_inserts, tf_updates, tf_skips = self._process_timeframe_records(
            asset, tf, price_records, prev_closes, all_batch_closes, existing_records, latest_candle_time
        )
        
        # Calculate data range
        data_range = self._calculate_data_range(candle_times)
        
        # Extract latest technical indicators from processed records
        latest_indicators = None
        if tf_inserts:
            # Get indicators from the last inserted record (latest timestamp)
            latest_record = max(tf_inserts, key=lambda x: x.get('candle_time', datetime.min))
            if 'technical_indicators' in latest_record:
                latest_indicators = latest_record['technical_indicators'].copy()
                latest_indicators['close'] = latest_record.get('close_price')
                latest_indicators['candle_time'] = latest_record.get('candle_time').isoformat() if latest_record.get('candle_time') else None
        elif tf_updates:
            # Get indicators from the last updated record
            latest_update = max(tf_updates, key=lambda x: x[1].get('candle_time', datetime.min))
            latest_data = latest_update[1]
            if 'technical_indicators' in latest_data:
                latest_indicators = latest_data['technical_indicators'].copy()
                latest_indicators['close'] = latest_data.get('close_price')
                latest_indicators['candle_time'] = latest_data.get('candle_time').isoformat() if latest_data.get('candle_time') else None
        
        tf_stats = {
            'inserted': len(tf_inserts),
            'updated': len(tf_updates),
            'skipped': len(tf_skips),
            'data_range': data_range,
            'latest_indicators': latest_indicators
        }
        
        return tf_stats, tf_inserts, tf_updates, tf_skips

    def _prepare_price_records(self, price_records: List[Dict[str, Any]], tf: str) -> List[Dict[str, Any]]:
        """
        Filter and sort price records for processing.
        
        Args:
            price_records (List[Dict[str, Any]]): Raw list of price data dictionaries
            tf (str): Timeframe string for logging purposes
        
        Returns:
            List[Dict[str, Any]]: Filtered and chronologically sorted price records.
                - Removes records without 'candle_time'
                - Sorts only if data appears out of chronological order
                - Preserves original order if already sorted for performance
        """
        # Filter out records without candle_time
        price_records = [d for d in price_records if d.get('candle_time') is not None]
        
        # Only sort if data appears to be out of chronological order
        if len(price_records) > 1:
            needs_sorting = False
            try:
                # Quick check: compare first few timestamps
                for i in range(min(3, len(price_records) - 1)):
                    if price_records[i]['candle_time'] > price_records[i + 1]['candle_time']:
                        needs_sorting = True
                        break
                
                if needs_sorting:
                    print(f"Data for {tf} is out of order, sorting chronologically...")
                    price_records = sorted(price_records, key=lambda d: d.get('candle_time'))
            except (TypeError, KeyError) as e:
                print(f"Warning: Cannot verify order for {tf}: {e}, proceeding without sort")
        
        return price_records

    def _setup_indicator_context(self, asset: Asset, tf: str, price_records: List[Dict[str, Any]]) -> Tuple[List[float], Optional[List]]:
        """
        Setup historical data context for technical indicator calculation.
        
        Args:
            asset (Asset): Asset object for database queries
            tf (str): Timeframe string for database filtering
            price_records (List[Dict[str, Any]]): Current batch of price records to be processed
        
        Returns:
            Tuple[List[float], Optional[List]]: A 2-tuple containing:
                - prev_closes (List[float]): Historical close prices (up to 200) from database
                    prior to the first new candle, ordered chronologically
                - all_batch_closes (Optional[List]): For bulk imports, list of close prices 
                    from current batch. None for real-time updates.
                    
        Context Detection:
            - Real-time mode: prev_closes populated, all_batch_closes is None
            - Bulk import mode: prev_closes empty, all_batch_closes populated
        """
        if not price_records:
            return [], None
            
        candle_times = [data['candle_time'] for data in price_records if 'candle_time' in data]
        
        # Get historical close prices (up to 200) prior to the first new candle
        prev_closes = []
        if candle_times:
            min_new_time = candle_times[0]
            prev_rows = self.db.query(PriceData.candle_time, PriceData.close_price).filter(
                PriceData.asset_id == asset.id,
                PriceData.timeframe == tf,
                PriceData.candle_time < min_new_time
            ).order_by(PriceData.candle_time.desc()).limit(200).all()
            prev_closes = [float(r.close_price) for r in reversed(prev_rows)]
            
            # Log scenario type
            if not prev_closes:
                print(f"********{tf}: Bulk historical import mode - no existing data found")
            else:
                print(f"********{tf}: Real-time update mode - using {len(prev_closes)} historical closes for indicators")

        # For bulk imports: prepare batch close prices
        all_batch_closes = None
        if not prev_closes and len(price_records) > 1:
            all_batch_closes = []
            for record in price_records:
                if 'close_price' in record and record['close_price'] is not None:
                    try:
                        all_batch_closes.append(float(record['close_price']))
                    except (ValueError, TypeError):
                        all_batch_closes.append(None)
                else:
                    all_batch_closes.append(None)
            print(f"********{tf}: Bulk import mode - using {len([c for c in all_batch_closes if c is not None])} closes from current batch for indicators")

        return prev_closes, all_batch_closes

    def _process_timeframe_records(self, asset: Asset, tf: str, price_records: List[Dict[str, Any]], 
                                  prev_closes: List[float], all_batch_closes: Optional[List], 
                                  existing_records: Dict, latest_candle_time) -> Tuple[List, List, List]:
        """
        Process individual records for a timeframe and compute technical indicators.
        
        Args:
            asset (Asset): Asset object for metadata
            tf (str): Timeframe string for logging and processing
            price_records (List[Dict[str, Any]]): Filtered and sorted price records
            prev_closes (List[float]): Historical close prices from database for indicator calculation
            all_batch_closes (Optional[List]): Close prices from current batch for bulk imports
            existing_records (Dict): Dictionary mapping candle_time to existing PriceData records
            latest_candle_time (datetime or None): Latest candle time for update eligibility check
        
        Returns:
            Tuple[List, List, List]: A 3-tuple containing:
                - tf_inserts (List[Dict]): Records with computed indicators ready for insertion
                - tf_updates (List[Tuple]): (existing_record, new_data, timeframe) tuples for updates
                - tf_skips (List[Tuple]): (data, timeframe) tuples for records that were skipped
                
        Processing Logic:
            - Computes RSI14, SMA200, EMA200 for each record
            - Uses context-aware indicator calculation (bulk vs real-time)
            - Only allows updates for the latest candle time
        """
        tf_inserts = []
        tf_updates = []
        tf_skips = []
        
        base_data_fields = {'asset_id': asset.id, 'timeframe': tf}
        closes = list(prev_closes)  # For real-time mode
        
        for record_index, data in enumerate(price_records):
            data.update(base_data_fields)
            
            # Compute technical indicators
            self._compute_and_set_indicators(data, record_index, prev_closes, all_batch_closes, closes, tf)
            
            # Check if record exists and determine operation
            existing = self._get_existing_record(existing_records, data['candle_time'])
            
            if not existing:
                tf_inserts.append(data)
            else:
                # Check if updatable (latest candle only)
                if latest_candle_time and compare_datetimes(data['candle_time'], latest_candle_time):
                    if self._should_update_existing_record(existing, data):
                        tf_updates.append((existing, data, tf))
                    else:
                        tf_skips.append((data, tf))
                else:
                    tf_skips.append((data, tf))
            
            # Update closes for real-time mode
            close_val = self._get_close_value(data)
            if close_val is not None and all_batch_closes is None:
                closes.append(close_val)
        
        return tf_inserts, tf_updates, tf_skips

    def _compute_and_set_indicators(self, data: Dict[str, Any], record_index: int, 
                                   prev_closes: List[float], all_batch_closes: Optional[List], 
                                   closes: List[float], tf: str):
        """
        Compute and set technical indicators for a single price record.
        
        Args:
            data (Dict[str, Any]): Price record dictionary to modify. Gets 'technical_indicators' 
                field added with computed values
            record_index (int): 0-based index of current record in the batch
            prev_closes (List[float]): Historical close prices from database
            all_batch_closes (Optional[List]): Close prices from current batch (bulk mode only)
            closes (List[float]): Accumulated close prices for real-time mode
            tf (str): Timeframe string for debug logging
        
        Returns:
            None: Modifies the 'data' dictionary in-place by adding 'technical_indicators' field
        
        Technical Indicators Computed:
            - RSI (14-period): Relative Strength Index
            - SMA (200-period): Simple Moving Average  
            - EMA (200-period): Exponential Moving Average
            
        Output Format in data['technical_indicators']:
            {
                'rsi_14': float or None,
                'sma_200': float or None, 
                'ema_200': float or None,
                'computed_at': ISO timestamp string
            }
        """
        close_val = self._get_close_value(data)
        
        if close_val is not None:
            # Determine working series based on mode
            if all_batch_closes is not None:
                # Bulk import mode: use historical + batch data up to current index
                working_series = prev_closes + [c for c in all_batch_closes[:record_index + 1] if c is not None]
            else:
                # Real-time mode: use historical + incremental
                working_series = closes + [close_val]
            
            # Compute indicators
            sma200 = self._compute_sma(working_series, 200)
            ema200 = self._compute_ema_last(working_series, 200)
            rsi14 = self._compute_rsi_last(working_series, 14)

            indicators = {
                'rsi_14': round(rsi14, 2) if rsi14 is not None else None,
                'sma_200': round(sma200, 8) if sma200 is not None else None,
                'ema_200': round(ema200, 8) if ema200 is not None else None
            }
            
            # Debug logging
            if all_batch_closes is not None and len(working_series) >= 200:
                print(f"********{tf}: Bulk import with full context - record {record_index + 1} has {len(working_series)} data points")
            elif len(working_series) == 1 and not prev_closes:
                print(f"********{tf}: First record in bulk import - indicators will be None")
            elif len(working_series) > 200:
                print(f"********{tf}: Real-time with full history - {len(working_series)} data points")
        else:
            # No close price available
            indicators = {
                'rsi_14': None,
                'sma_200': None,
                'ema_200': None
            }
        
        data['technical_indicators'] = indicators

    def _get_close_value(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Extract and validate close price from a price record.
        
        Args:
            data (Dict[str, Any]): Price record dictionary potentially containing 'close_price' key
        
        Returns:
            Optional[float]: Valid close price as float, or None if:
                - 'close_price' key is missing
                - 'close_price' value is None
                - 'close_price' cannot be converted to float (ValueError/TypeError)
        """
        if 'close_price' in data and data['close_price'] is not None:
            try:
                return float(data['close_price'])
            except (ValueError, TypeError):
                return None
        return None

    def _calculate_data_range(self, candle_times: List) -> Dict[str, Any]:
        """
        Calculate start and end times for a timeframe's data range.
        
        Args:
            candle_times (List): List of datetime objects representing candle timestamps
        
        Returns:
            Dict[str, Any]: Data range dictionary with keys:
                - 'start': datetime of earliest candle or None if empty list
                - 'end': datetime of latest candle or None if empty list
                
        Performance: O(n) single pass through the list to find min/max
        """
        data_range = {'start': None, 'end': None}
        if candle_times:
            min_time = max_time = candle_times[0]
            for time in candle_times[1:]:
                if time < min_time:
                    min_time = time
                elif time > max_time:
                    max_time = time
            data_range = {'start': min_time, 'end': max_time}
        return data_range

    def _execute_bulk_operations(self, all_records_to_insert: List, all_records_to_update: List, 
                                all_records_to_skip: List, asset: Asset) -> Tuple[int, int, int]:
        """
        Execute bulk insert and update operations with transaction management.
        
        Args:
            all_records_to_insert (List[Dict]): List of price record dictionaries ready for insertion
            all_records_to_update (List[Tuple]): List of (existing_record, new_data, timeframe) 
                tuples for update operations
            all_records_to_skip (List): List of skipped records (counted but not processed)
            asset (Asset): Asset object for conflict resolution fallback
        
        Returns:
            Tuple[int, int, int]: A 3-tuple containing:
                - total_inserted (int): Number of records successfully inserted
                - total_updated (int): Number of records successfully updated  
                - total_skipped (int): Number of records skipped
                
        Transaction Behavior:
            - Commits transaction on success
            - Rolls back on failure and re-raises exception (except constraint violations)
            - Handles duplicate key constraints gracefully with warnings
        """
        total_inserted = 0
        total_updated = 0
        total_skipped = len(all_records_to_skip)
        
        # Bulk insert
        if all_records_to_insert:
            total_inserted = self._execute_bulk_insert(all_records_to_insert, asset)
        
        # Bulk update
        if all_records_to_update:
            total_updated = self._execute_bulk_update(all_records_to_update)
        
        # Commit transaction
        try:
            self.db.commit()
            print(f"********unified_bulk_insert--> transaction committed successfully")
        except Exception as commit_error:
            self.db.rollback()
            if "duplicate key value violates unique constraint" in str(commit_error):
                print(f"Warning: Some records skipped due to constraint violations")
            else:
                raise
        
        return total_inserted, total_updated, total_skipped

    def _execute_bulk_insert(self, records_to_insert: List, asset: Asset) -> int:
        """
        Execute bulk insert with error handling and fallback strategy.
        
        Args:
            records_to_insert (List[Dict]): List of price record dictionaries to insert
            asset (Asset): Asset object for fallback conflict resolution
        
        Returns:
            int: Number of records successfully inserted
            
        Error Handling Strategy:
            1. Attempts bulk insert with db.add_all() for optimal performance
            2. On constraint violations, falls back to individual inserts
            3. Other exceptions are re-raised
            4. Includes db.flush() for immediate constraint checking
        """
        try:
            print(f"********unified_bulk_insert--> bulk inserting {len(records_to_insert)} records")
            new_price_objects = [PriceData(**data) for data in records_to_insert]
            self.db.add_all(new_price_objects)
            self.db.flush()
            print(f"********unified_bulk_insert--> successfully inserted {len(new_price_objects)} records")
            return len(new_price_objects)
        except Exception as e:
            print(f"********unified_bulk_insert--> bulk insert failed: {e}")
            self.db.rollback()
            
            # Fallback to individual inserts for constraint violations
            if "duplicate key value violates unique constraint" in str(e) or "UniqueViolation" in str(e):
                return self._handle_insert_conflicts(records_to_insert, asset)
            else:
                raise

    def _handle_insert_conflicts(self, records_to_insert: List, asset: Asset) -> int:
        """
        Handle insertion conflicts with individual record processing fallback.
        
        Args:
            records_to_insert (List[Dict]): List of price records that failed bulk insert
            asset (Asset): Asset object for individual record validation
        
        Returns:
            int: Number of records successfully inserted individually
            
        Conflict Resolution:
            - Processes each record individually to isolate conflicts
            - Checks for existing records before insertion attempt
            - Skips problematic records silently to prevent cascade failures
            - Used as fallback when bulk insert encounters duplicate key constraints
        """
        print("********unified_bulk_insert--> handling constraint violations with individual inserts")
        total_inserted = 0
        
        for data in records_to_insert:
            try:
                existing_check = self._get_existing_records(asset.id, data['timeframe'], [data['candle_time']])
                if not self._get_existing_record(existing_check, data['candle_time']):
                    individual_record = PriceData(**data)
                    self.db.add(individual_record)
                    self.db.flush()
                    total_inserted += 1
            except Exception:
                continue  # Skip problematic records
        
        return total_inserted

    def _execute_bulk_update(self, records_to_update: List) -> int:
        """
        Execute bulk update operations for existing records.
        
        Args:
            records_to_update (List[Tuple]): List of (existing_record, new_data, timeframe) tuples
                - existing_record: PriceData object from database
                - new_data: Dictionary with updated values
                - timeframe: String identifier for logging
        
        Returns:
            int: Number of records successfully updated
            
        Update Process:
            - Updates existing PriceData objects with new values
            - Calls db.flush() to persist changes immediately
            - Only processes records eligible for updates (latest candle time)
        """
        print(f"********unified_bulk_insert--> bulk updating {len(records_to_update)} records")
        for existing, data, tf in records_to_update:
            self._update_existing_record(existing, data)
        self.db.flush()
        print(f"********unified_bulk_insert--> successfully updated {len(records_to_update)} records")
        return len(records_to_update)

    def _update_asset_caches(self, asset: Asset, timeframes: List[str], timeframe_stats: Dict):
        """
        Update asset caches for all affected timeframes.
        
        Args:
            asset (Asset): Asset object whose cache needs updating
            timeframes (List[str]): List of timeframe strings that were processed
            timeframe_stats (Dict): Statistics dictionary with keys as timeframe strings,
                values as dictionaries containing:
                - 'inserted': int - number of new records
                - 'updated': int - number of updated records
                - 'data_range': dict with 'start' and 'end' datetime values
        
        Returns:
            None: Updates asset cache in-place
            
        Cache Update Logic:
            - Only updates cache for timeframes with actual data changes (inserted/updated > 0)
            - Handles cache update failures gracefully with warnings
            - Continues processing other timeframes even if one fails
        """
        print("********unified_bulk_insert--> updating asset cache for all timeframes")
        
        for tf in timeframes:
            try:
                tf_stats = timeframe_stats[tf]
                if tf_stats['inserted'] > 0 or tf_stats['updated'] > 0:
                    self._update_single_timeframe_cache(asset, tf, tf_stats)
            except Exception as cache_error:
                print(f"Warning: Cache update failed for timeframe {tf}: {str(cache_error)}")

    def _update_single_timeframe_cache(self, asset: Asset, tf: str, tf_stats: Dict):
        """
        Update cache for a single timeframe with new record counts and time ranges.
        
        Args:
            asset (Asset): Asset object whose timeframe cache needs updating
            tf (str): Timeframe string (e.g., '1m', '5m', '1h', '1d')
            tf_stats (Dict): Timeframe statistics containing:
                - 'inserted': int - number of new records inserted
                - 'data_range': dict with 'start' and 'end' datetime values
                - 'latest_indicators': dict - latest technical indicators (optional)
        
        Returns:
            None: Updates asset cache via asset.update_timeframe_data() and update_technical_metrics()
            
        Cache Calculation:
            - new_count = existing_count + newly_inserted_records
            - earliest_time = min(existing_earliest, new_data_start)
            - latest_time = max(existing_latest, new_data_end)
        """
        current_info = asset.get_timeframe_info(tf) if asset else {}
        current_count = current_info.get('count', 0) if current_info else 0
        new_count = current_count + tf_stats['inserted']
        
        # Calculate earliest and latest times
        data_range = tf_stats['data_range']
        earliest_time = latest_time = None
        
        if data_range['start'] and data_range['end']:
            earliest_time, latest_time = self._calculate_cache_times(current_info, data_range)
        
        # Update timeframe data cache
        asset.update_timeframe_data(
            timeframe=tf,
            count=new_count,
            earliest_time=earliest_time,
            latest_time=latest_time
        )
        
        # Update technical metrics if available
        if 'latest_indicators' in tf_stats and tf_stats['latest_indicators']:
            asset.update_technical_metrics(
                timeframe=tf,
                latest_metrics=tf_stats['latest_indicators']
            )
            print(f"********unified_bulk_insert--> technical metrics updated for {tf}")
        
        print(f"********unified_bulk_insert--> cache updated for {tf}: count={new_count}")

    def _calculate_cache_times(self, current_info: Dict, data_range: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Calculate earliest and latest times for cache update by merging existing and new data ranges.
        
        Args:
            current_info (Dict): Current timeframe cache info containing:
                - 'earliest_time': str or None - ISO timestamp of earliest existing record
                - 'latest_time': str or None - ISO timestamp of latest existing record
            data_range (Dict): New data range containing:
                - 'start': datetime - earliest time in new data
                - 'end': datetime - latest time in new data
        
        Returns:
            Tuple[Optional[str], Optional[str]]: A 2-tuple containing:
                - earliest_time: ISO string of overall earliest time or None
                - latest_time: ISO string of overall latest time or None
                
        Time Merging Logic:
            - earliest_time = min(existing_earliest, new_start) 
            - latest_time = max(existing_latest, new_end)
            - Handles ISO string parsing with timezone normalization
            - Gracefully handles parsing errors by using new data times
        """
        earliest_time = latest_time = None
        
        # Handle earliest time
        existing_earliest = current_info.get('earliest_time') if current_info else None
        if existing_earliest:
            try:
                existing_earliest_dt = datetime.fromisoformat(existing_earliest.replace('Z', '+00:00'))
                earliest_time = min(data_range['start'], existing_earliest_dt).isoformat()
            except (ValueError, AttributeError):
                earliest_time = data_range['start'].isoformat()
        else:
            earliest_time = data_range['start'].isoformat()
        
        # Handle latest time
        existing_latest = current_info.get('latest_time') if current_info else None
        if existing_latest:
            try:
                existing_latest_dt = datetime.fromisoformat(existing_latest.replace('Z', '+00:00'))
                latest_time = max(data_range['end'], existing_latest_dt).isoformat()
            except (ValueError, AttributeError):
                latest_time = data_range['end'].isoformat()
        else:
            latest_time = data_range['end'].isoformat()
        
        return earliest_time, latest_time

    def _build_final_results_with_aggregation(self, timeframes: List[str], timeframe_stats: Dict, 
                                             aggregation_stats: Dict) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Build and return final results structure including accurate aggregation statistics.
        
        Args:
            timeframes (List[str]): List of timeframe strings that were processed
            timeframe_stats (Dict): Statistics per timeframe with processing counts and data ranges
            aggregation_stats (Dict): Detailed statistics from auto-aggregation operations
        
        Returns:
            Union[Dict[str, Any], Dict[str, Dict[str, Any]]]: Result structure with accurate aggregation stats:
                - Single timeframe: Returns dict directly with keys:
                    - 'status': 'success'
                    - 'total_processed': int - sum of inserted + updated + skipped
                    - 'inserted_records': int - number of new records inserted
                    - 'updated_records': int - number of existing records updated
                    - 'skipped_records': int - number of records skipped
                    - 'data_range': dict with 'start' and 'end' datetime values
                    - 'aggregation_results': dict with aggregated timeframe stats (separated by insert/update)
                    - 'total_aggregated_inserted': int - total aggregated records that were new inserts
                    - 'total_aggregated_updated': int - total aggregated records that were updates
                    - 'success': True
                - Multiple timeframes: Returns dict mapping timeframe -> result dict
        """
        results = {}
        
        for tf in timeframes:
            tf_stats = timeframe_stats[tf]
            total_processed = tf_stats['inserted'] + tf_stats['updated'] + tf_stats['skipped']
            
            # Calculate aggregation totals with insert/update separation
            tf_aggregation_inserted = 0
            tf_aggregation_updated = 0
            tf_aggregation_results = {}
            
            for agg_key, agg_value in aggregation_stats.items():
                if self._is_aggregation_for_timeframe(tf, agg_key):
                    if agg_key.endswith('_inserted'):
                        timeframe_name = agg_key.replace('_inserted', '')
                        tf_aggregation_inserted += agg_value
                        tf_aggregation_results[f"{timeframe_name}_inserted"] = agg_value
                    elif agg_key.endswith('_updated'):
                        timeframe_name = agg_key.replace('_updated', '')
                        tf_aggregation_updated += agg_value
                        tf_aggregation_results[f"{timeframe_name}_updated"] = agg_value
                    else:
                        # Legacy format - treat as mixed
                        tf_aggregation_results[agg_key] = agg_value
            
            results[tf] = {
                'status': 'success',
                'total_processed': total_processed,
                'inserted_records': tf_stats['inserted'],
                'updated_records': tf_stats['updated'],
                'skipped_records': tf_stats['skipped'],
                'data_range': tf_stats['data_range'],
                'aggregation_results': tf_aggregation_results,
                'total_aggregated_inserted': tf_aggregation_inserted,
                'total_aggregated_updated': tf_aggregation_updated,
                'success': True
            }
        
        # Add overall aggregation summary if multiple timeframes
        if len(timeframes) > 1:
            total_aggregated_inserted = sum(
                result.get('total_aggregated_inserted', 0) for result in results.values()
            )
            total_aggregated_updated = sum(
                result.get('total_aggregated_updated', 0) for result in results.values()
            )
            
            for tf_result in results.values():
                tf_result['overall_aggregation_summary'] = {
                    'total_aggregated_timeframes': len([k for k in aggregation_stats.keys() if not k.endswith(('_inserted', '_updated'))]),
                    'total_aggregated_inserted': total_aggregated_inserted,
                    'total_aggregated_updated': total_aggregated_updated,
                    'aggregated_timeframes': list(set(k.replace('_inserted', '').replace('_updated', '') 
                                                   for k in aggregation_stats.keys()))
                }
        
        # Return single result for single timeframe, dict for multiple
        if len(timeframes) == 1:
            return results[timeframes[0]]
        else:
            return results

    def _perform_auto_aggregation(self, asset: Asset, timeframes: List[str], 
                                 timeframe_stats: Dict) -> Dict[str, int]:
        """
        Perform auto-aggregation to higher timeframes and return statistics.
        
        Args:
            asset (Asset): Asset object for aggregation operations
            timeframes (List[str]): List of source timeframes that were processed
            timeframe_stats (Dict): Statistics from the main bulk insert operation
        
        Returns:
            Dict[str, int]: Dictionary mapping target timeframe -> number of records created
                Example: {'4h': 24, '1d': 7, '1w': 1}
        """
        aggregation_results = {}
        
        try:
            # Process each source timeframe for aggregation
            for source_tf in timeframes:
                tf_stats = timeframe_stats[source_tf]
                
                # Only aggregate if we actually inserted or updated records
                if tf_stats['inserted'] > 0 or tf_stats['updated'] > 0:
                    print(f"********auto_aggregation--> starting aggregation from {source_tf}")
                    
                    # Get aggregatable timeframes for this source
                    target_timeframes = self.get_aggregatable_timeframes(source_tf)
                    
                    if target_timeframes:
                        print(f"********auto_aggregation--> {source_tf} can aggregate to: {target_timeframes}")
                        
                        # Determine time range for aggregation based on data range
                        data_range = tf_stats['data_range']
                        start_time = data_range.get('start')
                        end_time = data_range.get('end')
                        
                        # Perform bulk aggregation for all target timeframes
                        bulk_results = self.bulk_aggregate_and_store(
                            asset=asset,
                            source_timeframe=source_tf,
                            target_timeframes=target_timeframes,
                            start_time=start_time,
                            end_time=end_time
                        )
                        
                        # Merge results - now handling insert/update separately
                        for target_tf, result in bulk_results.items():
                            if isinstance(result, dict) and result.get('success', False):
                                # Use detailed stats from bulk_insert result
                                aggregation_key = f"{target_tf}_inserted"
                                update_key = f"{target_tf}_updated"
                                
                                aggregation_results[aggregation_key] = aggregation_results.get(aggregation_key, 0) + result.get('inserted_records', 0)
                                aggregation_results[update_key] = aggregation_results.get(update_key, 0) + result.get('updated_records', 0)
                                
                                inserted = result.get('inserted_records', 0)
                                updated = result.get('updated_records', 0)
                                print(f"********auto_aggregation--> {source_tf} -> {target_tf}: {inserted} inserted, {updated} updated")
                            elif isinstance(result, int) and result > 0:
                                # Fallback for old format - treat as total records
                                aggregation_results[target_tf] = aggregation_results.get(target_tf, 0) + result
                                print(f"********auto_aggregation--> {source_tf} -> {target_tf}: {result} records (mixed)")
                    else:
                        print(f"********auto_aggregation--> no aggregation targets for {source_tf}")
                else:
                    print(f"********auto_aggregation--> skipping {source_tf} (no changes)")
            
            # Log aggregation summary
            if aggregation_results:
                total_aggregated = sum(aggregation_results.values())
                print(f"********auto_aggregation--> completed: {total_aggregated} total aggregated records across {len(aggregation_results)} timeframes")
            else:
                print(f"********auto_aggregation--> no aggregation performed")
                
        except Exception as e:
            print(f"********auto_aggregation--> error during aggregation: {str(e)}")
            # Don't fail the main operation due to aggregation errors
        
        return aggregation_results

    def _can_aggregate_from_to(self, source_tf: str, target_tf: str) -> bool:
        """
        Check if target timeframe can be aggregated from source timeframe.
        
        Args:
            source_tf (str): Source timeframe (e.g., '1h')
            target_tf (str): Target timeframe (e.g., '4h')
        
        Returns:
            bool: True if target can be aggregated from source
        """
        try:
            hierarchy = self.get_timeframe_hierarchy()
            source_minutes = hierarchy.get(source_tf, {}).get('minutes', 0)
            target_minutes = hierarchy.get(target_tf, {}).get('minutes', 0)
            
            return (source_minutes > 0 and target_minutes > 0 and 
                   target_minutes > source_minutes and 
                   target_minutes % source_minutes == 0)
        except:
            return False

    def _is_aggregation_for_timeframe(self, source_tf: str, aggregation_key: str) -> bool:
        """
        Check if an aggregation result key belongs to the given source timeframe.
        
        Args:
            source_tf (str): Source timeframe (e.g., '1h')
            aggregation_key (str): Aggregation key (e.g., '4h_inserted', '1d', '1w_updated')
        
        Returns:
            bool: True if the aggregation key is for a target timeframe that can be 
                 aggregated from the source timeframe
        """
        # Extract the target timeframe from the key
        target_tf = aggregation_key
        if aggregation_key.endswith('_inserted'):
            target_tf = aggregation_key.replace('_inserted', '')
        elif aggregation_key.endswith('_updated'):
            target_tf = aggregation_key.replace('_updated', '')
        
        return self._can_aggregate_from_to(source_tf, target_tf)
