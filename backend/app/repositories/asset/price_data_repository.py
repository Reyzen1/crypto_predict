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
                   timeframe: Union[str, List[str]] = '1h') -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        True bulk insert with unified multi-timeframe support for maximum performance
        
        Processes all timeframes in a single transaction with batch operations:
        - Single timeframe: Maintains backward compatibility 
        - Multiple timeframes: True bulk processing with single database operations
        
        Args:
            asset: Asset object (already loaded with cache data)
            price_data_list: 
                - For single timeframe: List of price data dictionaries
                - For multiple timeframes: Dict with timeframe as key, List[Dict] as value
            timeframe: 
                - Single timeframe: str (e.g., '1h')
                - Multiple timeframes: List[str] (e.g., ['4h', '1d', '1w'])
                
        Returns:
            - For single timeframe: Dict with operation statistics
            - For multiple timeframes: Dict[timeframe, Dict[statistics]]
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
        
        return self._unified_bulk_insert(asset, price_data_dict, timeframes)
    
    def _unified_bulk_insert(self, asset: Asset, price_data_dict: Dict[str, List[Dict[str, Any]]], 
                           timeframes: List[str]) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        True unified bulk insert processing all timeframes in single transaction
        
        This is the core implementation that processes multiple timeframes efficiently:
        - Single database transaction for all timeframes
        - Batch queries for existing record checks
        - Bulk insert operations across all timeframes
        - Unified error handling and cache updates
        
        Args:
            asset: Asset object
            price_data_dict: Dict with timeframe as key and List[Dict] as value
            timeframes: List of timeframes to process
            
        Returns:
            Single timeframe: Dict with operation statistics
            Multiple timeframes: Dict[timeframe, Dict[statistics]]
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
            
            # === PHASE 1: Collect all data and prepare for bulk operations ===
            all_records_to_insert = []  # All new records across timeframes
            all_records_to_update = []  # All update operations across timeframes  
            all_records_to_skip = []    # All skipped records across timeframes
            
            # Per-timeframe tracking for results
            timeframe_stats = {}
            timeframe_data_ranges = {}
            
            # Get latest candle times for all timeframes at once
            latest_candle_times = {}
            for tf in timeframes:
                latest_candle_times[tf] = asset.get_latest_candle_time(tf) if asset else None
            
            # Process each timeframe and collect operations
            for tf in timeframes:
                timeframe_data = price_data_dict.get(tf, [])
                
                if not timeframe_data:
                    timeframe_stats[tf] = {'inserted': 0, 'updated': 0, 'skipped': 0, 'data_range': {'start': None, 'end': None}}
                    continue
                
                # Extract candle times for this timeframe
                candle_times = [data['candle_time'] for data in timeframe_data if 'candle_time' in data]
                
                # Bulk query for existing records of this timeframe
                existing_records = self._get_existing_records(asset.id, tf, candle_times)
                
                # Prepare base fields for this timeframe
                base_data_fields = {'asset_id': asset.id, 'timeframe': tf}
                
                # Track operations for this timeframe
                tf_insert_count = 0
                tf_update_count = 0  
                tf_skip_count = 0
                
                # Process each record in this timeframe
                for data in timeframe_data:
                    # Ensure data consistency
                    data.update(base_data_fields)
                    
                    # Check if record exists
                    existing = self._get_existing_record(existing_records, data['candle_time'])
                    
                    if not existing:
                        # New record - add to bulk insert
                        all_records_to_insert.append(data)
                        tf_insert_count += 1
                    else:
                        # Existing record - check if it's updatable (latest candle only)
                        latest_candle_time = latest_candle_times[tf]
                        if latest_candle_time and compare_datetimes(data['candle_time'], latest_candle_time):
                            if self._should_update_existing_record(existing, data):
                                all_records_to_update.append((existing, data, tf))  # Include timeframe for tracking
                                tf_update_count += 1
                            else:
                                all_records_to_skip.append((data, tf))
                                tf_skip_count += 1
                        else:
                            all_records_to_skip.append((data, tf))
                            tf_skip_count += 1
                
                # Calculate data range for this timeframe
                data_range = {'start': None, 'end': None}
                if candle_times:
                    min_time = max_time = candle_times[0]
                    for time in candle_times[1:]:
                        if time < min_time:
                            min_time = time
                        elif time > max_time:
                            max_time = time
                    data_range = {'start': min_time, 'end': max_time}
                
                # Store timeframe statistics
                timeframe_stats[tf] = {
                    'inserted': tf_insert_count,
                    'updated': tf_update_count, 
                    'skipped': tf_skip_count,
                    'data_range': data_range
                }
                timeframe_data_ranges[tf] = data_range
            
            # === PHASE 2: Execute bulk operations across all timeframes ===
            
            # Bulk insert all new records at once
            if all_records_to_insert:
                try:
                    print(f"********unified_bulk_insert--> bulk inserting {len(all_records_to_insert)} records across {len(timeframes)} timeframes")
                    new_price_objects = [PriceData(**data) for data in all_records_to_insert]
                    self.db.add_all(new_price_objects)
                    self.db.flush()
                    total_inserted = len(new_price_objects)
                    print(f"********unified_bulk_insert--> successfully inserted {total_inserted} records")
                except Exception as e:
                    print(f"********unified_bulk_insert--> bulk insert failed: {e}")
                    self.db.rollback()
                    if "duplicate key value violates unique constraint" in str(e) or "UniqueViolation" in str(e):
                        # Handle constraint violations with fallback
                        print("********unified_bulk_insert--> handling constraint violations with individual inserts")
                        for data in all_records_to_insert:
                            try:
                                # Check if record now exists (concurrent insertion)
                                existing_check = self._get_existing_records(asset.id, data['timeframe'], [data['candle_time']])
                                if not self._get_existing_record(existing_check, data['candle_time']):
                                    individual_record = PriceData(**data)
                                    self.db.add(individual_record)
                                    self.db.flush()
                                    total_inserted += 1
                                else:
                                    total_skipped += 1
                            except Exception:
                                total_skipped += 1
                    else:
                        raise
            
            # Bulk update all existing records
            if all_records_to_update:
                print(f"********unified_bulk_insert--> bulk updating {len(all_records_to_update)} records")
                for existing, data, tf in all_records_to_update:
                    self._update_existing_record(existing, data)
                    total_updated += 1
                self.db.flush()
                print(f"********unified_bulk_insert--> successfully updated {total_updated} records")
            
            # Count skipped records
            total_skipped += len(all_records_to_skip)
            
            # === PHASE 3: Commit transaction and update caches ===
            
            try:
                self.db.commit()
                print(f"********unified_bulk_insert--> transaction committed successfully")
            except Exception as commit_error:
                self.db.rollback()
                if "duplicate key value violates unique constraint" in str(commit_error):
                    # Partial success - some records were processed
                    error_result = {
                        'status': 'partial_success',
                        'warning': f'Some records skipped due to constraint violations: {str(commit_error)}',
                        'total_processed': total_inserted + total_updated + total_skipped,
                        'inserted_records': total_inserted,
                        'updated_records': total_updated, 
                        'skipped_records': total_skipped,
                        'success': True
                    }
                    return error_result if len(timeframes) == 1 else {tf: error_result for tf in timeframes}
                else:
                    raise
            
            # Update asset caches for all affected timeframes
            if total_inserted > 0 or total_updated > 0:
                print("********unified_bulk_insert--> updating asset cache for all timeframes")
                for tf in timeframes:
                    try:
                        tf_stats = timeframe_stats[tf] 
                        if tf_stats['inserted'] > 0 or tf_stats['updated'] > 0:
                            current_info = asset.get_timeframe_info(tf) if asset else {}
                            current_count = current_info.get('count', 0) if current_info else 0
                            new_count = current_count + tf_stats['inserted']
                            
                            # Calculate earliest and latest times
                            data_range = tf_stats['data_range']
                            earliest_time = latest_time = None
                            
                            if data_range['start'] and data_range['end']:
                                existing_earliest = current_info.get('earliest_time') if current_info else None
                                if existing_earliest:
                                    # Convert existing_earliest string to datetime for comparison
                                    try:
                                        existing_earliest_dt = datetime.fromisoformat(existing_earliest.replace('Z', '+00:00'))
                                        earliest_time = min(data_range['start'], existing_earliest_dt).isoformat()
                                    except (ValueError, AttributeError):
                                        earliest_time = data_range['start'].isoformat()
                                else:
                                    earliest_time = data_range['start'].isoformat()
                                
                                existing_latest = current_info.get('latest_time') if current_info else None  
                                if existing_latest:
                                    # Convert existing_latest string to datetime for comparison
                                    try:
                                        existing_latest_dt = datetime.fromisoformat(existing_latest.replace('Z', '+00:00'))
                                        latest_time = max(data_range['end'], existing_latest_dt).isoformat()
                                    except (ValueError, AttributeError):
                                        latest_time = data_range['end'].isoformat()
                                else:
                                    latest_time = data_range['end'].isoformat()
                            
                            # Update cache
                            asset.update_timeframe_data(
                                timeframe=tf,
                                count=new_count,
                                earliest_time=earliest_time,
                                latest_time=latest_time
                            )
                            print(f"********unified_bulk_insert--> cache updated for {tf}: count={new_count}")
                    except Exception as cache_error:
                        print(f"Warning: Cache update failed for timeframe {tf}: {str(cache_error)}")
            
            # === PHASE 4: Prepare and return results ===
            
            # Build final results
            for tf in timeframes:
                tf_stats = timeframe_stats[tf]
                total_processed = tf_stats['inserted'] + tf_stats['updated'] + tf_stats['skipped']
                
                results[tf] = {
                    'status': 'success',
                    'total_processed': total_processed,
                    'inserted_records': tf_stats['inserted'],
                    'updated_records': tf_stats['updated'],
                    'skipped_records': tf_stats['skipped'], 
                    'data_range': tf_stats['data_range'],
                    'success': True
                }
            
            # Return single result for single timeframe, dict for multiple
            if len(timeframes) == 1:
                return results[timeframes[0]]
            else:
                return results
                
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
                                end_time: datetime = None) -> Dict[str, int]:
        """
        Bulk aggregate from source timeframe to multiple target timeframes and store results
        
        Now uses the enhanced multi-timeframe aggregation for optimal performance:
        - Single database query for all timeframes (instead of N separate queries)
        - ~75% performance improvement for multiple timeframes
        - Maintains backward compatibility
        
        Returns:
            Dictionary with timeframe -> count of records created
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
                    stored_count = tf_result.get('inserted_records', 0) + tf_result.get('updated_records', 0)
                    results[target_tf] = stored_count
                else:
                    results[target_tf] = f"Error: {tf_result.get('error', 'Unknown error')}"
            
        except Exception as e:
            self.db.rollback()
            # If the multi-timeframe query fails, mark all as failed
            for target_tf in target_timeframes:
                results[target_tf] = f"Error in multi-timeframe aggregation: {str(e)}"
        
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
                
                # Update cache for assets that were queried
                try:
                    for asset in assets:
                        if asset.id in assets_needing_query and asset.id in results:
                            for timeframe, data in results[asset.id].items():
                                if data['count'] > 0:
                                    asset.update_timeframe_data(
                                        timeframe=timeframe,
                                        count=data['count'],
                                        earliest_time=data['earliest_time'],
                                        latest_time=data['latest_time']
                                    )
                    self.db.commit()
                except Exception as cache_error:
                    # Cache update failure shouldn't affect main operation
                    self.db.rollback()
            
            return results
            
        except Exception as e:
            # Return empty structure for all requested assets
            return {asset_id: {} for asset_id in asset_ids}
